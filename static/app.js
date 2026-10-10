document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const moodCards = document.querySelectorAll(".mood-card");
  const form = document.getElementById("adventure-form");
  const inputActivity = document.getElementById("input-activity");
  const timePills = document.querySelectorAll(".time-pill");
  const timeValDisplay = document.getElementById("time-val-display");
  const energyOptions = document.querySelectorAll(".energy-option");
  const inputSetting = document.getElementById("input-setting");
  const inputNote = document.getElementById("input-note");

  // State Elements
  const statePlaceholder = document.getElementById("state-placeholder");
  const stateLoading = document.getElementById("state-loading");
  const stateResult = document.getElementById("state-result");
  const stateError = document.getElementById("state-error");
  const errorMessageText = document.getElementById("error-message-text");
  const btnRetry = document.getElementById("btn-retry");
  const loadingStepText = document.getElementById("loading-step-text");

  // Status Indicator
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");

  // Audio Controls
  const btnPlayAudio = document.getElementById("btn-play-audio");
  const btnStopAudio = document.getElementById("btn-stop-audio");
  const audioPlayer = document.getElementById("audio-player");
  const audioStatusText = document.getElementById("audio-status-text");

  // Modal Elements
  const btnTraceModal = document.getElementById("btn-trace-modal");
  const modalTraces = document.getElementById("modal-traces");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnCloseModal2 = document.getElementById("btn-close-modal-2");
  const traceList = document.getElementById("trace-list");

  let currentAudioData = null;

  // 1. Initial Status Check (/api/status)
  checkSystemStatus();

  async function checkSystemStatus() {
    try {
      const resp = await fetch("/api/status");
      const data = await resp.json();
      if (data.ai_configured) {
        statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block";
        statusText.textContent = `HF AI Active (${data.model_name})`;
      } else {
        statusDot.className = "w-2.5 h-2.5 rounded-full bg-amber-500 inline-block";
        statusText.textContent = "Demo Mode (HF_TOKEN needed for live AI)";
      }
    } catch (e) {
      statusDot.className = "w-2.5 h-2.5 rounded-full bg-slate-400 inline-block";
      statusText.textContent = "Backend Active";
    }
  }

  // 2. Mood Cards Interactivity
  moodCards.forEach((card) => {
    card.addEventListener("click", () => {
      moodCards.forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");

      const activity = card.dataset.activity;
      const setting = card.dataset.setting;

      if (activity && inputActivity) {
        inputActivity.value = activity;
      }
      if (setting && inputSetting) {
        inputSetting.value = setting;
      }

      // Smooth scroll to planner form
      const plannerSection = document.getElementById("planner-section");
      if (plannerSection) {
        plannerSection.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  // 3. Time Pill Selection
  timePills.forEach((pill) => {
    pill.addEventListener("click", () => {
      timePills.forEach((p) => {
        p.classList.remove("bg-forest/10", "border-forest", "text-forest");
        p.classList.add("border-forest/20", "text-slate-700");
      });
      pill.classList.remove("border-forest/20", "text-slate-700");
      pill.classList.add("bg-forest/10", "border-forest", "text-forest");

      const radio = pill.querySelector('input[type="radio"]');
      if (radio) {
        radio.checked = true;
        timeValDisplay.textContent = `${radio.value} Minutes`;
      }
    });
  });

  // 4. Energy Level Options Selection
  energyOptions.forEach((label) => {
    label.addEventListener("click", () => {
      energyOptions.forEach((l) => {
        l.classList.remove("bg-forest/10", "border-forest", "text-forest");
        l.classList.add("border-forest/20", "text-slate-700");
      });
      label.classList.remove("border-forest/20", "text-slate-700");
      label.classList.add("bg-forest/10", "border-forest", "text-forest");
    });
  });

  // 5. Form Submit Handler
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      executePlanGenerator();
    });
  }

  if (btnRetry) {
    btnRetry.addEventListener("click", () => {
      executePlanGenerator();
    });
  }

  async function executePlanGenerator() {
    stopAllAudio();

    const activity = inputActivity.value;
    const timeRadio = document.querySelector('input[name="time"]:checked');
    const available_time_min = timeRadio ? parseInt(timeRadio.value) : 30;
    const energyRadio = document.querySelector('input[name="energy"]:checked');
    const energy_level = energyRadio ? energyRadio.value : "Medium";
    const setting = inputSetting.value;
    const note = inputNote ? inputNote.value.trim() : "";

    const interests = [];
    document.querySelectorAll('input[name="interest"]:checked').forEach((cb) => {
      interests.push(cb.value);
    });

    // UI Loading State
    statePlaceholder.classList.add("hidden");
    stateResult.classList.add("hidden");
    stateError.classList.add("hidden");
    stateLoading.classList.remove("hidden");

    loadingStepText.textContent = "Connecting to AI trail buddy & calculating TabPFN metrics...";

    try {
      const resp = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          activity: activity,
          available_time_min: available_time_min,
          energy_level: energy_level,
          setting: setting,
          interests: interests,
          optional_note: note || null
        })
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
      }

      const data = await resp.json();
      renderAdventurePlan(data);

    } catch (err) {
      console.error(err);
      stateLoading.classList.add("hidden");
      stateError.classList.remove("hidden");
      errorMessageText.textContent = err.message || "An unexpected error occurred.";
    }
  }

  // 6. Render Journal Entry Result
  function renderAdventurePlan(data) {
    stateLoading.classList.add("hidden");
    stateResult.classList.remove("hidden");

    const plan = data.plan || {};
    const tabpfn = data.tabpfn_analytics || {};
    const audio = data.audio_briefing || {};

    currentAudioData = audio;

    // AI vs Demo Attribution Badge
    const badgeAttr = document.getElementById("badge-attribution");
    if (data.is_ai_generated) {
      badgeAttr.className = "text-xs font-bold px-3.5 py-1 rounded-full flex items-center gap-1.5 bg-forest/10 text-forest border border-forest/20";
      badgeAttr.innerHTML = `<i data-lucide="sparkles" class="w-3.5 h-3.5"></i> <span>${data.attribution || "Generated by Open-Weight AI"}</span>`;
    } else {
      badgeAttr.className = "text-xs font-bold px-3.5 py-1 rounded-full flex items-center gap-1.5 bg-amber-100 text-amber-900 border border-amber-200";
      badgeAttr.innerHTML = `<i data-lucide="info" class="w-3.5 h-3.5"></i> <span>${data.attribution || "Demo plan — AI inference unavailable"}</span>`;
    }

    // TabPFN Badge
    document.getElementById("badge-tabpfn").textContent = `TabPFN Feasibility: ${tabpfn.suitability_score || 94}% (${tabpfn.recommended_pace || 'Optimal Pace'})`;

    // Title & Description
    document.getElementById("plan-title").textContent = plan.title || "Your Outdoor Adventure";
    document.getElementById("plan-description").textContent = plan.description || "";
    document.getElementById("plan-total-duration").textContent = `Total: ${plan.total_duration_min || 30} Mins`;

    // Timeline Steps
    const stepsContainer = document.getElementById("plan-steps");
    stepsContainer.innerHTML = "";
    (plan.steps || []).forEach((step, idx) => {
      const div = document.createElement("div");
      div.className = "relative pl-6";
      div.innerHTML = `
        <div class="absolute -left-[25px] top-0 w-6 h-6 rounded-full bg-forest text-paper font-bold text-xs flex items-center justify-center shadow-sm">
          ${step.step_number || idx + 1}
        </div>
        <div class="flex items-center justify-between mb-1">
          <h4 class="font-bold text-sm text-forest">${step.title}</h4>
          <span class="text-[11px] font-semibold text-forest bg-forest/10 px-2.5 py-0.5 rounded-full border border-forest/10">${step.duration_min} mins</span>
        </div>
        <p class="text-xs text-slate-600 leading-relaxed">${step.description}</p>
      `;
      stepsContainer.appendChild(div);
    });

    // Items to Bring
    const itemsList = document.getElementById("plan-items");
    itemsList.innerHTML = "";
    (plan.items_to_bring || []).forEach((item) => {
      const li = document.createElement("li");
      li.className = "flex items-center gap-2";
      li.innerHTML = `<input type="checkbox" class="accent-forest rounded cursor-pointer" /> <span>${item}</span>`;
      itemsList.appendChild(li);
    });

    // Safety Tips
    const tipsList = document.getElementById("plan-tips");
    tipsList.innerHTML = "";
    (plan.safety_tips || []).forEach((tip) => {
      const li = document.createElement("li");
      li.className = "flex items-start gap-2";
      li.innerHTML = `<span class="text-forest">•</span> <span>${tip}</span>`;
      tipsList.appendChild(li);
    });

    // Phone Free Challenge
    const challenge = plan.phone_free_challenge || {};
    document.getElementById("challenge-name").textContent = challenge.name || "Offline Challenge";
    document.getElementById("challenge-instructions").textContent = challenge.instructions || "";
    document.getElementById("challenge-phone-rule").textContent = challenge.phone_rule || "Put your phone in Do Not Disturb mode!";

    // Reflection Question
    document.getElementById("plan-reflection").textContent = `"${plan.reflection_question || 'What is one small natural detail you noticed today?'}"`;

    // Re-initialize Lucide Icons
    if (window.lucide) window.lucide.createIcons();
  }

  // 7. AUDIO PLAY & STOP CONTROLS
  if (btnPlayAudio) {
    btnPlayAudio.addEventListener("click", () => {
      if (!currentAudioData) return;

      stopAllAudio(); // Clear previous audio playback first

      if (currentAudioData.has_audio && currentAudioData.audio_base64) {
        audioPlayer.src = `data:${currentAudioData.mime_type};base64,${currentAudioData.audio_base64}`;
        audioPlayer.play();
        audioStatusText.textContent = "🔊 Playing ElevenLabs Audio Briefing...";
      } else if (currentAudioData.script && 'speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(currentAudioData.script);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.onend = () => {
          audioStatusText.textContent = "Audio Briefing Finished.";
        };
        window.speechSynthesis.speak(utterance);
        audioStatusText.textContent = "🔊 Speaking Guide via Neural Voice...";
      } else {
        alert("Audio Script: " + (currentAudioData.script || "Enjoy your adventure!"));
      }
    });
  }

  // STOP AUDIO BUTTON
  if (btnStopAudio) {
    btnStopAudio.addEventListener("click", () => {
      stopAllAudio();
      audioStatusText.textContent = "⏹️ Audio Stopped.";
    });
  }

  function stopAllAudio() {
    if (audioPlayer) {
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  // 8. Sentry Trace Modal
  if (btnTraceModal) {
    btnTraceModal.addEventListener("click", async () => {
      modalTraces.classList.remove("hidden");
      traceList.innerHTML = "<p class='text-slate-400 text-xs'>Fetching real-time Sentry agent traces...</p>";

      try {
        const resp = await fetch("/api/traces");
        const data = await resp.json();
        
        traceList.innerHTML = "";
        if (!data.traces || data.traces.length === 0) {
          traceList.innerHTML = "<p class='text-slate-400 text-xs'>No traces recorded yet. Run an adventure search first!</p>";
          return;
        }

        data.traces.forEach((trace) => {
          const div = document.createElement("div");
          div.className = "p-3 bg-slate-900 text-slate-100 rounded-xl border border-slate-700 space-y-1 font-mono";
          div.innerHTML = `
            <div class="flex items-center justify-between text-xs">
              <span class="text-sage font-bold">[${trace.op}] ${trace.span_name}</span>
              <span class="text-butter">${trace.duration_ms} ms</span>
            </div>
            <p class="text-[11px] text-slate-400">${trace.description}</p>
            <div class="text-[10px] text-slate-500 pt-1 border-t border-slate-800 flex justify-between">
              <span>Status: ${trace.status}</span>
              <span>${trace.timestamp}</span>
            </div>
          `;
          traceList.appendChild(div);
        });
      } catch (err) {
        traceList.innerHTML = "<p class='text-rose-400 text-xs'>Failed to fetch Sentry traces.</p>";
      }
    });
  }

  if (btnCloseModal) btnCloseModal.addEventListener("click", () => modalTraces.classList.add("hidden"));
  if (btnCloseModal2) btnCloseModal2.addEventListener("click", () => modalTraces.classList.add("hidden"));
});
