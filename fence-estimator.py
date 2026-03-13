import streamlit as st
from fpdf import FPDF

# ----------------------------
# Helpers
# ----------------------------
def build_quote_pdf(length_ft, height_ft, gates, terrain, demo_old, old_concrete,
                    posts, pickets, labor_hrs, demo_cost, total, per_ft):
    pdf = FPDF()
    pdf.add_page()

    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Roberts Residential LLC Fence Quote", align="C", ln=1)
    pdf.ln(6)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Fence Length: {length_ft} ft", ln=1)
    pdf.cell(0, 8, f"Fence Height: {height_ft} ft", ln=1)
    pdf.cell(0, 8, f"Gates: {gates}", ln=1)
    pdf.cell(0, 8, f"Terrain: {terrain}", ln=1)

    demo_text = "Yes" if demo_old else "No"
    pdf.cell(0, 8, f"Demo & Removal: {demo_text}", ln=1)
    if demo_old: pdf.cell(0, 8, f"Old posts in concrete: {'Yes' if old_concrete else 'No'}", ln=1)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, f"Total Installed Price: ${total:,.2f}", ln=1)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Price per foot: ${per_ft:,.2f}/ft", ln=1)
    pdf.ln(4)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Posts: {posts} | Pickets: {pickets} | Labor: {labor_hrs:.1f} hrs", ln=1)
    if demo_old:
