import math
from pathlib import Path

import streamlit as st
from fpdf import FPDF

# ============================================================
# Branding / Files (repo-root)
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
LOGO_APP_PATH = BASE_DIR / "FullLogo_NoBuffer.jpg"
LOGO_PDF_PATH = BASE_DIR / "FullLogo_Buffer.jpg"

PHONE_TEXT = "Phone: 706-570-6569"
EMAIL_TEXT = "Email: joe@roberts-residential.com"

PAGE_ICON = str(LOGO_APP_PATH) if LOGO_APP_PATH.exists() else "🧰"

# ============================================================
# Page setup
# ============================================================
st.set_page_config(
    page_title="Roberts Fence Estimator",
    page_icon=PAGE_ICON,     # image path or emoji supported [3](https://github.com/streamlit/streamlit/issues/11370)
    layout="centered"
)

st.title("Roberts Residential, LLC. Fence Estimator")
st.caption("Dothan, AL")

# Center logo in the app UI (customer-facing)
if LOGO_APP_PATH.exists():
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        st.image(str(LOGO_APP_PATH), use_container_width=True)

# ============================================================
# Admin Unlock (Option B)
# ============================================================
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

def unlock_admin(pin: str) -> bool:
    expected = st.secrets.get("ADMIN_PIN", "")
    # If no secret is set, do not allow unlock (safer for public app)
    if not expected:
        return False
    return pin == expected

with st.sidebar:
    st.markdown("## Admin")
    pin = st.text_input("Enter PIN", type="password", placeholder="••••")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Unlock", use_container_width=True):
            st.session_state.is_admin = unlock_admin(pin)
            if not st.session_state.is_admin:
                st.error("Incorrect PIN or ADMIN_PIN not set in secrets.")
    with c2:
        if st.button("Lock", use_container_width=True):
            st.session_state.is_admin = False
            st.success("Locked.")

# ============================================================
# Helpers
# ============================================================
def ceil_qty(x: float) -> int:
    return int(math.ceil(x))

def apply_waste_qty(qty: float, waste_pct: float) -> int:
    return ceil_qty(qty * (1.0 + waste_pct))

def pickets_per_ft_from_width_gap(picket_width_in: float, gap_in: float) -> float:
    return 12.0 / (picket_width_in + gap_in)

def money_md(x: float) -> str:
    # Escape $ so Streamlit Markdown doesn't treat it as math
    return f"\\${x:,.2f}"

def build_quote_pdf(quote: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    # --- 1) Logo (centered) ---
    top_y = 8
    if LOGO_PDF_PATH.exists():
        try:
            logo_w_mm = 75
            x = (pdf.w - logo_w_mm) / 2.0
            pdf.image(str(LOGO_PDF_PATH), x=x, y=top_y, w=logo_w_mm)
            pdf.set_y(top_y + 52)
        except Exception:
            pdf.set_y(16)
    else:
        pdf.set_y(16)

    # --- 2) Near-privacy note (ABOVE contact/title as requested) ---
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        0, 6,
        "Near-privacy wood fences may show small gaps over time due to shrinkage/seasonal movement.",
        align="C"
    )
    pdf.ln(4)

    # --- 3) Phone, 4) Email (centered lines) ---
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, PHONE_TEXT, ln=1, align="C")
    pdf.cell(0, 6, EMAIL_TEXT, ln=1, align="C")
    pdf.ln(6)

    # --- 5) Title (moved below Near-privacy + contact) ---
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Roberts Residential LLC Fence Quote", align="C", ln=1)
    pdf.ln(6)

    # Body
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

    out = pdf.output(dest="S")
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)

# ============================================================
# Defaults (Customer mode) vs Admin controls
# ============================================================
# Customer mode defaults
labor_rate = 65.0
waste_pct = 0.10
base_install_hr_per_ft_6 = 0.22
height_8_multiplier = 1.15
gate_labor_hrs_each = 3.0
demo_hr_per_ft = 0.12
concrete_post_extra_hr = 0.75

terrain_factors = {"Flat": 1.0, "Sloped/Hilly": 1.25, "Rocky": 1.50}
mat_markup = 1.15
rental_markup = 1.10

post_cost = 18.50
rail_cost = 7.25
picket_cost = 3.98
concrete_bag_cost = 4.38
gate_hw_cost = 37.98
base_bracket_cost = 14.78

include_consumables = True
consumables_per_ft = 0.30

