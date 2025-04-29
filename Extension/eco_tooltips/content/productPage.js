(async function () {
  const titleElement = document.getElementById("productTitle");
  if (!titleElement) return;

  const titleText = titleElement.textContent.trim();
  const info = (await window.ecoLookup?.(titleText)) || {
    impact: "Unknown",
    summary: "No environmental insights found for this product.",
    recyclable: null
  };

  let impactEmoji = "❓";
  if (info.impact === "High") impactEmoji = "🔥 High Impact";
  else if (info.impact === "Moderate") impactEmoji = "⚠️ Moderate Impact";
  else if (info.impact === "Low") impactEmoji = "🌱 Low Impact";

  let recycleNote = "";
  if (info.recyclable === true) recycleNote = "♻️ Recyclable";
  else if (info.recyclable === false) recycleNote = "🚯 Not recyclable";

  const panel = document.createElement("div");
  panel.className = "eco-panel";
  panel.style.marginTop = "12px";
  panel.style.padding = "12px";
  panel.style.backgroundColor = "#f4f4f4";
  panel.style.borderLeft = "5px solid #4caf50";
  panel.style.fontFamily = "Arial";
  panel.style.fontSize = "14px";
  panel.innerHTML = `
    <strong>🌍 Environmental Snapshot</strong><br/>
    ${impactEmoji} <strong>Impact Level:</strong> ${info.impact}<br/>
    <strong>Summary:</strong> ${info.summary}<br/>
    <strong>Recyclability:</strong> ${recycleNote}<br/>
    <em style="font-size: 12px;">Based on product title only. Accuracy may vary.</em>
  `;

  titleElement.insertAdjacentElement("afterend", panel);
})();
