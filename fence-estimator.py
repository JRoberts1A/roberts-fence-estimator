import math
import textwrap
from pathlib import Path
from datetime import date, timedelta

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
    page_icon=PAGE_ICON,   # image path or emoji supported [3](https://fpdf.org/en/doc/multicell.htm)
    layout="centered"
)

st.title("Roberts Residential, LLC. Fence Estimator")
st.caption("Dothan, AL")

# Center logo in app
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
    # Safer for public app: if no secret configured, never unlock
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
# Helpers / Constants
# ============================================================
NEAR_PRIVACY_GAP_IN = 0.125  # fixed internal assumption (not exposed)
QUOTE_VALID_DAYS_DEFAULT = 30  # admin-editable

def ceil_qty(x: float) -> int:
    return int(math.ceil(x))

def apply_waste_qty(qty: float, waste_pct: float) -> int:
    return ceil_qty(qty * (1.0 + waste_pct))

def pickets_per_ft_from_width_gap(picket_width_in: float, gap_in: float) -> float:
    return 12.0 / (picket_width_in + gap_in)

def money_md(x: float) -> str:
    # Escape $ so Streamlit markdown doesn't treat it as math
    return f"\\${x:,.2f}"

def pdf_bullets(pdf: FPDF, items: list[str], line_h: float = 6.0) -> None:
    """
    Safe bullet printing for fpdf2:
    - Forces X back to left margin before each multi_cell
    - Uses explicit available width (avoids w=0 cursor edge cases)
    - Wraps long text safely
    """
    effective_w = pdf.w - pdf.l_margin - pdf.r_margin

    for item in items:
        pdf.set_x(pdf.l_margin)

        bullet_txt = f"- {item}"
        bullet_txt = textwrap.fill(
            bullet_txt,
            width=110,
            break_long_words=True,
            break_on_hyphens=True
        )

        pdf.multi_cell(effective_w, line_h, bullet_txt)
        pdf.set_x(pdf.l_margin)

# ============================================================
# Scope Notes Defaults (Warranty intentionally silent)
# Implementation #2: Admin editable via sidebar text areas
# ============================================================
DEFAULT_SCOPE_INCLUDED = [
    "Layout and standard string-line alignment.",
    "Standard post spacing (typically 8 ft on center) unless noted otherwise.",
    "Post holes dug and posts set in concrete (standard 2 bags/post unless upgraded).",
    "Rails/stringers installed (3 rails @ 6 ft height; 4 rails @ 8 ft height).",
    "Dog-ear pickets installed in a near-privacy configuration.",
    "Gate installation per selection (standard hardware included).",
    "Standard fasteners/consumables allowance (nails/fasteners, blades, small materials).",
    "Basic jobsite cleanup and removal of typical construction debris."
]

DEFAULT_SCOPE_EXCLUDED = [
    "Haul-off/Disposal is an optional add-on when Demo & Removal is selected (priced separately).",
    "Painting, staining, sealing, or pressure washing unless specifically quoted.",
    "Permits, HOA approvals, surveys, or property-line dispute resolution.",
    "Utility mark-out delays; repairs to damaged utilities/irrigation are not included.",
    "Rock excavation, root removal, buried debris, or unforeseen subsurface conditions (change order if encountered).",
    "Concrete/brick/stone demolition beyond standard fence removal unless explicitly included.",
    "Landscaping restoration (sod, plants, mulch) unless included in scope.",
    "Custom gates, steel frames, upgraded hardware, or specialty materials unless quoted."
]

DEFAULT_TERMS = [
    "Quote is valid for the period shown on this document.",
    "Schedule is subject to material availability and weather conditions.",
    "Customer is responsible for confirming property lines, easements, and HOA requirements."
]

