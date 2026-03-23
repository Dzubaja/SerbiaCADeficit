"""
CSS styles and KPI card helpers for the dashboard.
Supports dark and light themes.
"""

# ── Shared CSS (both themes) ──────────────────────────────────────

_SHARED_CSS = """
    /* ── Import Google Font ────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global ────────────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1rem;
        max-width: 1400px;
    }


    /* ── KPI Cards (structure) ─────────────────────────────────────── */
    .kpi-card {
        border-radius: 12px;
        padding: 14px 14px 12px;
        text-align: center;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 12px 12px 0 0;
    }
    .kpi-card .kpi-label {
        font-size: 0.6rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .kpi-card .kpi-value {
        font-size: 1.25rem;
        font-weight: 800;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }
    .kpi-card .kpi-sub {
        font-size: 0.55rem;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    .kpi-card .kpi-change {
        font-size: 0.7rem;
        font-weight: 600;
        margin-top: 4px;
        letter-spacing: 0.3px;
    }

    /* Card accent top bars */
    .kpi-card:has(.kpi-positive)::before {
        background: linear-gradient(90deg, #06D6A0, #00B4D8);
    }
    .kpi-card:has(.kpi-negative)::before {
        background: linear-gradient(90deg, #FF6B8A, #FF006E);
    }
    .kpi-card:has(.kpi-neutral)::before {
        background: linear-gradient(90deg, #00D4FF, #7C5CFC);
    }
    /* Fallback */
    .kpi-card::before {
        background: linear-gradient(90deg, #00D4FF, #7C5CFC);
    }

    /* ── Tab styling (structure) ───────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 8px;
        letter-spacing: 0.3px;
    }

    /* ── Dashboard header (structure) ──────────────────────────────── */
    .dash-title {
        font-size: 1.7rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0;
    }
    .dash-subtitle {
        font-size: 0.82rem;
        font-weight: 500;
        margin-top: 4px;
        letter-spacing: 0.3px;
    }

    /* ── Section headers ───────────────────────────────────────────── */
    .section-header {
        font-size: 1.05rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.6rem;
        padding-bottom: 8px;
        letter-spacing: 0.2px;
    }

    /* ── Divider ───────────────────────────────────────────────────── */
    hr {
        border: none;
        height: 1px;
        margin: 0.8rem 0 1rem;
    }

    /* ── Dataframe styling ─────────────────────────────────────────── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }

    /* ── Metric cards (st.metric) structure ─────────────────────────── */
    [data-testid="stMetric"] {
        border-radius: 12px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    [data-testid="stMetricValue"] {
        font-weight: 800 !important;
    }

    /* ── Hide Streamlit branding ───────────────────────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Theme toggle button ───────────────────────────────────────── */
    .theme-toggle {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    /* ── Responsive: Mobile (< 768px) ────────────────────────────── */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            max-width: 100% !important;
        }

        /* Stack all Streamlit columns vertically */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.4rem !important;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* KPI cards — compact on mobile */
        .kpi-card {
            padding: 14px 12px 12px;
            border-radius: 12px;
        }
        .kpi-card .kpi-value {
            font-size: 1.3rem;
        }
        .kpi-card .kpi-label {
            font-size: 0.65rem;
            letter-spacing: 0.8px;
            margin-bottom: 6px;
        }
        .kpi-card .kpi-sub {
            font-size: 0.62rem;
        }
        .kpi-card .kpi-change {
            font-size: 0.72rem;
        }

        /* Dashboard header */
        .dash-title {
            font-size: 1.15rem !important;
        }
        .dash-subtitle {
            font-size: 0.7rem;
        }

        /* Section headers */
        .section-header {
            font-size: 0.88rem;
            margin-top: 0.8rem;
            margin-bottom: 0.4rem;
        }

        /* Tabs — horizontally scrollable */
        .stTabs [data-baseweb="tab-list"] {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            flex-wrap: nowrap !important;
            padding: 3px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 12px;
            font-size: 0.72rem;
            white-space: nowrap;
            flex-shrink: 0;
        }

        /* Metric cards */
        [data-testid="stMetric"] {
            padding: 10px 12px;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.65rem !important;
        }

        /* Tables — allow horizontal scroll */
        .stDataFrame {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }

        /* Plotly charts — constrain height */
        [data-testid="stPlotlyChart"] > div {
            min-height: 260px;
        }

        /* Slider — full width */
        .stSlider {
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
    }

    /* ── Responsive: Tablet (768px – 1024px) ─────────────────────── */
    @media (min-width: 769px) and (max-width: 1024px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }

        .kpi-card .kpi-value {
            font-size: 1.45rem;
        }
        .kpi-card .kpi-label {
            font-size: 0.68rem;
        }

        .dash-title {
            font-size: 1.4rem !important;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            font-size: 0.78rem;
        }
    }
"""


# ── Dark theme overrides ──────────────────────────────────────────

