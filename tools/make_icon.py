# -*- coding: utf-8 -*-
"""
Gerador do icone comercial do Farma Quantum.

Gera 'farma_quantum.ico' (multi-resolucao) e 'farma_quantum.png' (preview),
usados pelo build do .exe. Design: cruz farmaceutica branca sobre um
"squircle" com gradiente esmeralda/teal, anel sutil e brilho superior.

Uso:
    python tools/make_icon.py
"""
from PIL import Image, ImageDraw, ImageFilter

# Render em alta resolucao e reduz (supersampling) para bordas suaves.
S = 1024
ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]

# Paleta (identidade de farmacia / saude)
TOP = (16, 185, 168)     # teal #10b9a8
BOTTOM = (5, 102, 74)    # verde escuro #05664a
CROSS = (255, 255, 255)


def _gradient(size, top, bottom):
    base = Image.new("RGB", (size, size), top)
    grad = Image.new("L", (1, size))
    for y in range(size):
        grad.putpixel((0, y), int(255 * y / max(1, size - 1)))
    grad = grad.resize((size, size))
    bottom_img = Image.new("RGB", (size, size), bottom)
    return Image.composite(bottom_img, base, grad)


def _rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


def _cross_polygon(cx, cy, arm_len, arm_w, radius):
    """Desenha uma cruz (sinal de +) com bracos arredondados."""
    img = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(img)
    # barra vertical e horizontal
    d.rounded_rectangle(
        [cx - arm_w / 2, cy - arm_len / 2, cx + arm_w / 2, cy + arm_len / 2],
        radius=radius, fill=255,
    )
    d.rounded_rectangle(
        [cx - arm_len / 2, cy - arm_w / 2, cx + arm_len / 2, cy + arm_w / 2],
        radius=radius, fill=255,
    )
    return img


def build():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # 1) Fundo com gradiente em squircle
    grad = _gradient(S, TOP, BOTTOM).convert("RGBA")
    mask = _rounded_mask(S, radius=int(S * 0.235))
    img = Image.composite(grad, img, mask)

    draw = ImageDraw.Draw(img)

    # 2) Brilho superior (highlight) sutil
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([int(S * 0.05), int(-S * 0.45), int(S * 0.95), int(S * 0.45)],
                  fill=(255, 255, 255, 55))
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.04))
    glow = Image.composite(glow, Image.new("RGBA", (S, S), (0, 0, 0, 0)), mask)
    img = Image.alpha_composite(img, glow)

    # 3) Anel/badge atras da cruz
    ring = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(ring)
    r_out = int(S * 0.33)
    cx = cy = S // 2
    rdraw.ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out],
                  outline=(255, 255, 255, 70), width=int(S * 0.018))
    img = Image.alpha_composite(img, ring)

    # 4) Sombra da cruz
    arm_len = int(S * 0.46)
    arm_w = int(S * 0.155)
    radius = int(arm_w * 0.32)
    shadow_src = _cross_polygon(cx, cy + int(S * 0.012), arm_len, arm_w, radius)
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shadow.paste((0, 60, 45, 130), (0, 0), shadow_src)
    shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.012))
    img = Image.alpha_composite(img, shadow)

    # 5) Cruz farmaceutica branca
    cross_a = _cross_polygon(cx, cy, arm_len, arm_w, radius)
    cross_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cross_layer.paste(CROSS + (255,), (0, 0), cross_a)
    img = Image.alpha_composite(img, cross_layer)

    # Exporta preview PNG (256) e o ICO multi-resolucao
    base = img.resize((256, 256), Image.LANCZOS)
    base.save("farma_quantum.png")
    # O Pillow gera todas as resolucoes a partir da imagem base de 256x256.
    base.save("farma_quantum.ico", format="ICO",
              sizes=[(s, s) for s in ICON_SIZES])
    print("Gerado: farma_quantum.ico e farma_quantum.png")


if __name__ == "__main__":
    build()
