import os
import math
import streamlit as st
from fpdf import FPDF

# ----------------------------
# Logo + Contact (repo-root filenames per your screenshot)
# ----------------------------
LOGO_APP_PATH = "FullLogo_NoBuffer.jpg"
LOGO_PDF_PATH = "FullLogo_Buffer.jpg"

PHONE_TEXT = "Phone: 706-570-6569"
EMAIL_TEXT = "Email: joe@roberts-residential.com"

PAGE_ICON = LOGO_APP_PATH if os.path.exists(LOGO_APP_PATH) else "🧰"

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(
    page_title="Roberts Fence Estimator",
    page_icon=PAGE_ICON,   # page_icon supports image paths or emojis [3](https://github.com/streamlit/streamlit/issues/11370)
    layout="centered"
)
st.title("Roberts Residential, LLC. Fence Estimator")
st.caption("Dothan, AL")

# Center logo in the app UI
if os.path.exists(LOGO_APP_PATH):
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        st.image(LOGO_APP_PATH, use_container_width=True)

# ----------------------------
# Helpers
# ----------------------------
def ceil_qty(x: float) -> int:
    return int(math.ceil(x))

def apply_waste_qty(qty: float, waste_pct: float) -> int:
    return ceil_qty(qty * (1.0 + waste_pct))

def pickets_per_ft_from_width_gap(picket_width_in: float, gap_in: float) -> float:
    return 12.0 / (picket_width_in + gap_in)

def money_md(x: float) -> str:
    # Escape $ so Streamlit markdown doesn't treat it as math mode
    return f"\\${x:,.2f}"

def build_quote_pdf(quote: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    # --- PDF Header: centered logo + phone + email (each on its own line) ---
    top_y = 8
    if os.path.exists(LOGO_PDF_PATH):
        logo_w_mm = 75  # adjust 60–90 if you want bigger/smaller
        x = (pdf.w - logo_w_mm) / 2.0
        pdf.image(LOGO_PDF_PATH, x=x, y=top_y, w=logo_w_mm)
        pdf.set_y(top_y + 52)  # push content below the logo
    else:
        pdf.set_y(16)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, PHONE_TEXT, ln=1, align="C")
    pdf.cell(0, 6, EMAIL_TEXT, ln=1, align="C")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Roberts Residential LLC Fence Quote", align="C", ln=1)
    pdf.ln(6)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Fence Length: {quote['length_ft']} ft", ln=1)
    pdf.cell(0, 8, f"Fence Height: {quote['height_ft']} ft", ln=1)
    pdf.cell(0, 8, f"Gates: {quote['gates']}", ln=1)
    pdf.cell(0, 8, f"Terrain: {quote['terrain']}", ln=1)
    pdf.cell(0, 8, f"Demo & Removal: {'Yes' if quote['demo_old'] else 'No'}", ln=1)
    if quote["demo_old"]:
        pdf.cell(0, 8, f"Old posts in concrete: {'Yes' if quote['old_concrete'] else 'No'}", ln=1)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, f"Total Installed Price: ${quote['total']:,.2f}", ln=1)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Price per foot: ${quote['per_ft']:,.2f}/ft", ln=1)

    pdf.ln(4)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Posts: {quote['posts_w']} | Rails: {quote['rails_w']} | Pickets: {quote['pickets_w']}", ln=1)
    pdf.cell(0, 7, f"Concrete bags: {quote['bags_w']} | Labor: {quote['labor_hrs']:.1f} hrs @ ${quote['labor_rate']:,.2f}/hr", ln=1)

    if quote["rental_sell"] > 0:
        pdf.cell(0, 7, f"Rentals/Disposal: ${quote['rental_sell']:,.2f}", ln=1)

    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        0, 6,
        "Near-privacy wood fences may show small gaps over time due to shrinkage/seasonal movement."
    )

    # FPDF output may be str (pyfpdf) or bytes/bytearray (fpdf2). Handle both.
    out = pdf.output(dest="S")
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)

# ----------------------------
# Sidebar: assumptions
# ----------------------------
with st.sidebar:
    st.header("Assumptions")

    labor_rate = st.number_input("All-in Billable Labor Rate ($/hr)", min_value=1.0, value=65.0, step=1.0)
    waste_pct = st.slider("Waste % (materials/consumables)", 0, 25, 10) / 100.0

    st.subheader("Production")
    base_install_hr_per_ft_6 = st.number_input("Install hrs/ft (6 ft)", min_value=0.05, value=0.22, step=0.01)
    height_8_multiplier = st.number_input("8 ft labor multiplier", min_value=1.00, value=1.15, step=0.05)
    gate_labor_hrs_each = st.number_input("Gate labor add (hrs per gate)", min_value=0.0, value=3.0, step=0.5)

    demo_hr_per_ft = st.number_input("Demo base (hrs/ft)", min_value=0.0, value=0.12, step=0.01)
    concrete_post_extra_hr = st.number_input("Concrete post extra (hrs/post)", min_value=0.0, value=0.75, step=0.05)

    st.subheader("Terrain factors")
    terrain_factors = {
        "Flat": st.number_input("Flat factor", min_value=0.5, value=1.00, step=0.05),
        "Sloped/Hilly": st.number_input("Sloped/Hilly factor", min_value=0.5, value=1.25, step=0.05),
        "Rocky": st.number_input("Rocky factor", min_value=0.5, value=1.50, step=0.05),
    }

    st.subheader("Pricing (materials/rentals only)")
    mat_markup = st.number_input("Materials markup (1.15 = 15%)", min_value=1.0, value=1.15, step=0.01)
    rental_markup = st.number_input("Rentals/Disposal handling (1.10 = 10%)", min_value=1.0, value=1.10, step=0.01)

    st.subheader("Unit costs")
    post_cost = st.number_input("Post cost ($ each)", min_value=0.0, value=18.50, step=0.25)
    rail_cost = st.number_input("Rail/stringer cost ($ each)", min_value=0.0, value=7.25, step=0.25)
    picket_cost = st.number_input("Dog-ear picket cost ($ each)", min_value=0.0, value=3.98, step=0.05)
    concrete_bag_cost = st.number_input("Concrete bag (50-lb) cost ($)", min_value=0.0, value=4.38, step=0.05)
    gate_hw_cost = st.number_input("Gate hardware kit cost ($ each)", min_value=0.0, value=37.98, step=0.50)
    base_bracket_cost = st.number_input("Post base/bracket cost ($ each)", min_value=0.0, value=14.78, step=0.25)

    st.subheader("Consumables (includes nails/fasteners)")
    include_consumables = st.checkbox("Include consumables allowance", value=True)
    consumables_per_ft = st.number_input("Consumables allowance ($/ft)", min_value=0.0, value=0.30, step=0.05)

# ----------------------------
# Main form (ALL widgets + SUBMIT inside form)
# ----------------------------
with st.form("quote_form"):
    col1, col2 = st.columns(2)

    with col1:
        length_ft = st.number_input("Fence Length (ft)", min_value=20, value=200, step=10)
        height_ft = st.selectbox("Fence Height (ft)", [6, 8], index=0)
        gates = st.number_input("Number of Gates", min_value=0, value=1, step=1)

    with col2:
        terrain = st.selectbox("Terrain", ["Flat", "Sloped/Hilly", "Rocky"])
        demo_old = st.checkbox("Include Demo & Removal of Old Fence", value=True)
        old_concrete = st.checkbox("Old posts are in concrete", value=True) if demo_old else False

    st.markdown("### Near-Privacy Takeoff")
