#!/usr/bin/env python3
"""
Real SEC EDGAR XBRL Downloader
Downloads actual XBRL attachment files from SEC EDGAR for cross-validation.

Usage examples:
  # By ticker (recommended)
  python real_xbrl_downloader.py --ticker AAPL --form 10-K --limit 1 \
      --out data/raw/xbrl --ua "Your Name your.email@example.com"

  # By company name
  python real_xbrl_downloader.py --company "Microsoft" --form 10-Q --limit 2 \
      --out data/raw/xbrl --ua "Your Name your.email@example.com" --include-ixbrl
"""

from __future__ import annotations
import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


SEC_TICKERS_JSON = "https://www.sec.gov/files/company_tickers.json"
SUBMISSION_URL_TMPL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_DIR_URL_TMPL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_no_dashes}/"
INDEX_JSON_NAME = "index.json"

# Patterns for XBRL files (instance, schema, linkbases)
XBRL_FILE_PATTERNS = [
    r"(?i)\.xsd$",               # Taxonomy schema
    r"(?i)_pre\.xml$",           # Presentation linkbase
    r"(?i)_lab\.xml$",           # Label linkbase
    r"(?i)_def\.xml$",           # Definition linkbase
    r"(?i)_cal\.xml$",           # Calculation linkbase
    r"(?i)(?<!_pre)(?<!_lab)(?<!_def)(?<!_cal)\.xml$",  # Other XML (likely instance)
]

# Optional: Inline XBRL HTML
IXBRL_PATTERNS = [
    r"(?i)(ixbrl|inline).*\.htm(l)?$"
]


def build_session(user_agent: str, timeout: int = 20) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })

    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET", "HEAD"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)

    # Attach a default timeout to all requests via a small wrapper
    s.request = _with_timeout(s.request, timeout)  # type: ignore
    return s


