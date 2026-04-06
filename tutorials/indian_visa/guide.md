# Indian eVisa - Fill the Start Form and Stop Before Submission
## Overview
- This guide shows how to complete the first page of the Indian eVisa application with dummy data and stop safely before captcha submission.
- Target URL: `https://indianvisaonline.gov.in/evisa/tvoa.html`
- Prerequisites: No account required for the start page. Use dummy data only for testing, and do not submit a real application with sample values.

## Steps

### Step 1: Open the Indian eVisa home page
- **Action:** navigate
- **Target element:** `https://indianvisaonline.gov.in/evisa/tvoa.html`
- **Value:** None
- **Expected result:** The eVisa landing page loads.

### Step 2: Open the application form
- **Action:** click
- **Target element:** Button or link labeled `Apply here for e-visa`
- **Value:** None
- **Expected result:** The registration page opens at `https://indianvisaonline.gov.in/evisa/Registration`.

### Step 3: Select the applicant nationality
- **Action:** select
- **Target element:** Nationality dropdown `#nationality_id`
- **Value:** `UNITED STATES OF AMERICA`
- **Expected result:** The nationality field updates to the selected country.

### Step 4: Select the passport type
- **Action:** select
- **Target element:** Passport type dropdown `#ppt_type_id`
- **Value:** `ORDINARY PASSPORT`
- **Expected result:** The passport type field updates.

### Step 5: Select the port of arrival
- **Action:** select
- **Target element:** Port of arrival dropdown `#missioncode_id`
- **Value:** `Delhi` or `NEW DELHI`
- **Expected result:** The port field updates to the selected arrival location.

### Step 6: Enter the date of birth
- **Action:** type
- **Target element:** Date of birth field `#dob_id`
- **Value:** `15/03/1990`
- **Expected result:** The date of birth field is filled.

### Step 7: Enter the email address
- **Action:** type
- **Target element:** Email field `#email_id`
- **Value:** `john.smith.demo@example.com`
- **Expected result:** The primary email field is filled.

### Step 8: Confirm the email address
- **Action:** type
- **Target element:** Email confirmation field `#email_re_id`
- **Value:** `john.smith.demo@example.com`
- **Expected result:** The confirmation email field matches the main email field.

### Step 9: Choose the visa service
- **Action:** select
- **Target element:** Radio input `input[name="evisa_service"][value="31"]`
- **Value:** Check this option for `e-Tourist Visa (30 Days)`
- **Expected result:** The 30-day e-Tourist service is selected.

### Step 10: Set the expected date of arrival
- **Action:** type
- **Target element:** Expected arrival field `#jouryney_id`
- **Value:** `15/05/2026`
- **Expected result:** The arrival date field contains the sample date.

### Step 11: Acknowledge the instructions
- **Action:** select
- **Target element:** Checkbox `#read_instructions_check`
- **Value:** Check the box
- **Expected result:** The required acknowledgement is enabled.

### Step 12: Stop at the captcha step
- **Action:** wait
- **Target element:** Captcha field `#captcha`
- **Value:** Do not enter a value during the standard guide flow
- **Expected result:** The form is fully prepared up to captcha and no submission is made.

## Output
- Final deliverable: A filled first-page eVisa application stopped safely before captcha and submission.
- Verification: Success is confirmed when all fields above are filled and the only remaining manual step is captcha entry.

## Notes
- The government site can load slowly or show modal overlays. Close them before interacting with the form.
- The nationality and arrival-port dropdowns may trigger runtime dialogs. If a dialog appears, close it and continue.
- Do not automate captcha solving in this guide. The intended stopping point is before submission.