# ============================================================
# PDF Builder
# - Logo + title safe spacing (title won't collide with logo)
# - Divider line
# - Quote date / valid through
# - Detailed scope notes
# - Near-privacy note in body
# - Phone/Email last items printed in body
# - Haul-off line uses requested wording
# - Uses safe bullet printer to avoid multi_cell width errors
# ============================================================
def build_quote_pdf(quote: dict) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ----------------------------
    # Header: Logo + Title (no overlap)
    # ----------------------------
    top_y = 8
    title_y = 20  # fallback if no logo

    if LOGO_PDF_PATH.exists():
        try:
            logo_w_mm = 75
            x = (pdf.w - logo_w_mm) / 2.0
            pdf.image(str(LOGO_PDF_PATH), x=x, y=top_y, w=logo_w_mm)
            title_y = top_y + 58  # force title safely below logo block
        except Exception:
            title_y = 20

    pdf.set_y(title_y)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Roberts Residential LLC Fence Quote", align="C", ln=1)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 6, f"Quote Date: {quote.get('quote_date','')}", align="C", ln=1)
    pdf.cell(0, 6, f"Valid Through: {quote.get('valid_through','')}", align="C", ln=1)

    # Divider line
    pdf.ln(3)
    y = pdf.get_y()
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, y, pdf.w - 10, y)
    pdf.ln(8)

    # ----------------------------
    # Body: Details
    # ----------------------------
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Fence Length: {quote['length_ft']} ft", ln=1)
    pdf.cell(0, 8, f"Fence Height: {quote['height_ft']} ft", ln=1)
    pdf.cell(0, 8, f"Gates: {quote['gates']}", ln=1)
    pdf.cell(0, 8, f"Terrain: {quote['terrain']}", ln=1)
    pdf.cell(0, 8, f"Demo & Removal: {'Yes' if quote['demo_old'] else 'No'}", ln=1)

    if quote["demo_old"]:
        pdf.cell(0, 8, f"Old posts in concrete: {'Yes' if quote['old_concrete'] else 'No'}", ln=1)
        pdf.cell(0, 8, f"Haul-off/Disposal add-on: {'Yes' if quote.get('haul_off_selected', False) else 'No'}", ln=1)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 10, f"Total Installed Price: ${quote['total']:,.2f}", ln=1)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Price per foot: ${quote['per_ft']:,.2f}/ft", ln=1)

    pdf.ln(4)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Posts: {quote['posts_w']} | Rails: {quote['rails_w']} | Pickets: {quote['pickets_w']}", ln=1)
    pdf.cell(0, 7, f"Concrete bags: {quote['bags_w']} | Labor: {quote['labor_hrs']:.1f} hrs @ ${quote['labor_rate']:,.2f}/hr", ln=1)

    # Haul-off wording as requested
    if quote.get("haul_off_sell", 0) > 0:
        pdf.cell(
            0, 7,
            f"Haul-off/Disposal: removal and disposal of demo debris — ${quote['haul_off_sell']:,.2f}",
            ln=1
        )

    # Rentals line prints only if Admin enabled and included
    if quote.get("rental_sell", 0) > 0:
        pdf.cell(0, 7, f"Rentals/Disposal: ${quote['rental_sell']:,.2f}", ln=1)

    # ----------------------------
    # Scope notes (Admin editable) - SAFE multi_cell handling
    # ----------------------------
    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "What's Included", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf_bullets(pdf, quote.get("scope_included", []))

    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Exclusions / Assumptions", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf_bullets(pdf, quote.get("scope_excluded", []))

    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Terms", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf_bullets(pdf, quote.get("terms", []))

    # Near-privacy note in body
    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        pdf.w - pdf.l_margin - pdf.r_margin,
        6,
        "Near-privacy wood fences may show small gaps over time due to shrinkage/seasonal movement."
    )

    # Phone/Email LAST items printed in body
    pdf.ln(6)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, PHONE_TEXT, ln=1, align="C")
    pdf.cell(0, 5, EMAIL_TEXT, ln=1, align="C")

    out = pdf.output(dest="S")
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)

# ============================================================
# Defaults (Customer mode)
# ============================================================
# Default labor rate reduced to $45/hr
labor_rate = 45.0

waste_pct = 0.10
base_install_hr_per_ft_6 = 0.22
height_8_multiplier = 1.15
gate_labor_hrs_each = 3.0

demo_hr_per_ft = 0.12
concrete_post_extra_hr = 0.75

# Terrain is Admin-only (customer default)
terrain_factors = {"Flat": 1.0, "Sloped/Hilly": 1.25, "Rocky": 1.50}
terrain = "Flat"

mat_markup = 1.15
rental_markup = 1.10  # admin-only and not assumed

