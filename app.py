"""
SmartPick AI - persona-based smartphone recommender (weighted-sum scoring)
Reads sic_mobile_spec_PJ1.xlsx (read-only; the file is never modified).
Run with:  python -m streamlit run app.py
"""

import html
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ======================================================================
# 1. SETTINGS (safe to edit)
# ======================================================================
FILE_NAME = "sic_mobile_spec_PJ1.xlsx"
SHEET_NAME = 0
TOP_N = 5

# The Excel file has no currency column. Only 2 price cells contain "$" (e.g. "$1000"),
# and prices run from about 80 to 1200, so "$" is used. Change it here if that is wrong
# (for example "₹"), or set it to "" to show plain numbers.
CURRENCY_SYMBOL = "$"

DATA_PATH = Path(__file__).parent / FILE_NAME

FEATURES = ["price", "battery", "ram", "storage", "rating", "display", "processor", "camera"]
FEATURE_LABELS = {
    "price": "Price affordability", "battery": "Battery", "ram": "RAM", "storage": "Storage",
    "rating": "Rating", "display": "Display", "processor": "Processor (approx. tier)",
    "camera": "Camera",
}

# Persona weights in PERCENT. Each persona must add up to 100.
# These are starting heuristics, not validated rankings. Edit freely.
PERSONA_WEIGHTS = {
    "Student": {"price": 30, "battery": 20, "ram": 15, "storage": 15, "rating": 10,
                "display": 5, "processor": 5, "camera": 0},
    "Gaming": {"processor": 35, "ram": 20, "battery": 15, "display": 10, "storage": 10,
               "rating": 5, "price": 5, "camera": 0},
    "Photography": {"camera": 40, "rating": 15, "display": 10, "storage": 10, "battery": 10,
                    "processor": 5, "price": 10, "ram": 0},
    "Battery Lover": {"battery": 40, "price": 20, "rating": 10, "ram": 10, "storage": 10,
                      "processor": 5, "display": 5, "camera": 0},
    "All-Rounder": {"processor": 20, "battery": 20, "camera": 15, "ram": 10, "storage": 10,
                    "rating": 10, "display": 5, "price": 10},
}
PERSONA_ICONS = {"Student": "🎓", "Gaming": "🎮", "Photography": "📷",
                 "Battery Lover": "🔋", "All-Rounder": "⚖️"}

# Processor proxy. The file only has chip NAMES (no GHz or benchmark), and ~2/3 of phones
# say "not mentioned". Names cannot be ranked as numbers, so a few recognisable chips are
# placed in rough tiers (1 = entry, 2 = mid, 3 = upper-mid, 4 = flagship). This is an
# approximate judgement, NOT a benchmark. Chips that are ambiguous or misspelled in the
# file (e.g. "Gen8", "MediaTek", "Heilo80P") are NOT scored; their weight is re-shared.
# Patterns are matched against the processor text in lowercase with only letters/digits.
PROCESSOR_TIERS = [
    (4, r"snapdragon8gen2|snapdragon8plusgen1|dimensity9000|snapdragon888"),
    (3, r"dimensity1080"),
    (2, r"snapdragon750g|snapdragon720g|snapdragon695|dimensity700|dimensity720"),
    (1, r"snapdragon450|snapdragon439|sdm450|sdm439|snapdragon425|snapdragon410"),
]
TIER_NAMES = {1: "entry-level", 2: "mid-range", 3: "upper-mid", 4: "flagship"}

st.set_page_config(page_title="SmartPick AI", page_icon="📱", layout="wide")

# ======================================================================
# 2. STYLES (light background, dark text, violet/blue accents)
# ======================================================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@500;600;700;800&display=swap');
/* ===== THEME COLOURS: change only these lines to restyle the whole app ===== */
:root {
  --hero-1: #070f26;      /* hero gradient start (deep navy) */
  --hero-2: #14337a;      /* hero gradient middle */
  --hero-3: #3b5bdb;      /* hero gradient end */
  --tagline: #fde68a;     /* tagline text on the hero */
  --accent: #14337a;      /* price text */
  --accent-dark: #0a1a3a; /* score number, headings */
  --highlight: #f5b301;   /* Best Match badge, #1 card border, Run button (gold) */
  --highlight-text: #0a1a3a; /* text on gold (dark, so it stays readable) */
  --highlight-hover: #d99e00; /* gold when hovered */
  --soft-bg: #f3eeff;     /* chips and "why it scored well" box (light lavender) */
  --soft-text: #2e1f5e;   /* text inside those soft areas */
  --page-bg: #ebe5fb;     /* page background: lavender */
  --page-bg-2: #ddd4f6;   /* lavender, slightly deeper (bottom of the page) */
  --card-border: #d8cff2; /* thin border around cards */
  --stage-1: #3b5bdb;     /* spotlight stage behind each phone: centre */
  --stage-2: #14337a;     /* stage: middle */
  --stage-3: #070f26;     /* stage: edges (dark, cinematic) */
}
.stApp {background: linear-gradient(180deg, var(--page-bg) 0%, var(--page-bg-2) 100%);
  background-attachment: fixed; color-scheme: light; font-family: 'Inter', 'Segoe UI', sans-serif;}
