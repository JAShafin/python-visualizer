const EXAMPLES = {
  "Simple loop": `total = 0\nfor i in range(3):\n    total += i\nprint(total)`,
  "Function call": `def square(x):\n    return x * x\n\nvalue = square(5)\nprint(value)`,
  "List tracking": `numbers = [1, 2, 3]\nnumbers.append(4)\nprint(numbers)`
};

let traceEvents = [];
let currentStep = 0;

const codeInput = document.getElementById("codeInput");
const codeView = document.getElementById("codeView");
const stackView = document.getElementById("stackView");
const variablesView = document.getElementById("variablesView");
const outputView = document.getElementById("outputView");
const errorView = document.getElementById("errorView");
const timeline = document.getElementById("timeline");
const hintText = document.getElementById("hintText");
const learningMode = document.getElementById("learningMode");
const examples = document.getElementById("examples");

function initExamples() {
  Object.keys(EXAMPLES).forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    examples.appendChild(option);
  });
  examples.addEventListener("change", () => {
    codeInput.value = EXAMPLES[examples.value];
    renderCode();
  });
  examples.value = Object.keys(EXAMPLES)[0];
}

function renderCode(activeLine = -1) {
  const lines = codeInput.value.split("\n");
  codeView.innerHTML = lines
    .map((line, idx) => {
      const lineNumber = idx + 1;
      const activeClass = lineNumber === activeLine ? "line active" : "line";
      return `<span class="${activeClass}">${lineNumber.toString().padStart(2, "0")}: ${escapeHtml(line)}</span>`;
    })
    .join("");
}

function escapeHtml(str) {
  return str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function updateStepView() {
  if (!traceEvents.length) {
    renderCode();
    stackView.innerHTML = "";
    variablesView.innerHTML = "";
    hintText.textContent = "";
    return;
  }

  const event = traceEvents[currentStep];
  renderCode(event.line);

  stackView.innerHTML = (event.stack || [])
    .map((frame) => `<li>${frame.function} @ line ${frame.line}</li>`)
    .join("");

  const localsRows = Object.entries(event.locals || {}).map(
    ([key, value]) => `<tr><td>local</td><td>${escapeHtml(key)}</td><td>${escapeHtml(String(value))}</td></tr>`
  );
  const globalsRows = Object.entries(event.globals || {}).map(
    ([key, value]) => `<tr><td>global</td><td>${escapeHtml(key)}</td><td>${escapeHtml(String(value))}</td></tr>`
  );
  variablesView.innerHTML = [...globalsRows, ...localsRows].join("");

  outputView.textContent = event.stdout || "";

  if (learningMode.checked) {
    hintText.textContent = getHint(event);
  } else {
    hintText.textContent = "";
  }
}

function getHint(event) {
  if (event.event === "call") return "A function call started; watch new frame data in the stack.";
  if (event.event === "return") return "A function is returning; inspect variables before they leave scope.";
  if (event.event === "line") return "Line-by-line execution lets you inspect how values change.";
  if (event.event === "exception") return `An exception occurred: ${event.exception || "unknown"}`;
  return "Step through to understand state transitions.";
}

async function runTrace() {
  errorView.textContent = "";
  outputView.textContent = "";

  const response = await fetch("/api/trace", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code: codeInput.value })
  });

  const payload = await response.json();
  if (!response.ok || payload.status !== "ok") {
    traceEvents = [];
    currentStep = 0;
    timeline.max = 0;
    timeline.value = 0;
    errorView.textContent = payload.error || "Trace failed";
    updateStepView();
    return;
  }

  traceEvents = payload.events || [];
  currentStep = 0;
  timeline.max = Math.max(traceEvents.length - 1, 0);
  timeline.value = 0;
  outputView.textContent = payload.stdout || "";
  updateStepView();
}

function bindControls() {
  document.getElementById("runBtn").addEventListener("click", runTrace);

  document.getElementById("nextBtn").addEventListener("click", () => {
    if (!traceEvents.length) return;
    currentStep = Math.min(currentStep + 1, traceEvents.length - 1);
    timeline.value = currentStep;
    updateStepView();
  });

  document.getElementById("prevBtn").addEventListener("click", () => {
    if (!traceEvents.length) return;
    currentStep = Math.max(currentStep - 1, 0);
    timeline.value = currentStep;
    updateStepView();
  });

  document.getElementById("resetBtn").addEventListener("click", () => {
    currentStep = 0;
    timeline.value = 0;
    updateStepView();
  });

  timeline.addEventListener("input", () => {
    currentStep = Number(timeline.value);
    updateStepView();
  });

  learningMode.addEventListener("change", updateStepView);

  document.getElementById("saveBtn").addEventListener("click", () => {
    localStorage.setItem("python-visualizer-snippet", codeInput.value);
    hintText.textContent = "Snippet saved locally.";
  });

  document.getElementById("loadBtn").addEventListener("click", () => {
    const saved = localStorage.getItem("python-visualizer-snippet");
    if (saved) {
      codeInput.value = saved;
      renderCode();
      hintText.textContent = "Loaded saved snippet.";
    }
  });

  document.getElementById("shareBtn").addEventListener("click", async () => {
    const url = new URL(window.location.href);
    url.searchParams.set("code", btoa(unescape(encodeURIComponent(codeInput.value))));
    await navigator.clipboard.writeText(url.toString());
    hintText.textContent = "Share link copied to clipboard.";
  });

  codeInput.addEventListener("input", () => renderCode());
}

function loadInitialSnippet() {
  const params = new URLSearchParams(window.location.search);
  const encoded = params.get("code");
  if (encoded) {
    try {
      codeInput.value = decodeURIComponent(escape(atob(encoded)));
      return;
    } catch (_) {
      // keep fallback
    }
  }
  codeInput.value = EXAMPLES[examples.value];
}

initExamples();
bindControls();
loadInitialSnippet();
renderCode();
updateStepView();
