const runBtn = document.getElementById('run-btn');
const codeInput = document.getElementById('code-input');
const programInputs = document.getElementById('program-inputs');
const terminalDisplay = document.getElementById('terminal-display');

runBtn.addEventListener('click', async () => {
  const code = codeInput.value;
  const inputs = programInputs.value;

  if (!code.trim()) {
    alert("Please write some code first!");
    return;
  }

  terminalDisplay.innerText = "Running...";
  terminalDisplay.style.color = "#c9d1d9"; // Reset color to standard terminal text

  try {
    const response = await fetch('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: code, inputs: inputs })
    });

    const data = await response.json();

    // If Python crashed or had a syntax error, show it in red
    if (data.error) {
      terminalDisplay.innerText = data.error;
      terminalDisplay.style.color = "#ff7b72"; // Red error text
    }
    // Otherwise, show the normal print() outputs
    else {
      terminalDisplay.innerText = data.output || "Program finished with no output.";
    }

  } catch (err) {
    terminalDisplay.innerText = "Error: Could not connect to the server.";
    terminalDisplay.style.color = "#ff7b72";
  }
});