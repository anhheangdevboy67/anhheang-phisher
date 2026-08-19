// Point this at your deployed backend if the site is hosted separately
// from the API (e.g. static frontend + backend on another domain).
// Leave as "" to call the API on the same origin the page is served from.
const API_BASE = "";

const form = document.getElementById("inboxForm");
const nameInput = document.getElementById("name");
const messageInput = document.getElementById("message");
const submitBtn = document.getElementById("submitBtn");
const statusMsg = document.getElementById("statusMsg");
const terminalBody = document.getElementById("terminalBody");

function addTerminalLine(text, muted = false) {
  const line = document.createElement("p");
  line.className = "terminal__line" + (muted ? " terminal__line--muted" : "");
  line.textContent = text;
  const waiting = terminalBody.querySelector(".terminal__line--muted");
  if (waiting) waiting.remove();
  terminalBody.appendChild(line);

  const idle = document.createElement("p");
  idle.className = "terminal__line terminal__line--muted";
  idle.innerHTML = 'waiting for new messages<span class="cursor">_</span>';
  terminalBody.appendChild(idle);
}

function setStatus(text, kind) {
  statusMsg.textContent = text;
  statusMsg.className = "status" + (kind ? ` status--${kind}` : "");
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = nameInput.value.trim();
  const message = messageInput.value.trim();

  if (!name || !message) {
    setStatus("Please fill in both fields.", "err");
    return;
  }

  submitBtn.disabled = true;
  setStatus("Sending...");

  try {
    const res = await fetch(`${API_BASE}/api/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, message }),
    });

    if (!res.ok) throw new Error(`Server responded ${res.status}`);

    addTerminalLine(`> [${name}] ${message}`);
    setStatus("Message sent — it'll show up in the terminal inbox.", "ok");
    form.reset();
  } catch (err) {
    console.error(err);
    setStatus("Couldn't send your message. Please try again.", "err");
  } finally {
    submitBtn.disabled = false;
  }
});