post_cost = 18.50
rail_cost = 7.25
picket_cost = 3.98
concrete_bag_cost = 4.38
gate_hw_cost = 37.98

# Bracket/Base default $22
base_bracket_cost = 22.00

include_consumables = True
consumables_per_ft = 0.30

# Admin-only picket width selection (5.5 or 6.0)
picket_width_in = 5.5

# Rentals: NOT assumed; admin-only defaults OFF
enable_equipment_rental = False
equipment_rental_cost = 95.0
enable_bin_rental = False
bin_rental_cost = 250.0

# Haul-off/disposal add-on: customer selects, admin sets price
haul_off_cost = 250.0
haul_off_markup = 1.10

quote_valid_days = QUOTE_VALID_DAYS_DEFAULT

# ============================================================
# Admin-only controls (Terrain, picket width, scope notes, costs)
# ============================================================
if st.session_state.is_admin:
    with st.sidebar:
        st.markdown("## Assumptions (Admin)")

        labor_rate = st.number_input("All-in Billable Labor Rate ($/hr)", min_value=1.0, value=float(labor_rate), step=1.0)
        waste_pct = st.slider("Waste % (materials/consumables)", 0, 25, int(waste_pct * 100)) / 100.0

        st.subheader("Terrain (Admin-only)")
        terrain = st.selectbox("Terrain", ["Flat", "Sloped/Hilly", "Rocky"], index=0)

        st.subheader("Pickets (Admin-only)")
        picket_width_in = st.selectbox("Picket width (inches)", options=[5.5, 6.0], index=0)

        st.subheader("Production (Admin)")
        base_install_hr_per_ft_6 = st.number_input("Install hrs/ft (6 ft)", min_value=0.05, value=float(base_install_hr_per_ft_6), step=0.01)
        height_8_multiplier = st.number_input("8 ft labor multiplier", min_value=1.00, value=float(height_8_multiplier), step=0.05)
        gate_labor_hrs_each = st.number_input("Gate labor add (hrs per gate)", min_value=0.0, value=float(gate_labor_hrs_each), step=0.5)
        demo_hr_per_ft = st.number_input("Demo base (hrs/ft)", min_value=0.0, value=float(demo_hr_per_ft), step=0.01)
        concrete_post_extra_hr = st.number_input("Concrete post extra (hrs/post)", min_value=0.0, value=float(concrete_post_extra_hr), step=0.05)

        st.subheader("PDF (Admin)")
        quote_valid_days = st.number_input("Quote valid (days)", min_value=1, value=int(quote_valid_days), step=1)

        st.subheader("Pricing (Admin)")
        mat_markup = st.number_input("Materials markup (1.15 = 15%)", min_value=1.0, value=float(mat_markup), step=0.01)
        rental_markup = st.number_input("Rentals handling (1.10 = 10%)", min_value=1.0, value=float(rental_markup), step=0.01)

        st.subheader("Unit costs (Admin)")
        post_cost = st.number_input("Post cost ($ each)", min_value=0.0, value=float(post_cost), step=0.25)
        rail_cost = st.number_input("Rail/stringer cost ($ each)", min_value=0.0, value=float(rail_cost), step=0.25)
        picket_cost = st.number_input("Dog-ear picket cost ($ each)", min_value=0.0, value=float(picket_cost), step=0.05)
        concrete_bag_cost = st.number_input("Concrete bag (50-lb) cost ($)", min_value=0.0, value=float(concrete_bag_cost), step=0.05)
        gate_hw_cost = st.number_input("Gate hardware kit cost ($ each)", min_value=0.0, value=float(gate_hw_cost), step=0.50)
        base_bracket_cost = st.number_input("Bracket/Base unit cost ($ each)", min_value=0.0, value=float(base_bracket_cost), step=0.50)

        st.subheader("Consumables (Admin)")
        include_consumables = st.checkbox("Include consumables allowance", value=include_consumables)
        consumables_per_ft = st.number_input("Consumables allowance ($/ft)", min_value=0.0, value=float(consumables_per_ft), step=0.05)

        st.subheader("Rentals (Admin-only)")
        st.caption("Not assumed in customer quotes. Enable only when applicable.")
        enable_equipment_rental = st.checkbox("Include equipment rental", value=enable_equipment_rental)
        equipment_rental_cost = st.number_input("Equipment rental cost ($)", min_value=0.0, value=float(equipment_rental_cost), step=5.0)
        enable_bin_rental = st.checkbox("Include bin rental", value=enable_bin_rental)
        bin_rental_cost = st.number_input("Bin rental cost ($)", min_value=0.0, value=float(bin_rental_cost), step=10.0)

        st.subheader("Haul-off / Disposal (Admin)")
        st.caption("Customer can choose haul-off when Demo is selected; price controlled here.")
        haul_off_cost = st.number_input("Haul-off/disposal base cost ($)", min_value=0.0, value=float(haul_off_cost), step=10.0)
        haul_off_markup = st.number_input("Haul-off markup (1.10 = 10%)", min_value=1.0, value=float(haul_off_markup), step=0.01)

        # Implementation #2: Admin editable scope notes
        st.subheader("PDF Scope Notes (Admin)")
        included_text = st.text_area(
            "What's Included (one bullet per line)",
            value="\n".join(DEFAULT_SCOPE_INCLUDED),
            height=170
        )
        excluded_text = st.text_area(
            "Exclusions / Assumptions (one bullet per line)",
            value="\n".join(DEFAULT_SCOPE_EXCLUDED),
            height=170
        )
        terms_text = st.text_area(
            "Terms (one bullet per line)",
            value="\n".join(DEFAULT_TERMS),
            height=130
        )

        scope_included = [line.strip() for line in included_text.splitlines() if line.strip()]
        scope_excluded = [line.strip() for line in excluded_text.splitlines() if line.strip()]
        terms = [line.strip() for line in terms_text.splitlines() if line.strip()]
