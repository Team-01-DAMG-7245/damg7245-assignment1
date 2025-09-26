#!/usr/bin/env python3
"""
Real SEC EDGAR XBRL Downloader
Downloads actual XBRL files from SEC EDGAR for cross-validation
"""

import requests
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin
import time


class RealXBRLDownloader:
    """Downloads real XBRL files from SEC EDGAR"""
    
    def __init__(self, user_agent: str = "Sample Company <sample@example.com>"):
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        })
        
    def get_company_cik(self, company_name: str) -> Optional[str]:
        """Get CIK for company name using SEC company tickers API"""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            for item in data.values():
                if company_name.lower() in item.get('title', '').lower():
                    return str(item['cik_str']).zfill(10)
            
            # Fallback to known mappings
            cik_map = {
                'apple': '0000320193',
                'apple inc': '0000320193',
                'aapl': '0000320193',
                'microsoft': '0000789019',
                'msft': '0000789019',
                'google': '0001652044',
                'googl': '0001652044',
                'amazon': '0001018724',
                'amzn': '0001018724'
            }
            return cik_map.get(company_name.lower())
            
        except Exception as e:
            print(f"Error fetching CIK: {e}")
            return None
    
    def get_recent_filings(self, cik: str, filing_type: str = "10-K", limit: int = 1) -> List[Dict]:
        """Get recent filings for a company"""
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            filings = []
            
            # Get recent filings
            recent_filings = data.get('filings', {}).get('recent', {})
            
            if recent_filings:
                forms = recent_filings.get('form', [])
                accession_numbers = recent_filings.get('accessionNumber', [])
                filing_dates = recent_filings.get('filingDate', [])
                
                for i, form in enumerate(forms):
                    if form == filing_type and len(filings) < limit:
                        filings.append({
                            'form': form,
                            'accession_number': accession_numbers[i],
                            'filing_date': filing_dates[i],
                            'cik': cik
                        })
            
            return filings
            
        except Exception as e:
            print(f"Error fetching filings: {e}")
            return []
    
    def download_xbrl_files(self, company_name: str, filing_type: str = "10-K") -> List[Path]:
        """Download actual XBRL files from SEC EDGAR"""
        cik = self.get_company_cik(company_name)
        if not cik:
            print(f"CIK not found for {company_name}")
            return []
        
        filings = self.get_recent_filings(cik, filing_type, limit=1)
        if not filings:
            print(f"No {filing_type} filings found for {company_name}")
            return []
        
        output_dir = Path("data/raw/xbrl")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []
        
        for filing in filings:
            accession_number = filing['accession_number']
            filing_date = filing['filing_date']
            
            # Construct EDGAR URL for XBRL files
            # Format: https://www.sec.gov/Archives/edgar/data/{CIK}/{accession_number}/...
            accession_dash = accession_number.replace('-', '')
            base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_dash}/"
            
            try:
                # Download the index file to find XBRL files
                index_url = urljoin(base_url, "index.json")
                response = self.session.get(index_url)
                response.raise_for_status()
                
                index_data = response.json()
                xbrl_files = []
                
                # Find XBRL files in the filing
                for item in index_data.get('directory', {}).get('item', []):
                    name = item.get('name', '')
                    if name.endswith('.xml') and ('xbrl' in name.lower() or 'instance' in name.lower()):
                        xbrl_files.append(name)
                
                # Download XBRL files
                for xbrl_file in xbrl_files:
                    file_url = urljoin(base_url, xbrl_file)
                    
                    print(f"Downloading {xbrl_file}...")
                    response = self.session.get(file_url)
                    response.raise_for_status()
                    
                    # Save file
                    output_file = output_dir / f"{company_name}_{filing_date}_{xbrl_file}"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    downloaded_files.append(output_file)
                    print(f"Saved to {output_file}")
                    
                    # Rate limiting
                    time.sleep(0.1)
                
            except Exception as e:
                print(f"Error downloading XBRL files for {accession_number}: {e}")
                continue
        
        return downloaded_files


def main():
    """Test the real XBRL downloader"""
    downloader = RealXBRLDownloader()
    
    companies = ['Apple', 'Microsoft']
    
    for company in companies:
        print(f"\nDownloading XBRL files for {company}...")
        files = downloader.download_xbrl_files(company, '10-K')
        print(f"Downloaded {len(files)} files for {company}")


if __name__ == "__main__":
    main()
