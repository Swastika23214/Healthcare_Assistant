import os
import csv
import customtkinter as ctk
from tkinter import messagebox
from database import save_symptom_check, get_symptom_history
import sqlite3
from datetime import datetime
import pandas as pd
import numpy as np
import re

# Global variables to store cleaned data
symptom_disease_data = {}
disease_descriptions = {}
disease_precautions = {}

def normalize_symptom(symptom):
    """Normalize symptom names for matching"""
    if not symptom or pd.isna(symptom):
        return ""
    return symptom.strip().lower().replace(" ", "_").replace("-", "_")

def normalize_disease_name(disease):
    """Normalize disease names for consistency"""
    if not disease or pd.isna(disease):
        return ""
    return disease.strip().title()

def clean_and_load_data():
    """Clean and load the dataset in memory"""
    global symptom_disease_data, disease_descriptions, disease_precautions
    
    # Load main symptom-disease dataset
    symptom_file = "symptom_data/dataset.csv"
    if not os.path.exists(symptom_file):
        print(f"Error: Dataset file not found at {symptom_file}")
        return
    
    try:
        # Read the dataset using pandas for easier cleaning
        df = pd.read_csv(symptom_file)
        
        # Remove rows with missing disease names
        df = df.dropna(subset=['Disease'])
        
        # Normalize disease names
        df['Disease'] = df['Disease'].apply(normalize_disease_name)
        
        # Process symptom columns
        for i in range(1, 18):  # symptom_1 to symptom_17
            symptom_col = f"Symptom_{i}"
            if symptom_col in df.columns:
                # Normalize symptom names
                df[symptom_col] = df[symptom_col].apply(normalize_symptom)
        
        # Create symptom-disease mapping
        for _, row in df.iterrows():
            disease = row['Disease']
            symptoms = []
            
            for i in range(1, 18):
                symptom_col = f"Symptom_{i}"
                symptom = row[symptom_col]
                if symptom and not pd.isna(symptom):
                    symptoms.append(symptom)
            
            if symptoms:
                symptom_disease_data[disease] = symptoms
        
        # Add basic descriptions for diseases that don't have them
        for disease in symptom_disease_data.keys():
            if disease not in disease_descriptions:
                disease_descriptions[disease] = f"A medical condition characterized by symptoms such as {', '.join(symptom_disease_data[disease][:3])}."
        
        # Add basic precautions for diseases that don't have them
        for disease in symptom_disease_data.keys():
            if disease not in disease_precautions:
                disease_precautions[disease] = [
                    "Consult a healthcare professional for proper diagnosis",
                    "Follow prescribed treatment plan",
                    "Get adequate rest",
                    "Maintain a healthy lifestyle"
                ]
        
        print(f"Successfully loaded {len(symptom_disease_data)} diseases with symptoms")
        print(f"Added descriptions for {len(disease_descriptions)} diseases")
        print(f"Added precautions for {len(disease_precautions)} diseases")
        
    except Exception as e:
        print(f"Error loading and cleaning dataset: {e}")

def match_symptoms_to_diseases(user_symptoms):
    """
    Match user symptoms to potential diseases
    Returns list of (disease, match_percentage, matched_symptoms_count)
    """
    user_symptoms_normalized = [normalize_symptom(s) for s in user_symptoms]
    matches = []
    
    for disease, disease_symptoms in symptom_disease_data.items():
        matched = sum(1 for s in user_symptoms_normalized if s in disease_symptoms)
        if matched > 0:
            match_percentage = (matched / len(user_symptoms_normalized)) * 100
            matches.append((disease, match_percentage, matched))
    
    # Sort by match percentage (descending) and number of matched symptoms
    matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
    return matches

