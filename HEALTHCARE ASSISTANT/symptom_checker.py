import os
import csv
import customtkinter as ctk
from tkinter import messagebox
from database import save_symptom_check, get_symptom_history
import sqlite3
from datetime import datetime


# Load symptom-disease dataset

symptom_disease_data = {}
disease_descriptions = {}
disease_precautions = {}

def normalize_symptom(symptom):
    """Normalize symptom names for matching"""
    return symptom.strip().lower().replace(" ", "_").replace("-", "_")

def load_symptom_dataset():
    """
    Load symptom checker datasets from CSV files
    Expected CSV format for symptoms:
    - disease, symptom_1, symptom_2, ..., symptom_17
    
    Expected CSV for descriptions:
    - Disease, Description
    
    Expected CSV for precautions:
    - Disease, Precaution_1, Precaution_2, Precaution_3, Precaution_4
    """
    
    # Load main symptom-disease mapping
    symptom_file = "symptom_data/dataset.csv"
    if os.path.exists(symptom_file):
        try:
            with open(symptom_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    disease = row.get("Disease", "").strip()
                    if not disease:
                        continue
                    
                    symptoms = []
                    for i in range(1, 18):  # symptom_1 to symptom_17
                        symptom_col = f"Symptom_{i}"
                        symptom = row.get(symptom_col, "").strip()
                        if symptom:
                            symptoms.append(normalize_symptom(symptom))
                    
                    if symptoms:
                        symptom_disease_data[disease] = symptoms
        except Exception as e:
            print(f"Error loading symptom dataset: {e}")
    
    # Load disease descriptions
    desc_file = "symptom_data/symptom_Description.csv"
    if os.path.exists(desc_file):
        try:
            with open(desc_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    disease = row.get("Disease", "").strip()
                    description = row.get("Description", "").strip()
                    if disease and description:
                        disease_descriptions[disease] = description
        except Exception as e:
            print(f"Error loading descriptions: {e}")
    
    # Load disease precautions
    precaution_file = "symptom_data/symptom_precaution.csv"
    if os.path.exists(precaution_file):
        try:
            with open(precaution_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    disease = row.get("Disease", "").strip()
                    if not disease:
                        continue
                    
                    precautions = []
                    for i in range(1, 5):  # Precaution_1 to Precaution_4
                        precaution = row.get(f"Precaution_{i}", "").strip()
                        if precaution:
                            precautions.append(precaution)
                    
                    if precautions:
                        disease_precautions[disease] = precautions
        except Exception as e:
            print(f"Error loading precautions: {e}")

# Load datasets on module import
load_symptom_dataset()


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
        result_win.geometry("600x700")
        
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
    win.geometry("550x450")
    
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
    history_win.geometry("600x500")
    
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