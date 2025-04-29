// == Amazon Environmental Impact Tooltip ==
// Injected into Amazon product pages, fetches live CO₂ data from Flask API

const POSTCODE = "AB12CD"; // Replace or pass dynamically from popup if needed

// Function to inject a nice tooltip
function showTooltip(carbonKg) {
  const tooltip = document.createElement("div");
  tooltip.textContent = `🌍 Estimated CO₂: ${carbonKg.toFixed(2)} kg`;
  tooltip.style.position = "fixed";
  tooltip.style.bottom = "20px";
  tooltip.style.right = "20px";
  tooltip.style.padding = "10px 15px";
  tooltip.style.backgroundColor = "#1e1e1e";
  tooltip.style.color = "#fff";
  tooltip.style.fontSize = "14px";
  tooltip.style.borderRadius = "8px";
  tooltip.style.boxShadow = "0 4px 12px rgba(0,0,0,0.3)";
  tooltip.style.zIndex = "9999";

  document.body.appendChild(tooltip);

  setTimeout(() => tooltip.remove(), 10000);
}

// Fetch emissions from your Flask backend
async function fetchEnvironmentalDataLive(productUrl, postcode) {
  try {
    const response = await fetch("http://localhost:5000/estimate_emissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        amazon_url: productUrl,
        postcode: postcode
      }),
    });

    if (!response.ok) throw new Error(`API error ${response.status}`);

    const data = await response.json();
    console.log("🌿 Live data:", data);

    const carbonKg = data?.data?.attributes?.carbon_kg;
    if (carbonKg !== undefined) {
      showTooltip(carbonKg);
    } else {
      alert("❌ Could not estimate emissions for this product.");
    }
  } catch (error) {
    console.error("⚠️ Fetch failed:", error);
    alert("❌ Failed to contact backend for emissions data.");
  }
}

// Automatically run on Amazon product pages
if (
  window.location.hostname.includes("amazon.") &&
  window.location.href.includes("/dp/")
) {
  const currentUrl = window.location.href;
  console.log("🛒 Injecting live tooltip on:", currentUrl);
  fetchEnvironmentalDataLive(currentUrl, POSTCODE);
}
