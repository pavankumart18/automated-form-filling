# Overpass Turbo - Compare Hyderabad Data Layers
## Overview
- This guide shows how to use Overpass Turbo to query and compare hospitals, EV charging stations, schools, and parks in Hyderabad.
- Target URL: `https://overpass-turbo.eu/#map=12/17.3850/78.4867`
- Prerequisites: No account required. Overpass Turbo depends on public Overpass API capacity, so occasional rate limits are possible.

## Steps

### Step 1: Open Overpass Turbo
- **Action:** navigate
- **Target element:** `https://overpass-turbo.eu/#map=12/17.3850/78.4867`
- **Value:** None
- **Expected result:** The Overpass Turbo workspace loads with the query editor on the left and the map on the right.

### Step 2: Confirm the split workspace
- **Action:** inspect
- **Target element:** Left query editor and right map panel
- **Value:** None
- **Expected result:** You can see both the editor and the map controls before entering a query.

### Step 3: Enter the hospitals query
- **Action:** type
- **Target element:** Query editor, usually `.CodeMirror`, `.ace_editor`, or the visible `textarea`
- **Value:** 
```overpass
[out:json][timeout:25];
nwr["amenity"="hospital"](17.20,78.20,17.60,78.70);
out center;
```
- **Expected result:** The hospitals query is fully visible in the editor.

### Step 4: Run the hospitals query
- **Action:** click
- **Target element:** Toolbar button or menu item labeled `Run`
- **Value:** None
- **Expected result:** Hospital markers are returned and rendered on the map.

### Step 5: Zoom to the result set
- **Action:** click
- **Target element:** Map control labeled `zoom to data`
- **Value:** None
- **Expected result:** The map centers and fits the returned Hyderabad hospital features.

### Step 6: Inspect a hospital marker
- **Action:** click
- **Target element:** Any visible map marker in the returned result set
- **Value:** None
- **Expected result:** A popup or detail view shows tags such as name, address, or amenity type.

### Step 7: Open the Data tab
- **Action:** click
- **Target element:** Top action labeled `Data`
- **Value:** None
- **Expected result:** Tabular output for the current query is visible.

### Step 8: Return to the Map view
- **Action:** click
- **Target element:** Top action labeled `Map`
- **Value:** None
- **Expected result:** The map view is visible again.

### Step 9: Enter the EV charging query
- **Action:** type
- **Target element:** Query editor
- **Value:** 
```overpass
[out:json][timeout:25];
nwr["amenity"="charging_station"](17.20,78.20,17.60,78.70);
out center;
```
- **Expected result:** The editor contains the EV charging station query.

### Step 10: Run the EV charging query
- **Action:** click
- **Target element:** `Run`
- **Value:** None
- **Expected result:** EV charging points render on the map and can be compared against the hospital coverage.

### Step 11: Enter the schools query
- **Action:** type
- **Target element:** Query editor
- **Value:** 
```overpass
[out:json][timeout:20];
(
  nwr["amenity"="school"](17.33,78.38,17.47,78.56);
);
out center 80;
```
- **Expected result:** The editor contains the school query for a tighter Hyderabad area.

### Step 12: Run the schools query
- **Action:** click
- **Target element:** `Run`
- **Value:** None
- **Expected result:** School features render on the map within the smaller Hyderabad bounding box.

### Step 13: Enter the parks query
- **Action:** type
- **Target element:** Query editor
- **Value:** 
```overpass
[out:json][timeout:18];
node["leisure"="park"](17.35,78.41,17.45,78.54);
out 40;
```
- **Expected result:** The editor contains the park query for the urban core.

### Step 14: Run the parks query
- **Action:** click
- **Target element:** `Run`
- **Value:** None
- **Expected result:** Park points render on the map and can be compared against schools and EV coverage.

### Step 15: Finish on the comparison view
- **Action:** inspect
- **Target element:** Final map state after the park query completes
- **Value:** None
- **Expected result:** The map shows the last loaded layer and the user has completed a repeatable workflow for comparing city infrastructure.

## Output
- Final deliverable: A repeatable Overpass Turbo workflow that queries and visualizes four Hyderabad datasets.
- Verification: Success is confirmed when hospitals, EV charging stations, schools, and parks can each be queried and rendered in sequence.

## Notes
- Overpass Turbo can show API or quota errors. If a query fails, wait and retry rather than assuming the query text is wrong.
- The schools step is the most likely to hit API pressure. If needed, retry after a pause or reduce the bounding box further.
- If the `zoom to data` control is missing, manually pan or zoom the map back to Hyderabad using the map controls.
