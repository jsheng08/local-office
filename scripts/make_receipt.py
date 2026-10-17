"""Generate synthetic demo receipts (fictional data) into data/demo/receipts/.

Run: /usr/bin/python3 scripts/make_receipt.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "data" / "demo" / "receipts"

LINES = [
    "Restoran Nasi Kandar Seri Pantai (SYNTHETIC)",
    "No. 12, Jalan Plumbum, Seksyen 7",
    "40000 Shah Alam, Selangor",
    "SST No: W10-0000-00000000 (fake)",
    "",
    "Date: 2026-10-09   Time: 13:12",
    "Receipt No: SP-0001",
    "--------------------------------",
    "Nasi Kandar Ayam x4       RM  88.00",
    "Ikan Bakar x2             RM  44.00",
    "Teh Tarik x4              RM  16.00",
    "Roti Canai x4             RM  20.00",
    "--------------------------------",
    "Subtotal                  RM 168.00",
    "SST 6%                    RM  10.08",
    "TOTAL                     RM 178.08",
    "--------------------------------",
    "Payment: Card",
    "Note: Client lunch – SPL",
    "",
    "Thank you! Terima kasih!",
]

RECEIPT_002 = """Kopitiam Sri Damansara (SYNTHETIC)
Petaling Jaya, Selangor
SST No: W10-0000-00000001 (fake)

Date: 2026-10-12   Time: 12:40
Receipt No: KD-0002
--------------------------------
Nasi Lemak Rendang x1     RM  18.00
Char Kuey Teow x1         RM  16.00
Kopi O Ais x2             RM   9.00
Set Lunch Platter x1      RM  37.19
--------------------------------
Subtotal                  RM  80.19
SST 6%                    RM   4.81
TOTAL                     RM  85.00
--------------------------------
Payment: Cash
Note: Solo lunch
"""


def load_font(size):
    for path in (
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (600, 900), "white")
    draw = ImageDraw.Draw(img)
    title_font = load_font(20)
    font = load_font(20)
    y = 30
    for i, line in enumerate(LINES):
        f = title_font if i == 0 else font
        draw.text((20, y), line, fill="black", font=f)
        y += 36
    png = OUT / "receipt_grab_001.png"
    img.save(png)
    (OUT / "receipt_grab_001.txt").write_text("\n".join(LINES) + "\n", encoding="utf-8")
    (OUT / "receipt_002.txt").write_text(RECEIPT_002, encoding="utf-8")
    print("wrote", png)


if __name__ == "__main__":
    main()
