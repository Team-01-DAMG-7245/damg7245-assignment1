#!/usr/bin/env python3
import pdfplumber, camelot, pathlib, argparse

def count_rules(pdf, page_num):
    with pdfplumber.open(pdf) as doc:
        pg = doc.pages[page_num-1]
        return len(pg.lines) + len(pg.curves)

def expand_pages(s: str):
    pages=[]
    for chunk in s.split(","):
        if "-" in chunk:
            a,b = chunk.split("-"); pages += list(range(int(a), int(b)+1))
        else:
            pages.append(int(chunk))
    return pages

def extract_hybrid(pdf, pages, outdir, thresh=20):
    out = pathlib.Path(outdir); out.mkdir(parents=True, exist_ok=True)
    for p in pages:
        flavor = "lattice" if count_rules(pdf, p) >= thresh else "stream"
        tables = camelot.read_pdf(pdf, flavor=flavor, pages=str(p))
        if tables.n == 0 and flavor == "lattice":
            tables = camelot.read_pdf(pdf, flavor="stream", pages=str(p))
            flavor = "stream"
        for i, t in enumerate(tables):
            (out / f"{pathlib.Path(pdf).stem}_p{p:03d}_{flavor}_{i:02d}.csv").write_text(t.df.to_csv(index=False))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--pages", default="1-60")
    ap.add_argument("--out", default="data/parsed/tables/hybrid")
    ap.add_argument("--thresh", type=int, default=22)
    a = ap.parse_args()
    extract_hybrid(a.pdf, expand_pages(a.pages), a.out, a.thresh)
