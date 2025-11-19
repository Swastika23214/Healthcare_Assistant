import sqlite3
import customtkinter as ctk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import datetime
from datetime import timedelta
from fpdf import FPDF
import os


STANDARD_VITALS = {
    "bp_systolic": {"min": 90, "max": 120, "unit": "mmHg", "name": "Blood Pressure (Systolic)", "color": "#E74C3C"},
    "bp_diastolic": {"min": 60, "max": 80, "unit": "mmHg", "name": "Blood Pressure (Diastolic)", "color": "#9B59B6"},
    "sugar": {"min": 70, "max": 140, "unit": "mg/dL", "name": "Blood Sugar", "color": "#3498DB"},
    "pulse": {"min": 60, "max": 100, "unit": "bpm", "name": "Pulse Rate", "color": "#E67E22"}
}


def get_vitals_data(user_id, period="weekly"):
    """
    Fetch vitals data from database for specified period
    period: 'weekly' or 'monthly'
    """
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    
    # Calculate date range
    today = datetime.date.today()
    if period == "weekly":
        start_date = today - timedelta(days=7)
    else:  # monthly
        start_date = today - timedelta(days=30)
    
    cur.execute("""
        SELECT date, bp_systolic, bp_diastolic, sugar, weight, pulse, sleep_hours
        FROM vitals
        WHERE user_id=? AND date >= ?
        ORDER BY date ASC
    """, (user_id, start_date.isoformat()))
    
    data = cur.fetchall()
    conn.close()
    
    return data


def analyze_vitals(data):
    """
    Analyze vitals data and compare with standards
    Returns analysis dictionary with averages and status
    """
    if not data:
        return None
    
    analysis = {
        "count": len(data),
        "vitals": {}
    }
    
    # Calculate averages and status for each vital
    vitals_columns = {
        "bp_systolic": 1,
        "bp_diastolic": 2,
        "sugar": 3,
        "weight": 4,
        "pulse": 5,
        "sleep_hours": 6
    }
    
    for vital_name, col_idx in vitals_columns.items():
        values = [row[col_idx] for row in data if row[col_idx] is not None]
        
        if values:
            avg_value = sum(values) / len(values)
            
            # Determine status
            if vital_name in STANDARD_VITALS:
                std = STANDARD_VITALS[vital_name]
                if avg_value < std["min"]:
                    status = "Low"
                    color = "orange"
                elif avg_value > std["max"]:
                    status = "High"
                    color = "red"
                else:
                    status = "Normal"
                    color = "green"
            else:
                status = "Recorded"
                color = "blue"
            
            analysis["vitals"][vital_name] = {
                "average": avg_value,
                "min": min(values),
                "max": max(values),
                "status": status,
                "color": color,
                "values": values,
                "dates": [row[0] for row in data if row[col_idx] is not None]
            }
    
    return analysis


