from pathlib import Path
from PIL import Image


INPUT = Path("source-prepped.png")
OUTPUT = Path("ascii.svg")

COLUMNS = 100
ROWS = 53

# Negro = caracteres densos
# Blanco = espacio
RAMP = "@%#*+=-:.` "

FONT_SIZE = 12
CHAR_WIDTH = 0.60

BACKGROUND = "#0d1117"
COLOR = "#f0f6fc"
BORDER = "#30363d"

ROW_DELAY = 0.055
ROW_DURATION = 0.45


def main():
    image = Image.open(INPUT).convert("L")

    image = image.resize(
        (COLUMNS, ROWS)
    )

    pixels = image.load()

    width = int(
        COLUMNS * FONT_SIZE * CHAR_WIDTH
    )

    height = int(
        ROWS * FONT_SIZE * 1.15
    )

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" '
        f'height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    # Fondo negro estilo GitHub
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

    for row in range(ROWS):
        text = ""

        for column in range(COLUMNS):
            value = pixels[column, row]

            # Imagen:
            #
            # Negro  -> @
            # Gris   -> caracteres intermedios
            # Blanco -> espacio
            #
            index = int(
                (255 - value)
                / 255
                * (len(RAMP) - 1)
            )

            text += RAMP[index]

        y = (row + 1) * FONT_SIZE

        delay = row * ROW_DELAY

        svg.append(
            f'<text '
            f'x="8" '
            f'y="{y}" '
            f'fill="{COLOR}" '
            f'font-family="monospace" '
            f'font-size="{FONT_SIZE}px" '
            f'xml:space="preserve">'
            f'{text}'
            f'<animate '
            f'attributeName="opacity" '
            f'values="0;1" '
            f'dur="{ROW_DURATION}s" '
            f'begin="{delay}s" '
            f'fill="freeze"/>'
            f'</text>'
        )

    svg.append("</svg>")

    OUTPUT.write_text(
        "\n".join(svg),
        encoding="utf-8",
    )

    print(
        f"✓ ASCII SVG generado: {OUTPUT}"
    )


if __name__ == "__main__":
    main()
