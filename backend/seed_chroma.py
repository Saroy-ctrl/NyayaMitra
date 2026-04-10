"""
seed_chroma.py -- Index Indian legal corpus into ChromaDB.

Two indexing modes:
  1. Structured *_sections.txt files (SECTION:/ACT:/TITLE:/USE_CASES:/TEXT: format)
     -> each block becomes one document (high precision, manually curated)
  2. PDF files via pypdf -> chunked at 1500 chars with 200-char overlap
     -> skipped if a matching *_sections.txt already covers the same act

Usage:
    cd backend/
    python seed_chroma.py

Re-running is safe -- upsert replaces existing entries by ID.
"""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
LAWS_DIR = Path(__file__).parent / "data" / "laws"
DB_PATH = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "indian_laws"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

# ---------------------------------------------------------------------------
# Act name -> abbreviation map
# ---------------------------------------------------------------------------
ACT_ABBREV_MAP: dict[str, str] = {
    "Bharatiya Nyaya Sanhita 2023": "BNS",
    "Bharatiya Nagarik Suraksha Sanhita 2023": "BNSS",
    "Bharatiya Sakshya Adhiniyam 2023": "BSA",
    "Consumer Protection Act 2019": "CPA",
    "Negotiable Instruments Act 1881": "NI",
    "Transfer of Property Act 1882": "TPA",
    "Delhi Rent Control Act 1958": "DRCA",
    # Legacy names (for structured files that reference old section numbers)
    "Indian Penal Code 1860": "IPC",
    "Code of Criminal Procedure 1973": "CrPC",
    "Indian Evidence Act 1872": "IEA",
}

# PDF filename stem -> (act name, default use_cases tag string)
PDF_ACT_MAP: dict[str, tuple[str, str]] = {
    "bns": ("Bharatiya Nyaya Sanhita 2023", "fir,legal_notice"),
    "bnss": ("Bharatiya Nagarik Suraksha Sanhita 2023", "fir,legal_notice"),
    "bsa": ("Bharatiya Sakshya Adhiniyam 2023", "fir,legal_notice"),
    "consumer_protection_act": ("Consumer Protection Act 2019", "consumer_complaint"),
    "negotiable_instruments_act": ("Negotiable Instruments Act 1881", "cheque_bounce"),
    "transfer_of_property_act": ("Transfer of Property Act 1882", "tenant_eviction"),
    "rent_control_act": ("Delhi Rent Control Act 1958", "tenant_eviction"),
}

REQUIRED_FIELDS = {"SECTION", "ACT", "TITLE", "USE_CASES", "TEXT"}

import re as _re

_SECTION_START = _re.compile(r'(?m)^(\d{1,3}[A-Z]?)\.\s+([^\n]+)')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_abbreviation(act_name: str) -> str:
    mapped = ACT_ABBREV_MAP.get(act_name.strip())
    if mapped:
        return mapped
    words = [w for w in act_name.split() if len(w) > 2]
    return "".join(w[0].upper() for w in words[:4]) or "LAW"


def sanitize_id_part(value: str) -> str:
    result = []
    for ch in value:
        if ch in (" ", "/", "\\", "(", ")", ".", "-"):
            result.append("_")
        else:
            result.append(ch)
    return "".join(result)


def build_doc_id(act_name: str, section_number: str) -> str:
    abbrev = make_abbreviation(act_name)
    safe_section = sanitize_id_part(section_number.strip())
    return f"{abbrev}_{safe_section}"


# ---------------------------------------------------------------------------
# Structured .txt parser
# ---------------------------------------------------------------------------

