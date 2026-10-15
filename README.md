# Samsung Galaxy Specifications Scraper

Scrapes publicly available Galaxy device specification pages from Samsung Mobile Press and generates a Chatbase-ready plain-text knowledge base.

## What it does

- Crawls the Samsung Mobile Press Media Assets index
- Discovers individual Galaxy device pages
- Opens each device page and attempts to activate its **Tech Specs** section
- Extracts specification tables and specification text
- Saves all results to a single Chatbase-ready `.txt` file
- Optionally saves one separate `.txt` file per device

## Output

By default, the scraper creates:

```text
output/samsung_galaxy_specifications.txt
```

The file uses this structure:

```text
DEVICE: Galaxy S26 Ultra
URL: https://www.samsungmobilepress.com/media-assets/galaxy-s26-ultra

SPECIFICATIONS
Display - ...
Camera - ...
Battery - ...
```

## Installation

```bash
git clone https://github.com/trainermertens-a11y/samsung-galaxy-specs-scraper.git
cd samsung-galaxy-specs-scraper
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Basic run

```bash
python scraper/scrape_samsung_specs.py
```

This uses `requests` and BeautifulSoup. Use this first; it is faster and lighter.

## JavaScript-rendered pages

If Samsung loads specifications dynamically and the basic scraper returns incomplete data, install Playwright:

```bash
pip install -r requirements-playwright.txt
playwright install chromium
python scraper/scrape_samsung_specs.py --browser
```

## Optional: one file per device

```bash
python scraper/scrape_samsung_specs.py --split
```

This creates files such as:

```text
output/galaxy-s26-ultra.txt
output/galaxy-z-fold8.txt
output/galaxy-buds-on.txt
```

## Chatbase upload

1. Open your Chatbase workspace.
2. Go to **Knowledge Base**.
3. Upload `output/samsung_galaxy_specifications.txt`.
4. Alternatively, upload the individual files created with `--split`.

For best retrieval quality, use `--split`, because one file per device helps Chatbase avoid mixing specifications between models.

## Options

| Option | Description |
|---|---|
| `--browser` | Uses Playwright and Chromium for JavaScript-rendered pages |
| `--split` | Saves one TXT file per device in addition to the combined file |
| `--delay 1.5` | Sets a delay between requests; default is 1 second |

## Legal and responsible use

This project is intended for personal, internal, or research use. Respect Samsung’s Terms of Use, robots directives, rate limits, and applicable copyright rules. Do not redistribute Samsung-owned media assets or large portions of proprietary content without permission.

## License

MIT
