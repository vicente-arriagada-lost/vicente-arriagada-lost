import json
from pathlib import Path


INPUT = Path("data/contributions.json")
OUTPUT = Path("contrib-heatmap.svg")


# Dimensiones
CELL_SIZE = 13
CELL_GAP = 3

LEFT_MARGIN = 45
TOP_MARGIN = 45
RIGHT_MARGIN = 20
BOTTOM_MARGIN = 35


# Colores
BACKGROUND = "#0d1117"
BORDER = "#30363d"
TEXT = "#8b949e"
TITLE = "#c9d1d9"

LEVEL_COLORS = {
    0: "#161b22",
    1: "#0e4429",
    2: "#006d32",
    3: "#26a641",
    4: "#39d353",
}


def escape(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def get_level(count):
    if count == 0:
        return 0

    if count <= 2:
        return 1

    if count <= 5:
        return 2

    if count <= 9:
        return 3

    return 4


def main():
    if not INPUT.exists():
        raise FileNotFoundError(
            f"No existe {INPUT}. "
            "Primero ejecuta fetch_contributions.py."
        )

    data = json.loads(
        INPUT.read_text(encoding="utf-8")
    )

    weeks = data["weeks"]
    total = data["totalContributions"]

    number_of_weeks = len(weeks)

    width = (
        LEFT_MARGIN
        + number_of_weeks * (CELL_SIZE + CELL_GAP)
        + RIGHT_MARGIN
    )

    height = (
        TOP_MARGIN
        + 7 * (CELL_SIZE + CELL_GAP)
        + BOTTOM_MARGIN
    )

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" '
        f'height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    # Fondo
    svg.append(
        f'<rect '
        f'x="0" '
        f'y="0" '
        f'width="{width}" '
        f'height="{height}" '
        f'rx="12" '
        f'fill="{BACKGROUND}" '
        f'stroke="{BORDER}" '
        f'stroke-width="1"/>'
    )

    # Título
    svg.append(
        f'<text '
        f'x="{LEFT_MARGIN}" '
        f'y="25" '
        f'fill="{TITLE}" '
        f'font-family="monospace" '
        f'font-size="14px" '
        f'font-weight="bold">'
        f'{escape(data["username"])} · '
        f'{total} contributions'
        f'</text>'
    )

    # Días de la semana
    labels = [
        (1, "Mon"),
        (3, "Wed"),
        (5, "Fri"),
    ]

    for row, label in labels:
        y = (
            TOP_MARGIN
            + row * (CELL_SIZE + CELL_GAP)
            + CELL_SIZE - 2
        )

        svg.append(
            f'<text '
            f'x="8" '
            f'y="{y}" '
            f'fill="{TEXT}" '
            f'font-family="monospace" '
            f'font-size="9px">'
            f'{label}'
            f'</text>'
        )

    # Celdas
    for column, week in enumerate(weeks):
        days = week["contributionDays"]

        for row, day in enumerate(days):
            count = day["contributionCount"]
            level = get_level(count)

            x = (
                LEFT_MARGIN
                + column * (CELL_SIZE + CELL_GAP)
            )

            y = (
                TOP_MARGIN
                + row * (CELL_SIZE + CELL_GAP)
            )

            color = LEVEL_COLORS[level]

            svg.append(
                f'<rect '
                f'x="{x}" '
                f'y="{y}" '
                f'width="{CELL_SIZE}" '
                f'height="{CELL_SIZE}" '
                f'rx="2" '
                f'fill="{color}">'
                f'<title>'
                f'{escape(day["date"])}: '
                f'{count} contributions'
                f'</title>'
                f'</rect>'
            )

    # Leyenda
    legend_y = height - 18

    svg.append(
        f'<text '
        f'x="{LEFT_MARGIN}" '
        f'y="{legend_y}" '
        f'fill="{TEXT}" '
        f'font-family="monospace" '
        f'font-size="9px">'
        f'Less'
        f'</text>'
    )

    legend_x = LEFT_MARGIN + 32

    for level in range(5):
        x = (
            legend_x
            + level * (CELL_SIZE + CELL_GAP)
        )

        svg.append(
            f'<rect '
            f'x="{x}" '
            f'y="{legend_y - 9}" '
            f'width="{CELL_SIZE}" '
            f'height="{CELL_SIZE}" '
            f'rx="2" '
            f'fill="{LEVEL_COLORS[level]}"/>'
        )

    svg.append(
        f'<text '
        f'x="{legend_x + 5 * (CELL_SIZE + CELL_GAP) + 3}" '
        f'y="{legend_y}" '
        f'fill="{TEXT}" '
        f'font-family="monospace" '
        f'font-size="9px">'
        f'More'
        f'</text>'
    )

    svg.append("</svg>")

    OUTPUT.write_text(
        "\n".join(svg),
        encoding="utf-8",
    )

    print(f"✓ Heatmap generado: {OUTPUT}")


if __name__ == "__main__":
    main()