def parse_block(block: str, source_file: str) -> dict | None:
    """Parse one SECTION/ACT/TITLE/USE_CASES/TEXT block. Returns None if malformed."""
    lines = block.strip().splitlines()
    if not lines:
        return None

    fields: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_key == "TEXT":
                fields[current_key].append("")
            continue

        matched_key = None
        for key in REQUIRED_FIELDS:
            prefix = f"{key}:"
            if stripped.startswith(prefix):
                matched_key = key
                remainder = stripped[len(prefix):].strip()
                fields[matched_key] = [remainder] if remainder else []
                current_key = matched_key
                break

        if matched_key is None and current_key is not None:
            fields[current_key].append(stripped)

    for field in REQUIRED_FIELDS:
        if field not in fields or not any(v.strip() for v in fields[field]):
            content_preview = block.strip()[:60].replace("\n", " ")
            if content_preview:
                print(f"  [WARN] Skipping malformed block in {source_file} "
                      f"(missing '{field}'): {content_preview}...")
            return None

    return {
        "SECTION": " ".join(fields["SECTION"]).strip(),
        "ACT": " ".join(fields["ACT"]).strip(),
        "TITLE": " ".join(fields["TITLE"]).strip(),
        "USE_CASES": " ".join(fields["USE_CASES"]).strip(),
        "TEXT": " ".join(fields["TEXT"]).strip(),
    }


def parse_sections_from_txt(text: str) -> list[tuple[str, str, str]]:
    """Extract (section_num, title, body) from raw law text. Skips TOC entries (< 150 chars)."""
    matches = list(_SECTION_START.finditer(text))
    results = []
    for i, m in enumerate(matches):
        section_num = m.group(1)
        title_raw = m.group(2).strip().rstrip('.')
        title = title_raw.split('.--')[0].split('.\u2014')[0].strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if len(body) < 150:   # skip table-of-contents stubs
            continue
        results.append((section_num, title, body[:2000]))
    return results


def index_txt_file(txt_file: Path, collection, model, covered_acts: set[str]) -> int:
    """Parse a .txt law file into sections and upsert into ChromaDB with real section numbers."""
    stem = txt_file.stem.lower()
    if stem not in PDF_ACT_MAP:
        print(f"  [SKIP] {txt_file.name} -> not in PDF_ACT_MAP, skipping")
        return 0

    act_name, use_cases = PDF_ACT_MAP[stem]
    abbrev = make_abbreviation(act_name)

    if act_name in covered_acts:
        print(f"  [SKIP] {txt_file.name} -> {act_name} already covered")
        return 0

    raw_text = txt_file.read_text(encoding="utf-8", errors="ignore")
    sections = parse_sections_from_txt(raw_text)

    if not sections:
        print(f"  [WARN] {txt_file.name} -> 0 sections parsed, skipping")
        return 0

    # Deduplicate: keep the longest body per section number (body text > TOC stub)
    seen: dict[str, tuple[str, str, str]] = {}
    for sec_num, title, body in sections:
        if sec_num not in seen or len(body) > len(seen[sec_num][2]):
            seen[sec_num] = (sec_num, title, body)
    sections = list(seen.values())

    ids = []
    documents = []
    metadatas = []
    for sec_num, title, body in sections:
        doc_id = build_doc_id(act_name, sec_num)
        embed_text = f"{title}. {body}"
        ids.append(doc_id)
        documents.append(embed_text)
        metadatas.append({
            "section": sec_num,
            "act": act_name,
            "title": title,
            "use_cases": use_cases,
            "source_file": txt_file.name,
        })

    embeddings = model.encode(documents, show_progress_bar=False).tolist()
    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    print(f"[OK] {txt_file.name} -> {len(ids)} sections indexed ({act_name})")
    covered_acts.add(act_name)
    return len(ids)


