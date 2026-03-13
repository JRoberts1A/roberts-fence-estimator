import math

WASTE = 0.10
LABOR_RATE = 65.0  # billable, all-in

# Picket takeoff assumptions (near privacy)
PICKET_WIDTH_IN = 5.5
GAP_IN = 0.125  # 1/8"

# Consumables allowance (includes nails/fasteners)
CONSUMABLES_PER_FT = 0.30

def pickets_per_ft(width_in=5.5, gap_in=0.125):
    return 12.0 / (width_in + gap_in)

def waste_qty(qty):
    return math.ceil(qty * (1 + WASTE))

# Height option
height_ft = st.selectbox("Fence Height", [6, 8], index=0)

# Rails by height
rails_per_section = 3 if height_ft == 6 else 4

# Sections/posts
sections = math.ceil(length_ft / 8)
posts_total = sections + 1

# Near privacy pickets count
ppf = pickets_per_ft(PICKET_WIDTH_IN, GAP_IN)
pickets = math.ceil(length_ft * ppf)

# Waste applied
posts_w = waste_qty(posts_total)
pickets_w = waste_qty(pickets)
rails_w = waste_qty(sections * rails_per_section)

# Concrete bags (default 2 per post)
bags_per_post = 2
bags_total = posts_total * bags_per_post

# Gate posts upgrade (optional)
gate_posts = gates * 2
bags_per_gate_post = st.number_input("Bags per gate post (upgrade)", min_value=2, value=4, step=1)
bags_total = (posts_total - gate_posts) * bags_per_post + gate_posts * bags_per_gate_post
bags_w = math.ceil(bags_total * (1 + WASTE))

# Consumables
consumables_cost = (length_ft * CONSUMABLES_PER_FT) * (1 + WASTE)
