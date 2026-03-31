"""
Banking-specific style helpers.
Enhanced KPI cards with sparklines, QoQ, and YoY changes.
"""

import numpy as np
import hashlib


# ── SVG sparkline generator ───────────────────────────────────────────

def _sparkline_svg(values, width=80, height=24, color="#00D4FF", neg_color="#FF6B8A"):
    """Generate a tiny inline SVG sparkline from a list of numeric values."""
    vals = [v for v in values if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if len(vals) < 2:
        return ""

    mn, mx = min(vals), max(vals)
    rng = mx - mn if mx != mn else 1
    pad = 2  # padding
    w = width - 2 * pad
    h = height - 2 * pad

    points = []
    for i, v in enumerate(vals):
        x = pad + (i / (len(vals) - 1)) * w
        y = pad + h - ((v - mn) / rng) * h
        points.append(f"{x:.1f},{y:.1f}")

    polyline = " ".join(points)
    # Determine color: if last value > first, use positive color
    line_color = color if vals[-1] >= vals[0] else neg_color

    # Area fill (gradient from line to bottom)
    area_points = points + [f"{pad + w:.1f},{pad + h:.1f}", f"{pad:.1f},{pad + h:.1f}"]
    area_poly = " ".join(area_points)

    # Unique gradient ID to avoid collisions when multiple sparklines on page
    uid = hashlib.md5(polyline.encode()).hexdigest()[:8]
    gid = f"sf{uid}"

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="display:block;margin:4px auto 0;">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{line_color}" stop-opacity="0.15"/>'
        f'<stop offset="100%" stop-color="{line_color}" stop-opacity="0.01"/>'
        f'</linearGradient></defs>'
        f'<polygon points="{area_poly}" fill="url(#{gid})"/>'
        f'<polyline points="{polyline}" fill="none" stroke="{line_color}" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{points[-1].split(",")[0]}" cy="{points[-1].split(",")[1]}" '
        f'r="2" fill="{line_color}"/>'
        f'</svg>'
    )


# ── Change indicator HTML ─────────────────────────────────────────────

def _change_html(label, abs_change, pct_change, reverse_color=False):
    """Generate a compact change indicator line (e.g. 'QoQ: ▲ +1,234 (+2.1%)')."""
    if abs_change is None:
        return ""
    arrow = "&#9650;" if abs_change > 0 else "&#9660;" if abs_change < 0 else "&#8211;"
    # For external sector: deficit increase = bad (red for positive).
    # For banking: profit increase = good (green for positive). So normal coloring.
    if reverse_color:
        cls = "kpi-chg-neg" if abs_change > 0 else "kpi-chg-pos" if abs_change < 0 else ""
    else:
        cls = "kpi-chg-pos" if abs_change > 0 else "kpi-chg-neg" if abs_change < 0 else ""
    txt = f"{abs_change:+,.0f}"
    if pct_change is not None and pct_change != 0:
        txt += f" ({pct_change:+.1f}%)"
    return f'<span class="bk-change {cls}">{arrow} {txt} {label}</span>'


def _pct_change_html(label, pct_change, reverse_color=False):
    """Change indicator for ratio metrics (show only bp or pp change)."""
    if pct_change is None:
        return ""
    # Convert to basis points for small ratios
    bp = pct_change * 10000
    arrow = "&#9650;" if pct_change > 0 else "&#9660;" if pct_change < 0 else "&#8211;"
    if reverse_color:
        cls = "kpi-chg-neg" if pct_change > 0 else "kpi-chg-pos" if pct_change < 0 else ""
    else:
        cls = "kpi-chg-pos" if pct_change > 0 else "kpi-chg-neg" if pct_change < 0 else ""
    txt = f"{bp:+.0f} bp"
    return f'<span class="bk-change {cls}">{arrow} {txt} {label}</span>'


# ── Enhanced banking KPI card ─────────────────────────────────────────

def enhanced_kpi(label, value, unit="RSD 000", css_class="kpi-neutral",
                 sub_text="", sparkline_values=None,
                 qoq_abs=None, qoq_pct=None,
                 yoy_abs=None, yoy_pct=None,
                 is_ratio=False, higher_is_better=True):
    """Generate an enhanced KPI card with sparkline and QoQ/YoY changes.

    Args:
        label: KPI title
        value: current value
        unit: display unit
        css_class: kpi-positive, kpi-negative, or kpi-neutral
        sub_text: quarter label
        sparkline_values: list of recent values for sparkline (8 quarters)
        qoq_abs/qoq_pct: quarter-over-quarter changes
        yoy_abs/yoy_pct: year-over-year changes
        is_ratio: if True, show changes in basis points instead of absolute
        higher_is_better: determines color direction for changes
    """
    # Format value
    if value is None:
        formatted = "N/A"
    elif is_ratio:
        formatted = f"{value:.2%}"
    elif abs(value) >= 1e9:
        formatted = f"{value / 1e6:,.0f}M"
    elif abs(value) >= 1e6:
        formatted = f"{value / 1e3:,.0f}K"
    elif abs(value) >= 1000:
        formatted = f"{value:,.0f}"
    else:
        formatted = f"{value:,.1f}"

    # Sparkline
    spark_html = ""
    if sparkline_values and len(sparkline_values) >= 2:
        spark_html = _sparkline_svg(sparkline_values)

    # Change indicators
    reverse = not higher_is_better
    changes_parts = []
    if is_ratio:
        if qoq_pct is not None:
            changes_parts.append(_pct_change_html("QoQ", qoq_pct, reverse))
        if yoy_pct is not None:
            changes_parts.append(_pct_change_html("YoY", yoy_pct, reverse))
    else:
        if qoq_abs is not None or qoq_pct is not None:
            changes_parts.append(_change_html("QoQ", qoq_abs, qoq_pct, reverse))
        if yoy_abs is not None or yoy_pct is not None:
            changes_parts.append(_change_html("YoY", yoy_abs, yoy_pct, reverse))

    changes_html = "<br>".join(changes_parts)
    if changes_html:
        changes_html = f'<div class="bk-changes">{changes_html}</div>'

    return f"""
    <div class="kpi-card bk-kpi">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {css_class}">{formatted}</div>
        <div class="kpi-sub">{unit}{(' &middot; ' + sub_text) if sub_text else ''}</div>
        {spark_html}
        {changes_html}
    </div>
    """


# ── CSS for enhanced banking KPIs ─────────────────────────────────────

BANKING_CSS = """
    .bk-kpi {
        min-height: 140px;
    }
    .bk-changes {
        margin-top: 4px;
        line-height: 1.5;
    }
    .bk-change {
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.2px;
        white-space: nowrap;
    }
    .kpi-chg-pos { color: #06D6A0; }
    .kpi-chg-neg { color: #FF6B8A; }
"""

BANKING_CSS_LIGHT = """
    .kpi-chg-pos { color: #059669 !important; }
    .kpi-chg-neg { color: #DC2626 !important; }
"""


def get_banking_css(theme="light"):
    """Return banking-specific CSS."""
    css = BANKING_CSS
    if theme == "light":
        css += BANKING_CSS_LIGHT
    return f"<style>{css}</style>"


# ── Helpers kept for compatibility ────────────────────────────────────

def signal_icon(value, threshold_good, threshold_bad, higher_is_better=True):
    """Return a signal indicator string."""
    if higher_is_better:
        if value >= threshold_good:
            return "above-avg"
        elif value <= threshold_bad:
            return "below-avg"
    else:
        if value <= threshold_good:
            return "above-avg"
        elif value >= threshold_bad:
            return "below-avg"
    return "avg"
