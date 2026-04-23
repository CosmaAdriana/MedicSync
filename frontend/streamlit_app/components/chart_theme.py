"""
MedicSync — Unified Plotly chart theme.
Teal + slate palette, clean gridlines, 14px labels, no colorscales.
"""
import plotly.graph_objects as go

# ── Palette ───────────────────────────────────────────────────────────────────
TEAL       = "#4a9db3"
TEAL_MID   = "#7cbfd1"
TEAL_DARK  = "#2d7a8f"
SLATE_900  = "#0f172a"
SLATE_600  = "#475569"
SLATE_400  = "#94a3b8"
SLATE_200  = "#e2e8f0"
RED        = "#dc2626"
AMBER      = "#d97706"
GREEN      = "#059669"

PALETTE    = [TEAL, SLATE_600, TEAL_MID, AMBER, GREEN, RED, SLATE_400]
PIE_COLORS = [GREEN, RED, SLATE_400]   # admitted / critical / discharged

# ── Base styles ───────────────────────────────────────────────────────────────
_FONT = dict(
    family="'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif",
    size=14,
    color=SLATE_600,
)
_TITLE_FONT = dict(
    family="'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif",
    size=14,
    color=SLATE_900,
)
_AXIS = dict(
    showgrid=True,
    gridcolor=SLATE_200,
    gridwidth=1,
    zeroline=False,
    linecolor=SLATE_200,
    showline=True,
    tickfont=dict(size=13, color=SLATE_400),
    title_font=dict(size=13, color=SLATE_600),
)
_AXIS_NOGRID = {**_AXIS, "showgrid": False, "gridcolor": "rgba(0,0,0,0)"}


# ── Main theme function ───────────────────────────────────────────────────────
def apply(
    fig: go.Figure,
    *,
    title: str = None,
    height: int = 360,
    legend: bool = True,
    xangle: int = 0,
    dual_y: bool = False,
) -> go.Figure:
    """Apply the unified theme to any Figure in-place. Returns fig."""
    layout = dict(
        font=_FONT,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=12, r=16, t=44 if title else 28, b=8),
        xaxis={**_AXIS, "tickangle": xangle},
        yaxis=_AXIS,
        colorway=PALETTE,
        showlegend=legend,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=13, color=SLATE_600),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
        hoverlabel=dict(
            bgcolor=SLATE_900,
            font_size=13,
            font_color="white",
            bordercolor=SLATE_900,
        ),
        hovermode="x unified",
    )
    if title:
        layout["title"] = dict(
            text=title,
            font=_TITLE_FONT,
            x=0, xanchor="left",
            pad=dict(l=0, t=4),
        )
    if dual_y:
        layout["yaxis2"] = {**_AXIS_NOGRID, "overlaying": "y", "side": "right"}
    fig.update_layout(**layout)
    return fig


def bars(fig: go.Figure, color: str = TEAL) -> go.Figure:
    """Style all Bar traces: solid color, no border, clean text."""
    fig.update_traces(
        selector=dict(type="bar"),
        marker_color=color,
        marker_line_width=0,
        textfont=dict(size=13, color=SLATE_600),
    )
    return fig


def lines(fig: go.Figure) -> go.Figure:
    """Style all Scatter/line traces: uniform width, round markers."""
    fig.update_traces(
        selector=dict(mode="lines+markers"),
        line=dict(width=2),
        marker=dict(size=5, line=dict(width=0)),
    )
    return fig
