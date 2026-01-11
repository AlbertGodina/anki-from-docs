# generate_cards.py
"""
Generate Anki-ready flashcard suggestions (CSV) from PDF or DOCX documents.
Designed for structured educational notes in Catalan.
"""

from pathlib import Path
import csv
import re

import pdfplumber
from docx import Document


OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "suggested_cards.csv"


SECTION_REGEX = re.compile(r"^(\d+(\.\d+)*)\.\s*(.+)")
DEFINITION_STARTERS = (
    "Es denomina",
    "És",
    "Es produeix",
    "La",
    "El",
    "Els",
    "Les",
)


def extract_text(path: Path) -> list[str]:
    if path.suffix.lower() == ".pdf":
        return extract_pdf(path)
    if path.suffix.lower() == ".docx":
        return extract_docx(path)
    raise ValueError("Format no suportat. Usa PDF o DOCX.")


def extract_pdf(path: Path) -> list[str]:
    paragraphs = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split("\n"):
                line = line.strip()
                if line:
                    paragraphs.append(line)
    return paragraphs


def extract_docx(path: Path) -> list[str]:
    doc = Document(path)
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]


def detect_sections(paragraphs: list[str]) -> list[tuple[str, str]]:
    current_section = "General"
    result = []

    for p in paragraphs:
        match = SECTION_REGEX.match(p)
        if match:
            current_section = f"{match.group(1)} {match.group(3)}"
            continue
        result.append((current_section, p))

    return result


def is_definition(sentence: str) -> bool:
    return sentence.startswith(DEFINITION_STARTERS) and len(sentence.split()) > 8


def generate_basic_card(sentence: str) -> tuple[str, str]:
    words = sentence.split()
    key = " ".join(words[:5]) + "..."
    front = f"Defineix: {key}"
    back = sentence
    return front, back


def generate_cloze(sentence: str) -> str | None:
    words = sentence.split()
    if len(words) < 10:
        return None

    key_word = max(words, key=len)
    if len(key_word) < 6:
        return None

    return sentence.replace(key_word, f"{{{{c1::{key_word}}}}}", 1)


def generate_cards(sectioned_text: list[tuple[str, str]]) -> list[dict]:
    cards = []

    for section, sentence in sectioned_text:
        if is_definition(sentence):
            front, back = generate_basic_card(sentence)
            cards.append({
                "type": "basic",
                "front": front,
                "back": back,
                "section": section,
                "approved": "no",
            })

        cloze = generate_cloze(sentence)
        if cloze:
            cards.append({
                "type": "cloze",
                "front": cloze,
                "back": "",
                "section": section,
                "approved": "no",
            })

    return cards


def write_csv(cards: list[dict]) -> None:
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["type", "front", "back", "section", "approved"]
        )
        writer.writeheader()
        writer.writerows(cards)


def main():
    import sys

    if len(sys.argv) != 2:
        print("Ús: python generate_cards.py <document.pdf|document.docx>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        raise FileNotFoundError(path)

    paragraphs = extract_text(path)
    sectioned = detect_sections(paragraphs)
    cards = generate_cards(sectioned)
    write_csv(cards)

    print(f"✔ {len(cards)} cartes suggerides creades a {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