def symptom_checker_gui(user_id):
    """Main GUI for symptom checker"""
    
    def check_symptoms():
        symptoms_input = symptom_entry.get("1.0", "end-1c").strip()
        
        if not symptoms_input:
            messagebox.showerror("Error", "Please enter at least one symptom.")
            return
        
        # Parse symptoms (comma or newline separated)
        user_symptoms = [s.strip() for s in symptoms_input.replace("\n", ",").split(",") if s.strip()]
        
        if not user_symptoms:
            messagebox.showerror("Error", "Please enter valid symptoms.")
            return
        
        # Match symptoms
        matches = match_symptoms_to_diseases(user_symptoms)
        
        if not matches:
            messagebox.showinfo("No Match", "No diseases found matching your symptoms.\n\nPlease consult a healthcare professional.")
            return
        
        # Save to database
        save_symptom_check(user_id, user_symptoms, matches)
        
        # Show results
        show_results(user_symptoms, matches)
    
    def show_results(symptoms, matches):
        result_win = ctk.CTkToplevel()
        result_win.title("Symptom Check Results")
        screen_width =  result_win .winfo_screenwidth()
        screen_height =  result_win .winfo_screenheight()
        result_win.geometry(f"{screen_width}x{screen_height}")
        
        # Header
        ctk.CTkLabel(
            result_win, 
            text="🩺 Symptom Analysis Results", 
            font=("Arial", 20, "bold")
        ).pack(pady=15)
        
        ctk.CTkLabel(
            result_win, 
            text=f"Symptoms entered: {', '.join(symptoms)}", 
            font=("Arial", 12),
            wraplength=550
        ).pack(pady=5, padx=10)
        
        # Scrollable frame for results
        scroll_frame = ctk.CTkScrollableFrame(result_win, width=550, height=500)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Show top 5 matches
        top_matches = matches[:5]
        
        for idx, (disease, match_percent, matched_count) in enumerate(top_matches, 1):
            # Disease frame
            disease_frame = ctk.CTkFrame(scroll_frame)
            disease_frame.pack(pady=10, padx=5, fill="x")
            
            # Disease name and match percentage
            ctk.CTkLabel(
                disease_frame,
                text=f"{idx}. {disease}",
                font=("Arial", 16, "bold")
            ).pack(anchor="w", padx=10, pady=5)
            
            ctk.CTkLabel(
                disease_frame,
                text=f"Match: {match_percent:.0f}% ({matched_count}/{len(symptoms)} symptoms)",
                font=("Arial", 12),
                text_color="green" if match_percent >= 70 else "orange"
            ).pack(anchor="w", padx=10)
            
            # Description
            if disease in disease_descriptions:
                ctk.CTkLabel(
                    disease_frame,
                    text=f"Description: {disease_descriptions[disease]}",
                    font=("Arial", 11),
                    wraplength=500,
                    justify="left"
                ).pack(anchor="w", padx=10, pady=5)
            
            # Precautions
            if disease in disease_precautions:
                precautions_text = "Precautions:\n" + "\n".join(
                    [f"• {p}" for p in disease_precautions[disease]]
                )
                ctk.CTkLabel(
                    disease_frame,
                    text=precautions_text,
                    font=("Arial", 11),
                    wraplength=500,
                    justify="left",
                    text_color="#4A90E2"
                ).pack(anchor="w", padx=10, pady=5)
        
        # Disclaimer
        disclaimer_frame = ctk.CTkFrame(result_win, fg_color="red", corner_radius=10)
        disclaimer_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(
            disclaimer_frame,
            text=" IMPORTANT DISCLAIMER",
            font=("Arial", 14, "bold"),
            text_color="white"
        ).pack(pady=5)
        
        ctk.CTkLabel(
            disclaimer_frame,
            text="This is NOT a medical diagnosis. Please consult a qualified healthcare\nprofessional for proper diagnosis and treatment.",
            font=("Arial", 11),
            text_color="white",
            justify="center"
        ).pack(pady=5, padx=10)
        
        ctk.CTkButton(
            result_win, 
            text="Close", 
            command=result_win.destroy,
            width=200
        ).pack(pady=10)
    
    # Main window
    win = ctk.CTkToplevel()
    win.title("Symptom Checker")
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    win.geometry(f"{screen_width}x{screen_height}")

    
    ctk.CTkLabel(
        win, 
        text=" Symptom Checker", 
        font=("Arial", 20, "bold")
    ).pack(pady=15)
    
    ctk.CTkLabel(
        win, 
        text="Enter your symptoms (separated by commas or new lines)", 
        font=("Arial", 14)
    ).pack(pady=10)
    
    ctk.CTkLabel(
        win, 
        text="Examples: fever, headache, cough, fatigue", 
        font=("Arial", 11),
        text_color="gray"
    ).pack(pady=5)
    
    # Text box for symptoms
    symptom_entry = ctk.CTkTextbox(win, width=480, height=150, font=("Arial", 13))
    symptom_entry.pack(pady=10, padx=20)
    
    # Buttons
    button_frame = ctk.CTkFrame(win, fg_color="transparent")
    button_frame.pack(pady=15)
    
    ctk.CTkButton(
        button_frame, 
        text="Check Symptoms", 
        command=check_symptoms,
        width=180,
        height=40,
        font=("Arial", 14, "bold")
    ).pack(side="left", padx=10)
    
    ctk.CTkButton(
        button_frame, 
        text="View History", 
        command=lambda: view_history(user_id),
        width=180,
        height=40
    ).pack(side="left", padx=10)
    
    # Info label
    ctk.CTkLabel(
        win, 
        text=" Tip: Be as specific as possible with your symptoms",
        font=("Arial", 10),
        text_color="gray"
    ).pack(pady=5)

def view_history(user_id):
    """View symptom check history"""
    history_win = ctk.CTkToplevel()
    history_win.title("Symptom Check History")
    history_win.geometry("600x600")
    
    ctk.CTkLabel(
        history_win, 
        text=" Your Symptom Check History", 
        font=("Arial", 18, "bold")
    ).pack(pady=15)
    
    scroll_frame = ctk.CTkScrollableFrame(history_win, width=550, height=380)
    scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)
    
    records = get_symptom_history(user_id)
        
    if not records:
        ctk.CTkLabel(
            scroll_frame, 
            text="No symptom checks recorded yet.",
            font=("Arial", 14)
        ).pack(pady=20)
    else:
        for date, symptoms, diseases in records:
            record_frame = ctk.CTkFrame(scroll_frame)
            record_frame.pack(pady=8, padx=5, fill="x")
                
            ctk.CTkLabel(
                record_frame,
                text=f"Date: {date}",
                font=("Arial", 12, "bold")
            ).pack(anchor="w", padx=10, pady=3)
                
            ctk.CTkLabel(
                record_frame,
                text=f"Symptoms: {symptoms}",
                font=("Arial", 11),
                wraplength=500,
                justify="left"
            ).pack(anchor="w", padx=10, pady=2)
                
            ctk.CTkLabel(
                record_frame,
                text=f"Top Results: {diseases}",
                font=("Arial", 11),
                wraplength=500,
                justify="left",
                text_color="#4A90E2"
            ).pack(anchor="w", padx=10, pady=3)
    
    ctk.CTkButton(
        history_win, 
        text="Close", 
        command=history_win.destroy
    ).pack(pady=10)

# Initialize the application by cleaning and loading data
# Create symptom_data directory if it doesn't exist
if not os.path.exists("symptom_data"):
    os.makedirs("symptom_data")

# Clean and load the data when module is imported
clean_and_load_data()
