import streamlit as st
from fpdf import FPDF

# ----------------------------
# Helpers
# ----------------------------
def build_quote_pdf(
    length_ft, height_ft, gates, terrain, demo_old, old_concrete,
    posts, pickets, labor_hrs, demo_cost, total, per_ft
):
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

    pdf.cell(0, 8, f"Demo & Removal: {'Yes' if demo_old else 'No'}", ln=1)
    if demo_old:
        pdf.cell(0, 8, f"Old posts in concrete: {'Yes' if old_concrete else 'No'}", ln=1)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, f"Total Installed Price: ${total:,.2f}", ln=1)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Price per foot: ${per_ft:,.2f}/ft", ln=1)

    pdf.ln(4)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Posts: {posts} | Pickets: {pickets} | Labor: {labor_hrs:.1f} hrs", ln=1)
    if demo_old:
        pdf.cell(0, 7, f"Demo cost included: ${demo_cost:,.2f}", ln=1)

    # ---- FIX: Handle str vs bytes/bytearray safely ----
    out = pdf.output(dest="S")
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="Roberts Fence Estimator", layout="centered")
st.title("Roberts Residential, LLC. Fence Estimator")
st.caption("Dothan, AL")

# ----------------------------
# Inputs
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    length_ft = st.number_input("Fence Length (ft)", min_value=20, value=200, step=10)
    height_ft = st.number_input("Height (ft)", min_value=4, max_value=8, value=6)
    gates = st.number_input("Number of Gates", min_value=0, value=1, step=1)

with col2:
    terrain = st.selectbox("Terrain", ["Flat", "Sloped/Hilly", "Rocky"])
    demo_old = st.checkbox("Include Demo & Removal of Old Fence", value=True)
    old_concrete = st.checkbox("Old posts are in concrete", value=True) if demo_old else False

# Factors
terrain_factor = 1.0
soil_type = "normal"
if terrain == "Sloped/Hilly":
    terrain_factor = 1.25
elif terrain == "Rocky":
    terrain_factor = 1.5
    soil_type = "rocky"

# ----------------------------
# Calculate
# ----------------------------
if st.button("Calculate Quote", type="primary"):
    posts = int(length_ft / 8) + 1
    pickets = int(length_ft * 1.5)

    demo_cost = 0.0
    demo_hrs = 0.0
    if demo_old:
        demo_hrs = length_ft * 0.15
        if old_concrete:
            demo_hrs += posts * 2
        disposal_cost = 200.0
        demo_cost = (demo_hrs * 22) + disposal_cost

    labor_hrs = (length_ft * 0.25 * terrain_factor) + (gates * 2)
    if soil_type == "rocky":
        labor_hrs *= 1.3

    mat_cost = (
        (posts * 18.50) +
        (int(length_ft / 8) * 3 * 7.25) +
        (pickets * 4.50) +
        (posts * 2 * 6) +
        (gates * 350)
    )
    labor_cost = labor_hrs * 22
    subtotal = mat_cost + labor_cost + demo_cost
    total = round(subtotal * 1.40, 2)
    per_ft = round(total / length_ft, 2)

    # Display (escape $ in Streamlit Markdown)
    st.success(f"**Total Installed Price:** \\${total:,.2f} (\\${per_ft:,.2f}/ft)")
    st.write(f"Posts: {posts} | Pickets: {pickets} | Labor: {labor_hrs:.1f} hrs")
    if demo_old:
        st.info(f"Demo included: \\${demo_cost:,.2f}")

    # Build PDF and download
    pdf_bytes = build_quote_pdf(
        length_ft, height_ft, gates, terrain, demo_old, old_concrete,
        posts, pickets, labor_hrs, demo_cost, total, per_ft
    )

    st.download_button(
        label="📄 Download Professional Quote PDF",
        data=pdf_bytes,
        file_name="Roberts_Fence_Quote.pdf",
        mime="application/pdf",
    )  # downloads bytes to the user's browser [1](https://peerdh.com/blogs/programming-insights/streamlits-download-button-a-comprehensive-guide)

st.caption("Built for Roberts Residential LLC • Dothan, AL")
