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

  // Build the Explanation History! (Never deletes old stuff)
  let historyText = "";
  for (let i = 0; i <= currentStepIndex; i++) {
    if (traceData[i].explanation) {
      historyText += traceData[i].explanation + "\n\n"; // Adds space between steps
    }
  }
  explanationDisplay.innerText = historyText;
  // Auto-scroll to the bottom of the history box
  explanationDisplay.scrollTop = explanationDisplay.scrollHeight;

  // Update the right side boxes
  callStackDisplay.innerText = step.call_stack || "Main Script";
  outputDisplay.innerText = step.output || "";
  errorDisplay.innerText = step.error || "";
}