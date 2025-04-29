// File: eco-tooltips/utils/lookup.js

let insightMap = null;

// Load JSON once and cache it
async function loadInsights() {
  if (insightMap) return insightMap;
  const res = await fetch(chrome.runtime.getURL("eco-tooltips/data/material_insights.json"));
  insightMap = await res.json();
  return insightMap;
}

// Exposed global function for use in tooltip.js
window.ecoLookup = async function (productTitle) {
  const insights = await loadInsights();
  const lower = productTitle.toLowerCase();

  // Look for whole words or material mentions inside parentheses or specs
  for (const key in insights) {
    const pattern = new RegExp(`\\b${key}\\b`, 'i');
    if (pattern.test(lower)) {
      return insights[key];
    }
  }

  return {
    summary: "Environmental data not available. Product may contain plastic or electronics.",
    impact: "Unknown",
    recyclable: null
  };
};

