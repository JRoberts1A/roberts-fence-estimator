import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="Roberts Fence Estimator", layout="centered")
st.title("🛠️ Roberts Residential Fence Estimator")
st.caption("Dothan, AL • Fast • Reliable • In-House Crew")

col1, col2 = st.columns(2)
with col1:
    length_ft = st.number_input("Fence Length (ft)", min_value=20, value=200, step=10)
    height_ft = st.number_input("Height (ft)", min_value=4, max_value=8, value=6)
    gates = st.number_input("Number of Gates", min_value=0, value=1, step=1)
with col2:
    terrain = st.selectbox("Terrain", ["Flat", "Sloped/Hilly", "Rocky"])
    demo_old = st.checkbox("Include Demo & Removal of Old Fence", value=True)
    old_concrete = st.checkbox("Old posts are in concrete", value=True) if demo_old else False

terrain_factor = 1.0
soil_type = "normal"
if terrain == "Sloped/Hilly": terrain_factor = 1.25
if terrain == "Rocky": 
    terrain_factor = 1.5
    soil_type = "rocky"

if st.button("Calculate Quote", type="primary"):
    posts = int(length_ft / 8) + 1
    pickets = int(length_ft * 1.5)
    demo_hrs = 0
    demo_cost = 0
    if demo_old:
        demo_hrs = length_ft * 0.15
        if old_concrete:
            demo_hrs += posts * 2
        disposal_cost = 200 * 1
        demo_cost = (demo_hrs * 22) + disposal_cost
    
    labor_hrs = (length_ft * 0.25 * terrain_factor) + (gates * 2)
    if soil_type == "rocky": labor_hrs *= 1.3
    mat_cost = (posts * 18.50) + (int(length_ft/8)*3*7.25) + (pickets*4.50) + (posts*2*6) + (gates*350)
    labor_cost = labor_hrs * 22
    subtotal = mat_cost + labor_cost + demo_cost
    total = round(subtotal * 1.40, 2)
    per_ft = round(total / length_ft, 2)

    st.success(f"**Total Installed Price: ${total:,.2f}  (${per_ft:,.2f}/ft)")
    st.write(f"Posts: {posts} | Pickets: {pickets} | Labor: {round(labor_hrs,1)} hrs")
    if demo_old: st.info(f"Demo included: ${round(demo_cost,2)}")

    if st.button("📄 Download Professional Quote PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Roberts Residential LLC Fence Quote", align="C")
        pdf.ln(20)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Length: {length_ft} ft | Price: ${total:,}", ln=1)
        pdf.cell(0, 10, f"Per foot: ${per_ft} | Includes full demo & disposal", ln=1)
        pdf.output("Roberts_Fence_Quote.pdf")
        st.success("PDF downloaded! Email it to the customer right from your phone.")


st.caption("Built for Roberts Residential LLC • Dothan, AL • Powered by your in-house crew")





