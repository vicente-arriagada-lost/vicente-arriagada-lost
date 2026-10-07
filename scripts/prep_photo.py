from pathlib import Path
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove


INPUT = Path("source-photo.jpg")
OUTPUT = Path("source-prepped.png")


def main():
    if not INPUT.exists():
        print(f"ERROR: No se encontró {INPUT}")
        sys.exit(1)

    print("[1/3] Cargando imagen...")

    image = Image.open(INPUT).convert("RGBA")

    print("[2/3] Eliminando fondo...")

    image_no_bg = remove(image)

    # Crear fondo blanco
    background = Image.new("RGBA", image_no_bg.size, "white")
    background.alpha_composite(image_no_bg)

    # Convertir a RGB para OpenCV
    rgb = background.convert("RGB")
    img = np.array(rgb)

    # PIL usa RGB, OpenCV usa BGR
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    print("[3/3] Mejorando contraste...")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # CLAHE mejora el contraste local de la imagen.
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # Volver a RGB
    output = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)

    Image.fromarray(output).save(OUTPUT)

    print()
    print(f"Imagen preparada correctamente: {OUTPUT}")


if __name__ == "__main__":
    main()
