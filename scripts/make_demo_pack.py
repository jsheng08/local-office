#!/usr/bin/env python3
"""Generate synthetic upload artifacts using only the standard library and macOS tools."""
import html
import subprocess
import textwrap
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = "Sinar Pantai Logistics - CONFIDENTIAL - synthetic demo data"


def wrapped(text, width=88):
    return [line for paragraph in text.splitlines()
            for line in (textwrap.wrap(paragraph, width=width, break_long_words=False,
                                       break_on_hyphens=False) or [""])]


def pdf_bytes(text):
    lines = wrapped(text)
    pages = [lines[i:i+46] for i in range(0, len(lines), 46)]
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", 
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]
    ids = []
    def literal(value):
        return value.encode("cp1252").replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
    for n, page in enumerate(pages, 1):
        page_id = len(objects) + 1; ids.append(page_id)
        objects.append(("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % (page_id+1)).encode())
        stream = b"BT /F1 9 Tf 42 802 Td (" + literal(HEADER) + b") Tj ET\n"
        stream += b"BT /F1 11 Tf 14 TL 42 770 Td\n"
        stream += b"\n".join(b"(" + literal(line) + b") Tj T*" for line in page) + b"\nET\n"
        stream += b"BT /F1 9 Tf 42 30 Td (" + literal("Page %d of %d" % (n, len(pages))) + b") Tj ET"
        packed = zlib.compress(stream)
        objects.append(("<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(packed)).encode() + packed + b"\nendstream")
    objects[1] = ("<< /Type /Pages /Kids [%s] /Count %d >>" % (" ".join("%d 0 R" % p for p in ids), len(ids))).encode()
    out, offsets = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"), [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out)); out.extend(("%d 0 obj\n" % i).encode() + obj + b"\nendobj\n")
    xref = len(out)
    out.extend(("xref\n0 %d\n0000000000 65535 f \n" % len(offsets)).encode())
    for offset in offsets[1:]: out.extend(("%010d 00000 n \n" % offset).encode())
    out.extend(("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(offsets), xref)).encode())
    return bytes(out)


def main():
    dest = ROOT / "demo_uploads"; dest.mkdir(exist_ok=True)
    v2 = ""
    for version, filename in ((1, "1_SPL_client_brief_v1.pdf"), (2, "2_SPL_client_brief_v2_CHANGED.pdf")):
        text = (ROOT / "data/demo" / ("requirements_v%d.md" % version)).read_text(encoding="utf-8")
        (dest / filename).write_bytes(pdf_bytes(text))
        if version == 2: v2 = text
    (dest / "3_SPL_brief_v2.md").write_text(v2, encoding="utf-8")
    lines = wrapped(v2, 104)
    height = 150 + len(lines) * 20
    svg = dest / "4_SPL_brief_v2_photo_of_page.svg"
    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="%d" viewBox="0 0 1400 %d">' % (height+120, height+120)
                   + '<rect width="100%%" height="100%%" fill="#10201f"/>'.replace('%%','%')
                   + '<rect x="104" y="64" width="1210" height="%d" rx="5" fill="#080f0e"/>' % height
                   + '<rect x="90" y="50" width="1210" height="%d" fill="#efe7d8"/>' % height
                   + '<g fill="#162523" font-family="Helvetica,Arial,sans-serif" font-size="19">'
                   + '<text x="130" y="95" font-size="17">' + HEADER + '</text>'
                   + ''.join('<text x="130" y="%d">%s</text>' % (140+i*20, html.escape(line)) for i,line in enumerate(lines))
                   + '</g></svg>', encoding="utf-8")
    png = dest / "4_SPL_brief_v2_photo_of_page.png"
    errors = []
    for command in (["qlmanage", "-t", "-s", "1800", "-o", str(dest), str(svg)],
                    ["sips", "-s", "format", "png", str(svg), "--out", str(png)]):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=45)
            thumbnail = dest / (svg.name + ".png")
            if thumbnail.exists(): thumbnail.replace(png)
            if result.returncode == 0 and png.exists(): break
            errors.append(result.stderr.strip() or result.stdout.strip())
        except (OSError, subprocess.TimeoutExpired) as exc: errors.append(str(exc))
    generated = png.exists()
    (dest / "README.md").write_text('''# Local Office synthetic upload pack

1. Drop `1_SPL_client_brief_v1.pdf` into PRJ-SPL first. Run local Nemotron analysis, inspect citations and proposed tasks, then have the PM approve.
2. Drop `2_SPL_client_brief_v2_CHANGED.pdf` next. Re-analyze to show §6 deferred, §8 PDPA controls promoted, §9 earlier go-live, and §11 e-invoicing added. Review before/after proposals; PM approval is required to apply changes.
3. `3_SPL_brief_v2.md` is the equivalent UTF-8 text upload.
4. `4_SPL_brief_v2_photo_of_page.png` is a synthetic printed-page-on-a-desk illustration of the v2 text. It needs the local Omni model; OCR accuracy and the image upload path are **unverified until tested live**. The SVG source is retained for reproducibility and is not an accepted upload format.

The PDFs use Helvetica/WinAnsi with searchable text and multiple pages. PDF extraction is a limited stdlib parser; arbitrary embedded-font or scanned PDFs are not guaranteed. Scanned PDFs must be uploaded as page images. All content is confidential-labelled synthetic demo data.

Leave windows use `LO_TODAY=2026-10-17` for a reproducible demo, otherwise the machine's current date. No approved assignments are changed by the leave filter.

Regenerate with `.venv/bin/python scripts/make_demo_pack.py` (PNG conversion needs macOS qlmanage or sips).

PNG generation: ''' + ("succeeded; transcription not tested.\n" if generated else "FAILED: qlmanage and sips could not convert the SVG; PNG unavailable.\n"), encoding="utf-8")
    print("Generated PDFs, markdown, SVG and README in", dest)
    print("PNG generated" if generated else "PNG FAILED (qlmanage and sips): " + " | ".join(errors))


if __name__ == "__main__": main()
