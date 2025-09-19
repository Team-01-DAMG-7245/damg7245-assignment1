
import camelot, pathlib, argparse, json

def run(pdf, outdir):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    meta = []
    for flavor in ("lattice", "stream"):
        try:
            tables = camelot.read_pdf(pdf, flavor=flavor, pages="all")
            for i, t in enumerate(tables):
                fp = outdir / f"{pathlib.Path(pdf).stem}_{flavor}_{i:02d}.csv"
                t.to_csv(fp)
                meta.append({"flavor": flavor, "index": i, "csv": str(fp), "shape": t.df.shape})
        except Exception as e:
            meta.append({"flavor": flavor, "error": str(e)})
    return meta

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print(json.dumps(run(a.pdf, a.out), indent=2))