.block-container {max-width: 1150px; padding-top: 1.2rem;}
.stApp h1, .stApp h2, .stApp h3 {font-family: 'Poppins', 'Segoe UI', sans-serif; color: var(--accent-dark);}
.stApp [data-testid="stMarkdownContainer"] p, .stApp [data-testid="stWidgetLabel"] p,
.stApp .stRadio label p {color: #1e1b4b;}
[data-testid="stVerticalBlockBorderWrapper"] {background: rgba(255,255,255,.72); border-radius: 22px;
  border: 1px solid var(--card-border); box-shadow: 0 10px 30px rgba(76, 29, 149, .08);}
[data-testid="stExpander"] {background: rgba(255,255,255,.78); border-radius: 18px;
  border: 1px solid var(--card-border);}
[data-testid="stAlert"] {border-radius: 16px;}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #ffd34d, var(--highlight)); border: none; color: var(--highlight-text);
  font-weight: 700; padding: .7rem 2rem; border-radius: 999px; font-size: 1.08rem;
  box-shadow: 0 8px 20px rgba(245, 179, 1, .40); transition: transform .15s ease, box-shadow .15s ease;}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
  background: linear-gradient(135deg, var(--highlight), var(--highlight-hover)); color: var(--highlight-text);
  transform: translateY(-2px); box-shadow: 0 12px 26px rgba(245, 179, 1, .50);}

