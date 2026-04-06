# Mondula - Complete the Multi-Step Demo Form
## Overview
- This guide shows how to complete the Mondula multi-step form demo using sample text, date, selection, and contact values.
- Target URL: `https://mondula.com/msf-demo/`
- Prerequisites: No account required. The site may show a cookie banner on first load.

## Steps

### Step 1: Open the demo form
- **Action:** navigate
- **Target element:** `https://mondula.com/msf-demo/`
- **Value:** None
- **Expected result:** The Mondula demo page loads.

### Step 2: Accept the cookie banner if it appears
- **Action:** click
- **Target element:** A visible cookie button such as `Accept`, `Save preferences`, or `Allow all`
- **Value:** None
- **Expected result:** The cookie banner closes and the form remains visible.

### Step 3: Move from the intro screen to the first form page
- **Action:** click
- **Target element:** Button labeled `NEXT STEP`
- **Value:** None
- **Expected result:** The first form page opens and the text field `#msf-text-example-textfield` becomes visible.

### Step 4: Fill the first text field
- **Action:** type
- **Target element:** `#msf-text-example-textfield`
- **Value:** `Pavan Demo`
- **Expected result:** The text field contains the sample name.

### Step 5: Fill the first textarea
- **Action:** type
- **Target element:** `#msf-textarea-example-textarea`
- **Value:** `Testing a multi-page form automation workflow.`
- **Expected result:** The textarea contains the sample description.

### Step 6: Move to page two
- **Action:** click
- **Target element:** `NEXT STEP`
- **Value:** None
- **Expected result:** The next page loads and the date field `#msf-date-date-field-with-calender-popup` becomes visible.

### Step 7: Fill the first simple text field on page two
- **Action:** type
- **Target element:** First visible match for `#msf-text-simple-text-field`
- **Value:** `Automation Field Value`
- **Expected result:** The first simple text field is filled.

### Step 8: Fill the second simple text field on page two
- **Action:** type
- **Target element:** Second visible match for `#msf-text-simple-text-field`
- **Value:** `Second Value`
- **Expected result:** The second simple text field is filled.

### Step 9: Fill the custom textarea on page two
- **Action:** type
- **Target element:** `#msf-textarea-custom-textarea`
- **Value:** `This section demonstrates long-form answers.`
- **Expected result:** The textarea contains the sample long answer.

### Step 10: Fill the date field on page two
- **Action:** type
- **Target element:** `#msf-date-date-field-with-calender-popup`
- **Value:** `03/13/2026`
- **Expected result:** The date field contains the sample date.

### Step 11: Move to the selection page
- **Action:** click
- **Target element:** `NEXT STEP`
- **Value:** None
- **Expected result:** The page with radio buttons, checkboxes, and a dropdown becomes visible.

### Step 12: Select the radio option
- **Action:** select
- **Target element:** Radio input `#fw-12-3-0-0-2`
- **Value:** Check this input
- **Expected result:** One radio option is selected in the radio group.

### Step 13: Select the checkbox options
- **Action:** select
- **Target element:** Checkbox inputs `#fw-12-3-1-0-2` and `#fw-12-3-1-0-5`
- **Value:** Check both inputs
- **Expected result:** Two checkbox options are selected.

### Step 14: Select the dropdown value
- **Action:** select
- **Target element:** `#msf-select-please-choose-a-option-from-the-list`
- **Value:** Select option at index `2`
- **Expected result:** The dropdown shows the third available option.

### Step 15: Move to the conditional section
- **Action:** click
- **Target element:** `NEXT STEP`
- **Value:** None
- **Expected result:** The dish selector `#msf-select-dish` becomes visible.

### Step 16: Select the dish
- **Action:** select
- **Target element:** `#msf-select-dish`
- **Value:** Select option at index `1` (`Pizza`)
- **Expected result:** Conditional options appear for the chosen dish.

### Step 17: Select the conditional options
- **Action:** select
- **Target element:** Checkbox inputs `#fw-12-4-0-1-2`, `#fw-12-4-0-2-2`, `#fw-12-4-0-2-4`, `#fw-12-4-0-3-2`, `#fw-12-4-0-4-2`
- **Value:** Check all five inputs
- **Expected result:** The conditional section is fully populated for the selected dish.

### Step 18: Move to the contact page
- **Action:** click
- **Target element:** `NEXT STEP`
- **Value:** None
- **Expected result:** The final contact page loads and `#msf-text-first-name` is visible.

### Step 19: Fill the final contact form
- **Action:** type
- **Target element:** `#msf-text-first-name`, `#msf-text-last-name`, `#msf-date-date-of-birth`, `#msf-text-telephone`, `#msf-mail-email`, `#msf-textarea-feel-free-to-write-a-short-message`
- **Value:** `Pavan`, `Kumar`, `03/13/1992`, `9876543210`, `pavan@example.com`, `Please share plugin implementation details for production usage.`
- **Expected result:** All required final contact fields are filled.

### Step 20: Open the summary
- **Action:** click
- **Target element:** Button labeled `SHOW SUMMARY`
- **Value:** None
- **Expected result:** The summary view opens if available.

### Step 21: Reach the submit-ready state
- **Action:** wait
- **Target element:** Final summary or submit area
- **Value:** None
- **Expected result:** A visible `Submit` control or equivalent final state is present without actually submitting the form.

## Output
- Final deliverable: A fully completed demo form that reaches the summary or submit-ready state.
- Verification: Success is confirmed when all pages are completed and the final page exposes a `Submit` action or the summary view.

## Notes
- The `NEXT STEP` button may appear as a button, input, or link depending on the page state.
- If `SHOW SUMMARY` hides the submit area, one more click on `NEXT STEP` may be needed to reveal the final submit state.
- Some choices are identified here by element IDs instead of visible labels because the demo automation used exact inputs for repeatability.