# Admin mode: show/override controls
if st.session_state.is_admin:
    with st.sidebar:
        st.markdown("## Assumptions (Admin)")

        labor_rate = st.number_input("All-in Billable Labor Rate ($/hr)", min_value=1.0, value=float(labor_rate), step=1.0)
        waste_pct = st.slider("Waste % (materials/consumables)", 0, 25, int(waste_pct * 100)) / 100.0

        st.subheader("Production")
        base_install_hr_per_ft_6 = st.number_input("Install hrs/ft (6 ft)", min_value=0.05, value=float(base_install_hr_per_ft_6), step=0.01)
        height_8_multiplier = st.number_input("8 ft labor multiplier", min_value=1.00, value=float(height_8_multiplier), step=0.05)
        gate_labor_hrs_each = st.number_input("Gate labor add (hrs per gate)", min_value=0.0, value=float(gate_labor_hrs_each), step=0.5)
        demo_hr_per_ft = st.number_input("Demo base (hrs/ft)", min_value=0.0, value=float(demo_hr_per_ft), step=0.01)
        concrete_post_extra_hr = st.number_input("Concrete post extra (hrs/post)", min_value=0.0, value=float(concrete_post_extra_hr), step=0.05)

        st.subheader("Terrain factors")
        terrain_factors = {
            "Flat": st.number_input("Flat factor", min_value=0.5, value=float(terrain_factors["Flat"]), step=0.05),
            "Sloped/Hilly": st.number_input("Sloped/Hilly factor", min_value=0.5, value=float(terrain_factors["Sloped/Hilly"]), step=0.05),
            "Rocky": st.number_input("Rocky factor", min_value=0.5, value=float(terrain_factors["Rocky"]), step=0.05),
        }

        st.subheader("Pricing (materials/rentals only)")
        mat_markup = st.number_input("Materials markup (1.15 = 15%)", min_value=1.0, value=float(mat_markup), step=0.01)
        rental_markup = st.number_input("Rentals/Disposal handling (1.10 = 10%)", min_value=1.0, value=float(rental_markup), step=0.01)

        st.subheader("Unit costs")
        post_cost = st.number_input("Post cost ($ each)", min_value=0.0, value=float(post_cost), step=0.25)
        rail_cost = st.number_input("Rail/stringer cost ($ each)", min_value=0.0, value=float(rail_cost), step=0.25)
        picket_cost = st.number_input("Dog-ear picket cost ($ each)", min_value=0.0, value=float(picket_cost), step=0.05)
        concrete_bag_cost = st.number_input("Concrete bag (50-lb) cost ($)", min_value=0.0, value=float(concrete_bag_cost), step=0.05)
        gate_hw_cost = st.number_input("Gate hardware kit cost ($ each)", min_value=0.0, value=float(gate_hw_cost), step=0.50)
        base_bracket_cost = st.number_input("Post base/bracket cost ($ each)", min_value=0.0, value=float(base_bracket_cost), step=0.25)

        st.subheader("Consumables (includes nails/fasteners)")
        include_consumables = st.checkbox("Include consumables allowance", value=include_consumables)
        consumables_per_ft = st.number_input("Consumables allowance ($/ft)", min_value=0.0, value=float(consumables_per_ft), step=0.05)

# ============================================================
# Customer-facing Quote Form
# ============================================================
st.markdown("### Get Your Fence Quote")

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

    st.markdown("### Fence Style (Near-Privacy)")
    picket_width_in = st.number_input("Picket width (inches, actual)", min_value=4.0, value=5.5, step=0.1)
    install_gap_in = st.number_input("Install gap (inches)", min_value=0.0, value=0.125, step=0.025)

    st.markdown("### Rails / Stringers")
    rails_default = 3 if height_ft == 6 else 4
    rails_per_section = st.number_input("Rails per 8-ft section", min_value=2, value=int(rails_default), step=1)

    st.markdown("### Concrete Option")
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

    phd_rental_cost = 0.0
    bin_rental_cost = 0.0
    if demo_old and old_concrete:
        st.markdown("### Rentals / Disposal")
        rent_phd = st.checkbox("Rent post hole digger / breaker", value=True)
        rent_bin = st.checkbox("Rent portable rubbish bin", value=True)
        if rent_phd:
            phd_rental_cost = st.number_input("Equipment rental cost ($)", min_value=0.0, value=95.0, step=5.0)
        if rent_bin:
            bin_rental_cost = st.number_input("Bin rental cost ($)", min_value=0.0, value=250.0, step=10.0)

    # Submit button must be inside the form [1](https://codeberg.org/rdwz/gitmoji)
    submitted = st.form_submit_button("Calculate Quote", type="primary")

