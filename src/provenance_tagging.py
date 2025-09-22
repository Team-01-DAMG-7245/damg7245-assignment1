#!/usr/bin/env python3
"""
Provenance tagging for extracted content (Part 5)

- Defines a metadata schema for text and tables
- Emits .jsonl with one record per block
- Reassembles sections to Markdown grouped by section label
"""

import json
import argparse
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional


def _safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _iter_docling_blocks(doc_json: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    pages = doc_json.get("pages")
    texts = doc_json.get("texts", [])
    tables = doc_json.get("tables", [])

    # Build quick index maps by id if present
    text_by_id = {t.get("id", i): t for i, t in enumerate(texts)}
    table_by_id = {t.get("id", i): t for i, t in enumerate(tables)}

    if isinstance(pages, list):
        page_iter = enumerate(pages, start=1)
    elif isinstance(pages, dict):
        # keys may be strings; sort by numeric if possible
        try:
            keys = sorted(pages.keys(), key=lambda k: int(k))
        except Exception:
            keys = list(pages.keys())
        page_iter = ((i + 1, pages[k]) for i, k in enumerate(keys))
    else:
        return

    for page_num, page in page_iter:
        children = page.get("children", []) if isinstance(page, dict) else []
        for child in children:
            if not isinstance(child, dict):
                continue
            ref = child.get("$ref", "")
            bbox = child.get("bbox") or child.get("box") or child.get("bounds")
            if "/texts/" in ref:
                try:
                    idx = int(ref.split("/texts/")[-1].split("/")[0])
                except Exception:
                    idx = child.get("id")
                t = text_by_id.get(idx)
                if not t:
                    continue
                yield {
                    "block_type": "text",
                    "page": page_num,
                    "section": t.get("label") or t.get("category") or "unknown",
                    "text": t.get("text", ""),
                    "bbox": t.get("bbox") or bbox,
                    "raw": t,
                }
            elif "/tables/" in ref:
                try:
                    idx = int(ref.split("/tables/")[-1].split("/")[0])
                except Exception:
                    idx = child.get("id")
                tb = table_by_id.get(idx)
                if not tb:
                    continue
                yield {
                    "block_type": "table",
                    "page": page_num,
                    "section": tb.get("label") or tb.get("category") or "table",
                    "text": tb.get("caption", {}).get("text", ""),
                    "bbox": tb.get("bbox") or bbox,
                    "raw": tb,
                }


def build_record(base: Dict[str, Any], doc_meta: Dict[str, Any]) -> Dict[str, Any]:
    rec = {
        "doc_id": doc_meta.get("doc_id"),
        "company": doc_meta.get("company"),
        "fiscal_year": doc_meta.get("fiscal_year"),
        "page": base.get("page"),
        "section": base.get("section"),
        "block_type": base.get("block_type"),
        "bbox": base.get("bbox"),
        "text": base.get("text", ""),
        "source_path": doc_meta.get("source_path"),
    }
    # Include table data lightly if present
    if base.get("block_type") == "table":
        tab = base.get("raw", {})
        rec["table_shape"] = {
            "rows": len((tab.get("data", {}) or {}).get("grid", [])),
            "cols": (len(((tab.get("data", {}) or {}).get("grid", [])[0])) if ((tab.get("data", {}) or {}).get("grid", [])) else 0),
        }
    return rec


def emit_jsonl(doc_json_path: Path, out_dir: Path, company: str, fiscal_year: str) -> Path:
    doc = _safe_read_json(doc_json_path)
    if not doc:
        raise FileNotFoundError(f"Docling JSON not found or unreadable: {doc_json_path}")

    doc_id = doc.get("origin", {}).get("binary_hash") or doc_json_path.stem
    source_pdf = doc.get("origin", {}).get("source", {}).get("uri") or str(doc_json_path)

    meta = {
        "doc_id": doc_id,
        "company": company,
        "fiscal_year": fiscal_year,
        "source_path": source_pdf,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"{company}_{fiscal_year}.jsonl"

    count = 0
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for block in _iter_docling_blocks(doc) or []:
            rec = build_record(block, meta)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    print(f"Wrote {count} records to {jsonl_path}")
    return jsonl_path


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    return records


def reassemble_sections_to_markdown(jsonl_path: Path, out_dir: Path) -> Path:
    recs = load_jsonl(jsonl_path)
    if not recs:
        raise ValueError(f"No records in {jsonl_path}")

    # Group by section in reading order of pages then stable order
    sections: Dict[str, List[Dict[str, Any]]] = {}
    for r in sorted(recs, key=lambda x: (x.get("page", 0))):
        sec = r.get("section") or "unknown"
        sections.setdefault(sec, []).append(r)

    title = f"{recs[0].get('company', 'Company')} {recs[0].get('fiscal_year', '')}"
    lines: List[str] = [f"# {title} — Section Summary", ""]

    for sec_name, items in sections.items():
        lines.append(f"## {sec_name}")
        lines.append("")
        # Render text blocks first in page order
        for r in items:
            if r.get("block_type") == "text":
                lines.append(r.get("text", "").strip())
        # Render table placeholders with page and bbox
        any_table = any(r.get("block_type") == "table" for r in items)
        if any_table:
            lines.append("")
            lines.append("Tables:")
            lines.append("")
            lines.append("| Page | BBox | Caption |")
            lines.append("| --- | --- | --- |")
            for r in items:
                if r.get("block_type") == "table":
                    bbox = r.get("bbox")
                    bbox_str = json.dumps(bbox) if bbox else ""
                    cap = (r.get("text") or "").replace("\n", " ")
                    lines.append(f"| {r.get('page')} | {bbox_str} | {cap} |")
        lines.append("")

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / (jsonl_path.stem + "_sections.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")

    print(f"Markdown written to {md_path}")
    return md_path


def infer_company_year_from_pdf(pdf_path: Path) -> (str, str):
    name = pdf_path.stem
    parts = name.split("_")
    company = parts[0] if parts else name
    year = next((p for p in parts if p.isdigit()), "")
    return company, year


def main():
    p = argparse.ArgumentParser(description="Provenance tagging and section reassembly")
    p.add_argument("--docling-json", required=False, help="Path to Docling JSON file (export_to_dict)")
    p.add_argument("--pdf", required=False, help="Path to source PDF (used to infer company/year)")
    p.add_argument("--company", required=False)
    p.add_argument("--fiscal-year", required=False)
    p.add_argument("--out", default="data/parsed/docling", help="Output directory for JSONL/MD")
    args = p.parse_args()

    if not args.docling_json:
        # Try default locations derived from PDF
        if not args.pdf:
            raise SystemExit("Provide --docling-json or --pdf to locate it.")
        pdf_path = Path(args.pdf)
        docling_json = Path("data/parsed/docling") / f"{pdf_path.stem}.json"
    else:
        docling_json = Path(args.docling_json)

    if not docling_json.exists():
        raise SystemExit(f"Docling JSON not found: {docling_json}")

    if args.company and args.fiscal_year:
        company, fiscal_year = args.company, args.fiscal_year
    else:
    
        source_pdf = Path(args.pdf) if args.pdf else Path(docling_json.stem + ".pdf")
        company, fiscal_year = infer_company_year_from_pdf(source_pdf)

    out_dir = Path(args.out)
    jsonl_path = emit_jsonl(docling_json, out_dir, company, fiscal_year)
    reassemble_sections_to_markdown(jsonl_path, out_dir)


if __name__ == "__main__":
    main()