else:
    # Customer mode scope notes (defaults)
    scope_included = DEFAULT_SCOPE_INCLUDED
    scope_excluded = DEFAULT_SCOPE_EXCLUDED
    terms = DEFAULT_TERMS

# ============================================================
# Customer-facing Quote Form
# - Terrain hidden (admin-only)
# - Rentals hidden (admin-only)
# - Haul-off appears only when Demo selected (extra)
# - Enforce demo required if haul-off selected (validation)
# ============================================================
st.markdown("### Get Your Fence Quote")

with st.form("quote_form"):
    col1, col2 = st.columns(2)

    with col1:
        length_ft = st.number_input("Fence Length (ft)", min_value=20, value=200, step=10)
        height_ft = st.selectbox("Fence Height (ft)", [6, 8], index=0)
        gates = st.number_input("Number of Gates", min_value=0, value=1, step=1)

    with col2:
        demo_old = st.checkbox("Include Demo & Removal of Old Fence", value=True)
        old_concrete = st.checkbox("Old posts are in concrete", value=True) if demo_old else False

    # Haul-off/disposal add-on (extra)
    haul_off_selected = False
    if demo_old:
        haul_off_selected = st.checkbox("Add haul-off/disposal (extra)", value=False)
    else:
        haul_off_selected = False  # cannot be true if demo isn't selected

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

    # Streamlit forms require a submit button inside the form [4](https://peerdh.com/blogs/programming-insights/streamlits-download-button-a-comprehensive-guide)
    submitted = st.form_submit_button("Calculate Quote", type="primary")

