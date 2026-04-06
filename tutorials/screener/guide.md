# Screener.in - Research a Stock and Shortlist Candidates
## Overview
- This guide shows how to research a stock on Screener.in and use a prebuilt screen to find candidate companies.
- Target URL: `https://www.screener.in/`
- Prerequisites: No account required. The site is public.

## Steps

### Step 1: Open Screener.in
- **Action:** navigate
- **Target element:** Home page `https://www.screener.in/`
- **Value:** None
- **Expected result:** The Screener home page loads and the main company search box is visible.

### Step 2: Search for Reliance Industries
- **Action:** type
- **Target element:** Main search field, usually `input[placeholder*="Search for a company"]`
- **Value:** `Reliance Industries`
- **Expected result:** A visible search suggestion for Reliance Industries appears below the search box.

### Step 3: Open the Reliance company page
- **Action:** click
- **Target element:** Search result link labeled `Reliance Industries`
- **Value:** None
- **Expected result:** The browser opens the company page, typically `https://www.screener.in/company/RELIANCE/consolidated/`.

### Step 4: Review the key metrics block
- **Action:** inspect
- **Target element:** Metric tiles near the top of the company page, especially `Market Cap`, `Stock P/E`, and `ROCE`
- **Value:** None
- **Expected result:** You can see the high-level company snapshot before scrolling further.

### Step 5: Open the quarterly results section
- **Action:** click
- **Target element:** Link or tab labeled `Quarters` or `Quarterly`
- **Value:** None
- **Expected result:** The page moves to the quarterly results section and recent performance rows are visible.

### Step 6: Open the Profit & Loss section
- **Action:** click
- **Target element:** Link or tab labeled `Profit & Loss`
- **Value:** None
- **Expected result:** The Profit & Loss section is visible with revenue, expense, and margin information.

### Step 7: Open the Balance Sheet section
- **Action:** click
- **Target element:** Link or tab labeled `Balance Sheet`
- **Value:** None
- **Expected result:** The Balance Sheet section is visible with assets, liabilities, and equity information.

### Step 8: Open the Screens area
- **Action:** click
- **Target element:** Top navigation link labeled `Screens`
- **Value:** None
- **Expected result:** The browser opens Screener's public screen library, usually `https://www.screener.in/explore/`.

### Step 9: Show the full screen library
- **Action:** click
- **Target element:** Link labeled `Show all screens`
- **Value:** None
- **Expected result:** The browser opens the full list of public screens at `https://www.screener.in/screens/`.

### Step 10: Find the target stock screen
- **Action:** scroll
- **Target element:** Screen card or link labeled `High Growth, High RoE, Low PE`
- **Value:** None
- **Expected result:** The target screen card is visible in the full screen list.

### Step 11: Open the target stock screen
- **Action:** click
- **Target element:** Link labeled `High Growth, High RoE, Low PE`
- **Value:** None
- **Expected result:** The browser opens the screen results page, commonly `https://www.screener.in/screens/18/high-growth-high-roe-low-pe/`.

### Step 12: Review the filtered company table
- **Action:** inspect
- **Target element:** Main results table on the screen page
- **Value:** None
- **Expected result:** The filtered list of companies is visible, including names such as `Ganesh Infra`.

### Step 13: Open a shortlisted company
- **Action:** click
- **Target element:** Company link `Ganesh Infra`
- **Value:** None
- **Expected result:** The Ganesh Infra company page opens, typically `https://www.screener.in/company/GANESHIN/`.

## Output
- Final deliverable: A completed stock research flow that ends on the shortlisted company page after using a repeatable filter.
- Verification: Success is confirmed when the Ganesh Infra company page loads after starting from the Screener home page.

## Notes
- If the Reliance search suggestion does not appear immediately, wait briefly after typing before pressing Enter or clicking the result.
- If the top navigation route to `Screens` fails, navigate directly to `https://www.screener.in/explore/` or `https://www.screener.in/screens/`.
- If the exact screen card is hard to find in the full list, search the page for `High Growth` or navigate directly to `https://www.screener.in/screens/18/high-growth-high-roe-low-pe/`.
