# Tinkercad - Find Beginner Lessons and Design Inspiration
## Overview
- This guide shows how to use Tinkercad without logging in to find beginner lessons and inspect a community design for inspiration.
- Target URL: `https://www.tinkercad.com/`
- Prerequisites: No login required for the browsing flow shown here.

## Steps

### Step 1: Open Tinkercad
- **Action:** navigate
- **Target element:** `https://www.tinkercad.com/`
- **Value:** None
- **Expected result:** The Tinkercad home page loads.

### Step 2: Open the Learning Center
- **Action:** click
- **Target element:** Top navigation link labeled `Learn`
- **Value:** None
- **Expected result:** The browser opens the learning area, usually under `https://www.tinkercad.com/learn`.

### Step 3: Search for beginner tutorials
- **Action:** type
- **Target element:** Search field such as `input[placeholder*="Search tutorials"]` or the visible search input
- **Value:** `3D design basics`
- **Expected result:** The search query is entered and the results page opens after pressing Enter.

### Step 4: Stay on the 3D Design track
- **Action:** click
- **Target element:** Tab or link labeled `3D Designs`
- **Value:** None
- **Expected result:** The results are filtered to the 3D design learning track.

### Step 5: Review the lesson cards
- **Action:** scroll
- **Target element:** Results list of lesson cards
- **Value:** None
- **Expected result:** Multiple beginner-friendly lesson cards are visible.

### Step 6: Open an Airbus moon lesson
- **Action:** click
- **Target element:** A lesson card whose URL contains `airbus-traveling-to-the-moon`, `airbus-habitat-on-the-moon`, `airbus-living-on-the-moon`, or `airbus-driving-on-the-moon`
- **Value:** None
- **Expected result:** The browser opens the lesson overview page.

### Step 7: Review the lesson details
- **Action:** scroll
- **Target element:** Lesson overview content and visuals
- **Value:** None
- **Expected result:** The lesson visuals and instructions are visible for review.

### Step 8: Open the Community Gallery
- **Action:** click
- **Target element:** Top navigation link labeled `Gallery`
- **Value:** None
- **Expected result:** The browser opens `https://www.tinkercad.com/things`.

### Step 9: Browse the gallery
- **Action:** inspect
- **Target element:** Main gallery grid of community projects
- **Value:** None
- **Expected result:** Top community designs are visible.

### Step 10: Open the Spartan Helmet design
- **Action:** click
- **Target element:** Gallery link for `My take on a Greek Spartan Helmet - March 2026`
- **Value:** None
- **Expected result:** The browser opens the design page, typically `https://www.tinkercad.com/things/ddtuLraw1Zf-my-take-on-a-greek-spartan-helmet-march-2026`.

### Step 11: Inspect the 3D model
- **Action:** inspect
- **Target element:** 3D model viewer and project detail area
- **Value:** None
- **Expected result:** The model page is loaded and the design can be examined.

## Output
- Final deliverable: One lesson page and one gallery design page opened as references for a beginner Tinkercad learning session.
- Verification: Success is confirmed when the Airbus lesson page and the Greek Spartan Helmet project page both load correctly.

## Notes
- The `Learn` link can route to slightly different learning URLs depending on the site version.
- If the search flow fails, you can navigate directly to `https://www.tinkercad.com/learn/search/designs?q=3D%20design%20basics`.
- The exact Airbus moon lesson can vary. Use any visible Airbus moon lesson if the preferred card changes.