def _with_timeout(request_fn, timeout_default):
    def wrapped(method, url, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = timeout_default
        return request_fn(method, url, **kwargs)
    return wrapped


class RealXBRLDownloader:
    """Downloads XBRL attachments for recent filings of a company."""

    def __init__(self, user_agent: str, outdir: Path, rate_limit_s: float = 0.2, include_ixbrl: bool = False):
        self.user_agent = user_agent
        self.outdir = outdir
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.include_ixbrl = include_ixbrl
        self.rate_limit_s = rate_limit_s
        self.session = build_session(user_agent)

        # Cache for tickers map
        self._ticker_map = None

    # ---------- CIK Resolution ----------

    def _load_ticker_map(self) -> Dict[str, Dict[str, str]]:
        if self._ticker_map is not None:
            return self._ticker_map
        resp = self.session.get(SEC_TICKERS_JSON)
        resp.raise_for_status()
        data = resp.json()
        # Normalize into {lower_ticker: {"cik": "##########", "title": "..."}}
        m: Dict[str, Dict[str, str]] = {}
        for v in data.values():
            ticker = str(v.get("ticker", "")).lower()
            title = str(v.get("title", ""))
            cik = str(v.get("cik_str", "")).zfill(10)
            if ticker:
                m[ticker] = {"cik": cik, "title": title}
        self._ticker_map = m
        return m

    def get_cik_by_ticker(self, ticker: str) -> Optional[str]:
        m = self._load_ticker_map()
        info = m.get(ticker.lower())
        return info["cik"] if info else None

    def get_cik_by_company(self, company_name: str) -> Optional[str]:
        """
        Try exact ticker first (if a user passes a ticker in company field),
        otherwise substring match on company title.
        """
        # If the user types 'AAPL' into --company by mistake, honor it.
        cik = self.get_cik_by_ticker(company_name)
        if cik:
            return cik

        # Substring search on title (best-effort)
        m = self._load_ticker_map()
        name_l = company_name.lower()
        for info in m.values():
            if name_l in info["title"].lower():
                return info["cik"]
        return None

    # ---------- Filings Discovery ----------

    def get_recent_filings(self, cik: str, filing_type: str, limit: int = 1) -> List[Dict]:
        """Get recent filings (of a given form) for a CIK."""
        url = SUBMISSION_URL_TMPL.format(cik=cik)
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])

        results: List[Dict] = []
        for i, form in enumerate(forms):
            if form == filing_type:
                results.append({
                    "form": form,
                    "filing_date": dates[i],
                    "accession": accessions[i],
                    "cik": cik
                })
                if len(results) >= limit:
                    break
        return results

    # ---------- Download helpers ----------

    @staticmethod
    def _matches_any(name: str, patterns: List[str]) -> bool:
        return any(re.search(p, name) for p in patterns)

    def _filter_xbrl_files(self, items: List[Dict]) -> List[str]:
        names = []
        for item in items:
            name = item.get("name", "")
            if self._matches_any(name, XBRL_FILE_PATTERNS):
                names.append(name)
            elif self.include_ixbrl and self._matches_any(name, IXBRL_PATTERNS):
                names.append(name)
        # Deduplicate while preserving order
        dedup, seen = [], set()
        for n in names:
            if n not in seen:
                dedup.append(n)
                seen.add(n)
        return dedup

    def _download_file(self, url: str, dest: Path) -> None:
        r = self.session.get(url)
        r.raise_for_status()
        # Binary write (handles any encoding and avoids newline issues)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(r.content)
        time.sleep(self.rate_limit_s)

    def download_xbrl_attachments_for_filing(self, cik: str, accession: str, company_key: str, form: str) -> List[Path]:
        """
        Download XBRL attachments for a single filing given CIK + accession.
        Returns list of saved Paths.
        """
        accession_no_dashes = accession.replace("-", "")
        base = ARCHIVES_DIR_URL_TMPL.format(cik=int(cik), accession_no_no_dashes=accession_no_dashes)
        index_url = urljoin(base, INDEX_JSON_NAME)

        r = self.session.get(index_url)
        r.raise_for_status()
        idx = r.json()
        items = idx.get("directory", {}).get("item", [])
        targets = self._filter_xbrl_files(items)

        if not targets:
            print(f"[WARN] No XBRL-like files found in {accession}")
            return []

        filing_dir = self.outdir / company_key / form / accession
        saved: List[Path] = []
        for name in targets:
            file_url = urljoin(base, name)
            dest = filing_dir / name
            print(f"Downloading: {file_url} -> {dest}")
            try:
                self._download_file(file_url, dest)
                saved.append(dest)
            except Exception as e:
                print(f"[ERROR] Failed {name}: {e}")
        return saved

    # ---------- Public API ----------

    def run(self, company: Optional[str], ticker: Optional[str], form: str, limit: int) -> Dict[str, List[Path]]:
        """
        Resolve CIK, list recent filings, and download XBRL attachments.
        Returns mapping {accession: [paths]}.
        """
        if ticker:
            cik = self.get_cik_by_ticker(ticker)
            company_key = ticker.upper()
        else:
            cik = self.get_cik_by_company(company or "")
            company_key = (ticker or company or "company").replace(" ", "_")

        if not cik:
            raise RuntimeError("Could not resolve CIK. Try using --ticker or a different --company value.")

        filings = self.get_recent_filings(cik, form, limit=limit)
        if not filings:
            raise RuntimeError(f"No recent {form} filings found for CIK {cik}.")

        results: Dict[str, List[Path]] = {}
        for f in filings:
            accession = f["accession"]
            saved = self.download_xbrl_attachments_for_filing(cik, accession, company_key, form)
            results[accession] = saved
        return results


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download XBRL attachments from SEC EDGAR filings.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--ticker", type=str, help="Stock ticker, e.g., AAPL")
    g.add_argument("--company", type=str, help="Company name, e.g., 'Apple Inc'")

    p.add_argument("--form", type=str, default="10-K", help="Filing form, e.g., 10-K, 10-Q")
    p.add_argument("--limit", type=int, default=1, help="Number of most-recent filings to download")
    p.add_argument("--out", type=Path, default=Path("data/raw/xbrl"), help="Output directory")
    p.add_argument("--ua", type=str, required=True,
                   help="SEC-compliant User-Agent: 'Your Name your.email@example.com'")
    p.add_argument("--include-ixbrl", action="store_true", help="Also download inline XBRL HTML files")
    p.add_argument("--rate", type=float, default=0.2, help="Seconds to sleep between file downloads")
    return p.parse_args()


def main():
    args = parse_args()
    d = RealXBRLDownloader(
        user_agent=args.ua,
        outdir=args.out,
        rate_limit_s=args.rate,
        include_ixbrl=args.include_ixbrl
    )
    which = args.ticker or args.company
    print(f"Resolving CIK for {which} …")
    results = d.run(company=args.company, ticker=args.ticker, form=args.form, limit=args.limit)

    total = sum(len(v) for v in results.values())
    print("\n=== Summary ===")
    print(f"Saved {total} files across {len(results)} filing(s) into: {args.out.resolve()}")
    for acc, files in results.items():
        print(f"  {acc}: {len(files)} files")
        for f in files:
            print(f"    - {f}")


if __name__ == "__main__":
    main()