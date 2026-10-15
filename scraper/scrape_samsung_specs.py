import argparse
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.samsungmobilepress.com"
START = f"{BASE}/media-assets"
OUTPUT_DIR = Path("output")
SINGLE_OUTPUT = OUTPUT_DIR / "samsung_galaxy_specifications.txt"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    )
}

SKIP_URL_PARTS = [
    "galaxy_unpacked",
    "galaxy-for-the-planet",
    "galaxy-chat",
    "galaxy-express",
    "/news/",
    "/stories/",
    "/events/",
]

session = requests.Session()
session.headers.update(HEADERS)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "-", name) or "device"


def get_soup_requests(url: str) -> BeautifulSoup:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def get_soup_playwright(url: str) -> BeautifulSoup:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=HEADERS["User-Agent"])
        page.goto(url, wait_until="networkidle", timeout=60000)

        try:
            page.click("text=Tech Specs", timeout=5000)
            page.wait_for_timeout(2000)
        except Exception:
            pass

        html = page.content()
        browser.close()

    return BeautifulSoup(html, "lxml")


def get_soup(url: str, use_browser: bool = False) -> BeautifulSoup:
    if use_browser:
        return get_soup_playwright(url)
    return get_soup_requests(url)


def is_device_page(href: str) -> bool:
    lower_href = href.lower()

    if "/media-assets/" not in lower_href:
        return False

    return not any(part in lower_href for part in SKIP_URL_PARTS)


def find_device_links(soup: BeautifulSoup) -> set[str]:
    links = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].split("?")[0]

        if not is_device_page(href):
            continue

        links.add(urljoin(BASE, href))

    return links


def get_device_name(soup: BeautifulSoup, url: str) -> str:
    h1 = soup.find("h1")

    if h1:
        return clean(h1.get_text())

    title = soup.find("title")

    if title:
        return clean(title.get_text()).split("|")[0]

    slug = url.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").title()


def extract_table_rows(soup: BeautifulSoup) -> list[str]:
    rows = []

    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [
                clean(cell.get_text(" ", strip=True))
                for cell in tr.find_all(["th", "td"])
            ]
            cells = [cell for cell in cells if cell]

            if len(cells) >= 2:
                rows.append(" - ".join(cells))

    return rows


def extract_spec_blocks(soup: BeautifulSoup) -> list[str]:
    blocks = []
    seen = set()

    selectors = [
        "[class*='spec']",
        "[class*='Spec']",
        "[id*='spec']",
        "[id*='Spec']",
        "section",
    ]

    nodes = soup.select(", ".join(selectors))

    for node in nodes:
        text = clean(node.get_text(" ", strip=True))

        if not text or len(text) < 20 or text in seen:
            continue

        seen.add(text)
        blocks.append(text)

    return blocks


def scrape_device(url: str, use_browser: bool = False) -> tuple[str, str]:
    soup = get_soup(url, use_browser=use_browser)
    device_name = get_device_name(soup, url)

    table_rows = extract_table_rows(soup)
    spec_blocks = extract_spec_blocks(soup)

    lines = [
        f"DEVICE: {device_name}",
        f"URL: {url}",
        "",
    ]

    if table_rows:
        lines.extend(["SPECIFICATIONS", *table_rows, ""])

    if spec_blocks:
        lines.extend(["ADDITIONAL SPECIFICATION CONTENT"])

        for block in spec_blocks:
            lines.extend([block, ""])

    lines.extend(["-" * 80, ""])

    return "\n".join(lines), device_name


def discover_device_urls(use_browser: bool = False) -> list[str]:
    device_urls = set()
    page_number = 1

    while True:
        url = START if page_number == 1 else f"{START}?page={page_number}"
        print(f"Scanning index page {page_number}: {url}")

        try:
            soup = get_soup(url, use_browser=use_browser)
        except Exception as error:
            print(f"Stopping at page {page_number}: {error}")
            break

        found = find_device_links(soup)
        new_links = found - device_urls
        device_urls.update(new_links)

        print(f"Found {len(new_links)} new device links. Total: {len(device_urls)}")

        if not new_links:
            break

        page_number += 1
        time.sleep(1)

    return sorted(device_urls)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Samsung Mobile Press Galaxy device specifications for Chatbase."
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help="Use Playwright for JavaScript-rendered pages.",
    )
    parser.add_argument(
        "--split",
        action="store_true",
        help="Also save one TXT file per device.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between device-page requests.",
    )

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    device_urls = discover_device_urls(use_browser=args.browser)

    print(f"\nDiscovered {len(device_urls)} potential device pages.")

    all_results = []

    for index, url in enumerate(device_urls, start=1):
        print(f"[{index}/{len(device_urls)}] {url}")

        try:
            device_text, device_name = scrape_device(url, use_browser=args.browser)
            all_results.append(device_text)

            if args.split:
                device_file = OUTPUT_DIR / f"{safe_filename(device_name)}.txt"
                device_file.write_text(device_text, encoding="utf-8")

        except Exception as error:
            print(f"  Failed: {error}")

        time.sleep(args.delay)

    combined = (
        "SAMSUNG GALAXY DEVICE SPECIFICATIONS\n"
        "Source: Samsung Mobile Press\n"
        "Generated for Chatbase knowledge-base ingestion\n\n"
        + "\n".join(all_results)
    )

    SINGLE_OUTPUT.write_text(combined, encoding="utf-8")

    print(f"\nDone. Saved {len(all_results)} devices to {SINGLE_OUTPUT}")


if __name__ == "__main__":
    main()
