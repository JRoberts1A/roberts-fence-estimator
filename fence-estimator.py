import math
import streamlit as st
from fpdf import FPDF

# ----------------------------
# Page setup (keep this at the top)
# ----------------------------
st.set_page_config(page_title="Roberts Fence Estimator", layout="centered")  # [2](https://github.com/streamlit/streamlit/issues/10911)
st.title("Roberts Residential, LLC. Fence Estimator")
st.caption("Dothan, AL")

# ----------------------------
# Helpers
# ----------------------------
WASTE_DEFAULT = 0.10  # 10% waste

def ceil_qty(x: float) -> int:
    return int(math.ceil(x))

def apply_waste_qty(qty: float, waste_pct: float) -> int:
    return ceil_qty(qty * (1.0 + waste_pct))

def pickets_per_ft_from_width_gap(picket_width_in: float, gap_in: float) -> float:
    # pickets per ft = 12 / (width + gap)
    return 12.0 / (picket_width_in + gap_in)

def money(x: float) -> str:
    # For Streamlit Markdown strings, escape $ to avoid math-mode rendering.
    return f"\\${x:,.2f}"

def build_quote_pdf(quote: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Roberts Residential LLC Fence Quote", align="C", ln=1)
    pdf.ln(6)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Fence Length: {quote['length_ft']} ft", ln=1)
    pdf.cell(0, 8, f"Fence Height: {quote['height_ft']} ft", ln=1)
    pdf.cell(0, 8, f"Gates: {quote['gates']}", ln=1)
    pdf.cell(0, 8, f"Terrain: {quote['terrain']}", ln=1)
    pdf.cell(0, 8, f"Near privacy: {quote['near_privacy_desc']}", ln=1)
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
    pdf.cell(0, 7, f"Posts: {quote['posts_w']}  |  Rails: {quote['rails_w']}  |  Pickets: {quote['pickets_w']}", ln=1)
    pdf.cell(0, 7, f"Labor hours: {quote['labor_hrs']:.1f}  @  ${quote['labor_rate']:,.2f}/hr", ln=1)

    if quote["demo_old"]:
        pdf.cell(0, 7, f"Demo hours included: {quote['demo_hrs']:.1f}", ln=1)

    if quote["rental_total"] > 0:
        pdf.cell(0, 7, f"Rentals/Disposal: ${quote['rental_sell']:,.2f}", ln=1)

    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        0, 6,
        "Notes: Near-privacy wood fences may show small gaps over time due to shrinkage/seasonal movement. "
        "Pricing includes standard installation based on the inputs above."
    )

    # FPDF output can be str (pyfpdf) or bytes/bytearray (fpdf2). Handle both safely.
    out = pdf.output(dest="S")
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)


# ----------------------------
# Sidebar: Assumptions (easy tuning)
# ----------------------------
with st.sidebar:
    st.header("Assumptions")

    st.subheader("Labor (billable)")
    labor_rate = st.number_input("All-in Billable Labor Rate ($/hr)", min_value=1.0, value=65.0, step=1.0)

    st.subheader("Waste")
    waste_pct = st.slider("Waste % (materials/consumables)", 0, 25, int(WASTE_DEFAULT * 100)) / 100.0

    st.subheader("Production")
    base_install_hr_per_ft_6 = st.number_input("Install hrs/ft (6 ft fence)", min_value=0.05, value=0.22, step=0.01)
    height_8_multiplier = st.number_input("8 ft labor multiplier", min_value=1.00, value=1.15, step=0.05)
    gate_labor_hrs_each = st.number_input("Gate labor add (hrs per gate)", min_value=0.0, value=3.0, step=0.5)

    demo_hr_per_ft = st.number_input("Demo base (hrs/ft)", min_value=0.0, value=0.12, step=0.01)
    concrete_post_extra_hr = st.number_input("Concrete post extra (hrs/post)", min_value=0.0, value=0.75, step=0.05)

    st.subheader("Terrain factors")
    terrain_flat = st.number_input("Flat factor", min_value=0.5, value=1.00, step=0.05)
    terrain_slope = st.number_input("Sloped/Hilly factor", min_value=0.5, value=1.25, step=0.05)
    terrain_rocky = st.number_input("Rocky factor", min_value=0.5, value=1.50, step=0.05)

    st.subheader("Pricing (materials/rentals only)")
    mat_markup = st.number_input("Materials markup (e.g., 1.15 = 15%)", min_value=1.0, value=1.15, step=0.01)
    rental_markup = st.number_input("Rentals/Disposal handling (e.g., 1.10)", min_value=1.0, value=1.10, step=0.01)

    st.subheader("Unit costs (editable)")
    # Defaults include values you previously used + the screenshot examples you shared.
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
# Main inputs (use a form to avoid rerun weirdness)
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

    st.markdown("### Concrete / Pier Options")
    pier_option = st.selectbox(
        "Concrete option",
        [
            "Standard (2 bags per post)",
            "Heavy gate post piers (4 bags per gate post)",
            "Heavy piers all posts (3 bags per post)",
            "Bracket/base on pier (adds post bases)",
        ],
        index=0
    )

    st.markdown("### Near-Privacy Picket Takeoff")
    picket_width_in = st.number_input("Picket width (inches, actual)", min_value=4.0, value=5.5, step=0.1)
