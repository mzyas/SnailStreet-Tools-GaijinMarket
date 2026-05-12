# Gaijinmarket: Trade History Automator

A specialized data extraction and processing tool designed for the Gaijin Market. It automates the fetching of personal
trading history from a live browser session, parses complex HTML structures into structured data, and prepares it for
professional accounting (Excel/Google Sheets).

---

## 🛠️ Usage (Step-by-Step)

To ensure the script runs correctly, please follow these steps to set up your environment and capture data:

### 1. Initialize Chrome Environment
Run the provided batch file to launch a dedicated Chrome instance with remote debugging enabled:
- Execute start_chrome.bat.
- This script creates a standalone profile folder named ChromeGaijinMarketData in the project root to isolate your login session and data.

### 2. Prepare Trading Data
- Open [trade.gaijin.net](https://trade.gaijin.net) and log in to your account.
- Navigate to Notifications -> View All.
- Crucial Step: Manually scroll down the page until you reach the earliest transaction record you wish to capture (the script scrapes data currently loaded in the DOM).

### 3. Run the Script
- Execute main.py.
- Input Date: Enter the start date in YYYY/M/D format (e.g., 2026/4/1). 
    - Default: 31 days ago from today.
- Data Boundary: The script automatically sets the End Date to 23:59:59 of the day prior to execution. 
    - Design Note: This ensures you capture a "complete day" of data, avoiding overlap or confusion with ongoing trades from the current day when appending records to your CSV.

### 4. Data Export & Integration
- Once completed, the formatted data is automatically copied to your System Clipboard.
- Open the target file: Purchase_Sales_Records.csv.
- How to Paste: Select the 2nd Column (Type) of the first empty row and paste. 
    - Note: The 1st Column is intentionally left blank for user-defined IDs or custom indexing.
- Reference: The first two rows of the CSV serve as samples, containing pre-defined formulas for automatic tax and profit calculation.

---

## 🚀 Key Features

- Live Session Integration: Connects to an existing Chrome instance via CDP (Chrome DevTools Protocol), bypassing
  complex login/2FA hurdles.
- Intelligent Parsing: Uses regex and DOM traversal to extract transaction types (Buy/Sell), Item Types (
  Vehicle/Camouflage/Decor), Price, Quantity, and Order IDs.
- Bilingual Architecture: Built to handle multiple languages (EN/CN). It utilizes a modular dictionary system to
  categorize items based on global naming conventions.
- Dynamic Filtering: Allows users to define a specific date range for data extraction via an interactive CLI.
- Clipboard Ready: Automatically formats and copies results into a Tab-Separated Values (TSV) format, ready for
  immediate pasting into Excel or Google Sheets.

---

## ⚙️ How it Works

1. Browser Connection: The script utilizes connect_over_cdp to attach to a running Chrome instance (default port 9222).
   This leverages the user's active session and cookies without manual re-login.
2. Tab Detection: It iterates through all open browser tabs to locate the specific trading history page (
   trade.gaijin.net/history).
3. Data Extraction & Filtering:
    - Scans the DOM for all .message nodes.
    - Applies a date filter based on user input, ensuring only relevant historical records are processed.
4. Heuristic Classification:
    - Vehicles: Identified by detecting bracket patterns ( ) and nation-specific keywords (e.g., USA, Germany, Japan).
    - Decorations/Others: Cross-referenced against an external CSV-based database (Item_Name/Decoration_*.csv).
5. Data Normalization: Maps the raw HTML data into a standardized 14-column TSV structure (Type, Name, Date, Buy/Sell
   Price, Order ID, etc.).
6. Output: Copies the final string to the system clipboard using pyperclip for a seamless "One-Click" export experience.

Data source Example
![img01: Data source Example](./img/example01.png?raw=true)

Compiler Run Example
![img02: Compiler Run Example](./img/example02.png?raw=true)

Scraped Output Example
![img03: Scraped Output Example](./img/example03.png?raw=true)

---

## 📂 Project Structure

```text
├── main.py              # CLI entry point
├── gui.py               # Tkinter GUI  (zero extra dependency)
├── core.py              # Shared browser / fetch / export logic
├── parser.py            # DOM parsing and data normalization
├── itemName.py          # Nation list + external item database (language-aware)
├── version.py           # Single source of truth for version number
├── i18n/                # JSON-based multilingual translation files
│   ├── __init__.py      #   LanguageManager singleton
│   ├── zh_CN.json       #   中文 (Chinese)
│   └── en_US.json       #   English
├── Item_Name/           # External CSV assets for item categorization
│   ├── Decoration_zh.csv
│   └── Decoration_eng.csv
├── start_chrome.bat     # Launch Chrome with remote debugging (port 9222)
├── requirements.txt     # Python dependencies
└── Purchase_Sales_Records/
    └── GaiJinMarket.xlsx  # Excel template with auto-tax formulas

```

---

## 🔧 Installation

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Playwright browser (required for browser automation)
playwright install chromium
```

---

## 🖥️ GUI Mode (Recommended)

```bash
python gui.py
```

| Feature | Description |
|---------|-------------|
| 🌐 **Language Switch** | Click "中文" / "EN" to toggle UI + item database language |
| 🚀 **Launch Chrome** | Starts `start_chrome.bat` from within the app |
| 📅 **Date Range** | GUI date input with auto-calculated end date |
| 📋 **Copy TSV** | One-click clipboard export |
| 💾 **Export CSV** | Save to `.csv` file with headers + OrderID |

All messages are logged in the bottom panel with timestamps.

---

## 🌍 Multilingual Architecture

```
                    ┌──────────────────────────┐
                    │   i18n/LanguageManager    │
                    │   (Singleton, key-based)  │
                    └──────────┬───────────────┘
                               │  lm.t("group.key")
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ zh_CN.json│   │ en_US.json│   │ (future) │
        │  prompt   │   │  prompt   │   │  ja_JP   │
        │  parser   │   │  parser   │   │  ...     │
        │  gui      │   │  gui      │   │          │
        └──────────┘   └──────────┘   └──────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    itemName.py       │
                    │  NATIONS  (per lang) │
                    │  OTHER_ITEMS (CSV)   │
                    │  reload_lang()       │
                    └──────────────────────┘
```

1. `detect_language()` reads page title ("通知" / "Notifications") to detect language
2. `itemName.reload_lang()` loads matching `Decoration_*.csv` + nation list
3. `lm.t("parser.xxx")` returns buy/sell keywords in the correct language
4. GUI calls `reload_language()` to refresh all widget texts on the fly

---

## 🛠️ Tech Stack

- **Language**: Python 3.9+
- **Browser Automation**: [Playwright](https://playwright.dev/python/) (Sync API)
- **GUI**: Tkinter (Python standard library – zero extra dependency)
- **i18n**: JSON-based key-value translations with fallback
- **Data Processing**: Regex (`re`), `datetime`, `csv`
- **Clipboard**: `pyperclip`
- **Packaging**: PyInstaller (optional, for `.exe`)

---

## 📝 Changelog

### v1.0.0 (2026-05-12)
- Initial release
- CLI mode (`main.py`) with date filtering, TSV clipboard output
- GUI mode (`gui.py`) with TreeView, CSV export, log panel
- Multilingual support: zh_CN / en_US (auto-detect + manual switch)
- Chrome CDP connection (port 9222) via `start_chrome.bat`
- `requirements.txt` + `version.py` for dependency tracking
