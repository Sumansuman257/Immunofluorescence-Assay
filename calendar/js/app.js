(() => {
  "use strict";

  const STORAGE_KEY = "kairos.calendar.v1";
  const HOUR_HEIGHT = 48;

  const PRESETS = {
    observatory: {
      accent: "#3DDC97",
      signal: "#FF8A4C",
      surface: "#0D1B24",
      ink: "#E8F1F5",
      radius: 16,
      density: 1,
      type: 1,
      motion: "lively",
      displayFont: "Syne",
      popupStyle: "toast",
      browserNotify: true,
      soundAlerts: true,
    },
    ember: {
      accent: "#F0A202",
      signal: "#E4572E",
      surface: "#1A1210",
      ink: "#F7EFE8",
      radius: 10,
      density: 0.95,
      type: 1.02,
      motion: "calm",
      displayFont: "Syne",
      popupStyle: "modal",
      browserNotify: true,
      soundAlerts: true,
    },
    glacier: {
      accent: "#7BDFF2",
      signal: "#B388EB",
      surface: "#0B1C24",
      ink: "#EAF6F9",
      radius: 22,
      density: 1.05,
      type: 1,
      motion: "lively",
      displayFont: "Manrope",
      popupStyle: "toast",
      browserNotify: true,
      soundAlerts: false,
    },
    mono: {
      accent: "#D7DEDC",
      signal: "#A7F3D0",
      surface: "#111111",
      ink: "#F4F4F4",
      radius: 4,
      density: 1,
      type: 0.98,
      motion: "off",
      displayFont: "'Courier New', monospace",
      popupStyle: "toast-only",
      browserNotify: true,
      soundAlerts: false,
    },
  };

  const defaultState = () => {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    const tomorrow = new Date(now);
    tomorrow.setDate(now.getDate() + 1);
    const ty = tomorrow.getFullYear();
    const tm = String(tomorrow.getMonth() + 1).padStart(2, "0");
    const td = String(tomorrow.getDate()).padStart(2, "0");

    return {
      view: "month",
      cursor: isoDate(now),
      calendars: [
        { id: "work", name: "Work", color: "#3DDC97", visible: true },
        { id: "life", name: "Life", color: "#FF8A4C", visible: true },
        { id: "focus", name: "Deep Focus", color: "#7BDFF2", visible: true },
      ],
      events: [
        {
          id: uid(),
          title: "Launch planning standup",
          date: `${y}-${m}-${d}`,
          start: nearTime(1),
          end: nearTime(1.75),
          calendarId: "work",
          allDay: false,
          energy: "medium",
          reminder: 5,
          repeat: "none",
          location: "Main studio",
          notes: "Ship blockers + demo checklist",
        },
        {
          id: uid(),
          title: "Design critique",
          date: `${y}-${m}-${d}`,
          start: nearTime(2.5),
          end: nearTime(3.5),
          calendarId: "work",
          allDay: false,
          energy: "high",
          reminder: 15,
          repeat: "weekly",
          location: "Board room",
          notes: "Bring three comps",
        },
        {
          id: uid(),
          title: "Evening run",
          date: `${ty}-${tm}-${td}`,
          start: "18:30",
          end: "19:15",
          calendarId: "life",
          allDay: false,
          energy: "low",
          reminder: 30,
          repeat: "daily",
          location: "River path",
          notes: "",
        },
        {
          id: uid(),
          title: "Focus block — Kairos polish",
          date: `${y}-${m}-${d}`,
          start: nearTime(4),
          end: nearTime(5.5),
          calendarId: "focus",
          allDay: false,
          energy: "high",
          reminder: 5,
          repeat: "none",
          location: "",
          notes: "No meetings. Headphones on.",
        },
      ],
      settings: { ...PRESETS.observatory },
      firedReminders: {},
      snoozed: {},
    };
  };

  let state = loadState();
  let editingId = null;
  let commandIndex = 0;
  let audioCtx = null;

  const els = {
    periodLabel: $("#periodLabel"),
    viewShell: $("#viewShell"),
    liveClock: $("#liveClock"),
    layerList: $("#layerList"),
    incomingList: $("#incomingList"),
    conflictList: $("#conflictList"),
    urgencyRibbon: $("#urgencyRibbon"),
    eventModal: $("#eventModal"),
    themeModal: $("#themeModal"),
    commandModal: $("#commandModal"),
    toastStack: $("#toastStack"),
    pulseOverlay: $("#pulseOverlay"),
    pulseTitle: $("#pulseTitle"),
    pulseMeta: $("#pulseMeta"),
  };

  init();

  function init() {
    applyTheme();
    bindUI();
    render();
    tickClock();
    setInterval(tickClock, 1000);
    setInterval(checkReminders, 5000);
    requestNotifyPermission();
    // Demo toast shortly after load so the popup system is obvious
    setTimeout(() => {
      const next = upcomingEvents(1)[0];
      if (next) {
        pushToast({
          title: "Kairos is watching your timeline",
          body: `Next up: ${next.title} · ${formatWhen(next)}`,
          eventId: next.id,
        });
      }
    }, 1200);
  }

  function bindUI() {
    $("#prevBtn").addEventListener("click", () => shiftPeriod(-1));
    $("#nextBtn").addEventListener("click", () => shiftPeriod(1));
    $("#todayBtn").addEventListener("click", () => {
      state.cursor = isoDate(new Date());
      save();
      render();
    });

    document.querySelectorAll(".view-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.view = btn.dataset.view;
        document.querySelectorAll(".view-tab").forEach((b) => b.classList.toggle("active", b === btn));
        save();
        render();
      });
    });

    $("#addEventBtn").addEventListener("click", () => openEventModal());
    $("#closeEventModal").addEventListener("click", () => els.eventModal.close());
    $("#cancelEventBtn").addEventListener("click", () => els.eventModal.close());
    $("#deleteEventBtn").addEventListener("click", deleteEditingEvent);
    $("#eventForm").addEventListener("submit", saveEventFromForm);
    $("#eventAllDay").addEventListener("change", (e) => {
      $("#eventStart").disabled = e.target.checked;
      $("#eventEnd").disabled = e.target.checked;
    });

    $("#quickForm").addEventListener("submit", (e) => {
      e.preventDefault();
      const text = $("#quickInput").value.trim();
      if (!text) return;
      const parsed = parseNatural(text);
      if (!parsed) {
        pushToast({ title: "Couldn’t parse that", body: "Try: Team sync tomorrow 2pm 30m" });
        return;
      }
      state.events.push(parsed);
      $("#quickInput").value = "";
      save();
      render();
      pushToast({ title: "Event captured", body: `${parsed.title} · ${formatWhen(parsed)}`, eventId: parsed.id });
    });

    $("#addCalendarBtn").addEventListener("click", () => {
      const name = prompt("Calendar layer name?");
      if (!name) return;
      const colors = ["#3DDC97", "#FF8A4C", "#7BDFF2", "#F0A202", "#E4572E", "#A7F3D0"];
      state.calendars.push({
        id: uid(),
        name: name.trim(),
        color: colors[state.calendars.length % colors.length],
        visible: true,
      });
      save();
      render();
    });

    $("#themeBtn").addEventListener("click", openThemeModal);
    $("#closeThemeModal").addEventListener("click", () => els.themeModal.close());
    $("#saveThemeBtn").addEventListener("click", () => {
      readThemeForm();
      applyTheme();
      save();
      els.themeModal.close();
      pushToast({ title: "Theme applied", body: "Your calendar look is updated." });
    });

    document.querySelectorAll(".preset").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.settings = { ...PRESETS[btn.dataset.preset] };
        fillThemeForm();
        applyTheme();
        save();
      });
    });

    $("#exportDataBtn").addEventListener("click", exportData);
    $("#importDataBtn").addEventListener("click", () => $("#importFile").click());
    $("#importFile").addEventListener("change", importData);

    $("#commandBtn").addEventListener("click", openCommand);
    $("#commandInput").addEventListener("input", () => renderCommandResults($("#commandInput").value));
    $("#commandInput").addEventListener("keydown", onCommandKey);

    $("#pulseDismiss").addEventListener("click", () => {
      els.pulseOverlay.classList.add("hidden");
    });
    $("#pulseSnooze").addEventListener("click", () => {
      const id = els.pulseOverlay.dataset.eventId;
      if (id) state.snoozed[id] = Date.now() + 5 * 60 * 1000;
      save();
      els.pulseOverlay.classList.add("hidden");
      pushToast({ title: "Snoozed", body: "I’ll nudge you again in 5 minutes." });
    });

    window.addEventListener("keydown", (e) => {
      const meta = e.metaKey || e.ctrlKey;
      if (meta && e.key.toLowerCase() === "k") {
        e.preventDefault();
        openCommand();
      }
      if (meta && e.key.toLowerCase() === "n") {
        e.preventDefault();
        openEventModal();
      }
      if (e.key === "Escape") {
        els.commandModal.close();
        els.pulseOverlay.classList.add("hidden");
      }
    });
  }

  function render() {
    renderLayers();
    renderIncoming();
    renderConflicts();
    renderPeriodLabel();
    renderUrgency();

    const view = state.view;
    if (view === "month") renderMonth();
    else if (view === "week") renderWeek();
    else if (view === "day") renderDay();
    else if (view === "agenda") renderAgenda();
    else if (view === "orbit") renderOrbit();
  }

  function renderPeriodLabel() {
    const cursor = parseISO(state.cursor);
    const fmt = new Intl.DateTimeFormat(undefined, {
      month: "long",
      year: "numeric",
      ...(state.view === "day" || state.view === "orbit"
        ? { day: "numeric", weekday: "short" }
        : {}),
      ...(state.view === "week" ? { day: "numeric" } : {}),
    });
    if (state.view === "week") {
      const start = startOfWeek(cursor);
      const end = addDays(start, 6);
      els.periodLabel.textContent = `${fmtMonthDay(start)} – ${fmtMonthDay(end)}, ${end.getFullYear()}`;
    } else if (state.view === "agenda") {
      els.periodLabel.textContent = "Agenda horizon";
    } else {
      els.periodLabel.textContent = fmt.format(cursor);
    }
  }

  function renderLayers() {
    els.layerList.innerHTML = state.calendars
      .map(
        (c) => `
      <li class="layer-item">
        <label>
          <input type="checkbox" data-layer="${c.id}" ${c.visible ? "checked" : ""} />
          <span class="layer-swatch" style="background:${c.color}"></span>
          <span>${escapeHtml(c.name)}</span>
        </label>
      </li>`
      )
      .join("");

    els.layerList.querySelectorAll("input[data-layer]").forEach((input) => {
      input.addEventListener("change", () => {
        const cal = state.calendars.find((c) => c.id === input.dataset.layer);
        if (cal) cal.visible = input.checked;
        save();
        render();
      });
    });
  }

  function renderIncoming() {
    const upcoming = upcomingEvents(5);
    if (!upcoming.length) {
      els.incomingList.innerHTML = `<p class="hint">Nothing scheduled soon.</p>`;
      return;
    }
    els.incomingList.innerHTML = upcoming
      .map((ev) => {
        const cal = calendarOf(ev);
        return `
        <button class="incoming-item" data-id="${ev.id}" style="width:100%;border:0;background:rgba(255,255,255,.03);text-align:left">
          <span class="layer-swatch" style="background:${cal?.color || "var(--accent)"}"></span>
          <span>
            <strong>${escapeHtml(ev.title)}</strong>
            <span>${formatWhen(ev)} · ${countdownLabel(ev)}</span>
          </span>
        </button>`;
      })
      .join("");

    els.incomingList.querySelectorAll("[data-id]").forEach((btn) => {
      btn.addEventListener("click", () => openEventModal(btn.dataset.id));
    });
  }

  function renderConflicts() {
    const conflicts = findConflicts();
    if (!conflicts.length) {
      els.conflictList.innerHTML = `<p class="hint">Clear skies — no overlaps.</p>`;
      return;
    }
    els.conflictList.innerHTML = conflicts
      .slice(0, 4)
      .map(
        (c) => `
      <div class="conflict-item">
        <div>
          <strong>${escapeHtml(c.a.title)} ↔ ${escapeHtml(c.b.title)}</strong>
          <span>${c.date} · ${c.a.start}–${c.a.end}</span>
        </div>
      </div>`
      )
      .join("");
  }

  function renderUrgency() {
    const soon = upcomingEvents(1)[0];
    if (!soon) {
      els.urgencyRibbon.classList.remove("hot");
      return;
    }
    const mins = minutesUntil(soon);
    if (mins >= 0 && mins <= 120) els.urgencyRibbon.classList.add("hot");
    else els.urgencyRibbon.classList.remove("hot");
  }

  function renderMonth() {
    const cursor = parseISO(state.cursor);
    const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
    const start = startOfWeek(first);
    const days = [];
    for (let i = 0; i < 42; i++) days.push(addDays(start, i));

    const dow = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
      .map((d) => `<div class="dow">${d}</div>`)
      .join("");

    const cells = days
      .map((day) => {
        const key = isoDate(day);
        const inMonth = day.getMonth() === cursor.getMonth();
        const isToday = key === isoDate(new Date());
        const events = eventsOn(key).slice(0, 3);
        const extra = Math.max(0, eventsOn(key).length - 3);
        return `
        <div class="day-cell ${inMonth ? "" : "outside"} ${isToday ? "today" : ""}" data-date="${key}">
          <div class="day-num">${day.getDate()}</div>
          ${events
            .map((ev) => {
              const cal = calendarOf(ev);
              return `<button class="event-chip energy-${ev.energy}" data-id="${ev.id}" style="--chip:${cal?.color || "var(--accent)"}">${escapeHtml(ev.title)}</button>`;
            })
            .join("")}
          ${extra ? `<div class="more-count">+${extra} more</div>` : ""}
        </div>`;
      })
      .join("");

    els.viewShell.innerHTML = `<div class="month-grid">${dow}${cells}</div>`;
    wireDayCells();
    wireEventChips();
  }

  function renderWeek() {
    const start = startOfWeek(parseISO(state.cursor));
    renderTimeGrid([...Array(7)].map((_, i) => addDays(start, i)), 7);
  }

  function renderDay() {
    renderTimeGrid([parseISO(state.cursor)], 1);
  }

  function renderTimeGrid(days, cols) {
    const heads = days
      .map((d) => {
        const key = isoDate(d);
        const label = d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
        return `<div class="day-head">${label}${key === isoDate(new Date()) ? " · today" : ""}</div>`;
      })
      .join("");

    const labels = [...Array(24)]
      .map((_, h) => `<div class="time-label" style="grid-column:1;grid-row:${h + 2}">${String(h).padStart(2, "0")}:00</div>`)
      .join("");

    const colsHtml = days
      .map((day, idx) => {
        const key = isoDate(day);
        const blocks = eventsOn(key)
          .filter((e) => !e.allDay)
          .map((ev) => {
            const cal = calendarOf(ev);
            const top = timeToMinutes(ev.start) / 60 * HOUR_HEIGHT;
            const height = Math.max(28, (timeToMinutes(ev.end) - timeToMinutes(ev.start)) / 60 * HOUR_HEIGHT);
            return `<button class="block-event" data-id="${ev.id}" style="top:${top}px;height:${height}px;--chip:${cal?.color || "var(--accent)"}">
              <strong>${escapeHtml(ev.title)}</strong>
              <span>${ev.start}–${ev.end}</span>
            </button>`;
          })
          .join("");
        return `<div class="day-col" data-date="${key}" style="grid-column:${idx + 2};grid-row:2 / span 24">${blocks}</div>`;
      })
      .join("");

    els.viewShell.innerHTML = `
      <div class="time-grid" style="--cols:${cols}">
        <div></div>
        ${heads}
        ${labels}
        ${colsHtml}
      </div>`;

    els.viewShell.querySelectorAll(".day-col").forEach((col) => {
      col.addEventListener("dblclick", (e) => {
        if (e.target.closest(".block-event")) return;
        const rect = col.getBoundingClientRect();
        const y = e.clientY - rect.top;
        const minutes = Math.round((y / HOUR_HEIGHT) * 60 / 15) * 15;
        const start = minutesToTime(Math.max(0, Math.min(23 * 60 + 45, minutes)));
        const end = minutesToTime(Math.min(24 * 60, timeToMinutes(start) + 60));
        openEventModal(null, { date: col.dataset.date, start, end });
      });
    });
    wireEventChips();
  }

  function renderAgenda() {
    const start = parseISO(state.cursor);
    const groups = [];
    for (let i = 0; i < 14; i++) {
      const day = addDays(start, i);
      const key = isoDate(day);
      const list = eventsOn(key);
      if (list.length) groups.push({ day, key, list });
    }

    if (!groups.length) {
      els.viewShell.innerHTML = `<div class="empty-state">No events in the next two weeks. Capture one with Quick capture or + Event.</div>`;
      return;
    }

    els.viewShell.innerHTML = `<div class="agenda-list">${groups
      .map(({ day, list }) => {
        const label = day.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
        return `<div class="agenda-day">
          <div class="agenda-date">${label}</div>
          <div class="agenda-events">
            ${list
              .map((ev) => {
                const cal = calendarOf(ev);
                return `<button class="agenda-item" data-id="${ev.id}">
                  <span class="dot" style="background:${cal?.color || "var(--accent)"}"></span>
                  <span>
                    <strong>${escapeHtml(ev.title)}</strong><br/>
                    <span style="color:var(--ink-dim);font-size:.82rem">${ev.allDay ? "All day" : `${ev.start}–${ev.end}`}${ev.location ? " · " + escapeHtml(ev.location) : ""}</span>
                  </span>
                  <span class="countdown">${countdownLabel(ev)}</span>
                </button>`;
              })
              .join("")}
          </div>
        </div>`;
      })
      .join("")}</div>`;

    wireEventChips();
  }

  function renderOrbit() {
    const day = parseISO(state.cursor);
    const key = isoDate(day);
    const events = eventsOn(key).filter((e) => !e.allDay);
    const label = day.toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });

    const nodes = events
      .map((ev) => {
        const cal = calendarOf(ev);
        const angle = (timeToMinutes(ev.start) / (24 * 60)) * 360;
        const dist = 38 + (ev.energy === "high" ? 4 : ev.energy === "low" ? -2 : 0);
        return `<button class="orbit-event" data-id="${ev.id}" style="transform: rotate(${angle}deg) translateY(-${dist}%) rotate(${-angle}deg); border-color:${cal?.color || "var(--accent)"}">
          <strong>${escapeHtml(ev.title)}</strong>
          <span>${ev.start}</span>
        </button>`;
      })
      .join("");

    els.viewShell.innerHTML = `
      <div class="orbit-wrap">
        <div class="orbit-ring">
          <div class="orbit-core">
            <div>
              <strong>${label}</strong>
              <p style="color:var(--ink-dim);margin:6px 0 0">${events.length} timed event${events.length === 1 ? "" : "s"} in orbit</p>
            </div>
          </div>
          ${nodes || ""}
        </div>
      </div>`;
    wireEventChips();
  }

  function wireDayCells() {
    els.viewShell.querySelectorAll(".day-cell").forEach((cell) => {
      cell.addEventListener("click", (e) => {
        if (e.target.closest("[data-id]")) return;
        state.cursor = cell.dataset.date;
        openEventModal(null, { date: cell.dataset.date, start: "09:00", end: "10:00" });
      });
    });
  }

  function wireEventChips() {
    els.viewShell.querySelectorAll("[data-id]").forEach((el) => {
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        openEventModal(el.dataset.id);
      });
    });
  }

  function openEventModal(id = null, defaults = {}) {
    editingId = resolveEventId(id);
    const ev = editingId ? state.events.find((e) => e.id === editingId) : null;
    $("#eventModalTitle").textContent = ev ? "Edit event" : "New event";
    $("#deleteEventBtn").classList.toggle("hidden", !ev);

    $("#eventCalendar").innerHTML = state.calendars
      .map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`)
      .join("");

    $("#eventTitle").value = ev?.title || "";
    $("#eventDate").value = ev?.date || defaults.date || state.cursor;
    $("#eventStart").value = ev?.start || defaults.start || "09:00";
    $("#eventEnd").value = ev?.end || defaults.end || "10:00";
    $("#eventCalendar").value = ev?.calendarId || state.calendars[0]?.id;
    $("#eventAllDay").checked = !!ev?.allDay;
    $("#eventEnergy").value = ev?.energy || "medium";
    $("#eventReminder").value = String(ev?.reminder ?? 5);
    $("#eventRepeat").value = ev?.repeat || "none";
    $("#eventLocation").value = ev?.location || "";
    $("#eventNotes").value = ev?.notes || "";
    $("#eventStart").disabled = $("#eventAllDay").checked;
    $("#eventEnd").disabled = $("#eventAllDay").checked;

    els.eventModal.showModal();
    $("#eventTitle").focus();
  }

  function saveEventFromForm(e) {
    e.preventDefault();
    const payload = {
      title: $("#eventTitle").value.trim(),
      date: $("#eventDate").value,
      start: $("#eventAllDay").checked ? "00:00" : $("#eventStart").value,
      end: $("#eventAllDay").checked ? "23:59" : $("#eventEnd").value,
      calendarId: $("#eventCalendar").value,
      allDay: $("#eventAllDay").checked,
      energy: $("#eventEnergy").value,
      reminder: Number($("#eventReminder").value),
      repeat: $("#eventRepeat").value,
      location: $("#eventLocation").value.trim(),
      notes: $("#eventNotes").value.trim(),
    };

    if (!payload.title) return;
    if (!payload.allDay && timeToMinutes(payload.end) <= timeToMinutes(payload.start)) {
      pushToast({ title: "Check times", body: "End time must be after start time." });
      return;
    }

    if (editingId) {
      const idx = state.events.findIndex((ev) => ev.id === editingId);
      if (idx >= 0) state.events[idx] = { ...state.events[idx], ...payload };
    } else {
      state.events.push({ id: uid(), ...payload });
    }

    // Clear fired reminder so edits can notify again
    if (editingId) delete state.firedReminders[editingId];

    save();
    els.eventModal.close();
    render();
    pushToast({ title: "Saved", body: payload.title });
  }

  function deleteEditingEvent() {
    if (!editingId) return;
    if (!confirm("Delete this event?")) return;
    state.events = state.events.filter((e) => e.id !== editingId);
    delete state.firedReminders[editingId];
    delete state.snoozed[editingId];
    save();
    els.eventModal.close();
    render();
  }

  function openThemeModal() {
    fillThemeForm();
    els.themeModal.showModal();
  }

  function fillThemeForm() {
    const s = state.settings;
    $("#accentColor").value = s.accent;
    $("#signalColor").value = s.signal;
    $("#surfaceColor").value = s.surface;
    $("#inkColor").value = s.ink;
    $("#radiusRange").value = s.radius;
    $("#densityRange").value = s.density;
    $("#typeRange").value = s.type;
    $("#motionSelect").value = s.motion;
    $("#displayFont").value = s.displayFont;
    $("#popupStyle").value = s.popupStyle;
    $("#browserNotify").checked = !!s.browserNotify;
    $("#soundAlerts").checked = !!s.soundAlerts;
  }

  function readThemeForm() {
    state.settings = {
      accent: $("#accentColor").value,
      signal: $("#signalColor").value,
      surface: $("#surfaceColor").value,
      ink: $("#inkColor").value,
      radius: Number($("#radiusRange").value),
      density: Number($("#densityRange").value),
      type: Number($("#typeRange").value),
      motion: $("#motionSelect").value,
      displayFont: $("#displayFont").value,
      popupStyle: $("#popupStyle").value,
      browserNotify: $("#browserNotify").checked,
      soundAlerts: $("#soundAlerts").checked,
    };
  }

  function applyTheme() {
    const s = state.settings;
    const root = document.documentElement;
    root.style.setProperty("--accent", s.accent);
    root.style.setProperty("--signal", s.signal);
    root.style.setProperty("--bg-1", s.surface);
    root.style.setProperty("--ink", s.ink);
    root.style.setProperty("--radius", `${s.radius}px`);
    root.style.setProperty("--density", s.density);
    root.style.setProperty("--type", s.type);
    root.style.setProperty("--display", s.displayFont);
    document.body.classList.toggle("motion-off", s.motion === "off");
    document.body.classList.toggle("motion-calm", s.motion === "calm");
  }

  function openCommand() {
    $("#commandInput").value = "";
    commandIndex = 0;
    renderCommandResults("");
    els.commandModal.showModal();
    $("#commandInput").focus();
  }

  function renderCommandResults(query) {
    const q = query.trim().toLowerCase();
    const actions = [
      { label: "New event", run: () => openEventModal() },
      { label: "Go to today", run: () => { state.cursor = isoDate(new Date()); save(); render(); } },
      { label: "View · Month", run: () => setView("month") },
      { label: "View · Week", run: () => setView("week") },
      { label: "View · Day", run: () => setView("day") },
      { label: "View · Agenda", run: () => setView("agenda") },
      { label: "View · Orbit", run: () => setView("orbit") },
      { label: "Open theme forge", run: () => openThemeModal() },
      { label: "Enable browser notifications", run: () => requestNotifyPermission(true) },
    ];

    const eventHits = visibleEvents()
      .filter((e) => !q || e.title.toLowerCase().includes(q) || (e.notes || "").toLowerCase().includes(q))
      .slice(0, 8)
      .map((e) => ({
        label: `${e.title} · ${e.date} ${e.allDay ? "all day" : e.start}`,
        run: () => openEventModal(e.id),
      }));

    const filteredActions = actions.filter((a) => !q || a.label.toLowerCase().includes(q));
    const items = [...filteredActions, ...eventHits];

    const list = $("#commandResults");
    list.innerHTML = items
      .map((item, i) => `<li><button type="button" class="${i === commandIndex ? "active" : ""}" data-i="${i}">${escapeHtml(item.label)}</button></li>`)
      .join("") || `<li style="padding:12px;color:var(--ink-dim)">No matches</li>`;

    list._items = items;
    list.querySelectorAll("button[data-i]").forEach((btn) => {
      btn.addEventListener("click", () => {
        items[Number(btn.dataset.i)].run();
        els.commandModal.close();
      });
    });
  }

  function onCommandKey(e) {
    const list = $("#commandResults");
    const items = list._items || [];
    if (e.key === "ArrowDown") {
      e.preventDefault();
      commandIndex = Math.min(items.length - 1, commandIndex + 1);
      renderCommandResults($("#commandInput").value);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      commandIndex = Math.max(0, commandIndex - 1);
      renderCommandResults($("#commandInput").value);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (items[commandIndex]) {
        items[commandIndex].run();
        els.commandModal.close();
      } else if ($("#commandInput").value.trim()) {
        const parsed = parseNatural($("#commandInput").value.trim());
        if (parsed) {
          state.events.push(parsed);
          save();
          render();
          els.commandModal.close();
          pushToast({ title: "Created from command", body: parsed.title });
        }
      }
    }
  }

  function setView(view) {
    state.view = view;
    document.querySelectorAll(".view-tab").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
    save();
    render();
  }

  function shiftPeriod(dir) {
    const d = parseISO(state.cursor);
    if (state.view === "month") d.setMonth(d.getMonth() + dir);
    else if (state.view === "week" || state.view === "agenda") d.setDate(d.getDate() + dir * 7);
    else d.setDate(d.getDate() + dir);
    state.cursor = isoDate(d);
    save();
    render();
  }

  function checkReminders() {
    const now = Date.now();
    for (const ev of visibleEvents()) {
      if (ev.allDay) continue;
      const startMs = eventStartMs(ev);
      const remindAt = startMs - (Number(ev.reminder) || 0) * 60 * 1000;
      const snoozeUntil = state.snoozed[ev.id] || 0;
      if (now < remindAt || now > startMs + 2 * 60 * 1000) continue;
      if (snoozeUntil && now < snoozeUntil) continue;
      if (state.firedReminders[ev.id] && (!snoozeUntil || state.firedReminders[ev.id] > snoozeUntil)) continue;

      state.firedReminders[ev.id] = now;
      delete state.snoozed[ev.id];
      save();
      fireAlert(ev);
    }
  }

  function fireAlert(ev) {
    const mins = Math.max(0, Math.round(minutesUntil(ev)));
    const body = mins === 0 ? "Starting now" : `Starts in ${mins} minute${mins === 1 ? "" : "s"}`;
    const style = state.settings.popupStyle;

    if (style !== "toast-only") {
      showPulse(ev, body);
    }
    if (style !== "modal") {
      pushToast({ title: ev.title, body: `${body}${ev.location ? " · " + ev.location : ""}`, eventId: ev.id });
    }

    if (state.settings.browserNotify && "Notification" in window && Notification.permission === "granted") {
      try {
        new Notification(`Kairos · ${ev.title}`, { body, silent: !state.settings.soundAlerts });
      } catch (_) {}
    }

    if (state.settings.soundAlerts) playChime();
    renderUrgency();
  }

  function showPulse(ev, meta) {
    els.pulseTitle.textContent = ev.title;
    els.pulseMeta.textContent = `${meta}${ev.location ? " · " + ev.location : ""}`;
    els.pulseOverlay.dataset.eventId = ev.id;
    els.pulseOverlay.classList.remove("hidden");
  }

  function pushToast({ title, body, eventId }) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(body || "")}</p>
      <div class="toast-actions">
        ${eventId ? `<button class="ghost-btn" data-open="${eventId}">Open</button>` : ""}
        <button class="primary-btn" data-close>Dismiss</button>
      </div>`;
    els.toastStack.appendChild(toast);
    toast.querySelector("[data-close]").addEventListener("click", () => toast.remove());
    const openBtn = toast.querySelector("[data-open]");
    if (openBtn) openBtn.addEventListener("click", () => { openEventModal(eventId); toast.remove(); });
    setTimeout(() => toast.remove(), 9000);
  }

  function playChime() {
    try {
      audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.type = "sine";
      o.frequency.setValueAtTime(660, audioCtx.currentTime);
      o.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.12);
      g.gain.value = 0.0001;
      g.gain.exponentialRampToValueAtTime(0.05, audioCtx.currentTime + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.35);
      o.connect(g);
      g.connect(audioCtx.destination);
      o.start();
      o.stop(audioCtx.currentTime + 0.4);
    } catch (_) {}
  }

  function requestNotifyPermission(force) {
    if (!("Notification" in window)) return;
    if (Notification.permission === "granted") {
      if (force) pushToast({ title: "Notifications on", body: "Browser alerts are enabled." });
      return;
    }
    if (Notification.permission !== "denied") {
      Notification.requestPermission().then((perm) => {
        if (force) pushToast({ title: perm === "granted" ? "Notifications enabled" : "Permission blocked", body: perm === "granted" ? "You’ll get desktop popups for reminders." : "Enable them in browser settings." });
      });
    }
  }

  /* ---------- Natural language ---------- */
  function parseNatural(text) {
    let working = text.trim();
    let date = parseISO(state.cursor);
    let durationMin = 60;
    let start = "09:00";

    if (/tomorrow/i.test(working)) {
      date = addDays(new Date(), 1);
      working = working.replace(/tomorrow/i, "").trim();
    } else if (/today/i.test(working)) {
      date = new Date();
      working = working.replace(/today/i, "").trim();
    } else {
      const md = working.match(/\b(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?\b/);
      if (md) {
        const year = md[3] ? (md[3].length === 2 ? 2000 + Number(md[3]) : Number(md[3])) : new Date().getFullYear();
        date = new Date(year, Number(md[1]) - 1, Number(md[2]));
        working = working.replace(md[0], "").trim();
      }
    }

    const dur = working.match(/\b(\d+)\s*(h|hr|hrs|hour|hours|m|min|mins|minutes)\b/i);
    if (dur) {
      durationMin = /h/i.test(dur[2]) ? Number(dur[1]) * 60 : Number(dur[1]);
      working = working.replace(dur[0], "").trim();
    }

    const time = working.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b/i);
    if (time) {
      let h = Number(time[1]);
      const m = Number(time[2] || 0);
      const ap = (time[3] || "").toLowerCase();
      if (ap === "pm" && h < 12) h += 12;
      if (ap === "am" && h === 12) h = 0;
      if (!ap && h < 8) h += 12; // assume afternoon for bare small hours in casual capture
      start = `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
      working = working.replace(time[0], "").trim();
    }

    const title = working.replace(/\s{2,}/g, " ").replace(/^[-–—]+|[-–—]+$/g, "").trim();
    if (!title) return null;

    const end = minutesToTime(Math.min(24 * 60 - 1, timeToMinutes(start) + durationMin));
    return {
      id: uid(),
      title,
      date: isoDate(date),
      start,
      end,
      calendarId: state.calendars[0]?.id || "work",
      allDay: false,
      energy: "medium",
      reminder: 5,
      repeat: "none",
      location: "",
      notes: "Added via quick capture",
    };
  }

  /* ---------- Data helpers ---------- */
  function visibleEvents() {
    const visible = new Set(state.calendars.filter((c) => c.visible).map((c) => c.id));
    return expandRepeats(state.events.filter((e) => visible.has(e.calendarId)));
  }

  function expandRepeats(events) {
    const out = [];
    const horizonStart = addDays(new Date(), -7);
    const horizonEnd = addDays(new Date(), 60);

    for (const ev of events) {
      if (!ev.repeat || ev.repeat === "none") {
        out.push(ev);
        continue;
      }
      let cursor = parseISO(ev.date);
      let guard = 0;
      while (cursor <= horizonEnd && guard < 400) {
        if (cursor >= horizonStart) {
          out.push({
            ...ev,
            date: isoDate(cursor),
            id: `${ev.id}:${isoDate(cursor)}`,
            _sourceId: ev.id,
          });
        }
        if (ev.repeat === "daily") cursor = addDays(cursor, 1);
        else if (ev.repeat === "weekly") cursor = addDays(cursor, 7);
        else if (ev.repeat === "monthly") {
          cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, cursor.getDate());
        } else break;
        guard++;
      }
    }
    return out;
  }

  function resolveEventId(id) {
    if (!id) return null;
    if (state.events.some((e) => e.id === id)) return id;
    const source = String(id).split(":")[0];
    return state.events.some((e) => e.id === source) ? source : null;
  }

  function eventsOn(dateKey) {
    return visibleEvents()
      .filter((e) => e.date === dateKey)
      .sort((a, b) => timeToMinutes(a.start) - timeToMinutes(b.start));
  }

  function upcomingEvents(limit = 5) {
    const now = Date.now();
    return visibleEvents()
      .map((e) => ({ e, t: eventStartMs(e) }))
      .filter(({ t }) => t >= now - 5 * 60 * 1000)
      .sort((a, b) => a.t - b.t)
      .slice(0, limit)
      .map(({ e }) => e);
  }

  function findConflicts() {
    const byDate = {};
    for (const ev of visibleEvents()) {
      if (ev.allDay) continue;
      (byDate[ev.date] ||= []).push(ev);
    }
    const conflicts = [];
    for (const [date, list] of Object.entries(byDate)) {
      const sorted = [...list].sort((a, b) => timeToMinutes(a.start) - timeToMinutes(b.start));
      for (let i = 0; i < sorted.length; i++) {
        for (let j = i + 1; j < sorted.length; j++) {
          const a = sorted[i];
          const b = sorted[j];
          if (timeToMinutes(b.start) < timeToMinutes(a.end)) {
            conflicts.push({ date, a, b });
          } else break;
        }
      }
    }
    return conflicts;
  }

  function calendarOf(ev) {
    return state.calendars.find((c) => c.id === ev.calendarId);
  }

  function eventStartMs(ev) {
    const [h, m] = (ev.start || "00:00").split(":").map(Number);
    const d = parseISO(ev.date);
    d.setHours(h, m, 0, 0);
    return d.getTime();
  }

  function minutesUntil(ev) {
    return (eventStartMs(ev) - Date.now()) / 60000;
  }

  function countdownLabel(ev) {
    const mins = minutesUntil(ev);
    if (mins < -30) return "done";
    if (mins < 0) return "now";
    if (mins < 60) return `${Math.round(mins)}m`;
    if (mins < 60 * 24) return `${Math.round(mins / 60)}h`;
    return `${Math.round(mins / (60 * 24))}d`;
  }

  function formatWhen(ev) {
    const d = parseISO(ev.date);
    const day = d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
    return ev.allDay ? `${day} · all day` : `${day} · ${ev.start}`;
  }

  function exportData() {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `kairos-backup-${isoDate(new Date())}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  function importData(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result);
        if (!data.events || !data.calendars) throw new Error("Invalid file");
        state = { ...defaultState(), ...data };
        applyTheme();
        save();
        render();
        pushToast({ title: "Import complete", body: `${state.events.length} events loaded.` });
      } catch (err) {
        pushToast({ title: "Import failed", body: "That file doesn’t look like a Kairos backup." });
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  }

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      const parsed = JSON.parse(raw);
      return {
        ...defaultState(),
        ...parsed,
        settings: { ...PRESETS.observatory, ...(parsed.settings || {}) },
        firedReminders: parsed.firedReminders || {},
        snoozed: parsed.snoozed || {},
      };
    } catch {
      return defaultState();
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function tickClock() {
    const now = new Date();
    els.liveClock.textContent = now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  /* ---------- utils ---------- */
  function $(sel) {
    return document.querySelector(sel);
  }

  function uid() {
    return `ev_${Math.random().toString(36).slice(2, 10)}${Date.now().toString(36).slice(-4)}`;
  }

  function isoDate(d) {
    const x = new Date(d);
    return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`;
  }

  function parseISO(s) {
    const [y, m, d] = s.split("-").map(Number);
    return new Date(y, m - 1, d);
  }

  function addDays(d, n) {
    const x = new Date(d);
    x.setDate(x.getDate() + n);
    return x;
  }

  function startOfWeek(d) {
    const x = new Date(d);
    x.setDate(x.getDate() - x.getDay());
    x.setHours(0, 0, 0, 0);
    return x;
  }

  function timeToMinutes(t) {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
  }

  function minutesToTime(mins) {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
  }

  function nearTime(hoursFromNow) {
    const d = new Date(Date.now() + hoursFromNow * 3600 * 1000);
    d.setMinutes(Math.round(d.getMinutes() / 15) * 15, 0, 0);
    return minutesToTime(d.getHours() * 60 + d.getMinutes());
  }

  function fmtMonthDay(d) {
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
