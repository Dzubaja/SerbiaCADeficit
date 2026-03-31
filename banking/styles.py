"""
Banking-specific style helpers.
Reuses the existing KPI card pattern from dashboard.styles.
"""

from dashboard.styles import kpi_card  # reuse existing KPI card


def bank_kpi(label, value, fmt="{:,.0f}", unit="RSD 000",
             css_class="kpi-neutral", sub_text="", change=None, change_pct=None):
    """Convenience wrapper for banking KPI cards."""
    if value is None:
        return kpi_card(label, 0, unit=unit, css_class=css_class,
                        sub_text=sub_text)

    # Auto-detect format
    if isinstance(fmt, str) and "%" in fmt:
        formatted_val = value * 100  # kpi_card expects the raw number
        unit = "%"
    else:
        formatted_val = value

    return kpi_card(
        label, formatted_val, unit=unit, css_class=css_class,
        sub_text=sub_text, change=change, change_pct=change_pct,
    )


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
