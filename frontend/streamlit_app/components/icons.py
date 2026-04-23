"""Lucide-style inline SVG icons (stroke-width 1.75, 16×16)."""


def _svg(paths: str, size: int = 16, color: str = "currentColor") -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-2px;display:inline-block">{paths}</svg>'
    )


HOME = _svg(
    '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
    '<polyline points="9 22 9 12 15 12 15 22"/>'
)
HOSPITAL = _svg(
    '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/>'
    '<path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/>'
    '<path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/>'
    '<path d="M10 6h4"/><path d="M10 10h4"/>'
    '<path d="M10 14h4"/><path d="M10 18h4"/>'
)
BUILDING = _svg(
    '<rect width="16" height="20" x="4" y="2" rx="2" ry="2"/>'
    '<path d="M9 22v-4h6v4"/>'
    '<path d="M8 6h.01"/><path d="M16 6h.01"/>'
    '<path d="M12 6h.01"/><path d="M12 10h.01"/>'
    '<path d="M12 14h.01"/><path d="M16 10h.01"/>'
    '<path d="M16 14h.01"/><path d="M8 10h.01"/>'
    '<path d="M8 14h.01"/>'
)
USER = _svg(
    '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>'
    '<circle cx="12" cy="7" r="4"/>'
)
ACTIVITY = _svg('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>')
PACKAGE = _svg(
    '<path d="m7.5 4.27 9 5.15"/>'
    '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>'
    '<path d="m3.3 7 8.7 5 8.7-5"/>'
    '<path d="M12 22V12"/>'
)
CART = _svg(
    '<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/>'
    '<path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>'
)
BAR_CHART = _svg(
    '<line x1="18" x2="18" y1="20" y2="10"/>'
    '<line x1="12" x2="12" y1="20" y2="4"/>'
    '<line x1="6" x2="6" y1="20" y2="14"/>'
)
BOT = _svg(
    '<path d="M12 8V4H8"/>'
    '<rect width="16" height="12" x="4" y="8" rx="2"/>'
    '<path d="M2 14h2"/><path d="M20 14h2"/>'
    '<path d="M15 13v2"/><path d="M9 13v2"/>'
)
CALENDAR = _svg(
    '<rect width="18" height="18" x="3" y="4" rx="2" ry="2"/>'
    '<line x1="16" x2="16" y1="2" y2="6"/>'
    '<line x1="8" x2="8" y1="2" y2="6"/>'
    '<line x1="3" x2="21" y1="10" y2="10"/>'
)
LOGOUT = _svg(
    '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
    '<polyline points="16 17 21 12 16 7"/>'
    '<line x1="21" x2="9" y1="12" y2="12"/>'
)
BELL = _svg(
    '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>'
    '<path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>'
)
LOCK = _svg(
    '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>'
    '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
)
ALERT = _svg(
    '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
    '<path d="M12 9v4"/><path d="M12 17h.01"/>'
)
ALERT_CIRCLE = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<line x1="12" x2="12" y1="8" y2="12"/>'
    '<line x1="12" x2="12.01" y1="16" y2="16"/>'
)
CHECK_CIRCLE = _svg(
    '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
    '<polyline points="22 4 12 14.01 9 11.01"/>'
)
X_CIRCLE = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<path d="m15 9-6 6"/><path d="m9 9 6 6"/>'
)
FILE_TEXT = _svg(
    '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>'
    '<polyline points="14 2 14 8 20 8"/>'
    '<line x1="16" x2="8" y1="13" y2="13"/>'
    '<line x1="16" x2="8" y1="17" y2="17"/>'
    '<line x1="10" x2="8" y1="9" y2="9"/>'
)
MAIL = _svg(
    '<rect width="20" height="16" x="2" y="4" rx="2"/>'
    '<path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>'
)
SETTINGS = _svg(
    '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>'
    '<circle cx="12" cy="12" r="3"/>'
)
CLOCK = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<polyline points="12 6 12 12 16 14"/>'
)
UMBRELLA = _svg(
    '<path d="M23 12a11.05 11.05 0 0 0-22 0zm-5 7a3 3 0 0 1-6 0v-7"/>'
)
SUN = _svg(
    '<circle cx="12" cy="12" r="4"/>'
    '<path d="M12 2v2"/><path d="M12 20v2"/>'
    '<path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/>'
    '<path d="M2 12h2"/><path d="M20 12h2"/>'
    '<path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>'
)
SNOWFLAKE = _svg(
    '<line x1="2" x2="22" y1="12" y2="12"/>'
    '<line x1="12" x2="12" y1="2" y2="22"/>'
    '<path d="m20 16-4-4 4-4"/><path d="m4 8 4 4-4 4"/>'
    '<path d="m16 4-4 4-4-4"/><path d="m8 20 4-4 4 4"/>'
)
LEAF = _svg(
    '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>'
    '<path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>'
)
FLOWER = _svg(
    '<path d="M12 7.5a4.5 4.5 0 1 1 4.5 4.5M12 7.5A4.5 4.5 0 1 0 7.5 12M12 7.5V9m-4.5 3H9m3 4.5v-1.5m4.5-3H15"/>'
    '<circle cx="12" cy="12" r="3"/>'
    '<path d="m8 16 1.5-1.5"/>'
)
TRASH = _svg(
    '<path d="M3 6h18"/>'
    '<path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>'
    '<path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>'
)
PLUS = _svg('<path d="M5 12h14"/><path d="M12 5v14"/>')
TARGET = _svg(
    '<circle cx="12" cy="12" r="10"/>'
    '<circle cx="12" cy="12" r="6"/>'
    '<circle cx="12" cy="12" r="2"/>'
)
TRUCK = _svg(
    '<path d="M5 17H3a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11v10"/>'
    '<path d="M12 17h9"/><path d="M14.5 17v-5h7l2 5"/>'
    '<circle cx="7.5" cy="17.5" r="2.5"/>'
    '<circle cx="17.5" cy="17.5" r="2.5"/>'
)
