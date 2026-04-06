# eBay Advanced Search - Find Filtered Listings
## Overview
- This guide shows how to use eBay Advanced Search to find new Sony WH-1000XM5 listings with exclusions and price filters.
- Target URL: `https://www.ebay.com/sch/ebayadvsearch`
- Prerequisites: No login required for search.

## Steps

### Step 1: Open eBay Advanced Search
- **Action:** navigate
- **Target element:** `https://www.ebay.com/sch/ebayadvsearch`
- **Value:** None
- **Expected result:** The advanced search form loads.

### Step 2: Enter the main keywords
- **Action:** type
- **Target element:** Keyword field `#_nkw` or `input[name="_nkw"]`
- **Value:** `Sony WH-1000XM5`
- **Expected result:** The main search term appears in the keyword field.

### Step 3: Set exact keyword matching
- **Action:** select
- **Target element:** Keyword match dropdown `select[name="_in_kw"]`
- **Value:** `Exact words, exact order`
- **Expected result:** Search matching is restricted to the exact phrase order.

### Step 4: Exclude unwanted terms
- **Action:** type
- **Target element:** Exclusion field `#_ex_kw` or `input[name="_ex_kw"]`
- **Value:** `broken parts only`
- **Expected result:** Listings containing those words are excluded from the search.

### Step 5: Search title and description
- **Action:** select
- **Target element:** Checkbox or label `Title and description`
- **Value:** Check the box
- **Expected result:** The search includes both listing titles and descriptions.

### Step 6: Set the minimum price
- **Action:** type
- **Target element:** Minimum price field `input[name="_udlo"]`
- **Value:** `150`
- **Expected result:** The lower bound for price filtering is set.

### Step 7: Set the maximum price
- **Action:** type
- **Target element:** Maximum price field `input[name="_udhi"]`
- **Value:** `400`
- **Expected result:** The upper bound for price filtering is set.

### Step 8: Filter to new items
- **Action:** select
- **Target element:** Condition option `New`
- **Value:** Check or select `New`
- **Expected result:** Only new-condition items remain eligible for the search.

### Step 9: Run the advanced search
- **Action:** click
- **Target element:** Button labeled `Search`
- **Value:** None
- **Expected result:** The results page opens with the advanced filters applied.

## Output
- Final deliverable: A filtered eBay results page for Sony WH-1000XM5 listings.
- Verification: Success is confirmed when the browser lands on a results URL similar to `https://www.ebay.com/sch/i.html?...` and the listings reflect the keyword, exclusion, price, and condition filters.

## Notes
- The results URL in the recorded demo included `_nkw=Sony+WH-1000XM5`, `_ex_kw=broken+parts+only`, `_udlo=150`, `_udhi=400`, and `LH_ItemCondition=1000`.
- Some eBay layouts present the `New` filter as a checkbox and others as a selectable option inside the condition area. Use whichever visible control maps to `New`.
- If the Search button is not visible, pressing Enter from a focused form field usually triggers the same action.
