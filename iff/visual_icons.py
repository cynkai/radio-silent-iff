from typing import Final


PATHS: Final = {
    "count": "M4 5h16M4 12h16M4 19h16M8 3v4M16 10v4M10 17v4",
    "accept": "M4 12l5 5L20 6",
    "reject": "M6 6l12 12M6 18L18 6",
    "neutral": "M5 12h14",
    "alert": "M12 3L22 21H2ZM12 9v5M12 17v1",
    "R1": "M5 8a8 8 0 1 1-1 8M5 3v5h5",
    "R2": "M12 2a10 10 0 1 0 0 20 10 10 0 1 0 0-20M12 6v6l4 2",
    "R3": "M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6ZM8 8l8 8M8 16l8-8",
    "R4": "M3 3h12v12H3ZM9 9h12v12H9Z",
    "R5": "M2 12h4l3-8 6 16 3-8h4",
    "R6": "M8 3h8M8 21h8M8 3v5l8 8v5M16 3v5l-8 8v5",
    "R7": "M4 8a11 11 0 0 1 16 0M7 11a7 7 0 0 1 10 0M10 14a3 3 0 0 1 4 0M3 3l18 18",
}


def icon(name: str) -> str:
    return ('<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true" '
            'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
            f'stroke-linejoin="round"><path d="{PATHS[name]}"/></svg>')