_DARK_CSS = """
    /* ── Dark: backgrounds ───────────────── */
    .stApp { background-color: #060B18; }

    .kpi-card {
        background: linear-gradient(145deg, #0F1629 0%, #131A2E 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .kpi-card:hover { box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); }
    .kpi-card .kpi-label { color: #8B95A8; }
    .kpi-card .kpi-sub   { color: #5A6478; }

    .kpi-positive { color: #06D6A0; text-shadow: 0 0 20px rgba(6, 214, 160, 0.3); }
    .kpi-card:has(.kpi-positive) { box-shadow: 0 4px 20px rgba(6, 214, 160, 0.08); }
    .kpi-negative { color: #FF6B8A; text-shadow: 0 0 20px rgba(255, 107, 138, 0.3); }
    .kpi-card:has(.kpi-negative) { box-shadow: 0 4px 20px rgba(255, 107, 138, 0.08); }
    .kpi-neutral  { color: #00D4FF; text-shadow: 0 0 20px rgba(0, 212, 255, 0.3); }
    .kpi-card:has(.kpi-neutral) { box-shadow: 0 4px 20px rgba(0, 212, 255, 0.08); }

    .kpi-change-pos { color: #06D6A0; }
    .kpi-change-neg { color: #FF6B8A; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #0A0F1F;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }
    .stTabs [data-baseweb="tab"] { color: #6B7A90; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(124, 92, 252, 0.12)) !important;
        color: #E2E8F0 !important;
        border-bottom: none !important;
    }

    /* Header */
    .dash-title { background: linear-gradient(135deg, #E2E8F0, #00D4FF); }
    .dash-subtitle { color: #5A6478; }
    .section-header { color: #C8D1DC; border-bottom: 1px solid rgba(255, 255, 255, 0.06); }

    /* Divider */
    hr { background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.2), rgba(124, 92, 252, 0.2), transparent); }

    /* Metric */
    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #0F1629 0%, #131A2E 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    [data-testid="stMetricLabel"] { color: #8B95A8 !important; }
    [data-testid="stMetricValue"] { color: #00D4FF !important; }

    /* Slider */
    .stSlider > div > div > div { color: #00D4FF; }
"""


# ── Light theme overrides ─────────────────────────────────────────

_LIGHT_CSS = """
    /* ── Light: backgrounds ──────────────── */
    .stApp { background-color: #F1F5F9 !important; }

    /* Override Streamlit dark widgets */
    .stApp [data-testid="stAppViewContainer"] { background-color: #F1F5F9; }
    .stApp [data-testid="stHeader"] { background-color: #F1F5F9; }
    .stApp section[data-testid="stSidebar"] { background-color: #E2E8F0; }

    /* Text color overrides */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #334155;
    }
    .stApp .stMarkdown p { color: #334155; }

    /* Selectbox, slider, inputs */
    .stApp [data-baseweb="select"] > div { background-color: #FFFFFF; border-color: #CBD5E1; }
    .stApp [data-baseweb="select"] span { color: #334155 !important; }
    .stApp .stSlider label, .stApp .stSelectbox label { color: #475569 !important; }

    /* KPI cards */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    .kpi-card:hover { box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); }
    .kpi-card .kpi-label { color: #64748B; }
    .kpi-card .kpi-sub   { color: #94A3B8; }

    .kpi-positive { color: #059669; text-shadow: none; }
    .kpi-negative { color: #DC2626; text-shadow: none; }
    .kpi-neutral  { color: #0891B2; text-shadow: none; }
    .kpi-card:has(.kpi-positive) { box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    .kpi-card:has(.kpi-negative) { box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    .kpi-card:has(.kpi-neutral)  { box-shadow: 0 1px 3px rgba(0,0,0,0.06); }

    .kpi-change-pos { color: #059669 !important; }
    .kpi-change-neg { color: #DC2626 !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] { color: #64748B; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(8, 145, 178, 0.08), rgba(109, 40, 217, 0.08)) !important;
        color: #1E293B !important;
        border-bottom: none !important;
    }

    /* Header */
    .dash-title { background: linear-gradient(135deg, #1E293B, #0891B2); }
    .dash-subtitle { color: #64748B; }
    .section-header { color: #1E293B; border-bottom: 1px solid #E2E8F0; }

    /* Divider */
    hr { background: linear-gradient(90deg, transparent, rgba(8, 145, 178, 0.25), rgba(109, 40, 217, 0.2), transparent); }

    /* Metric */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
    }
    [data-testid="stMetricLabel"] { color: #64748B !important; }
    [data-testid="stMetricValue"] { color: #0891B2 !important; }

    /* Dataframe */
    .stApp .stDataFrame { background: #FFFFFF; border-radius: 12px; }
    .stApp [data-testid="stDataFrame"] th { background: #E2E8F0 !important; color: #1E293B !important; }
    .stApp [data-testid="stDataFrame"] td { color: #334155 !important; }

    /* Slider */
    .stSlider > div > div > div { color: #0891B2; }
"""


def get_css(theme="dark"):
    """Return the full CSS block for the given theme."""
    overrides = _DARK_CSS if theme == "dark" else _LIGHT_CSS
    return f"<style>{_SHARED_CSS}{overrides}</style>"


# Keep backward compat
CUSTOM_CSS = get_css("dark")


def kpi_card(label: str, value: float, unit: str = "EUR mn",
             css_class: str = "kpi-neutral", sub_text: str = "",
             change: float = None, change_pct: float = None):
    """Generate HTML for a single KPI card with optional YoY change."""
    if value is None:
        formatted = "N/A"
    elif abs(value) >= 1000:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.1f}"

    change_html = ""
    if change is not None:
        arrow = "&#9650;" if change > 0 else "&#9660;" if change < 0 else "&#8211;"
        cls = "kpi-change-neg" if change > 0 else "kpi-change-pos" if change < 0 else ""
        txt = f"{change:+,.0f}"
        if change_pct is not None:
            txt += f" ({change_pct:+.1f}%)"
        change_html = f'<div class="kpi-change {cls}">{arrow} {txt} YoY</div>'

    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {css_class}">{formatted}</div>
        <div class="kpi-sub">{unit}{(' &middot; ' + sub_text) if sub_text else ''}</div>
        {change_html}
    </div>
    """
