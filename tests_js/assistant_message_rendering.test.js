const assert = require("node:assert/strict");

const {
  formatDurationLabel,
  renderMessageContent,
} = require("../static/assistant/assistant_message_rendering.js");

function createElement(tagName, ownerDocument) {
  const element = {
    tagName: String(tagName || "div").toUpperCase(),
    ownerDocument,
    className: "",
    textContent: "",
    children: [],
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    querySelector(selector) {
      const className = selector.charAt(0) === "." ? selector.slice(1) : selector;

      function visit(node) {
        if ((node.className || "").split(/\s+/).includes(className)) {
          return node;
        }
        for (let index = 0; index < (node.children || []).length; index += 1) {
          const match = visit(node.children[index]);
          if (match) {
            return match;
          }
        }
        return null;
      }

      return visit(this);
    },
  };

  Object.defineProperty(element, "innerHTML", {
    get() {
      return "";
    },
    set() {
      element.children = [];
      element.textContent = "";
    },
  });

  return element;
}

function createDocument() {
  return {
    createElement(tagName) {
      return createElement(tagName, this);
    },
  };
}

function flattenTexts(node) {
  const values = [];

  function visit(current) {
    if (current.textContent) {
      values.push(current.textContent);
    }
    (current.children || []).forEach(visit);
  }

  visit(node);
  return values.join(" | ");
}

async function runTest(name, fn) {
  try {
    await fn();
    console.log("ok - " + name);
  } catch (error) {
    console.error("fail - " + name);
    throw error;
  }
}

async function main() {
  await runTest("formats long duration labels to business-friendly text", async () => {
    assert.equal(formatDurationLabel("140:47:22"), "140h 47m 22s");
    assert.equal(formatDurationLabel("texto livre"), "texto livre");
  });

  await runTest("renders ranking payload as structured analytical card", async () => {
    const documentRef = createDocument();
    const bubble = createElement("div", documentRef);

    renderMessageContent(documentRef, bubble, {
      content: "fallback",
      payload: {
        type: "ranking",
        title: "Top 5 agentes mais improdutivos",
        period: "01/01/2026 ate 10/03/2026",
        total_agents: 45,
        items: [
          {
            rank: 1,
            name: "ADRIELY.SANTOS",
            value: "140:47:22",
            label: "improdutivo",
            value_type: "duration",
          },
          {
            rank: 2,
            name: "KAINAN.NUNES",
            value: "136:05:24",
            label: "improdutivo",
            value_type: "duration",
          },
        ],
      },
    });

    assert.equal(bubble.querySelector(".assistant-ranking") !== null, true);
    assert.equal(bubble.querySelector(".assistant-ranking__title").textContent, "Top 5 agentes mais improdutivos");
    assert.match(bubble.querySelector(".assistant-ranking__meta").textContent, /01\/01\/2026 -> 10\/03\/2026/);
    assert.match(bubble.querySelector(".assistant-ranking__meta").textContent, /45 agentes/);
    assert.equal(bubble.querySelector(".assistant-ranking-name").textContent, "ADRIELY.SANTOS");
    assert.match(flattenTexts(bubble), /140h 47m 22s improdutivo/);
  });

  await runTest("falls back to plain text when payload is not analytical", async () => {
    const documentRef = createDocument();
    const bubble = createElement("div", documentRef);

    renderMessageContent(documentRef, bubble, {
      content: "Resumo operacional concluido.",
      payload: {},
    });

    assert.equal(bubble.textContent, "Resumo operacional concluido.");
    assert.equal(bubble.children.length, 0);
  });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
