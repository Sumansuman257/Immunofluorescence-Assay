const PROTOCOL = [
  {
    id: 1,
    title: "Fix cells",
    detail: "100% methanol · 10 minutes",
    minutes: 10,
  },
  {
    id: 2,
    title: "Permeabilize",
    detail: "0.2% Triton X-100 · 10 minutes",
    minutes: 10,
  },
  {
    id: 3,
    title: "Block",
    detail: "1% PBS–BSA · 30 minutes",
    minutes: 30,
  },
  {
    id: 4,
    title: "Primary antibody",
    detail: "Incubation · 60 minutes",
    minutes: 60,
  },
  {
    id: 5,
    title: "Secondary antibody",
    detail: "Fluorophore conjugation · 60 minutes",
    minutes: 60,
  },
];

const timers = new Map();

function updateCurrentTime() {
  const now = new Date();
  document.getElementById("currentTime").textContent = now.toLocaleTimeString();
}

function formatRemaining(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}m ${String(seconds).padStart(2, "0")}s`;
}

function renderSteps() {
  const root = document.getElementById("steps");
  root.innerHTML = PROTOCOL.map(
    (step) => `
    <article class="step" id="step-${step.id}" data-step="${step.id}">
      <p class="step-index">${String(step.id).padStart(2, "0")}</p>
      <div>
        <h2>${step.title}</h2>
        <p class="detail">${step.detail}</p>
      </div>
      <div class="controls">
        <button type="button" data-action="start" data-id="${step.id}">Start</button>
      </div>
      <p class="meta" id="status-${step.id}"></p>
      <p class="countdown" id="countdown-${step.id}" aria-live="polite"></p>
    </article>`
  ).join("");
}

function clearTimer(stepId) {
  const existing = timers.get(stepId);
  if (existing) {
    clearInterval(existing);
    timers.delete(stepId);
  }
}

function startStep(stepId) {
  const step = PROTOCOL.find((item) => item.id === stepId);
  if (!step) return;

  clearTimer(stepId);

  const article = document.getElementById(`step-${stepId}`);
  const button = article.querySelector('[data-action="start"]');
  const status = document.getElementById(`status-${stepId}`);
  const countdown = document.getElementById(`countdown-${stepId}`);

  button.disabled = true;
  countdown.classList.remove("done");

  const startTime = new Date();
  status.textContent = `Started at ${startTime.toLocaleTimeString()}`;

  let totalSeconds = step.minutes * 60;
  countdown.textContent = `Time remaining: ${formatRemaining(totalSeconds)}`;

  const intervalId = setInterval(() => {
    totalSeconds -= 1;
    if (totalSeconds <= 0) {
      clearTimer(stepId);
      countdown.textContent = "Step completed — move to the next stage";
      countdown.classList.add("done");
      button.disabled = false;
      button.textContent = "Restart";
      return;
    }
    countdown.textContent = `Time remaining: ${formatRemaining(totalSeconds)}`;
  }, 1000);

  timers.set(stepId, intervalId);
}

function resetAll() {
  PROTOCOL.forEach((step) => {
    clearTimer(step.id);
    const article = document.getElementById(`step-${step.id}`);
    const button = article.querySelector('[data-action="start"]');
    button.disabled = false;
    button.textContent = "Start";
    document.getElementById(`status-${step.id}`).textContent = "";
    const countdown = document.getElementById(`countdown-${step.id}`);
    countdown.textContent = "";
    countdown.classList.remove("done");
  });
}

document.getElementById("steps").addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  if (target.dataset.action !== "start") return;
  const id = Number(target.dataset.id);
  startStep(id);
});

document.getElementById("resetAll").addEventListener("click", resetAll);

renderSteps();
updateCurrentTime();
setInterval(updateCurrentTime, 1000);
