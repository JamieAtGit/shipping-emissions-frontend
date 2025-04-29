# Eco Tooltips

This module adds environmental insight tooltips to Amazon product listings.

## How It Works
- On hover, products trigger tooltips based on detected keywords in their titles.
- Tooltips display material impacts pulled from a keyword map (`lookup.js`).
- Easy to expand by editing `material_insights.json` or improving lookup logic.

## Usage
1. Include `contentScript.js` in your extension's manifest.
2. Ensure `lookup.js` and `tooltip.js` are loaded in the proper order.
3. Style is controlled by `tooltip.css`.

## To Do
- Connect to real product metadata.
- Expand keywords + integrate lifecycle datasets.
- Add hover-to-click interaction for deeper insights.