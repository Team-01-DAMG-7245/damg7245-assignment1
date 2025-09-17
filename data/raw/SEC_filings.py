from sec_edgar_downloader import Downloader

dl = Downloader("Team1", "lerdwanawattana.n@northeastern.edu", "data/raw/SEC_filings")

# Get 10-K filings for Apple (AAPL) for the fiscal years 2023 and 2024
dl.get("10-K", "AAPL", after="2022-12-31", before="2024-12-31")