def generate_report_pdf(user_id, user_name, period, analysis, save_path):
    """
    Generate PDF report with vitals analysis
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 10, "Health Vitals Report", ln=True, align="C")
        pdf.ln(5)
        
        # User Info
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"Patient Name: {user_name}", ln=True)
        pdf.cell(0, 8, f"Report Period: {period.capitalize()}", ln=True)
        pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.cell(0, 8, f"Total Records: {analysis['count']}", ln=True)
        pdf.ln(5)
        
        # Divider
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Vitals Summary
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Vitals Summary", ln=True)
        pdf.ln(3)
        
        for vital_name, vital_data in analysis["vitals"].items():
            if vital_name in STANDARD_VITALS:
                std = STANDARD_VITALS[vital_name]
                
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, std["name"], ln=True)
                
                pdf.set_font("Arial", "", 11)
                pdf.cell(0, 6, f"  Average: {vital_data['average']:.1f} {std['unit']}", ln=True)
                pdf.cell(0, 6, f"  Range: {vital_data['min']:.1f} - {vital_data['max']:.1f} {std['unit']}", ln=True)
                pdf.cell(0, 6, f"  Standard Range: {std['min']} - {std['max']} {std['unit']}", ln=True)
                
                # Status with color indicator
                status_text = f"  Status: {vital_data['status']}"
                if vital_data['status'] == "Normal":
                    pdf.set_text_color(0, 128, 0)  # Green
                elif vital_data['status'] == "High":
                    pdf.set_text_color(255, 0, 0)  # Red
                else:
                    pdf.set_text_color(255, 165, 0)  # Orange
                
                pdf.cell(0, 6, status_text, ln=True)
                pdf.set_text_color(0, 0, 0)  # Reset to black
                pdf.ln(3)
        
        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(128, 128, 128)
        pdf.multi_cell(0, 5, "Disclaimer: This report is for informational purposes only and should not be considered as medical advice. Please consult with a healthcare professional for proper diagnosis and treatment.")
        
        # Save PDF
        pdf.output(save_path)
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False


def create_vitals_graphs(analysis, period):
    """
    Create clear matplotlib line graphs for vitals comparison
    Returns figure object with improved visualization
    """
    # Only include vitals we want to plot (exclude sleep_hours and weight)
    vitals_to_plot = []
    for vital_name, vital_data in analysis["vitals"].items():
        if vital_name in STANDARD_VITALS:  # Only plot standard vitals
            vitals_to_plot.append((vital_name, vital_data))
    
    if not vitals_to_plot:
        return None
    
    # Create figure with subplots
    num_plots = len(vitals_to_plot)
    fig = Figure(figsize=(14, 10), facecolor='white')
    
    # Create 2x2 grid for 4 vitals
    rows = 2
    cols = 2
    
    for idx, (vital_name, vital_data) in enumerate(vitals_to_plot, 1):
        ax = fig.add_subplot(rows, cols, idx)
        std = STANDARD_VITALS[vital_name]
        
        # Get data
        dates = vital_data["dates"]
        values = vital_data["values"]
        
        if not dates or not values:
            continue
        
        # Convert dates to readable format
        date_labels = []
        for d in dates:
            if "-" in d:
                parts = d.split("-")
                if len(parts) == 3:
                    date_labels.append(f"{parts[1]}/{parts[2]}")
                else:
                    date_labels.append(d)
            else:
                date_labels.append(d)
        
        x_positions = range(len(values))
        
        # Plot standard range as shaded area (GREEN ZONE)
        ax.axhspan(std["min"], std["max"], alpha=0.2, color='green', label='Normal Range', zorder=1)
        
        # Plot user's actual values with line and markers
        ax.plot(x_positions, values, 
                marker='o', 
                linewidth=3, 
                markersize=8, 
                color=std["color"], 
                label='Your Values',
                zorder=3)
        
        # Plot average line
        ax.axhline(y=vital_data["average"], 
                   color='orange', 
                   linestyle='--', 
                   linewidth=2, 
                   alpha=0.8, 
                   label=f'Your Average: {vital_data["average"]:.1f}',
                   zorder=2)
        
        # Plot min and max standard lines
        ax.axhline(y=std["min"], color='green', linestyle=':', linewidth=1.5, alpha=0.6, zorder=2)
        ax.axhline(y=std["max"], color='green', linestyle=':', linewidth=1.5, alpha=0.6, zorder=2)
        
        # Add min/max text annotations
        ax.text(len(values)-0.5, std["min"], f'Min: {std["min"]}', 
                verticalalignment='bottom', horizontalalignment='right', 
                fontsize=9, color='green', weight='bold')
        ax.text(len(values)-0.5, std["max"], f'Max: {std["max"]}', 
                verticalalignment='top', horizontalalignment='right', 
                fontsize=9, color='green', weight='bold')
        
        # Styling
        ax.set_title(std["name"], fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.set_ylabel(f'{std["unit"]}', fontsize=11, fontweight='bold')
        
        # Set x-axis
        ax.set_xticks(x_positions)
        ax.set_xticklabels(date_labels, rotation=45, ha='right', fontsize=9)
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Legend
        ax.legend(fontsize=9, loc='upper left', framealpha=0.9)
        
        # Add status indicator
        status = vital_data["status"]
        status_color = {'Normal': 'green', 'High': 'red', 'Low': 'orange'}
        ax.text(0.98, 0.98, f'Status: {status}', 
                transform=ax.transAxes,
                fontsize=11, fontweight='bold',
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor=status_color.get(status, 'gray'), alpha=0.3))
        
        # Set y-axis limits with padding
        y_min = min(min(values), std["min"]) * 0.9
        y_max = max(max(values), std["max"]) * 1.1
        ax.set_ylim(y_min, y_max)
    
    # Overall title
    fig.suptitle(f'{period.capitalize()} Health Vitals Report - Comparison with Standards', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # Add description
    fig.text(0.5, 0.02, 
             '📊 Green shaded area = Normal/Healthy range | 🔴 Your line = Actual readings | 🟠 Dashed line = Your average',
             ha='center', fontsize=10, style='italic', color='gray')
    
    fig.tight_layout(rect=[0, 0.03, 1, 0.96])
    
    return fig


def report_generation_gui(user_id, user_name):
    """
    Main GUI for report generation
    """
    
    def generate_report(period):
        # Fetch data
        data = get_vitals_data(user_id, period)
        
        if not data:
            messagebox.showwarning(
                "No Data", 
                f"No vitals data found for the last {period} period.\n\nPlease add some vitals data first."
            )
            return
        
        # Analyze data
        analysis = analyze_vitals(data)
        
        # Show report window
        show_report_window(period, analysis)
    
    def show_report_window(period, analysis):
        report_win = ctk.CTkToplevel()
        report_win.title(f"{period.capitalize()} Vitals Report")
        screen_width = report_win.winfo_screenwidth()
        screen_height = report_win.winfo_screenheight()
        report_win.geometry(f"{screen_width}x{screen_height}")

        # Create notebook/tabs
        tab_view = ctk.CTkTabview(report_win, width=1150, height=720)
        tab_view.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Tab 1: Summary
        tab_view.add(" Summary")
        summary_frame = tab_view.tab(" Summary")
        create_summary_tab(summary_frame, period, analysis)
        
        # Tab 2: Graphs
        tab_view.add(" Visual Analysis")
        graph_frame = tab_view.tab(" Visual Analysis")
        create_graph_tab(graph_frame, analysis, period)
        
        # Download button
        button_frame = ctk.CTkFrame(report_win, fg_color="transparent")
        button_frame.pack(pady=10)
        
        def download_report():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"health_report_{period}_{datetime.date.today()}.pdf"
            )
            
            if file_path:
                success = generate_report_pdf(user_id, user_name, period, analysis, file_path)
                if success:
                    messagebox.showinfo("Success", f"Report saved successfully!\n\n{file_path}")
                else:
                    messagebox.showerror("Error", "Failed to generate PDF report.")
        
        ctk.CTkButton(
            button_frame,
            text=" Download Report (PDF)",
            command=download_report,
            width=200,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#4CAF50",
            hover_color="#45a049"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="Close",
            command=report_win.destroy,
            width=150,
            height=40
        ).pack(side="left", padx=10)
    
    def create_summary_tab(parent, period, analysis):
        scroll_frame = ctk.CTkScrollableFrame(parent, width=1100, height=650)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Header
        ctk.CTkLabel(
            scroll_frame,
            text=f"🏥 {period.capitalize()} Health Report",
            font=("Arial", 22, "bold")
        ).pack(pady=15)
        
        ctk.CTkLabel(
            scroll_frame,
            text=f"Patient: {user_name} | Total Records: {analysis['count']}",
            font=("Arial", 14)
        ).pack(pady=5)
        
        # Vitals Cards (excluding sleep_hours)
        for vital_name, vital_data in analysis["vitals"].items():
            if vital_name in STANDARD_VITALS:  # Only show standard vitals
                create_vital_card(scroll_frame, vital_name, vital_data)
    
    def create_vital_card(parent, vital_name, vital_data):
        std = STANDARD_VITALS[vital_name]
        
        # Card frame
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(pady=10, padx=20, fill="x")
        
        # Header
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text=std["name"],
            font=("Arial", 18, "bold")
        ).pack(side="left")
        
        # Status badge
        status_colors = {"Normal": "#4CAF50", "High": "#F44336", "Low": "#FF9800"}
        status_frame = ctk.CTkFrame(
            header_frame,
            fg_color=status_colors.get(vital_data["status"], "#2196F3"),
            corner_radius=15
        )
        status_frame.pack(side="right")
        
        ctk.CTkLabel(
            status_frame,
            text=vital_data["status"],
            font=("Arial", 12, "bold"),
            text_color="white"
        ).pack(padx=15, pady=5)
        
        # Content
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=10)
        
        # Left column - Your values
        left_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            left_col,
            text="Your Statistics:",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", pady=5)
        
        ctk.CTkLabel(
            left_col,
            text=f"Average: {vital_data['average']:.1f} {std['unit']}",
            font=("Arial", 13)
        ).pack(anchor="w", pady=2)
        
        ctk.CTkLabel(
            left_col,
            text=f"Minimum: {vital_data['min']:.1f} {std['unit']}",
            font=("Arial", 13)
        ).pack(anchor="w", pady=2)
        
        ctk.CTkLabel(
            left_col,
            text=f"Maximum: {vital_data['max']:.1f} {std['unit']}",
            font=("Arial", 13)
        ).pack(anchor="w", pady=2)
        
        # Right column - Standard values
        right_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True)
        
        ctk.CTkLabel(
            right_col,
            text="Standard Range:",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", pady=5)
        
        ctk.CTkLabel(
            right_col,
            text=f"Normal: {std['min']} - {std['max']} {std['unit']}",
            font=("Arial", 13),
            text_color="#4CAF50"
        ).pack(anchor="w", pady=2)
        
        # Recommendation
        if vital_data["status"] != "Normal":
            recommendation = get_recommendation(vital_name, vital_data["status"])
            rec_frame = ctk.CTkFrame(card, fg_color="#FFF3CD", corner_radius=8)
            rec_frame.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(
                rec_frame,
                text="⚠️ Recommendation:",
                font=("Arial", 12, "bold"),
                text_color="#856404"
            ).pack(anchor="w", padx=10, pady=5)
            
            ctk.CTkLabel(
                rec_frame,
                text=recommendation,
                font=("Arial", 11),
                text_color="#856404",
                wraplength=1000,
                justify="left"
            ).pack(anchor="w", padx=10, pady=5)
    
    def get_recommendation(vital_name, status):
        recommendations = {
            "bp_systolic": {
                "High": "Your blood pressure is elevated. Consider reducing salt intake, exercising regularly, and managing stress. Consult a doctor if it persists.",
                "Low": "Your blood pressure is low. Stay hydrated, avoid sudden position changes, and eat regular meals. Consult a doctor if you feel dizzy."
            },
            "bp_diastolic": {
                "High": "Your diastolic pressure is high. Monitor it regularly and consult a healthcare provider for proper management.",
                "Low": "Your diastolic pressure is low. Ensure adequate hydration and consult a doctor if symptoms occur."
            },
            "sugar": {
                "High": "Your blood sugar is elevated. Limit sugary foods, increase physical activity, and monitor regularly. Consult a doctor for diabetes screening.",
                "Low": "Your blood sugar is low. Eat regular meals with complex carbohydrates. Keep quick sugar sources handy if you're diabetic."
            },
            "pulse": {
                "High": "Your pulse rate is elevated. Rest adequately, manage stress, and avoid excessive caffeine. Consult a doctor if it continues.",
                "Low": "Your pulse rate is low. If you're not an athlete and feel dizzy or weak, consult a healthcare provider."
            }
        }
        
        return recommendations.get(vital_name, {}).get(status, "Maintain healthy lifestyle habits and regular check-ups.")
    
    def create_graph_tab(parent, analysis, period):
        # Info label at top
        info_frame = ctk.CTkFrame(parent, fg_color="#E8F5E9", corner_radius=10)
        info_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            info_frame,
            text=" How to read the graphs:",
            font=("Arial", 13, "bold")
        ).pack(anchor="w", padx=15, pady=5)
        
        ctk.CTkLabel(
            info_frame,
            text="• Green shaded area = Normal/Healthy range for that vital\n• Colored line with dots = Your actual readings over time\n• Orange dashed line = Your average value\n• Your readings should ideally stay within the green zone",
            font=("Arial", 11),
            justify="left"
        ).pack(anchor="w", padx=15, pady=5)
        
        # Create matplotlib figure
        fig = create_vitals_graphs(analysis, period)
        
        if fig:
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        else:
            ctk.CTkLabel(
                parent,
                text="No graph data available",
                font=("Arial", 14)
            ).pack(pady=50)
    
    # Main window
    win = ctk.CTkToplevel()
    win.title("Health Report Generator")
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    win.geometry(f"{screen_width}x{screen_height}")

    ctk.CTkLabel(
        win,
        text=" Generate Health Report",
        font=("Arial", 22, "bold")
    ).pack(pady=20)
    
    ctk.CTkLabel(
        win,
        text="Select the report period to generate vitals analysis",
        font=("Arial", 14)
    ).pack(pady=10)
    
    # Report period buttons
    button_frame = ctk.CTkFrame(win, fg_color="transparent")
    button_frame.pack(pady=30)
    
    ctk.CTkButton(
        button_frame,
        text=" Weekly Report\n(Last 7 Days)",
        command=lambda: generate_report("weekly"),
        width=200,
        height=80,
        font=("Arial", 14, "bold"),
        fg_color="#2196F3",
        hover_color="#1976D2"
    ).pack(pady=10)
    
    ctk.CTkButton(
        button_frame,
        text=" Monthly Report\n(Last 30 Days)",
        command=lambda: generate_report("monthly"),
        width=200,
        height=80,
        font=("Arial", 14, "bold"),
        fg_color="#9C27B0",
        hover_color="#7B1FA2"
    ).pack(pady=10)
    
    ctk.CTkLabel(
        win,
        text=" Make sure you have entered vitals data first",
        font=("Arial", 11),
        text_color="gray"
    ).pack(pady=10)
