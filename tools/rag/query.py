#!/usr/bin/env python3
"""Query the RAG index. Usage: uv run query.py <search terms> [-n 5]"""

import argparse
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / ".chromadb"


def query(text: str, n_results: int = 5) -> None:
    if not DB_PATH.exists():
        print("Index not found. Run: uv run index.py", file=sys.stderr)
        sys.exit(1)

    import os
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("HF_HUB_VERBOSITY", "error")

    import chromadb
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(DB_PATH))
    collection = client.get_collection("docs")

    embedding = model.encode([text]).tolist()
    results = collection.query(
        query_embeddings=embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
        score = 1 - dist  # cosine similarity
        source = meta["source"]
        heading = meta.get("heading", "")
        header = f"[{i+1}] {source}"
        if heading:
            header += f" § {heading}"
        header += f"  (score: {score:.3f})"
        print(header)
        print("-" * len(header))
        # Print first 400 chars of the chunk
        preview = doc[:400].replace("\n", " ").strip()
        if len(doc) > 400:
            preview += "..."
        print(preview)
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the openstars RAG index")
    parser.add_argument("query", nargs="+", help="Search terms")
    parser.add_argument("-n", "--num-results", type=int, default=5, help="Number of results (default: 5)")
    args = parser.parse_args()

    query(" ".join(args.query), n_results=args.num_results)
