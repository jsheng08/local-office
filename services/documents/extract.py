"""Bounded, stdlib-only extraction of simple PDF text streams (not OCR).

Supports literal/hex strings and common text operators; embedded fonts, CMaps,
encryption and complex layouts are intentionally not interpreted.
"""
import re
import zlib

LIMIT = 16 * 1024 * 1024
MARKER = re.compile(r"§(\d+)\.")


def number_paragraphs(text):
    text = text.strip()
    auto = not bool(MARKER.search(text))
    if auto:
        text = "\n\n".join("§%d. %s" % (i, p.strip()) for i, p in
                           enumerate(re.split(r"\n\s*\n", text), 1) if p.strip())
    return text, list(dict.fromkeys("§" + n for n in MARKER.findall(text))), auto


def _tokens(data):
    i = 0
    while i < len(data):
        c = data[i]
        if c in b" \t\r\n\x00\x0c":
            i += 1
        elif c == 37:
            end = data.find(b"\n", i)
            i = len(data) if end < 0 else end + 1
        elif c == 40:
            i += 1
            depth, out = 1, bytearray()
            while i < len(data) and depth:
                c = data[i]; i += 1
                if c == 92:
                    if i >= len(data):
                        break
                    c = data[i]; i += 1
                    if c in b"01234567":
                        octal = bytes([c])
                        while i < len(data) and len(octal) < 3 and data[i] in b"01234567":
                            octal += data[i:i+1]; i += 1
                        out.append(int(octal, 8) & 255)
                    elif c in (10, 13):
                        if c == 13 and data[i:i+1] == b"\n": i += 1
                    else:
                        out.append({110:10,114:13,116:9,98:8,102:12}.get(c,c))
                elif c == 40:
                    depth += 1; out.append(c)
                elif c == 41:
                    depth -= 1
                    if depth: out.append(c)
                else: out.append(c)
            yield bytes(out)
        elif c == 60 and data[i:i+2] != b"<<":
            end = data.find(b">", i+1)
            if end < 0: return
            h = re.sub(rb"\s", b"", data[i+1:end])
            if len(h) % 2: h += b"0"
            try: yield bytes.fromhex(h.decode("ascii"))
            except ValueError: pass
            i = end + 1
        elif c in b"[]<>":
            yield chr(c); i += 1
        else:
            start = i
            while i < len(data) and data[i] not in b" \t\r\n()<>[]%": i += 1
            if i == start: i += 1
            yield data[start:i].decode("latin1")


def _decode(value):
    if value.startswith((b"\xfe\xff", b"\xff\xfe")):
        return value.decode("utf-16", errors="replace")
    return value.decode("cp1252", errors="replace")


def _stream_text(data):
    output, operands = [], []
    active = False
    for token in _tokens(data):
        if token == "BT":
            active = True; operands = []
        elif token == "ET":
            if active: output.append("\n")
            active = False; operands = []
        elif active:
            if token in ("Tj", "TJ", "'", '"'):
                if token in ("'", '"'): output.append("\n")
                output.extend(_decode(t) for t in operands if isinstance(t, bytes))
                operands = []
            elif token in ("Td", "TD", "T*", "Tm"):
                newline = token in ("T*", "Tm")
                if token in ("Td", "TD"):
                    try: newline = float(operands[-1]) != 0
                    except (ValueError, IndexError, TypeError): pass
                if newline: output.append("\n")
                operands = []
            elif isinstance(token, str) and re.fullmatch(r"[A-Za-z]+", token):
                operands = []
            else:
                operands.append(token)
    return "".join(output)


def extract_pdf(data):
    if not data.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF header")
    if b"/Encrypt" in data:
        raise ValueError("Encrypted PDFs are not supported")
    texts, total = [], 0
    # Parse indirect objects, then their stream dictionaries. Stream lengths are
    # preferred when direct; endstream handles indirect /Length objects.
    for obj in re.finditer(rb"\b\d+\s+\d+\s+obj\b(.*?)endobj", data, re.S):
        body = obj.group(1)
        match = re.search(rb"stream\r?\n", body)
        if not match: continue
        header = body[:match.start()]
        length = re.search(rb"/Length\s+(\d+)\s*(?!\d)(?!\s+\d+\s+R)", header)
        raw = body[match.end():]
        raw = raw[:int(length.group(1))] if length else raw.split(b"endstream", 1)[0].rstrip(b"\r\n")
        if b"/FlateDecode" in header:
            decoder = zlib.decompressobj()
            raw = decoder.decompress(raw, LIMIT - total + 1)
            if decoder.unconsumed_tail or not decoder.eof:
                raise ValueError("PDF stream exceeds extraction limit or is incomplete")
        elif b"/Filter" in header:
            continue
        total += len(raw)
        if total > LIMIT: raise ValueError("PDF exceeds extraction limit")
        text = _stream_text(raw)
        if text.strip(): texts.append(text.strip())
    return "\n\n".join(texts)
