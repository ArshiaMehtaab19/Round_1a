import fitz  # PyMuPDF
import json
import re
import statistics
import unicodedata
from pathlib import Path

# ------------ CONFIG ------------
INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
MAX_PAGES = 50
MAX_TITLE_LINES = 4
MERGE_FONT_EPS = 0.25
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
# --------------------------------

RE_NUMERIC = re.compile(r"^\d+(\.\d+)(\s+.)?$")
RE_NUMERIC_STRICT = re.compile(r"^\d+(\.\d+)*\s+[A-Za-z]")
RE_LEADING_KEYWORD = re.compile(r"^(Chapter|Section|Appendix|Table of Contents|Contents)\b", re.I)
RE_HAS_UPPER = re.compile(r"[A-Z]")
RE_DEVANAGARI = re.compile(r"[\u0900-\u097F]")

def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[.·•…]+$", "", text)
    text = re.sub(r"[\uFFFD\uFFFC\uFFFB\uFEFF]", "", text)  # BOMs, invisible
    text = re.sub(r"[�￱￭￸]+", "", text)  # Corrupt glyphs from fonts
    return text

def looks_like_numbered(text: str) -> bool:
    return bool(RE_NUMERIC_STRICT.match(text) or RE_LEADING_KEYWORD.match(text))

def is_heading_candidate_base(text: str) -> bool:
    if not text:
        return False
    if RE_DEVANAGARI.search(text):
        return True
    if text[0].islower():
        return False
    if not RE_HAS_UPPER.search(text):
        return False
    return True

def classify_level_by_font(size, h1, h2, h3):
    if size >= h1 - 0.5:
        return "H1"
    elif size >= h2 - 0.5:
        return "H2"
    elif size >= h3 - 0.5:
        return "H3"
    return None

def normalize_from_toc(toc):
    outline = []
    for level, title, page in toc:
        if level <= 1:
            lvl = "H1"
        elif level == 2:
            lvl = "H2"
        else:
            lvl = "H3"
        outline.append({"level": lvl, "text": clean_text(title), "page": page})
    return outline

def infer_title(doc):
    try:
        page = doc[0]
    except Exception:
        return ""
    spans = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                txt = clean_text(span["text"])
                if txt:
                    spans.append((txt, span["size"]))
    if not spans:
        return ""
    spans.sort(key=lambda x: -x[1])
    max_font = spans[0][1]
    title_lines = [txt for txt, sz in spans if abs(sz - max_font) < 0.5][:MAX_TITLE_LINES]
    return clean_text(" ".join(title_lines)) if title_lines else ""

def extract_candidates(doc, title):
    candidates = []
    all_font_sizes = []
    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                line_text = ""
                max_font = 0.0
                for span in line.get("spans", []):
                    txt = clean_text(span["text"])
                    if not txt:
                        continue
                    line_text += txt + " "
                    sz = span["size"]
                    all_font_sizes.append(sz)
                    max_font = max(max_font, sz)
                line_text = clean_text(line_text)
                if not line_text:
                    continue
                if is_heading_candidate_base(line_text) or looks_like_numbered(line_text):
                    candidates.append({
                        "text": line_text,
                        "font_size": max_font,
                        "page": page_num
                    })
    return candidates, all_font_sizes

def merge_candidates(cands, max_words):
    if not cands:
        return []
    merged = [cands[0].copy()]
    for cur in cands[1:]:
        prev = merged[-1]
        same_page = (prev["page"] == cur["page"])
        close_font = abs(prev["font_size"] - cur["font_size"]) < MERGE_FONT_EPS
        prev_words = len(prev["text"].split())
        cur_words = len(cur["text"].split())
        if same_page and close_font and prev_words <= 8 and cur_words <= 8:
            prev["text"] = clean_text(prev["text"] + " " + cur["text"])
        else:
            if (cur_words > max_words) and (not looks_like_numbered(cur["text"])):
                continue
            merged.append(cur.copy())
    return merged

def determine_font_thresholds(font_sizes):
    if not font_sizes:
        return 0, 0, 0
    uniq = sorted(set(font_sizes), reverse=True)
    h1 = uniq[0]
    h2 = uniq[1] if len(uniq) > 1 else h1 - 1
    h3 = uniq[2] if len(uniq) > 2 else h2 - 1
    return h1, h2, h3

from pdf2image import convert_from_path
import pytesseract

def ocr_page_images(pdf_path: Path):
    images = convert_from_path(str(pdf_path))
    texts = []
    for image in images:
        # OCR with multilingual support
        text = pytesseract.image_to_string(image, lang="eng+hin+tel")
        texts.append(text)
    return "\n".join(texts)

def process_pdf(pdf_path: Path) -> dict:
    doc = fitz.open(pdf_path)
    if len(doc) > MAX_PAGES:
        raise ValueError(f"{pdf_path.name} exceeds {MAX_PAGES} pages")

    try:
        toc = doc.get_toc(simple=True)
    except Exception:
        toc = []

    # If structured TOC exists, use it
    if toc and any(level >= 2 for level, *_ in toc):
        return {"title": infer_title(doc), "outline": normalize_from_toc(toc)}

    title = infer_title(doc)
    cands, all_font_sizes = extract_candidates(doc, title)

    # If no text candidates found, try OCR fallback
    if not cands:
        print(f"⚠️ No extractable text in {pdf_path.name}. Trying OCR...")
        ocr_text = ocr_page_images(pdf_path)
        with open(OUTPUT_DIR / f"{pdf_path.stem}_ocr.txt", "w", encoding="utf-8") as f:
            f.write(ocr_text)
        return {"title": title, "outline": []}

    lengths = [len(c["text"].split()) for c in cands]
    if lengths:
        try:
            p90 = int(statistics.quantiles(lengths, n=10)[-1])
        except Exception:
            p90 = max(lengths)
        MAX_WORDS = max(10, min(30, p90))
    else:
        MAX_WORDS = 20

    merged = merge_candidates(cands, MAX_WORDS)
    h1, h2, h3 = determine_font_thresholds(all_font_sizes)

    outline = []
    for item in merged:
        text, size, page = item["text"], item["font_size"], item["page"]
        if looks_like_numbered(text):
            level = "H3"
        else:
            level = classify_level_by_font(size, h1, h2, h3)
        if not level:
            continue
        outline.append({"level": level, "text": text, "page": page})

    return {"title": title, "outline": outline}


def main():
    pdfs = sorted([p for p in INPUT_DIR.glob("*.pdf") if p.is_file()])
    if not pdfs:
        print("No PDFs found in 'input/'")
        return

    for pdf_path in pdfs:
        try:
            res = process_pdf(pdf_path)
            out_file = OUTPUT_DIR / f"{pdf_path.stem}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(res, f, indent=4, ensure_ascii=False)
            print(f"✅ {pdf_path.name} -> {out_file}")
        except Exception as e:
            print(f"❌ {pdf_path.name}: {e}")

if __name__ == "__main__":
    main()