/* ---------- CSS phone (used in hero and on cards when there is no photo) ---------- */
.phone {position: relative; width: 88px; height: 176px; border-radius: 22px; padding: 5px;
  background: linear-gradient(145deg, #2b3654, #0a1020); transform: rotate(-6deg);
  box-shadow: 0 22px 34px rgba(0,0,0,.55), inset 0 0 0 1.5px rgba(255,255,255,.18); transition: transform .35s ease;}
.phone .scr {position: relative; width: 100%; height: 100%; border-radius: 17px; overflow: hidden;
  background: linear-gradient(160deg, var(--g1), var(--g2));}
.phone .scr::before {content: ""; position: absolute; top: 7px; left: 50%; width: 9px; height: 9px;
  transform: translateX(-50%); border-radius: 50%; background: #05070d; z-index: 2;}
.phone .scr::after {content: ""; position: absolute; inset: 0;
  background: linear-gradient(115deg, rgba(255,255,255,.38) 0%, rgba(255,255,255,0) 42%);}
.phone .bar {position: absolute; left: 14%; right: 14%; height: 7px; border-radius: 6px; background: rgba(255,255,255,.30);}
.phone .b1 {bottom: 30px;} .phone .b2 {bottom: 18px; right: 36%;}

/* ---------- hero (cinematic) ---------- */
.sp-hero {position: relative; overflow: hidden; border-radius: 28px; padding: 2.8rem 2.4rem 2.5rem 2.4rem;
  margin-bottom: 1.2rem; min-height: 230px; box-shadow: 0 20px 46px rgba(7, 15, 38, .35);
  background: linear-gradient(120deg, var(--hero-1), var(--hero-2), var(--hero-3), var(--hero-2), var(--hero-1));
  background-size: 300% 300%; animation: sp-shift 18s ease infinite;
  border-top: 4px solid var(--highlight); border-bottom: 4px solid var(--highlight);}
.sp-hero::before {content: ""; position: absolute; right: -70px; top: -90px; width: 320px; height: 320px;
  border-radius: 50%; background: radial-gradient(circle, rgba(245,179,1,.55), rgba(245,179,1,0) 70%);}
.sp-hero::after {content: ""; position: absolute; left: 30%; bottom: -130px; width: 300px; height: 300px;
  border-radius: 50%; background: radial-gradient(circle, rgba(196,181,253,.40), rgba(196,181,253,0) 70%);}
.sp-grain {position: absolute; inset: 0; opacity: .16; mix-blend-mode: overlay; pointer-events: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");}
.sp-eyebrow {position: relative; z-index: 2; font-size: .75rem; font-weight: 700; letter-spacing: .38em;
  color: var(--highlight); text-transform: uppercase; margin-bottom: .5rem;}
.sp-title {position: relative; z-index: 2; font-family: 'Poppins', 'Segoe UI', sans-serif; font-size: 3.1rem;
  font-weight: 800; color: #ffffff; letter-spacing: -.5px; text-shadow: 0 6px 24px rgba(0,0,0,.45);}
.sp-tag {position: relative; z-index: 2; font-size: 1.2rem; color: var(--tagline); margin-top: .35rem; font-weight: 500;}
.sp-hero-phones {position: absolute; z-index: 1; right: 3.2rem; top: 50%; transform: translateY(-50%);
  display: flex; align-items: center; gap: .6rem;}
.sp-hero-phones .phone {width: 74px; height: 148px; border-radius: 19px; animation: sp-float 6s ease-in-out infinite;}
.sp-hero-phones .hp1 {transform: rotate(-10deg) translateY(12px); animation-delay: 0s;}
.sp-hero-phones .hp2 {transform: rotate(0deg) scale(1.15); animation-delay: -2s;}
.sp-hero-phones .hp3 {transform: rotate(10deg) translateY(16px); animation-delay: -4s;}
@keyframes sp-float {0%,100% {margin-top: 0;} 50% {margin-top: -12px;}}
@keyframes sp-shift {0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;}}
@media (max-width: 800px) {.sp-hero-phones {display: none;} .sp-title {font-size: 2.3rem;}}

/* ---------- results heading ---------- */
.sp-now {margin-top: 1.1rem; font-size: .75rem; font-weight: 700; letter-spacing: .38em; color: #9a6b00;}
.sp-showtitle {font-family: 'Poppins', 'Segoe UI', sans-serif; font-size: 1.9rem; font-weight: 800;
  color: var(--accent-dark); margin-bottom: .3rem;}
.sp-showtitle::after {content: ""; display: block; width: 70px; height: 4px; border-radius: 4px;
  margin-top: .3rem; background: var(--highlight);}

/* ---------- result cards ---------- */
.sp-grid {display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1.2rem;}
.sp-card {background: #ffffff; border: 1px solid var(--card-border); border-radius: 26px; overflow: hidden;
  box-shadow: 0 10px 28px rgba(76, 29, 149, .12); transition: transform .22s ease, box-shadow .22s ease;
  animation: sp-rise .75s cubic-bezier(.2,.7,.2,1) backwards;}
.sp-card:nth-child(2) {animation-delay: .10s;} .sp-card:nth-child(3) {animation-delay: .20s;}
.sp-card:nth-child(4) {animation-delay: .30s;} .sp-card:nth-child(5) {animation-delay: .40s;}
@keyframes sp-rise {from {opacity: 0; transform: translateY(30px) scale(.97);} to {opacity: 1; transform: none;}}
.sp-card:hover {transform: translateY(-6px); box-shadow: 0 20px 40px rgba(76, 29, 149, .22);}
.sp-card:hover .phone {transform: rotate(0deg) scale(1.07);}
.sp-card.best {border: 2px solid var(--highlight); box-shadow: 0 14px 36px rgba(245, 179, 1, .36);}
.sp-stage {position: relative; height: 225px; display: flex; align-items: center; justify-content: center;
  overflow: hidden; background: radial-gradient(ellipse at 50% 22%, var(--stage-1) 0%, var(--stage-2) 42%, var(--stage-3) 100%);}
.sp-stage::before {content: ""; position: absolute; top: -30px; left: 50%; width: 200px; height: 270px;
  transform: translateX(-50%); background: linear-gradient(180deg, rgba(255,255,255,.30), rgba(255,255,255,0));
  clip-path: polygon(36% 0, 64% 0, 100% 100%, 0 100%);}
.sp-stage::after {content: ""; position: absolute; bottom: 14px; left: 50%; width: 150px; height: 18px;
  transform: translateX(-50%); background: radial-gradient(ellipse, rgba(0,0,0,.6), rgba(0,0,0,0) 70%);}
.sp-stage .phone, .sp-photo {position: relative; z-index: 1;}
.sp-photo {max-height: 180px; max-width: 78%; object-fit: contain; filter: drop-shadow(0 18px 22px rgba(0,0,0,.55));}
.sp-top {position: absolute; z-index: 3; top: .9rem; left: 1rem; display: flex; gap: .5rem; align-items: center;}
.sp-rank {background: rgba(255,255,255,.18); color: #ffffff; font-weight: 800; padding: .2rem .75rem;
  border-radius: 999px; font-size: .85rem; backdrop-filter: blur(4px); border: 1px solid rgba(255,255,255,.25);}
.sp-best {background: var(--highlight); color: var(--highlight-text); font-weight: 700; padding: .2rem .75rem;
  border-radius: 999px; font-size: .85rem;}
.sp-cap {position: absolute; z-index: 3; bottom: .5rem; right: .9rem; font-size: .68rem; color: rgba(255,255,255,.6);}
.sp-body {padding: 1.15rem 1.3rem 1.3rem 1.3rem;}
.sp-head {display: flex; justify-content: space-between; align-items: center; gap: .8rem;}
.sp-name {font-family: 'Poppins', 'Segoe UI', sans-serif; font-size: 1.15rem; font-weight: 700;
  color: var(--accent-dark); margin-bottom: .15rem;}
.sp-price {font-size: 1.4rem; font-weight: 800; color: var(--accent);}
.sp-ring {flex: none; width: 70px; height: 70px; border-radius: 50%; display: grid; place-items: center;
  background: conic-gradient(var(--highlight) calc(var(--p) * 1%), #e6e0f7 0);}
.sp-ring span {width: 54px; height: 54px; border-radius: 50%; background: #ffffff; display: grid;
  place-items: center; font-family: 'Poppins', 'Segoe UI', sans-serif; font-weight: 800; font-size: 1.15rem;
  color: var(--accent-dark);}
.sp-scoretxt {font-size: .82rem; color: #6b6290; margin: .5rem 0 .6rem 0;}
.sp-chips {display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .6rem;}
.sp-chip {background: var(--soft-bg); color: var(--soft-text); font-weight: 600; font-size: .8rem;
  padding: .25rem .7rem; border-radius: 999px; border: 1px solid #e4daf9;}
.sp-row {display: flex; justify-content: space-between; gap: .8rem; padding: .32rem 0;
  border-top: 1px solid #f0ebfb; font-size: .88rem;}
.sp-k {color: #6b6290;}
.sp-v {color: #1e1b4b; font-weight: 600; text-align: right;}
.sp-why {margin-top: .8rem; background: var(--soft-bg); border-radius: 16px; padding: .75rem .95rem;
  font-size: .85rem; color: var(--soft-text); border-left: 4px solid var(--highlight);}
.sp-why ul {margin: .3rem 0 0 1.1rem; padding: 0;}
.sp-note {margin-top: .5rem; font-size: .78rem; color: #6b6290;}
@media (prefers-reduced-motion: reduce) {
  .sp-card, .sp-hero, .sp-hero-phones .phone {animation: none !important;}
}
</style>
""",
    unsafe_allow_html=True,
)

# ======================================================================
# 3. SAFE PARSING HELPERS
# ======================================================================
# "not mentioned" is how your file marks unknown processors.
MISSING_TEXT = {"", "nan", "none", "n/a", "na", "-", "--", "null", "nil", "unknown", "not mentioned"}
NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?|\.\d+")


def is_missing(v):
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip().lower() in MISSING_TEXT
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def first_number(v):
    """First number in a value ('$1000' -> 1000.0, '5,000 mAh' -> 5000.0). NaN if none."""
    if is_missing(v) or isinstance(v, (bool, np.bool_)):
        return np.nan
    if isinstance(v, (int, float, np.integer, np.floating)):
        v = float(v)
        return v if np.isfinite(v) else np.nan
    m = NUM_RE.search(str(v))
    if not m:
        return np.nan
    try:
        return float(m.group().replace(",", ""))
    except ValueError:
        return np.nan


def positive(x):
    return x if (not np.isnan(x) and x > 0) else np.nan


def parse_price(v):
    return positive(first_number(v))          # handles 1000 and "$1000"


def parse_rating(v):
    return positive(first_number(v))          # rating of 0 or less = not rated


def parse_memory_gb(v):
    """Storage/RAM in GB. Handles 128, '256GB' and '1TB' (TB -> x1024)."""
    x = positive(first_number(v))
    if np.isnan(x):
        return x
    if isinstance(v, str):
        t = v.lower()
        if re.search(r"\d\s*tb", t):
            return x * 1024
        if re.search(r"\d\s*mb", t):
            return x / 1024
    return x


def parse_ram_gb(v):
    x = parse_memory_gb(v)
    return x if (not np.isnan(x) and x <= 64) else np.nan


def parse_battery(v):
    x = positive(first_number(v))
    return x if (not np.isnan(x) and 500 <= x <= 20000) else np.nan


def parse_camera_mp(v):
    """Camera column is a plain megapixel number in your file. 0 = invalid."""
    return positive(first_number(v))


def parse_size_inches(v):
    x = first_number(v)
    return x if (not np.isnan(x) and 2 <= x <= 12) else np.nan


def display_type_score(v):
    """OLED-family 1.0, LCD-family 0.5. 'other_types' is unknown and is skipped, not scored 0."""
    if not isinstance(v, str):
        return np.nan
    t = v.lower()
    if re.search(r"amoled|oled|ltpo|retina", t):
        return 1.0
    if re.search(r"ips|lcd|tft|led|pls|\bva\b", t):
        return 0.5
    return np.nan


def processor_tier(v):
    """Approximate tier (1-4) from the chip name, or NaN if not recognised."""
    if is_missing(v):
        return np.nan
    key = re.sub(r"[^a-z0-9]", "", str(v).lower())
    for tier, pattern in PROCESSOR_TIERS:
        if re.search(pattern, key):
            return float(tier)
    return np.nan


def clean_text(v):
    return np.nan if is_missing(v) else re.sub(r"\s+", " ", str(v)).strip()


def raw_text(v):
    if is_missing(v):
        return np.nan
    if isinstance(v, (float, np.floating)) and float(v).is_integer():
        return str(int(v))
    return re.sub(r"\s+", " ", str(v)).strip()


def fmt_num(x):
    if x is None or pd.isna(x):
        return "Not listed"
    x = float(x)
    return f"{int(x):,}" if x.is_integer() else f"{x:,.2f}".rstrip("0").rstrip(".")


def esc(v):
    return html.escape("Not listed" if (v is None or (not isinstance(v, str) and pd.isna(v))) else str(v))


# ======================================================================
# 4. LOAD THE EXCEL FILE (read-only) AND CLEAN IT IN MEMORY
# ======================================================================
@st.cache_data(show_spinner="Loading your dataset...")
def load_data(path_str, modified_time):
    raw = pd.read_excel(path_str, sheet_name=SHEET_NAME)
    raw.columns = [str(c).strip().lower() for c in raw.columns]
    raw = raw.dropna(how="all").reset_index(drop=True)
    duplicates = int(raw.duplicated().sum())
    raw = raw.drop_duplicates().reset_index(drop=True)

    def col(name):
        return raw[name] if name in raw.columns else pd.Series(np.nan, index=raw.index, dtype=object)

    df = pd.DataFrame(index=raw.index)
    names = col("name").map(clean_text)
    df["name"] = [n if isinstance(n, str) else f"Unnamed phone (row {i + 2})" for i, n in zip(raw.index, names)]
    df["price"] = col("price").map(parse_price).astype(float)
    df["rating_n"] = col("rating").map(parse_rating).astype(float)
    df["ram_gb"] = col("ram").map(parse_ram_gb).astype(float)
    df["storage_gb"] = col("storage").map(parse_memory_gb).astype(float)
    df["battery_mah"] = col("battery").map(parse_battery).astype(float)
    df["camera_mp"] = col("camera").map(parse_camera_mp).astype(float)
    df["size_in"] = col("display_size").map(parse_size_inches).astype(float)
    df["display_type"] = col("display_type").map(clean_text)
    df["type_score"] = df["display_type"].map(display_type_score).astype(float)
    df["cpu_tier"] = col("processor").map(processor_tier).astype(float)

    df["processor_raw"] = col("processor").map(raw_text)
    df["weight_raw"] = col("weight").map(raw_text)
    return raw, df, duplicates


# ======================================================================
# 5. SCORING ENGINE:  Final Score = sum(weight x normalized score)
# ======================================================================
def check_weights():
    for persona, weights in PERSONA_WEIGHTS.items():
        total = sum(weights.get(f, 0) for f in FEATURES)
        if total != 100:
            return f"The weights for '{persona}' add up to {total}%, not 100%. Fix PERSONA_WEIGHTS."
    return None


def minmax(s):
    """Scale to 0-1 inside the pool. Missing stays missing. If everyone is equal -> 0.5."""
    lo, hi = s.min(), s.max()
    if pd.isna(lo):
        return pd.Series(np.nan, index=s.index)
    if hi == lo:
        return s.where(s.isna(), 0.5)
    return (s - lo) / (hi - lo)


def display_score(pool):
    """60% panel type + 40% screen size. Uses whichever part is available."""
    t = pool["type_score"]
    z = minmax(pool["size_in"])
    out = pd.Series(np.nan, index=pool.index)
    both = t.notna() & z.notna()
    out[both] = 0.6 * t[both] + 0.4 * z[both]
    out[t.notna() & z.isna()] = t[t.notna() & z.isna()]
    out[t.isna() & z.notna()] = z[t.isna() & z.notna()]
    return out


def compute_ranking(df, persona, budget):
    """Budget filter -> normalize -> weighted sum -> sort -> top N."""
    pool = df[df["price"].notna() & (df["price"] <= budget)].copy()
    if pool.empty:
        return None

    norm = pd.DataFrame(index=pool.index)
    norm["price"] = (1 - pool["price"] / budget).clip(0, 1)   # cheaper = higher
    norm["battery"] = minmax(pool["battery_mah"])
    norm["ram"] = minmax(pool["ram_gb"])
    norm["storage"] = minmax(pool["storage_gb"])
    norm["rating"] = minmax(pool["rating_n"])
    norm["processor"] = minmax(pool["cpu_tier"])
    norm["camera"] = minmax(pool["camera_mp"])
    norm["display"] = display_score(pool)
    norm = norm[FEATURES]

    weights = np.array([PERSONA_WEIGHTS[persona].get(f, 0) for f in FEATURES], dtype=float) / 100
    values = norm.to_numpy(dtype=float)
    available = ~np.isnan(values)
    usable = weights * available                      # weights of features this phone has
    total = usable.sum(axis=1, keepdims=True)
    used = np.divide(usable, total, out=np.zeros_like(usable), where=total > 0)  # re-shared, sums to 1
    contrib = used * np.nan_to_num(values) * 100      # points each feature adds
    score = contrib.sum(axis=1)                       # always between 0 and 100

    used_df = pd.DataFrame(used, index=pool.index, columns=FEATURES)
    contrib_df = pd.DataFrame(contrib, index=pool.index, columns=FEATURES)
    pool["score"] = score
    keep = pd.Series(total.ravel() > 0, index=pool.index)
    pool = pool[keep]

    ranked = pool.sort_values(["score", "rating_n", "price"], ascending=[False, False, True],
                              na_position="last").head(TOP_N)
    return {
        "ranked": ranked, "norm": norm.loc[ranked.index], "used": used_df.loc[ranked.index],
        "contrib": contrib_df.loc[ranked.index], "n_eligible": len(pool),
    }


# ======================================================================
# 6. CARDS AND EXPLANATIONS
# ======================================================================
def price_text(price, symbol):
    return "Price not listed" if pd.isna(price) else f"{symbol}{fmt_num(price)}"


def display_text(row):
    kind = row["display_type"]
    if kind == "other_types":
        kind = "Other panel type"
    size = np.nan if pd.isna(row["size_in"]) else f"{fmt_num(row['size_in'])} in"
    parts = [p for p in [size, kind] if isinstance(p, str)]
    return " · ".join(parts) if parts else np.nan


def value_text(feature, row, symbol):
    if feature == "price":
        return price_text(row["price"], symbol)
    if feature == "battery":
        return f"{fmt_num(row['battery_mah'])} mAh"
    if feature == "ram":
        return f"{fmt_num(row['ram_gb'])} GB"
    if feature == "storage":
        return f"{fmt_num(row['storage_gb'])} GB"
    if feature == "rating":
        return fmt_num(row["rating_n"])
    if feature == "display":
        return str(display_text(row))
    if feature == "processor":
        return f"{row['processor_raw']} (approx. {TIER_NAMES.get(int(row['cpu_tier']), 'unranked')} tier)"
    return f"{fmt_num(row['camera_mp'])} MP"


def build_reasons(idx, result, persona, budget, symbol):
    row = result["ranked"].loc[idx]
    norm, used, contrib = result["norm"].loc[idx], result["used"].loc[idx], result["contrib"].loc[idx]
    reasons, notes = [], []
    gap = budget - row["price"]
    reasons.append(
        f"Within budget: {price_text(row['price'], symbol)}"
        + (f", {symbol}{fmt_num(gap)} under your maximum." if gap > 0 else ", right at your maximum.")
    )
    top = [f for f in contrib.sort_values(ascending=False).index if contrib[f] > 0][:3]
    for f in top:
        reasons.append(
            f"{FEATURE_LABELS[f]}: {value_text(f, row, symbol)} → "
            f"{contrib[f]:.1f} of its {row['score']:.1f} points ({persona} weight {used[f] * 100:.0f}%)."
        )
    missing = [FEATURE_LABELS[f] for f in FEATURES if PERSONA_WEIGHTS[persona].get(f, 0) > 0 and pd.isna(norm[f])]
    if missing:
        notes.append("Not available for this phone: " + ", ".join(missing) +
                     ". Their weight was shared among the other features, not scored as zero.")
    return reasons, notes


# ---- optional real photos: put image files in the "phone_images" folder next to app.py ----
IMAGE_DIR = Path(__file__).parent / "phone_images"
PHOTOS = {}          # filled in below; maps a simplified file name to the image data
GRADIENTS = [("#f5b301", "#e11d48"), ("#22d3ee", "#6366f1"), ("#a78bfa", "#ec4899"),
             ("#34d399", "#0ea5e9"), ("#fb923c", "#db2777"), ("#facc15", "#16a34a")]


def simple(text):
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


@st.cache_data(show_spinner=False)
def load_photos(folder_str, folder_mtime):
    """Reads images from the folder (read-only). Returns {simplified name: data URI}."""
    import base64
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    found, skipped = {}, []
    folder = Path(folder_str)
    if not folder.is_dir():
        return found, skipped
    for f in sorted(folder.iterdir()):
        kind = mime.get(f.suffix.lower())
        if not kind:
            continue
        if f.stat().st_size > 2_000_000:
            skipped.append(f.name)
            continue
        found[simple(f.stem)] = f"data:{kind};base64," + base64.b64encode(f.read_bytes()).decode()
    return found, skipped


def find_photo(name):
    """Match by the full name or by the name without the '(256 GB)' part."""
    for key in (simple(name), simple(re.sub(r"\(.*?\)", "", str(name)))):
        if key and key in PHOTOS:
            return PHOTOS[key]
    return None


def phone_render(name, extra_class=""):
    """Stylised phone drawn with CSS. Colours depend only on the name; it is NOT the real phone."""
    g1, g2 = GRADIENTS[sum(ord(c) for c in str(name)) % len(GRADIENTS)]
    return (f'<div class="phone {extra_class}" style="--g1:{g1};--g2:{g2}"><div class="scr">'
            '<div class="bar b1"></div><div class="bar b2"></div></div></div>')


def build_card(rank, row, reasons, notes, symbol):
    score = max(0.0, min(100.0, float(row["score"])))
    ram = np.nan if pd.isna(row["ram_gb"]) else f"{fmt_num(row['ram_gb'])} GB"
    storage = np.nan if pd.isna(row["storage_gb"]) else f"{fmt_num(row['storage_gb'])} GB"
    battery = np.nan if pd.isna(row["battery_mah"]) else f"{fmt_num(row['battery_mah'])} mAh"
    rating = np.nan if pd.isna(row["rating_n"]) else fmt_num(row["rating_n"])
    camera = np.nan if pd.isna(row["camera_mp"]) else f"{fmt_num(row['camera_mp'])} MP"
    weight = np.nan if not isinstance(row["weight_raw"], str) else f"{row['weight_raw']} (unit not stated)"
    proc = row["processor_raw"] if isinstance(row["processor_raw"], str) else "Not mentioned in data"

    photo = find_photo(row["name"])
    out = f'<div class="sp-card{" best" if rank == 1 else ""}"><div class="sp-stage"><div class="sp-top">'
    out += f'<div class="sp-rank">#{rank}</div>'
    if rank == 1:
        out += '<div class="sp-best">🏆 Best Match</div>'
    out += "</div>"
    if photo:
        out += f'<img class="sp-photo" src="{photo}" alt="{esc(row["name"])}">'
    else:
        out += phone_render(row["name"]) + '<div class="sp-cap">Illustration</div>'
    out += '</div><div class="sp-body"><div class="sp-head"><div>'
    out += f'<div class="sp-name">{esc(row["name"])}</div>'
    out += f'<div class="sp-price">{esc(price_text(row["price"], symbol))}</div></div>'
    out += f'<div class="sp-ring" style="--p:{score:.1f}"><span>{score:.0f}</span></div></div>'
    out += f'<div class="sp-scoretxt">Weighted score: <b>{score:.1f} / 100</b></div>'

    chips = []
    if not pd.isna(row["rating_n"]):
        chips.append(f"⭐ {rating}")
    for label, value in [("RAM", ram), ("Storage", storage), ("Battery", battery), ("Camera", camera)]:
        if isinstance(value, str):
            chips.append(f"{label} {value}")
    if chips:
        out += '<div class="sp-chips">' + "".join(f'<span class="sp-chip">{esc(c)}</span>' for c in chips) + "</div>"

    def spec(label, value):
        return f'<div class="sp-row"><div class="sp-k">{esc(label)}</div><div class="sp-v">{esc(value)}</div></div>'

    out += spec("Rating", rating) + spec("Processor", proc) + spec("Camera", camera)
    out += spec("RAM", ram) + spec("Storage", storage) + spec("Battery", battery)
    out += spec("Display", display_text(row)) + spec("Weight", weight)
    out += '<div class="sp-why"><b>Why it scored well</b><ul>' + "".join(f"<li>{esc(r)}</li>" for r in reasons) + "</ul></div>"
    out += "".join(f'<div class="sp-note">ℹ️ {esc(n)}</div>' for n in notes)
    return out + "</div></div>"


# ======================================================================
# 7. LOAD DATA (friendly errors)
# ======================================================================
weight_error = check_weights()
if weight_error:
    st.error(weight_error)
    st.stop()

if not DATA_PATH.exists():
    st.error(f"Could not find **{FILE_NAME}** in {DATA_PATH.parent}")
    st.info("Put the Excel file in the same folder as app.py, or fix FILE_NAME at the top of app.py.")
    st.stop()

try:
    raw_df, df, dup_removed = load_data(str(DATA_PATH), DATA_PATH.stat().st_mtime)
except PermissionError:
    st.error("The Excel file is open in another program. Close Excel, then refresh this page.")
    st.stop()
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not read the Excel file: {exc}")
    st.stop()

missing_required = [c for c in ["name", "price"] if c not in raw_df.columns]
if missing_required:
    st.error("The Excel file needs these columns, but they were not found: " + ", ".join(missing_required))
    st.stop()

valid_prices = df["price"].dropna()
if valid_prices.empty:
    st.error("No valid prices were found in the 'price' column, so no recommendation can be made.")
    st.stop()

SYMBOL = CURRENCY_SYMBOL
PHOTOS, skipped_photos = load_photos(
    str(IMAGE_DIR), IMAGE_DIR.stat().st_mtime if IMAGE_DIR.is_dir() else 0)

# ======================================================================
# 8. HEADER + CONTROL PANEL
# ======================================================================
hero_phones = (phone_render("alpha", "hp1") + phone_render("bravo", "hp2") + phone_render("charlie", "hp3"))
st.markdown(
    '<div class="sp-hero"><div class="sp-grain"></div>'
    '<div class="sp-eyebrow">Personalised phone picks</div>'
    '<div class="sp-title">📱 SmartPick AI</div>'
    '<div class="sp-tag">Your Budget. Your Priorities. Your Perfect Phone.</div>'
    f'<div class="sp-hero-phones">{hero_phones}</div></div>',
    unsafe_allow_html=True,
)

p_min, p_max = float(valid_prices.min()), float(valid_prices.max())
default_price = float(np.clip(valid_prices.median(), p_min, p_max))
step = 10 if bool((valid_prices % 10 == 0).all()) else 1

with st.container(border=True):
    st.subheader("1. Choose your persona")
    persona = st.radio(
        "Persona", list(PERSONA_WEIGHTS.keys()), horizontal=True,
        format_func=lambda p: f"{PERSONA_ICONS[p]} {p}", label_visibility="collapsed",
    )

    st.subheader("2. Set your maximum price")
    if p_max > p_min:
        budget = st.slider("Maximum price", int(p_min), int(p_max), int(round(default_price / step) * step),
                           step=step, format=f"{SYMBOL}%d", label_visibility="collapsed")
    else:
        budget = p_max
        st.info(f"Every phone in the dataset costs {price_text(p_max, SYMBOL)}.")

    n_in_budget = int((valid_prices <= budget).sum())
    st.caption(f"Budget: **{price_text(budget, SYMBOL)}** · {n_in_budget:,} of {len(valid_prices):,} "
               f"phones are at or below this. Slider range comes from your data "
               f"({price_text(p_min, SYMBOL)} to {price_text(p_max, SYMBOL)}).")

    st.subheader("3. Run")
    run_clicked = st.button("🚀 Run Recommendation", type="primary")

# ======================================================================
# 9. RUN THE RECOMMENDATION (results stored so the page stays stable)
# ======================================================================
if run_clicked:
    if "result" in st.session_state:
        st.session_state["previous"] = st.session_state["result"]
    ranking = compute_ranking(df, persona, float(budget))
    st.session_state["result"] = {"persona": persona, "budget": float(budget), "ranking": ranking}

result = st.session_state.get("result")

if result is None:
    st.info("👆 Pick a persona, set your maximum price and click **Run Recommendation**.")
else:
    ranking = result["ranking"]
    if (result["persona"], result["budget"]) != (persona, float(budget)):
        st.warning("You changed the controls since the last run. Click **Run Recommendation** to update the results.")

    st.markdown(
        '<div class="sp-now">NOW SHOWING</div>'
        f'<div class="sp-showtitle">{PERSONA_ICONS[result["persona"]]} Top phones for {html.escape(result["persona"])} '
        f'under {html.escape(price_text(result["budget"], SYMBOL))}</div>',
        unsafe_allow_html=True,
    )

    if ranking is None:
        cheapest = df.loc[df["price"].idxmin()]
        st.warning(
            f"No phones are priced at or below {price_text(result['budget'], SYMBOL)}. "
            f"The cheapest phone in the dataset is {cheapest['name']} at "
            f"{price_text(cheapest['price'], SYMBOL)}. Please increase the price limit. "
            "Your budget has not been changed."
        )
    else:
        ranked = ranking["ranked"]
        if len(ranked) < TOP_N:
            st.info(f"Only {len(ranked)} phone(s) are available within this budget, so only those are shown.")
        st.caption(f"{ranking['n_eligible']:,} eligible phones were scored; the top {len(ranked)} are shown. "
                   "Scores compare each phone with the other phones inside your budget.")

        # ---- compare with the previous run -------------------------------
        prev = st.session_state.get("previous")
        if prev and prev["ranking"] is not None and prev["persona"] != result["persona"]:
            old_names = list(prev["ranking"]["ranked"]["name"])
            new_names = list(ranked["name"])
            shared = [n for n in new_names if n in old_names]
            added = [n for n in new_names if n not in old_names]
            dropped = [n for n in old_names if n not in new_names]
            same_budget = prev["budget"] == result["budget"]
            msg = (f"**{prev['persona']} → {result['persona']}** "
                   f"({'same budget' if same_budget else 'the budget also changed'}). ")
            if not shared:
                msg += "None of the previous top phones appear in the new list."
            else:
                msg += (f"{len(shared)} phone(s) appear in both lists. This overlap is genuine: those phones "
                        "score well under both sets of weights in your dataset.")
            if added:
                msg += "\n\n**New in the top list:** " + ", ".join(added)
            if dropped:
                msg += "\n\n**Dropped out:** " + ", ".join(dropped)
            st.info(msg)

        cards = []
        for rank, idx in enumerate(ranked.index, start=1):
            reasons, notes = build_reasons(idx, ranking, result["persona"], result["budget"], SYMBOL)
            cards.append(build_card(rank, ranked.loc[idx], reasons, notes, SYMBOL))
        st.markdown('<div class="sp-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)

        # ---- how is the score calculated? -------------------------------
        with st.expander("How is the score calculated?"):
            st.markdown(
                "**Weighted Score = Sum of (Feature Weight × Normalized Feature Score)**\n\n"
                "1. Phones above your maximum price are removed first.\n"
                "2. Each feature is scaled to 0–1 among the remaining phones (lowest = 0, highest = 1). "
                "Price affordability is `1 − price ÷ your maximum price`.\n"
                "3. Each normalized score is multiplied by the persona's weight and the results are added "
                "up, then shown out of 100.\n"
                "4. If a phone has no usable value for a feature, that feature is skipped and its weight is "
                "shared proportionally among the features the phone does have. Missing is never scored as zero.\n\n"
                "Things to be aware of: about two-thirds of phones say **\"not mentioned\"** for the processor, "
                "and the rest are placed in rough tiers by chip name (not a benchmark). Display is 60% panel "
                "type (OLED-family above LCD-family; \"other_types\" is skipped) and 40% screen size. "
                "The weights are starting heuristics, not validated rankings."
            )
            weights_table = pd.DataFrame(
                {"Feature": [FEATURE_LABELS[f] for f in FEATURES],
                 "Weight": [f"{PERSONA_WEIGHTS[result['persona']].get(f, 0)}%" for f in FEATURES]}
            )
            st.markdown(f"**Weights for {result['persona']}** (total 100%)")
            st.table(weights_table)

            choice = st.selectbox(
                "Show the calculation for:", list(ranked.index),
                format_func=lambda i: f"#{list(ranked.index).index(i) + 1} {ranked.loc[i, 'name']}",
            )
            n_row, u_row, c_row = ranking["norm"].loc[choice], ranking["used"].loc[choice], ranking["contrib"].loc[choice]
            rows = []
            for f in FEATURES:
                base_w = PERSONA_WEIGHTS[result["persona"]].get(f, 0)
                if base_w == 0:
                    continue
                rows.append({
                    "Feature": FEATURE_LABELS[f],
                    "Persona weight": f"{base_w}%",
                    "Weight used": f"{u_row[f] * 100:.1f}%",
                    "Normalized score (0–1)": "Not available" if pd.isna(n_row[f]) else f"{n_row[f]:.3f}",
                    "Contribution (points)": f"{c_row[f]:.2f}",
                })
            rows.append({"Feature": "TOTAL", "Persona weight": "100%", "Weight used": f"{u_row.sum() * 100:.1f}%",
                         "Normalized score (0–1)": "", "Contribution (points)": f"{c_row.sum():.2f}"})
            st.table(pd.DataFrame(rows))
            st.caption(f"Final score shown on the card: {ranked.loc[choice, 'score']:.2f} / 100. "
                       "Rows may differ from the total by a rounding of 0.01.")

# ======================================================================
# 10. DATA CHECK + SELF-TEST (for you, the developer)
# ======================================================================
st.write("")
with st.expander("🧪 Data check and self-test"):
    st.write(f"Rows used: **{len(raw_df):,}** · Exact duplicate rows ignored in memory: **{dup_removed}** "
             "(your Excel file is never changed) · Currency symbol shown: "
             f"**{SYMBOL if SYMBOL else 'none'}**")
    st.write(f"Price range found: **{price_text(p_min, SYMBOL)} to {price_text(p_max, SYMBOL)}** "
             f"({len(valid_prices):,} valid prices out of {len(df):,} rows)")

    shown = sum(1 for n in df["name"] if find_photo(n))
    st.write(f"Phone photos: **{len(PHOTOS)}** image file(s) found in `{IMAGE_DIR.name}` · "
             f"**{shown}** of {len(df)} phones have a matching photo. Phones without one show an illustration.")
    if skipped_photos:
        st.warning("Skipped because they are over 2 MB: " + ", ".join(skipped_photos))

    coverage = pd.DataFrame({
        "Feature": ["Price", "Battery", "RAM", "Storage", "Rating", "Camera",
                    "Display type (OLED/LCD known)", "Display size", "Processor (recognised chip)"],
        "Phones with a usable value": [int(df[c].notna().sum()) for c in
                                       ["price", "battery_mah", "ram_gb", "storage_gb", "rating_n",
                                        "camera_mp", "type_score", "size_in", "cpu_tier"]],
    })
    coverage["Out of"] = len(df)
    st.table(coverage)

    pairs = {"price": "price", "ram": "ram_gb", "storage": "storage_gb", "battery": "battery_mah",
             "camera": "camera_mp", "processor": "cpu_tier", "display_size": "size_in",
             "display_type": "type_score", "rating": "rating_n"}
    available_cols = [c for c in pairs if c in raw_df.columns]
    pick = st.selectbox("Compare raw Excel values with what the app understood:", available_cols)
    st.dataframe(pd.DataFrame({"raw value in Excel": raw_df[pick].head(10).astype(str),
                               "understood as": df[pairs[pick]].head(10)}), hide_index=True)

    st.markdown("**Self-test at the current budget**")
    checks = [("Every persona's weights add up to 100%", check_weights() is None)]
    tops = {}
    for p in PERSONA_WEIGHTS:
        r = compute_ranking(df, p, float(budget))
        if r is None:
            checks.append((f"{p}: no phones in budget (nothing to test, nothing fabricated)", True))
            continue
        top = r["ranked"]
        tops[p] = list(top["name"])
        checks.append((f"{p}: at most {TOP_N} results", len(top) <= TOP_N))
        checks.append((f"{p}: all prices at or below the budget", bool((top["price"] <= budget).all())))
        checks.append((f"{p}: scores between 0 and 100", bool(top["score"].between(0, 100).all())))
        checks.append((f"{p}: contributions add up to the score",
                       bool(np.allclose(r["contrib"].sum(axis=1), top["score"], atol=1e-4))))
    for label, ok in checks:
        st.write(("✅ " if ok else "❌ ") + label)
    if "Student" in tops and "Gaming" in tops:
        overlap = len(set(tops["Student"]) & set(tops["Gaming"]))
        st.write(f"ℹ️ Student vs Gaming at this budget: {overlap} of {TOP_N} phones are shared.")