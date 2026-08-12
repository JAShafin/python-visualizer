let traceData = [];
let currentStepIndex = 0;

// Connect to the UI Elements from index.html
const codeInput = document.getElementById('code-input');
const programInputs = document.getElementById('program-inputs');
const runBtn = document.getElementById('run-btn');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const resetBtn = document.getElementById('reset-btn');
const timeline = document.getElementById('timeline');

// Connect to the Display Data Boxes
const codeDisplay = document.getElementById('code-display');
const callStackDisplay = document.getElementById('call-stack-display');
const explanationDisplay = document.getElementById('explanation-display');
const outputDisplay = document.getElementById('output-display');
const errorDisplay = document.getElementById('error-display');

// When the user clicks "Run Trace"
runBtn.addEventListener('click', async () => {
  const code = codeInput.value;
  const inputs = programInputs.value;

  if (!code.trim()) {
    alert("Please enter some Python code to trace.");
    return;
  }

  try {
    const response = await fetch('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code, inputs: inputs })
    });

    const data = await response.json();

    if (data.error && !data.trace) {
      errorDisplay.innerText = data.error;
      return;
    }

    traceData = data.trace || [];
    if (traceData.length === 0) {
      explanationDisplay.innerText = "No trace data generated.";
      return;
    }

    // Setup timeline and starting state
    timeline.max = traceData.length - 1;
    currentStepIndex = 0;
    timeline.value = 0;

    updateUI();

  } catch (err) {
    errorDisplay.innerText = "Failed to connect to the server.";
  }
});

// Function to update the screen whenever you click Next or Previous
function updateUI() {
  if (traceData.length === 0) return;

  const step = traceData[currentStepIndex];

  // Update Timeline slider
  timeline.value = currentStepIndex;

  // Highlight the current line of code in the black window
  const codeLines = codeInput.value.split('\n');
  let highlightedCode = '';

  for (let i = 0; i < codeLines.length; i++) {
    const lineNum = String(i + 1).padStart(2, '0');

    if (step.line === i + 1) {
      highlightedCode += `<span style="background-color: #3b5998; color: white; display: block;">${lineNum}: ${codeLines[i]}</span>`;
    } else {
      highlightedCode += `${lineNum}: ${codeLines[i]}\n`;
    }
  }
  codeDisplay.innerHTML = highlightedCode;

  // Update the right side boxes
  callStackDisplay.innerText = step.call_stack || "Main";
  explanationDisplay.innerText = step.explanation || "No changes to report.";
  outputDisplay.innerText = step.output || "";
  errorDisplay.innerText = step.error || "";
}

// Button Click Events
nextBtn.addEventListener('click', () => {
  if (currentStepIndex < traceData.length - 1) {
    currentStepIndex++;
    updateUI();
  }
});

prevBtn.addEventListener('click', () => {
  if (currentStepIndex > 0) {
    currentStepIndex--;
    updateUI();
  }
});

resetBtn.addEventListener('click', () => {
  currentStepIndex = 0;
  updateUI();
});

timeline.addEventListener('input', (e) => {
  currentStepIndex = parseInt(e.target.value);
  updateUI();
});