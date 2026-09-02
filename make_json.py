"""Build barrel indexes and document metadata from a news CSV file."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from text_processing import singular_candidate, tokenize

BASE_DIR = Path(__file__).resolve().parent
TEXT_FIELDS = ("source_name", "author", "title", "description", "content", "category", "full_content")
METADATA_FIELDS = ("title", "description", "url", "url_to_image")


def normalized_tokens(row: dict[str, str]) -> list[str]:
    text = " ".join(row.get(field) or "" for field in TEXT_FIELDS)
    return [singular_candidate(token) for token in tokenize(text)]


def build_indices(rows: Iterable[dict[str, str]], limit: int | None = None):
    forward_index: dict[str, list[str]] = {}
    barrels: dict[str, Any] = {
        **{letter: defaultdict(dict) for letter in "abcdefghijklmnopqrstuvwxyz"},
        "other": defaultdict(dict),
    }
    metadata: dict[str, dict[str, str]] = {}
    doc_lengths: dict[str, int] = {}

    for position, row in enumerate(rows, start=1):
        if limit is not None and position > limit:
            break
        doc_id = str(row.get("article_id") or "").strip()
        if not doc_id:
            raise ValueError(f"Row {position + 1} has no article_id")
        if doc_id in metadata:
            raise ValueError(f"Duplicate article_id {doc_id!r} at row {position + 1}")

        tokens = normalized_tokens(row)
        counts = Counter(tokens)
        forward_index[doc_id] = sorted(counts)
        doc_lengths[doc_id] = len(tokens)
        metadata[doc_id] = {field: str(row.get(field) or "") for field in METADATA_FIELDS}
        for token, count in counts.items():
            name = token[0] if token and "a" <= token[0] <= "z" else "other"
            barrels[name][token][doc_id] = count
        if position % 10_000 == 0:
            print(f"Indexed {position:,} documents...", flush=True)

    return forward_index, barrels, metadata, doc_lengths


def write_json(path: Path, value: object) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, separators=(",", ":"))


def generate(data_path: Path, output_dir: Path, limit: int | None = None) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    with data_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None or "article_id" not in reader.fieldnames:
            raise ValueError("CSV must have a header containing article_id")
        forward, barrels, metadata, lengths = build_indices(reader, limit)

    write_json(output_dir / "forward_index.json", forward)
    for name, barrel in barrels.items():
        write_json(output_dir / f"barrel_{name}.json", barrel)
    write_json(output_dir / "doc_metadata.json", metadata)
    write_json(output_dir / "doc_lengths.json", lengths)
    return len(metadata)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=BASE_DIR / "datasets" / "data.csv", help="input CSV")
    parser.add_argument("--output", type=Path, default=BASE_DIR / "datasets", help="index output directory")
    parser.add_argument("--limit", type=int, default=None, help="index only the first N rows")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        csv.field_size_limit(sys.maxsize)
    except OverflowError:
        csv.field_size_limit(2**31 - 1)
    args = parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    try:
        count = generate(args.data.resolve(), args.output.resolve(), args.limit)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Index generation failed: {exc}") from exc
    print(f"Indexed {count:,} documents into {args.output.resolve()}")
