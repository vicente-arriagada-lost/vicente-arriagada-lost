from pathlib import Path

OUTPUT = Path("info-card.svg")

WIDTH = 700
HEIGHT = 750

BACKGROUND = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
ACCENT = "#58a6ff"
GREEN = "#3fb950"

INFO = [
    ("OS", "Void Linux"),
    ("DE", "KDE Plasma"),
    ("WM", "KWin Wayland"),
    ("Shell", "Bash"),
]

STACK = [
    "Kotlin",
    "Java",
    "Spring Boot",
    "React",
    "SQL",
    "Git",
]

FOCUS = [
    "Cybersecurity",
    "CTF",
    "Linux",
    "Software Development",
]

TOOLS = [
    "Docker",
    "PostgreSQL",
    "MongoDB",
    "DBeaver",
]


def esc(text):
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def add_text(
    svg,
    x,
    y,
    text,
    color=TEXT,
    size=16,
    weight="normal",
    delay=0,
):
    svg.append(
        f'<text '
        f'x="{x}" '
        f'y="{y}" '
        f'fill="{color}" '
        f'font-family="monospace" '
        f'font-size="{size}px" '
        f'font-weight="{weight}" '
        f'opacity="1">'
        f'{esc(text)}'
        f'<animate '
        f'attributeName="opacity" '
        f'values="0;1" '
        f'dur="0.45s" '
        f'begin="{delay:.2f}s" '
        f'fill="freeze"/>'
        f'</text>'
    )


def main():
    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{WIDTH}" '
        f'height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">'
    )

    # Fondo principal
    svg.append(
        f'<rect '
        f'x="1" '
        f'y="1" '
        f'width="{WIDTH - 2}" '
        f'height="{HEIGHT - 2}" '
        f'rx="12" '
        f'fill="{BACKGROUND}" '
        f'stroke="{BORDER}" '
        f'stroke-width="2"/>'
    )

    # Barra superior estilo terminal
    svg.append(
        f'<rect '
        f'x="1" '
        f'y="1" '
        f'width="{WIDTH - 2}" '
        f'height="42" '
        f'rx="12" '
        f'fill="#161b22"/>'
    )

    # Botones de ventana
    svg.append('<circle cx="22" cy="22" r="6" fill="#ff5f56"/>')
    svg.append('<circle cx="42" cy="22" r="6" fill="#ffbd2e"/>')
    svg.append('<circle cx="62" cy="22" r="6" fill="#27c93f"/>')

    # Terminal title
    add_text(
        svg,
        90,
        28,
        "vicente@github",
        MUTED,
        14,
        "normal",
        0.1,
    )

    # whoami
    add_text(
        svg,
        28,
        78,
        "whoami",
        GREEN,
        18,
        "bold",
        0.3,
    )

    add_text(
        svg,
        28,
        104,
        "Vicente Arriagada",
        TEXT,
        17,
        "bold",
        0.4,
    )

    # Información del sistema
    y = 142
    delay = 0.55

    for key, value in INFO:
        add_text(
            svg,
            28,
            y,
            f"{key:<8}",
            ACCENT,
            14,
            "bold",
            delay,
        )

        add_text(
            svg,
            125,
            y,
            value,
            TEXT,
            14,
            "normal",
            delay + 0.05,
        )

        y += 28
        delay += 0.08

    # Stack
    y += 12

    add_text(
        svg,
        28,
        y,
        "Stack",
        GREEN,
        17,
        "bold",
        delay,
    )

    y += 30
    delay += 0.08

    for index, item in enumerate(STACK):
        prefix = "└─" if index == len(STACK) - 1 else "├─"

        add_text(
            svg,
            32,
            y,
            f"{prefix} {item}",
            TEXT,
            14,
            "normal",
            delay,
        )

        y += 25
        delay += 0.07

    # Focus
    y += 12

    add_text(
        svg,
        28,
        y,
        "Focus",
        GREEN,
        17,
        "bold",
        delay,
    )

    y += 30
    delay += 0.08

    for index, item in enumerate(FOCUS):
        prefix = "└─" if index == len(FOCUS) - 1 else "├─"

        add_text(
            svg,
            32,
            y,
            f"{prefix} {item}",
            TEXT,
            14,
            "normal",
            delay,
        )

        y += 25
        delay += 0.07

    # Tools
    y += 12

    add_text(
        svg,
        28,
        y,
        "Tools",
        GREEN,
        17,
        "bold",
        delay,
    )

    y += 30
    delay += 0.08

    for index, item in enumerate(TOOLS):
        prefix = "└─" if index == len(TOOLS) - 1 else "├─"

        add_text(
            svg,
            32,
            y,
            f"{prefix} {item}",
            TEXT,
            14,
            "normal",
            delay,
        )

        y += 25
        delay += 0.07

    svg.append("</svg>")

    OUTPUT.write_text(
        "\n".join(svg),
        encoding="utf-8",
    )

    print(f"Info card creada: {OUTPUT}")


if __name__ == "__main__":
    main()
