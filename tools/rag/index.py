#!/usr/bin/env python3
"""Build or rebuild the RAG index from all docs in the repo."""

import argparse
import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = Path(__file__).parent / ".chromadb"

DOC_GLOBS = [
    "**/*.md",
    "**/*.txt",
]

CHUNK_SIZE = 600   # characters
CHUNK_OVERLAP = 100


def chunk_text(text: str, source: str) -> list[dict]:
    """Split text into overlapping chunks, preserving markdown section context."""
    chunks = []
    # Track the current heading for context
    heading = ""
    heading_re = re.compile(r"^#{1,3} .+", re.MULTILINE)

    # Split into paragraphs first, then group into chunks
    paragraphs = re.split(r"\n{2,}", text)
    current = ""
    current_start = 0
    char_pos = 0

    for para in paragraphs:
        # Update heading context if this paragraph is a heading
        if heading_re.match(para.strip()):
            heading = para.strip().lstrip("#").strip()

        if len(current) + len(para) + 2 > CHUNK_SIZE and current:
            chunks.append({
                "text": current.strip(),
                "source": source,
                "heading": heading,
            })
            # Overlap: keep last CHUNK_OVERLAP chars
            overlap_start = max(0, len(current) - CHUNK_OVERLAP)
            current = current[overlap_start:] + "\n\n" + para
        else:
            current = (current + "\n\n" + para) if current else para

        char_pos += len(para) + 2

    if current.strip():
        chunks.append({
            "text": current.strip(),
            "source": source,
            "heading": heading,
        })

    return chunks


def collect_files() -> list[Path]:
    files = []
    for glob in DOC_GLOBS:
        files.extend(REPO_ROOT.glob(glob))
    return sorted(set(files))


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def build_index(force: bool = False) -> None:
    import os
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("HF_HUB_VERBOSITY", "error")

    import chromadb
    from sentence_transformers import SentenceTransformer

    print("Loading embedding model...", flush=True)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_or_create_collection(
        name="docs",
        metadata={"hnsw:space": "cosine"},
    )

    files = collect_files()
    print(f"Found {len(files)} documents", flush=True)

    added = updated = skipped = 0

    for path in files:
        rel = str(path.relative_to(REPO_ROOT))
        fhash = file_hash(path)
        doc_id_prefix = rel.replace("/", "__").replace(".", "_")

        # Check if file changed by looking for existing chunks with this hash
        existing = collection.get(
            where={"source": rel},
            include=["metadatas"],
        )
        if not force and existing["ids"] and existing["metadatas"][0].get("hash") == fhash:
            skipped += 1
            continue

        # Remove stale chunks for this file
        if existing["ids"]:
            collection.delete(ids=existing["ids"])

        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text, rel)
        if not chunks:
            continue

        ids = [f"{doc_id_prefix}__chunk{i}" for i in range(len(chunks))]
        texts = [c["text"] for c in chunks]
        metadatas = [{"source": c["source"], "heading": c["heading"], "hash": fhash} for c in chunks]

        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

        if existing["ids"]:
            updated += 1
        else:
            added += 1

    print(f"Done. Added={added} Updated={updated} Skipped={skipped} Total chunks={collection.count()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build RAG index for openstars docs")
    parser.add_argument("--force", action="store_true", help="Re-index all files regardless of changes")
    args = parser.parse_args()
    build_index(force=args.force)