def index_structured_txt(txt_file: Path, collection, model) -> int:
    """Parse a structured *_sections.txt file and upsert into ChromaDB."""
    raw_text = txt_file.read_text(encoding="utf-8", errors="ignore")
    blocks = raw_text.split("\n---")

    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []

    for block in blocks:
        parsed = parse_block(block, txt_file.name)
        if parsed is None:
            continue

        doc_id = build_doc_id(parsed["ACT"], parsed["SECTION"])
        embed_text = f"{parsed['TITLE']}. {parsed['TEXT']}"

        ids.append(doc_id)
        documents.append(embed_text)
        metadatas.append({
            "section": parsed["SECTION"],
            "act": parsed["ACT"],
            "title": parsed["TITLE"],
            "use_cases": parsed["USE_CASES"],
            "source_file": txt_file.name,
        })

    if not ids:
        print(f"  [WARN] {txt_file.name} -> 0 valid sections, skipping")
        return 0

    embeddings = model.encode(documents, show_progress_bar=False).tolist()
    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    print(f"[OK] {txt_file.name} -> {len(ids)} sections indexed")
    return len(ids)


# ---------------------------------------------------------------------------
# PDF chunker
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if len(c) > 100]  # skip tiny trailing chunks


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            print(f"  [ERROR] pypdf not installed. Cannot parse {pdf_path.name}")
            return ""

    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages)
    except Exception as exc:
        print(f"  [ERROR] Failed to read {pdf_path.name}: {exc}")
        return ""


def index_pdf(pdf_file: Path, collection, model, covered_acts: set[str]) -> int:
    """Chunk a PDF and upsert chunks into ChromaDB. Skip if act already covered."""
    stem = pdf_file.stem.lower()
    if stem not in PDF_ACT_MAP:
        print(f"  [SKIP] {pdf_file.name} -> not in PDF_ACT_MAP, skipping")
        return 0

    act_name, use_cases = PDF_ACT_MAP[stem]
    abbrev = make_abbreviation(act_name)

    if act_name in covered_acts:
        print(f"  [SKIP] {pdf_file.name} -> {act_name} already covered by structured .txt")
        return 0

    raw_text = extract_pdf_text(pdf_file)
    if not raw_text.strip():
        print(f"  [WARN] {pdf_file.name} -> no text extracted, skipping")
        return 0

    chunks = chunk_text(raw_text)
    if not chunks:
        print(f"  [WARN] {pdf_file.name} -> 0 chunks produced, skipping")
        return 0

    ids = [f"{abbrev}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "section": f"chunk_{i}",
            "act": act_name,
            "title": f"{act_name} (chunk {i})",
            "use_cases": use_cases,
            "source_file": pdf_file.name,
        }
        for i in range(len(chunks))
    ]

    embeddings = model.encode(chunks, show_progress_bar=False).tolist()
    collection.upsert(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
    print(f"[OK] {pdf_file.name} -> {len(chunks)} chunks indexed ({act_name})")
    return len(chunks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def seed() -> None:
    if not LAWS_DIR.exists():
        print(f"ERROR: Laws directory not found: {LAWS_DIR}")
        return

    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Embedding model loaded")

    client = chromadb.PersistentClient(path=str(DB_PATH))

    # Drop existing collection so stale chunk_N entries are fully removed
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"[RESET] Dropped existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass  # collection didn't exist yet

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    total_indexed = 0
    covered_acts: set[str] = set()

    # Pass 1: .txt law files -- section-level indexing with real section numbers
    txt_files = sorted(LAWS_DIR.glob("*.txt"))
    if txt_files:
        print(f"\nPass 1: {len(txt_files)} .txt law file(s)")
    for txt_file in txt_files:
        n = index_txt_file(txt_file, collection, model, covered_acts)
        total_indexed += n

    # Pass 2: PDF files (for acts not covered by structured files)
    pdf_files = sorted(LAWS_DIR.glob("*.pdf"))
    if pdf_files:
        print(f"\nPass 2: {len(pdf_files)} PDF file(s)")
    for pdf_file in pdf_files:
        n = index_pdf(pdf_file, collection, model, covered_acts)
        total_indexed += n

    final_count = collection.count()
    print(f"\n[TOTAL] {final_count} documents in ChromaDB ({total_indexed} upserted this run)")


if __name__ == "__main__":
    seed()
