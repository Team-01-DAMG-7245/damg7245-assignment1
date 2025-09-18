#!/usr/bin/env python3
import pdfplumber, pandas as pd, pathlib, argparse, json

def extract_pdfplumber(pdf, outdir):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    meta = []
    with pdfplumber.open(pdf) as doc:
        for pno, page in enumerate(doc.pages, start=1):
            tables = page.find_tables(table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 5,
            })
            for i, tbl in enumerate(tables):
                df = pd.DataFrame(tbl.extract())
                fp = outdir / f"{pathlib.Path(pdf).stem}_p{pno:03d}_{i:02d}.csv"
                df.to_csv(fp, index=False)
                meta.append({"page": pno, "index": i, "csv": str(fp), "shape": df.shape})
    return meta

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(json.dumps(extract_pdfplumber(a.pdf, a.out), indent=2))
