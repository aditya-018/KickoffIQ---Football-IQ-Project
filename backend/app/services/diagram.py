PITCH_WIDTH = 760
PITCH_HEIGHT = 500


def render_pitch_svg(scenario_type: str) -> str:
    markers = {
        "offside": _offside_markers(),
        "penalty": _penalty_markers(),
        "throw_in": _throw_in_markers(),
    }[scenario_type]

    return f"""
<svg viewBox="0 0 {PITCH_WIDTH} {PITCH_HEIGHT}" role="img" aria-label="Football pitch diagram" xmlns="http://www.w3.org/2000/svg">
  <rect width="{PITCH_WIDTH}" height="{PITCH_HEIGHT}" rx="12" fill="#147a4a"/>
  <rect x="24" y="24" width="712" height="452" fill="none" stroke="#e9fff3" stroke-width="4"/>
  <line x1="380" y1="24" x2="380" y2="476" stroke="#e9fff3" stroke-width="3"/>
  <circle cx="380" cy="250" r="58" fill="none" stroke="#e9fff3" stroke-width="3"/>
  <rect x="24" y="142" width="112" height="216" fill="none" stroke="#e9fff3" stroke-width="3"/>
  <rect x="624" y="142" width="112" height="216" fill="none" stroke="#e9fff3" stroke-width="3"/>
  <rect x="24" y="196" width="38" height="108" fill="none" stroke="#e9fff3" stroke-width="3"/>
  <rect x="698" y="196" width="38" height="108" fill="none" stroke="#e9fff3" stroke-width="3"/>
  {markers}
</svg>
""".strip()


def _player(x: int, y: int, color: str, label: str) -> str:
    return f"""
  <g>
    <circle cx="{x}" cy="{y}" r="17" fill="{color}" stroke="#ffffff" stroke-width="3"/>
    <text x="{x}" y="{y + 5}" text-anchor="middle" font-size="13" font-weight="700" fill="#ffffff">{label}</text>
  </g>
""".strip()


def _ball(x: int, y: int) -> str:
    return f'<circle cx="{x}" cy="{y}" r="9" fill="#ffffff" stroke="#111827" stroke-width="3"/>'


def _label(x: int, y: int, text: str) -> str:
    return f'<text x="{x}" y="{y}" font-size="17" font-weight="700" fill="#f8fafc">{text}</text>'


def _offside_markers() -> str:
    return "\n  ".join(
        [
            '<line x1="555" y1="24" x2="555" y2="476" stroke="#ffd166" stroke-width="4" stroke-dasharray="10 10"/>',
            _label(566, 54, "second-last defender"),
            _player(610, 218, "#e11d48", "A"),
            _player(500, 302, "#e11d48", "A"),
            _player(555, 250, "#2563eb", "D"),
            _player(690, 250, "#2563eb", "GK"),
            _ball(470, 210),
            '<path d="M480 212 C515 198 555 202 600 216" fill="none" stroke="#ffffff" stroke-width="3" marker-end="url(#arrow)"/>',
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="5" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#ffffff"/></marker></defs>',
        ]
    )


def _penalty_markers() -> str:
    return "\n  ".join(
        [
            '<circle cx="654" cy="250" r="5" fill="#e9fff3"/>',
            '<path d="M650 160 L720 160 L720 340 L650 340 Z" fill="#f43f5e" opacity="0.18"/>',
            _label(500, 126, "foul inside penalty area"),
            _player(655, 244, "#e11d48", "A"),
            _player(638, 270, "#2563eb", "D"),
            _player(704, 250, "#2563eb", "GK"),
            _ball(650, 230),
            '<path d="M638 270 L655 244" stroke="#ffd166" stroke-width="5" stroke-linecap="round"/>',
        ]
    )


def _throw_in_markers() -> str:
    return "\n  ".join(
        [
            '<line x1="24" y1="24" x2="736" y2="24" stroke="#ffd166" stroke-width="7"/>',
            _label(290, 64, "ball crossed the touchline"),
            _player(342, 24, "#e11d48", "A"),
            _player(420, 74, "#2563eb", "D"),
            _ball(342, 8),
            '<path d="M342 8 L342 44" stroke="#ffffff" stroke-width="3" stroke-dasharray="7 7"/>',
        ]
    )
