from pathlib import Path
from PIL import Image


INPUT = Path("source-prepped.png")
OUTPUT = Path("ascii.svg")

# Tamaño aproximado del ASCII.
COLUMNS = 100
ROWS = 53

# Caracteres ordenados de claro → oscuro.
RAMP = " .`:-=+*cs#%@"

# Apariencia
FONT_SIZE = 12
CHAR_WIDTH = 0.60
COLOR = "#c9d1d9"

# Animación
ROW_DELAY = 0.055
ROW_DURATION = 0.45


def brightness_to_char(brightness):
    """
    Convierte luminosidad 0-255 en un carácter.
    0   = negro
    255 = blanco
    """
    index = int((255 - brightness) / 255 * (len(RAMP) - 1))
    return RAMP[index]


def resize_image(image):
    """
    Ajusta la imagen a nuestra cuadrícula ASCII.
    """
    return image.resize(
        (COLUMNS, ROWS),
        Image.Resampling.LANCZOS
    )


def generate_ascii(image):
    pixels = image.load()

    rows = []

    for y in range(ROWS):
        line = []

        for x in range(COLUMNS):
            brightness = pixels[x, y]
            char = brightness_to_char(brightness)

            line.append(char)

        rows.append("".join(line))

    return rows


def escape_xml(text):
    """
    Escapa caracteres especiales para SVG/XML.
    """
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def create_svg(rows):
    width = int(COLUMNS * FONT_SIZE * CHAR_WIDTH)
    height = int(ROWS * FONT_SIZE * 1.15)

    svg = []

    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )

    svg.append("""
<style>
.ascii-row {
    opacity: 0;
    animation: appear 0.45s ease-out forwards;
}

@keyframes appear {
    from {
        opacity: 0;
        transform: translateX(-12px);
    }

    to {
        opacity: 1;
        transform: translateX(0);
    }
}
</style>
""")

    svg.append(
        f'<rect width="100%" height="100%" fill="white"/>'
    )

    for y, row in enumerate(rows):

        # No renderizar filas completamente vacías.
        if not row.strip():
            continue

        escaped = escape_xml(row)

        x = 0
        y_position = int((y + 1) * FONT_SIZE * 1.15)

        delay = y * ROW_DELAY

        svg.append(
            f'<text '
            f'x="{x}" '
            f'y="{y_position}" '
            f'class="ascii-row" '
            f'fill="{COLOR}" '
            f'font-family="monospace" '
            f'font-size="{FONT_SIZE}px" '
            f'xml:space="preserve" '
            f'style="animation-delay:{delay:.3f}s">'
            f'{escaped}'
            f'</text>'
        )

    svg.append("</svg>")

    return "\n".join(svg)


def main():
    if not INPUT.exists():
        raise SystemExit(
            f"No se encontró {INPUT}"
        )

    print("[1/3] Cargando imagen...")

    image = Image.open(INPUT).convert("L")

    print("[2/3] Generando ASCII...")

    image = resize_image(image)

    rows = generate_ascii(image)

    print("[3/3] Generando SVG...")

    svg = create_svg(rows)

    OUTPUT.write_text(svg, encoding="utf-8")

    print()
    print(f"SVG generado correctamente: {OUTPUT}")
    print(f"Tamaño: {COLUMNS} x {ROWS}")
    print(f"Caracteres: {COLUMNS * ROWS}")


if __name__ == "__main__":
    main()
