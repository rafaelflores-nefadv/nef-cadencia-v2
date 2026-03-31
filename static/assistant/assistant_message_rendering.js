(function (root, factory) {
  "use strict";

  var api = factory(root);
  root.AssistantMessageRendering = api;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";

  function formatDurationLabel(rawValue) {
    var match = String(rawValue || "").match(/^(\d+):(\d{2}):(\d{2})$/);
    if (!match) {
      return String(rawValue || "");
    }
    return match[1] + "h " + match[2] + "m " + match[3] + "s";
  }

  function buildRankingCard(documentRef, payload) {
    var card = documentRef.createElement("section");
    card.className = "assistant-ranking";

    var title = documentRef.createElement("div");
    title.className = "assistant-ranking__title";
    title.textContent = payload.title || "Ranking operacional";
    card.appendChild(title);

    var meta = documentRef.createElement("div");
    meta.className = "assistant-ranking__meta";
    var metaParts = [];
    if (payload.period) {
      metaParts.push("Periodo: " + payload.period.replace(" ate ", " -> "));
    }
    if (payload.total_agents) {
      metaParts.push("Base analisada: " + payload.total_agents + " agentes");
    }
    meta.textContent = metaParts.join(" | ");
    card.appendChild(meta);

    var list = documentRef.createElement("div");
    list.className = "assistant-ranking__list";

    var items = Array.isArray(payload.items) ? payload.items : [];
    for (var i = 0; i < items.length; i += 1) {
      var item = items[i];
      var row = documentRef.createElement("article");
      row.className = "assistant-ranking-item";

      var rank = documentRef.createElement("div");
      rank.className = "assistant-ranking-item__rank";
      rank.textContent = String(item.rank || i + 1);

      var body = documentRef.createElement("div");
      body.className = "assistant-ranking-item__body";

      var name = documentRef.createElement("div");
      name.className = "assistant-ranking-name";
      name.textContent = item.name || "Sem identificacao";

      var value = documentRef.createElement("div");
      value.className = "assistant-ranking-value";
      var rawValue = item.value || "";
      var formattedValue = item.value_type === "duration"
        ? formatDurationLabel(rawValue)
        : item.value_type === "percentage" && rawValue !== ""
            && rawValue !== null && rawValue !== undefined
          ? rawValue + "%"
          : rawValue;
      value.textContent = [
        formattedValue,
        item.label || ""
      ].filter(function (part) {
        return String(part || "").trim() !== "";
      }).join(" ");

      body.appendChild(name);
      body.appendChild(value);
      row.appendChild(rank);
      row.appendChild(body);
      list.appendChild(row);
    }

    card.appendChild(list);
    return card;
  }

  function renderMessageContent(documentRef, bubbleEl, message) {
    var payload = message && typeof message.payload === "object" ? message.payload : {};
    if (payload && payload.type === "ranking") {
      bubbleEl.textContent = "";
      bubbleEl.appendChild(buildRankingCard(documentRef, payload));
      return;
    }
    bubbleEl.textContent = (message && message.content) || "";
  }

  return {
    formatDurationLabel: formatDurationLabel,
    renderMessageContent: renderMessageContent,
  };
});
