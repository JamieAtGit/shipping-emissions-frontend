// File: eco-tooltips/content/tooltip.js
(function () {
  const tooltip = document.createElement("div");
  tooltip.className = "eco-tooltip";
  tooltip.style.display = "none";
  document.body.appendChild(tooltip);

  function showTooltip(e, text) {
    tooltip.textContent = text;
    tooltip.style.left = `${e.pageX + 12}px`;
    tooltip.style.top = `${e.pageY + 12}px`;
    tooltip.style.display = "block";
  }

  function hideTooltip() {
    tooltip.style.display = "none";
  }

  function attachHoverListeners() {
    const productTiles = document.querySelectorAll('[data-component-type="s-search-result"]');

    productTiles.forEach((tile) => {
      if (!tile.dataset.tooltipAttached) {
        tile.dataset.tooltipAttached = "true";

        tile.addEventListener("mouseover", async (e) => {
          const title = tile.querySelector("h2")?.innerText || "Unknown product";

          const info = (await window.ecoLookup?.(title)) || {
            summary: "Unknown product. No environmental data found.",
            impact: "Unknown",
            recyclable: null
          };

          let impactEmoji = "❓";
          if (info.impact === "High") impactEmoji = "🔥 High Impact";
          else if (info.impact === "Moderate") impactEmoji = "⚠️ Moderate Impact";
          else if (info.impact === "Low") impactEmoji = "🌱 Low Impact";

          // Optional: Remove old badge if it exists
          const existingBadge = tile.querySelector(".eco-badge");
          if (existingBadge) existingBadge.remove();

          // 👇 Create and insert the badge
          const badge = document.createElement("span");
          badge.textContent = impactEmoji;
          badge.classList.add("eco-badge");

          if (info.impact === "High") badge.classList.add("high");
          else if (info.impact === "Moderate") badge.classList.add("moderate");
          else if (info.impact === "Low") badge.classList.add("low");

          const titleElement = tile.querySelector("h2");
          if (titleElement) {
            titleElement.appendChild(badge);
          }


          let recycleNote = "";
          if (info.recyclable === true) recycleNote = "♻️ Recyclable";
          else if (info.recyclable === false) recycleNote = "🚯 Not recyclable";

          const tooltipHTML = `
            <strong>${impactEmoji}</strong><br/>
            ${info.summary}<br/>
            <em>${recycleNote}</em>
          `;

          tooltip.innerHTML = tooltipHTML;
          tooltip.style.left = `${e.pageX + 12}px`;
          tooltip.style.top = `${e.pageY + 12}px`;
          tooltip.style.display = "block";
        });

        tile.addEventListener("mousemove", (e) => {
          tooltip.style.left = `${e.pageX + 12}px`;
          tooltip.style.top = `${e.pageY + 12}px`;
        });

        tile.addEventListener("mouseout", hideTooltip);
      }
    });
  }

  setTimeout(attachHoverListeners, 3000);
})();
