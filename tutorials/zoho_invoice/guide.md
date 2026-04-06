# Zoho Invoice - Create a GST Invoice
## Overview
- This guide shows how to create a sample GST invoice in Zoho's free invoice generator and prepare it for PDF export.
- Target URL: `https://www.zoho.com/in/invoice/free-invoice-generator.html`
- Prerequisites: No login required. This uses Zoho's public invoice generator.

## Steps

### Step 1: Open Zoho Invoice
- **Action:** navigate
- **Target element:** `https://www.zoho.com/in/invoice/`
- **Value:** None
- **Expected result:** The Zoho Invoice landing page loads.

### Step 2: Open the free invoice generator
- **Action:** navigate
- **Target element:** `https://www.zoho.com/in/invoice/free-invoice-generator.html`
- **Value:** None
- **Expected result:** The invoice form and invoice preview are visible on one page.

### Step 3: Enter your business name
- **Action:** type
- **Target element:** Company field `#address1`
- **Value:** `TechStar Solutions Pvt Ltd`
- **Expected result:** The company name appears in the seller section.

### Step 4: Enter the contact name
- **Action:** type
- **Target element:** Contact field `#custName`
- **Value:** `Pavan Kumar`
- **Expected result:** The contact name appears in the seller section.

### Step 5: Enter the seller address lines
- **Action:** type
- **Target element:** Address fields `#address2`, `#address3`, and `#companyState`
- **Value:** `42 MG Road`, `Hyderabad`, `Telangana`
- **Expected result:** The full seller address is visible in the invoice header.

### Step 6: Enter the client company
- **Action:** type
- **Target element:** Bill To fields `#billingAddress1`, `#billingAddress2`, `#billingAddress3`, and `#customerState`
- **Value:** `Acme Corp International`, `100 Business Park`, `Mumbai`, `Maharashtra`
- **Expected result:** The client billing block is filled.

### Step 7: Set the invoice number
- **Action:** type
- **Target element:** Invoice number field `#invNumber`
- **Value:** `INV-2026-001`
- **Expected result:** The invoice number updates in the invoice preview.

### Step 8: Add line item 1
- **Action:** type
- **Target element:** Item row 1 fields `#itemDesc\.1`, `#itemQty\.1`, `#itemRate\.1`, `#itemTax1\.1`
- **Value:** `Web Development Services`, `40`, `2500`, `9`
- **Expected result:** Row 1 shows the service, quantity, rate, and GST value.

### Step 9: Add line item 2
- **Action:** type
- **Target element:** Item row 2 fields `#itemDesc\.2`, `#itemQty\.2`, `#itemRate\.2`, `#itemTax1\.2`
- **Value:** `UI/UX Design`, `20`, `3000`, `9`
- **Expected result:** Row 2 is added to the invoice and totals update.

### Step 10: Add line item 3
- **Action:** type
- **Target element:** Item row 3 fields `#itemDesc\.3`, `#itemQty\.3`, `#itemRate\.3`, `#itemTax1\.3`
- **Value:** `Server Hosting (Annual)`, `1`, `18000`, `9`
- **Expected result:** Row 3 is added to the invoice and totals update again.

### Step 11: Add payment notes
- **Action:** type
- **Target element:** Notes field `#customerNotes`
- **Value:** `Payment due within 30 days.`
- **Expected result:** The customer note appears in the lower section of the invoice.

### Step 12: Add payment terms or bank details
- **Action:** type
- **Target element:** Terms field `#terms`
- **Value:** `Bank: HDFC | IFSC: HDFC0001234`
- **Expected result:** The terms section is populated with payment instructions.

### Step 13: Review totals
- **Action:** scroll
- **Target element:** Totals block near `Sub Total`
- **Value:** None
- **Expected result:** The subtotal, GST, and grand total are visible for review.

### Step 14: Open the export action
- **Action:** click
- **Target element:** Button labeled `Download/Print`
- **Value:** None
- **Expected result:** Zoho opens the print or download flow for PDF export.

## Output
- Final deliverable: A completed sample GST invoice ready to print or export as PDF.
- Verification: Success is confirmed when the invoice shows all three line items, the totals are visible, and the `Download/Print` action is available.

## Notes
- Zoho sometimes shows chat or promo widgets. If they cover the form, close them before typing.
- The page recalculates totals after each line item. If values do not update immediately, click outside the current field.
- Depending on the browser, `Download/Print` may open a print dialog instead of saving automatically.