# ============================================================
# Calculate & Results (Customer-facing)
# ============================================================
if submitted:
    terrain_factor = terrain_factors[terrain]

    sections = ceil_qty(length_ft / 8.0)
    posts = sections + 1

    ppf = pickets_per_ft_from_width_gap(picket_width_in, install_gap_in)
    pickets = ceil_qty(length_ft * ppf)
    rails = sections * int(rails_per_section)

    posts_w = apply_waste_qty(posts, waste_pct)
    pickets_w = apply_waste_qty(pickets, waste_pct)
    rails_w = apply_waste_qty(rails, waste_pct)

    gate_posts = gates * 2

    if pier_option == "Standard (2 bags per post)":
        bags_total = posts * 2
        bases_total = 0
    elif pier_option == "Heavy gate post piers (4 bags per gate post)":
        bags_total = (posts - gate_posts) * 2 + gate_posts * 4
        bases_total = 0
    elif pier_option == "Heavy piers all posts (3 bags per post)":
        bags_total = posts * 3
        bases_total = 0
    else:
        bags_total = posts * 2
        bases_total = posts

    bags_w = apply_waste_qty(bags_total, waste_pct)
    bases_w = apply_waste_qty(bases_total, waste_pct) if bases_total > 0 else 0

    # Consumables modeled as per-foot allowance (includes nails/fasteners)
    consumables_cost = 0.0
    if include_consumables:
        consumables_cost = (length_ft * consumables_per_ft) * (1.0 + waste_pct)

    # Materials cost (then marked up)
    mat_cost = (
        (posts_w * post_cost) +
        (rails_w * rail_cost) +
        (pickets_w * picket_cost) +
        (bags_w * concrete_bag_cost) +
        (gates * gate_hw_cost) +
        (bases_w * base_bracket_cost)
    )
    mat_sell = mat_cost * mat_markup

    # Labor (billable rate; no markup applied again)
    height_factor = 1.0 if height_ft == 6 else float(height_8_multiplier)
    install_hrs = (length_ft * base_install_hr_per_ft_6 * terrain_factor) * height_factor
    install_hrs += gates * gate_labor_hrs_each

    demo_hrs = 0.0
    if demo_old:
        demo_hrs = length_ft * demo_hr_per_ft
        if old_concrete:
            demo_hrs += posts * concrete_post_extra_hr

    labor_hrs = install_hrs + demo_hrs
    labor_sell = labor_hrs * labor_rate

    rental_total = phd_rental_cost + bin_rental_cost
    rental_sell = rental_total * rental_markup if rental_total > 0 else 0.0

    total = mat_sell + consumables_cost + labor_sell + rental_sell
    per_ft = total / float(length_ft)

    # --- Customer-facing results (clean) ---
    st.success(f"**Total Installed Price:** {money_md(total)} ({money_md(per_ft)}/ft)")

    st.markdown("### What’s Included")
    st.markdown(
        "- Materials and professional installation (dog-ear near-privacy)\n"
        "- Standard concrete set per post (2 bags/post) unless upgraded\n"
        "- Cleanup and haul-off (when demo is selected)\n"
        "- Near-privacy note: wood may shrink and small gaps may appear over time"
    )

    # Build PDF + Download
    quote = {
        "length_ft": int(length_ft),
        "height_ft": int(height_ft),
        "gates": int(gates),
        "terrain": terrain,
        "demo_old": bool(demo_old),
        "old_concrete": bool(old_concrete),
        "posts_w": int(posts_w),
        "rails_w": int(rails_w),
        "pickets_w": int(pickets_w),
        "bags_w": int(bags_w),
        "labor_hrs": float(labor_hrs),
        "labor_rate": float(labor_rate),
        "rental_sell": float(rental_sell),
        "total": float(total),
        "per_ft": float(per_ft),
    }

    pdf_bytes = build_quote_pdf(quote)

    # st.download_button sends bytes to the user’s browser [2](https://cheat-sheet.streamlit.app/)
    st.download_button(
        label="📄 Download Professional Quote PDF",
        data=pdf_bytes,
        file_name="Roberts_Fence_Quote.pdf",
        mime="application/pdf",
    )

st.caption("Built for Roberts Residential LLC • Dothan, AL")