# ============================================================
# Calculate & Results
# ============================================================
if submitted:
    # Enforce: Demo must be selected if haul-off is selected
    if haul_off_selected and not demo_old:
        st.error("To select haul-off/disposal, 'Include Demo & Removal of Old Fence' must also be selected.")
        st.stop()

    terrain_factor = terrain_factors.get(terrain, 1.0)

    # Rails fixed automatically
    rails_per_section = 3 if height_ft == 6 else 4

    # Basic takeoff
    sections = ceil_qty(length_ft / 8.0)
    posts = sections + 1
    rails = sections * rails_per_section

    # Pickets based on admin picket width + fixed near-privacy gap
    ppf = pickets_per_ft_from_width_gap(picket_width_in, NEAR_PRIVACY_GAP_IN)
    pickets = ceil_qty(length_ft * ppf)

    # Waste on quantities
    posts_w = apply_waste_qty(posts, waste_pct)
    rails_w = apply_waste_qty(rails, waste_pct)
    pickets_w = apply_waste_qty(pickets, waste_pct)

    gate_posts = gates * 2

    # Concrete options
    if pier_option == "Standard (2 bags per post)":
        bags_total = posts * 2
        bases_total = 0
    elif pier_option == "Heavy gate post piers (4 bags per gate post)":
        bags_total = (posts - gate_posts) * 2 + gate_posts * 4
        bases_total = 0
    elif pier_option == "Heavy piers all posts (3 bags per post)":
        bags_total = posts * 3
        bases_total = 0
    else:  # Bracket/base
        bags_total = posts * 2
        bases_total = posts

    bags_w = apply_waste_qty(bags_total, waste_pct)
    bases_w = apply_waste_qty(bases_total, waste_pct) if bases_total > 0 else 0

    # Consumables (includes nails/fasteners)
    consumables_cost = 0.0
    if include_consumables:
        consumables_cost = (length_ft * consumables_per_ft) * (1.0 + waste_pct)

    # Materials + markup
    mat_cost = (
        (posts_w * post_cost) +
        (rails_w * rail_cost) +
        (pickets_w * picket_cost) +
        (bags_w * concrete_bag_cost) +
        (gates * gate_hw_cost) +
        (bases_w * base_bracket_cost)
    )
    mat_sell = mat_cost * mat_markup

    # Labor
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

    # Haul-off/disposal add-on (extra)
    haul_off_sell = 0.0
    if demo_old and haul_off_selected:
        haul_off_sell = float(haul_off_cost) * float(haul_off_markup)

    # Rentals NOT assumed — admin-only and requires unlock + enable + demo+concrete
    rental_total = 0.0
    if st.session_state.is_admin and demo_old and old_concrete:
        if enable_equipment_rental:
            rental_total += equipment_rental_cost
        if enable_bin_rental:
            rental_total += bin_rental_cost
    rental_sell = rental_total * rental_markup if rental_total > 0 else 0.0

    total = mat_sell + consumables_cost + labor_sell + haul_off_sell + rental_sell
    per_ft = total / float(length_ft)

    # Customer-facing output (simple)
    st.success(f"**Total Installed Price:** {money_md(total)} ({money_md(per_ft)}/ft)")

    st.markdown("### What’s Included")
    st.markdown(
        "- Materials and professional installation (dog-ear near-privacy)\n"
        "- Standard concrete set per post (2 bags/post) unless upgraded\n"
        "- Demo & Removal (when selected)\n"
        "- Haul-off/disposal available as an add-on when demo is selected\n"
        "- Wood may shrink and small gaps may appear over time"
    )

    # Quote dates
    quote_date_val = date.today()
    valid_through_val = quote_date_val + timedelta(days=int(quote_valid_days))

    quote = {
        "length_ft": int(length_ft),
        "height_ft": int(height_ft),
        "gates": int(gates),
        "terrain": terrain,
        "demo_old": bool(demo_old),
        "old_concrete": bool(old_concrete),

        "haul_off_selected": bool(haul_off_selected),
        "haul_off_sell": float(haul_off_sell),

        "posts_w": int(posts_w),
        "rails_w": int(rails_w),
        "pickets_w": int(pickets_w),
        "bags_w": int(bags_w),

        "labor_hrs": float(labor_hrs),
        "labor_rate": float(labor_rate),

        "rental_sell": float(rental_sell),

        "total": float(total),
        "per_ft": float(per_ft),

        "quote_date": quote_date_val.strftime("%b %d, %Y"),
        "valid_through": valid_through_val.strftime("%b %d, %Y"),

        "scope_included": scope_included,
        "scope_excluded": scope_excluded,
        "terms": terms,
    }

    pdf_bytes = build_quote_pdf(quote)

    # Download button sends bytes to browser [5](https://github.com/py-pdf/fpdf2/issues/464)
    st.download_button(
        label="📄 Download Professional Quote PDF",
        data=pdf_bytes,
        file_name="Roberts_Fence_Quote.pdf",
        mime="application/pdf",
    )

st.caption("Built for Roberts Residential LLC • Dothan, AL")
