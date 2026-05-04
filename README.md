---

## 🛠️ Usage (Step-by-Step)

To ensure the script runs correctly, please follow these steps to set up your environment and capture data:

### 1. Initialize Chrome Environment
Run the provided batch file to launch a dedicated Chrome instance with remote debugging enabled:
*   Execute `start_chrome.bat`.
*   This script creates a standalone profile folder named `ChromeGaijinMarketData` in the project root to isolate your login session and data.

### 2. Prepare Trading Data
*   Open [trade.gaijin.net](https://trade.gaijin.net) and log in to your account.
*   Navigate to **Notifications** -> **View All**.
*   **Crucial Step:** Manually scroll down the page until you reach the earliest transaction record you wish to capture (the script scrapes data currently loaded in the DOM).

### 3. Run the Script
*   Execute `main.py`.
*   **Input Date:** Enter the start date in `YYYY/M/D` format (e.g., `2026/4/1`). 
    *   *Default:* 31 days ago from today.
*   **Data Boundary:** The script automatically sets the **End Date to 23:59:59 of the day prior** to execution. 
    *   *Design Note:* This ensures you capture a "complete day" of data, avoiding overlap or confusion with ongoing trades from the current day when appending records to your CSV.

### 4. Data Export & Integration
*   Once completed, the formatted data is automatically copied to your **System Clipboard**.
*   Open the target file: `Purchase_Sales_Records.csv`.
*   **How to Paste:** Select the **2nd Column (Type)** of the first empty row and paste. 
    *   *Note:* The **1st Column** is intentionally left blank for user-defined IDs or custom indexing.
*   *Reference:* The first two rows of the CSV serve as samples, containing pre-defined formulas for automatic tax and profit calculation.

---