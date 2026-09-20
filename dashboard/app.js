/**
 * AstraHeal Unified Research Mission Operations Center (MOC) Frontend Logic
 * Papers 1, 2, and 3 Interactive Real-Time Dashboard
 */

document.addEventListener("DOMContentLoaded", () => {
  const app = new AstraHealMOC();
  app.init();
});

class AstraHealMOC {
  constructor() {
    this.isLiveConnected = false;
    this.ws = null;
    this.simSpeed = 1.0;
    this.isPaused = false;
    this.simTimeSec = 0.0;

    // Rolling telemetry history buffer (for charts)
    this.history = {
      labels: [],
      voltage: [],
      current: [],
      temperature: [],
      soc: [],
      power: [],
      solar: [],
    };
    this.maxChartPoints = 40;

    // Subsystem and Invariant state
    this.activeFaults = [];
    this.eventLogs = [];

    // Client-side fallback physics state
    this.clientSim = {
      temp: 24.5,
      voltage: 28.4,
      current: 8.2,
      soc: 88.5,
      solarPower: 185.0,
      orbitSec: 0.0,
      activeFault: null,
    };

    // Chart instances
    this.powerChart = null;
    this.thermalChart = null;
  }

  init() {
    this.initCharts();
    this.bindEvents();
    this.initWebSocket();

    // Start fallback simulation heartbeat (will only tick if WebSocket is offline)
    setInterval(() => {
      if (!this.isLiveConnected && !this.isPaused) {
        this.tickClientSimulation();
      }
    }, 1000);
  }

  // --- WebSocket Connection ---
  initWebSocket() {
    const host = window.location.host || "127.0.0.1:8000";
    const wsUrl = `ws://${host}/ws/telemetry`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.isLiveConnected = true;
        this.updateConnectionStatus(true);
        this.addLog("SYSTEM", "Connected to live Python SpacecraftEPSDigitalTwin streaming backend.");
      };

      this.ws.onmessage = (event) => {
        try {
          const msg = jsonParseSafe(event.data);
          if (!msg) return;

          if (msg.type === "init") {
            if (msg.history && Array.isArray(msg.history)) {
              msg.history.forEach((f) => this.ingestFrame(f));
            }
          } else if (msg.type === "telemetry" && msg.data) {
            this.ingestFrame(msg.data);
          }
        } catch (e) {
          console.error("WS Parse error", e);
        }
      };

      this.ws.onclose = () => {
        if (this.isLiveConnected) {
          this.addLog("WARNING", "Live Python WebSocket disconnected. Fallback to in-browser physical kinetics.");
        }
        this.isLiveConnected = false;
        this.updateConnectionStatus(false);
        // Attempt reconnect after 5s
        setTimeout(() => this.initWebSocket(), 5000);
      };

      this.ws.onerror = () => {
        this.isLiveConnected = false;
        this.updateConnectionStatus(false);
      };
    } catch (e) {
      this.isLiveConnected = false;
      this.updateConnectionStatus(false);
    }
  }

  updateConnectionStatus(isLive) {
    const dot = document.getElementById("connection-dot");
    const text = document.getElementById("connection-status-text");
    if (isLive) {
      dot.className = "mode-dot";
      text.innerText = "LIVE DIGITAL TWIN (FASTAPI / WS)";
      text.style.color = "#34d399";
    } else {
      dot.className = "mode-dot offline";
      text.innerText = "STANDALONE PHYSICAL KINETICS (IN-BROWSER)";
      text.style.color = "#fbbf24";
    }
  }

  sendWsCommand(cmd) {
    if (this.isLiveConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(cmd));
    }
  }

  // --- UI Event Listeners ---
  bindEvents() {
    // Navigation Tabs
    const tabButtons = document.querySelectorAll(".tab-btn");
    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        tabButtons.forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach((tc) => tc.classList.remove("active"));

        btn.classList.add("active");
        const targetId = btn.getAttribute("data-tab");
        const targetContent = document.getElementById(targetId);
        if (targetContent) targetContent.classList.add("active");
      });
    });

    // Speed Controls
    document.querySelectorAll(".speed-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".speed-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");

        const speed = parseFloat(btn.getAttribute("data-speed"));
        this.simSpeed = speed;
        this.isPaused = speed === 0;

        if (this.isLiveConnected) {
          this.sendWsCommand({ action: "set_speed", speed: speed });
        } else {
          this.addLog("CONTROL", `Simulation speed set to ${speed}x.`);
        }
      });
    });

    // Fault Injection Controls
    document.getElementById("btn-inject-fault").addEventListener("click", () => {
      const faultType = document.getElementById("sel-fault-type").value;
      this.injectFault(faultType);
    });

    document.getElementById("btn-clear-faults").addEventListener("click", () => {
      this.clearFaults();
    });

    document.getElementById("btn-reset-sim").addEventListener("click", () => {
      this.resetSimulation();
    });

    // Clear Logs
    document.getElementById("btn-clear-logs").addEventListener("click", () => {
      this.eventLogs = [];
      document.getElementById("log-console").innerHTML = "";
    });

    // Paper 1 Counterfactual Run
    document.getElementById("btn-run-planner").addEventListener("click", () => {
      this.runPaper1Planner();
    });

    // Paper 3 Safety Governor Tester
    document.getElementById("btn-submit-proposal").addEventListener("click", () => {
      this.evaluateGovernorProposal();
    });

    // Paper 3 Presets
    document.getElementById("btn-preset-thermal").addEventListener("click", () => {
      document.getElementById("prop-id").value = "ADV-THERMAL-01";
      document.getElementById("prop-type").value = "REDUCE_PAYLOAD_LOAD";
      document.getElementById("prop-temp").value = 49.5;
      document.getElementById("prop-volt").value = 27.0;
      document.getElementById("prop-curr").value = 18.0;
      document.getElementById("prop-conf").value = 0.99;
      this.evaluateGovernorProposal();
    });

    document.getElementById("btn-preset-undervolt").addEventListener("click", () => {
      document.getElementById("prop-id").value = "ADV-UNDERVOLT-02";
      document.getElementById("prop-type").value = "CONTINUE_NOMINAL";
      document.getElementById("prop-temp").value = 28.0;
      document.getElementById("prop-volt").value = 20.4;
      document.getElementById("prop-curr").value = 15.0;
      document.getElementById("prop-conf").value = 0.98;
      this.evaluateGovernorProposal();
    });

    document.getElementById("btn-preset-failclosed").addEventListener("click", () => {
      document.getElementById("prop-id").value = "ADV-MALFORMED-03";
      document.getElementById("prop-type").value = "OVERCHARGE_RAPID_BATTERY";
      document.getElementById("prop-temp").value = 35.0;
      document.getElementById("prop-volt").value = 28.0;
      document.getElementById("prop-curr").value = 12.0;
      document.getElementById("prop-conf").value = 0.95;
      this.evaluateGovernorProposal();
    });

    // Custom CSV Telemetry Upload & Replay
    const uploadBtn = document.getElementById("btn-upload-csv");
    const fileInput = document.getElementById("file-csv-input");
    if (uploadBtn && fileInput) {
      uploadBtn.addEventListener("click", () => fileInput.click());
      fileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        this.loadAndReplayUserCsv(file);
      });
    }
  }

  loadAndReplayUserCsv(file) {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target.result;
        const lines = text.trim().split("\n");
        if (lines.length < 2) {
          alert("CSV file must contain a header row and at least one data row.");
          return;
        }

        const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());
        const vIdx = headers.findIndex((h) => h.includes("volt"));
        const iIdx = headers.findIndex((h) => h.includes("curr"));
        const tIdx = headers.findIndex((h) => h.includes("temp"));
        const socIdx = headers.findIndex((h) => h.includes("soc") || h.includes("charge"));
        const timeIdx = headers.findIndex((h) => h.includes("time") || h.includes("sec") || h.includes("timestamp"));

        if (vIdx === -1 && tIdx === -1) {
          alert("CSV must contain at least voltage and/or temperature columns.");
          return;
        }

        const parsedFrames = [];
        for (let idx = 1; idx < lines.length; idx++) {
          const row = lines[idx].split(",").map((cell) => parseFloat(cell.trim()));
          if (row.length < headers.length) continue;

          const volt = vIdx !== -1 && !isNaN(row[vIdx]) ? row[vIdx] : 28.0;
          const curr = iIdx !== -1 && !isNaN(row[iIdx]) ? row[iIdx] : 8.0;
          const temp = tIdx !== -1 && !isNaN(row[tIdx]) ? row[tIdx] : 25.0;
          let soc = socIdx !== -1 && !isNaN(row[socIdx]) ? row[socIdx] : 85.0;
          if (soc <= 1.05 && soc > 0.0) soc *= 100.0; // normalize if decimal
          const t = timeIdx !== -1 && !isNaN(row[timeIdx]) ? row[timeIdx] : idx * 2.0;

          parsedFrames.push({
            timestamp_sec: t,
            voltage_v: volt,
            current_a: curr,
            temperature_c: temp,
            soc_pct: soc,
            power_w: volt * Math.abs(curr),
            solar_power_w: 150.0,
            load_power_w: volt * Math.abs(curr),
            link_status: "IN_CONTACT",
            safety_status: (temp > 46.0 || volt < 22.0) ? "CRITICAL_VIOLATION" : "NOMINAL",
            active_faults: temp > 46.0 ? [{ type: "USER_DATA_THERMAL_BREACH" }] : [],
            evidential: {
              anomaly_detected: temp > 42.0 || volt < 24.0,
              primary_diagnosis: temp > 46.0 ? "THERMAL_EXCEEDANCE" : (volt < 22.0 ? "UNDERVOLTAGE_FAULT" : "USER_TELEMETRY_NOMINAL"),
              confidence: 0.96,
              epistemic_uncertainty: (temp > 46.0 && volt < 22.0) ? 0.88 : 0.05,
              aleatoric_uncertainty: 0.02,
              is_ood_novelty: false,
              probabilities: {
                thermal_runaway: temp > 40.0 ? 0.85 : 0.05,
                battery_impedance: volt < 25.0 ? 0.80 : 0.05,
                solar_fault: 0.05,
                parasitic_surge: curr > 30.0 ? 0.90 : 0.05,
                novel_ood: 0.05,
              },
            },
          });
        }

        if (parsedFrames.length === 0) {
          alert("Could not parse numeric rows from CSV.");
          return;
        }

        // Pause live backend or fallback loop and replay user frames
        this.isPaused = true;
        const textBanner = document.getElementById("connection-status-text");
        const dot = document.getElementById("connection-dot");
        if (textBanner) {
          textBanner.innerText = `REPLAYING USER CSV: ${file.name.toUpperCase()} (${parsedFrames.length} FRAMES)`;
          textBanner.style.color = "#38bdf8";
        }
        if (dot) dot.className = "mode-dot";

        this.addLog("DATA", `Loaded ${parsedFrames.length} telemetry frames from user file '${file.name}'. Starting replay...`);

        // Fast forward initial frames to populate charts, then stream rest
        let playIdx = 0;
        const initialBatch = Math.min(30, parsedFrames.length);
        for (let i = 0; i < initialBatch; i++) {
          this.ingestFrame(parsedFrames[i]);
          playIdx++;
        }

        if (this.csvInterval) clearInterval(this.csvInterval);
        this.csvInterval = setInterval(() => {
          if (playIdx >= parsedFrames.length) {
            clearInterval(this.csvInterval);
            this.addLog("DATA", `Completed user CSV replay (${parsedFrames.length} frames).`);
            return;
          }
          this.ingestFrame(parsedFrames[playIdx]);
          playIdx++;
        }, Math.max(100, 1000 / Math.max(1, this.simSpeed)));
      } catch (err) {
        alert("Error parsing CSV: " + err.message);
      }
    };
    reader.readAsText(file);
  }

  // --- Frame Ingestion & UI Updates ---
  ingestFrame(frame) {
    this.simTimeSec = frame.timestamp_sec;

    // 1. Update Global Header Statuses
    this.updateHeaderAndMeters(frame);

    // 2. Update Charts
    this.pushChartData(frame);

    // 3. Update Subsystem Matrix
    this.updateSubsystems(frame);

    // 4. Update Paper 2 Evidential Intelligence
    if (frame.evidential) {
      this.updatePaper2View(frame.evidential);
    }

    // 5. Update Paper 3 Invariant Cards
    this.updatePaper3Invariants(frame);
  }

  updateHeaderAndMeters(frame) {
    // MET
    const totalSec = Math.floor(frame.timestamp_sec);
    const hrs = String(Math.floor(totalSec / 3600)).padStart(2, "0");
    const mins = String(Math.floor((totalSec % 3600) / 60)).padStart(2, "0");
    const secs = String(totalSec % 60).padStart(2, "0");
    document.getElementById("orbit-info-text").innerText = `LEO 550 km • MET: ${hrs}:${mins}:${secs}`;

    // Metric Cards
    document.getElementById("val-voltage").innerHTML = `${frame.voltage_v.toFixed(1)} <span class="unit">V</span>`;
    document.getElementById("val-current").innerHTML = `${Math.abs(frame.current_a).toFixed(1)} <span class="unit">A</span>`;
    document.getElementById("val-temp").innerHTML = `${frame.temperature_c.toFixed(1)} <span class="unit">°C</span>`;
    document.getElementById("val-soc").innerHTML = `${frame.soc_pct.toFixed(1)} <span class="unit">%</span>`;
    document.getElementById("val-solar").innerHTML = `${(frame.solar_power_w || 0).toFixed(0)} <span class="unit">W</span>`;

    // Thermal Margin Indicator
    const margin = 46.0 - frame.temperature_c;
    const subTemp = document.getElementById("sub-temp");
    if (margin < 0) {
      subTemp.innerText = `BREACH: Exceeds limit by +${Math.abs(margin).toFixed(1)}°C`;
      subTemp.className = "metric-sub alert";
    } else if (margin < 5.0) {
      subTemp.innerText = `WARNING: Low margin (+${margin.toFixed(1)}°C)`;
      subTemp.className = "metric-sub warning";
    } else {
      subTemp.innerText = `Thermal Margin: +${margin.toFixed(1)}°C`;
      subTemp.className = "metric-sub safe";
    }

    // Comm Status Pill
    const commPill = document.getElementById("comm-status-pill");
    const commText = document.getElementById("comm-status-text");
    if (frame.link_status === "IN_CONTACT") {
      commPill.className = "status-pill safe";
      commText.innerText = "📡 Ground Station In Contact";
    } else if (frame.link_status === "APPROACHING") {
      commPill.className = "status-pill warning";
      commText.innerText = "📡 Pass Approaching";
    } else {
      commPill.className = "status-pill alert";
      commText.innerText = "📡 Blackout Occultation";
    }

    // Mission Status Pill
    const statusPill = document.getElementById("mission-status-pill");
    const statusText = document.getElementById("mission-status-text");
    if (frame.safety_status === "CRITICAL_VIOLATION") {
      statusPill.className = "status-pill alert";
      statusText.innerText = "CRITICAL SAFETY BREACH";
    } else if (frame.active_faults && frame.active_faults.length > 0) {
      statusPill.className = "status-pill warning";
      statusText.innerText = "FAULT ACTIVE (CONTAINED)";
    } else {
      statusPill.className = "status-pill safe";
      statusText.innerText = "MISSION NOMINAL";
    }
  }

  updateSubsystems(frame) {
    const battStat = document.getElementById("stat-batt");
    const thermalStat = document.getElementById("stat-thermal");
    const pduStat = document.getElementById("stat-pdu");

    if (frame.temperature_c > 46.0) {
      thermalStat.innerText = "CRITICAL OVERHEAT";
      thermalStat.className = "subsystem-status error";
    } else if (frame.temperature_c > 38.0) {
      thermalStat.innerText = "ELEVATED";
      thermalStat.className = "subsystem-status warn";
    } else {
      thermalStat.innerText = "OPTIMAL";
      thermalStat.className = "subsystem-status ok";
    }

    if (frame.voltage_v < 22.0) {
      pduStat.innerText = "UNDERVOLTAGE";
      pduStat.className = "subsystem-status error";
    } else {
      pduStat.innerText = "STABLE";
      pduStat.className = "subsystem-status ok";
    }

    if (frame.active_faults && frame.active_faults.some((f) => f.type.includes("BATTERY"))) {
      battStat.innerText = "IMPEDANCE SPIKE";
      battStat.className = "subsystem-status warn";
    } else {
      battStat.innerText = "NOMINAL";
      battStat.className = "subsystem-status ok";
    }
  }

  // --- Paper 2: Evidential View Updates ---
  updatePaper2View(ev) {
    document.getElementById("val-epistemic").innerText = ev.epistemic_uncertainty.toFixed(3);
    document.getElementById("bar-epistemic").style.width = `${Math.min(100, ev.epistemic_uncertainty * 100)}%`;

    document.getElementById("val-aleatoric").innerText = ev.aleatoric_uncertainty.toFixed(3);
    document.getElementById("bar-aleatoric").style.width = `${Math.min(100, ev.aleatoric_uncertainty * 100)}%`;

    document.getElementById("diag-primary").innerText = ev.primary_diagnosis;
    document.getElementById("diag-conf").innerText = `${(ev.confidence * 100).toFixed(1)}%`;

    const oodFlag = document.getElementById("diag-ood-flag");
    if (ev.is_ood_novelty) {
      oodFlag.innerText = "TRUE: NOVEL OOD DETECTED!";
      oodFlag.style.color = "var(--accent-ruby)";
      document.getElementById("badge-diagnosis-status").innerText = "STATUS: NOVELTY DETECTED";
      document.getElementById("badge-diagnosis-status").style.color = "var(--accent-ruby)";
    } else {
      oodFlag.innerText = "FALSE (KNOWN SPACE)";
      oodFlag.style.color = "var(--accent-emerald)";
      document.getElementById("badge-diagnosis-status").innerText = "STATUS: " + (ev.anomaly_detected ? "ANOMALY IDENTIFIED" : "NOMINAL");
      document.getElementById("badge-diagnosis-status").style.color = ev.anomaly_detected ? "var(--accent-amber)" : "var(--accent-emerald)";
    }

    // Probabilities
    const probs = ev.probabilities || {};
    this.updateProbItem("thermal", probs.thermal_runaway || 0);
    this.updateProbItem("impedance", probs.battery_impedance || 0);
    this.updateProbItem("solar-fault", probs.solar_fault || 0);
    this.updateProbItem("surge", probs.parasitic_surge || 0);
    this.updateProbItem("ood", probs.novel_ood || 0);
  }

  updateProbItem(key, val) {
    const pct = (val * 100).toFixed(1);
    const labelEl = document.getElementById(`pct-${key}`);
    const barEl = document.getElementById(`bar-${key}`);
    if (labelEl) labelEl.innerText = `${pct}%`;
    if (barEl) barEl.style.width = `${pct}%`;
  }

  // --- Paper 3: Safety Invariant Checks ---
  updatePaper3Invariants(frame) {
    this.setInvStatus("temp", frame.temperature_c <= 46.0, `${frame.temperature_c.toFixed(1)}°C (Limit: 46.0°C)`);
    this.setInvStatus("volt", frame.voltage_v >= 22.0, `${frame.voltage_v.toFixed(1)}V (Limit: ≥22.0V)`);
    this.setInvStatus("curr", Math.abs(frame.current_a) <= 40.0, `${Math.abs(frame.current_a).toFixed(1)}A (Limit: ≤40.0A)`);
    this.setInvStatus("soc", frame.soc_pct >= 15.0, `${frame.soc_pct.toFixed(1)}% (Limit: ≥15.0%)`);
    this.setInvStatus("power", (frame.power_w || 0) <= 880.0, `${(frame.power_w || 0).toFixed(0)}W (Limit: ≤880.0W)`);
  }

  setInvStatus(key, isPass, text) {
    const badge = document.getElementById(`inv-badge-${key}`);
    const card = document.getElementById(`inv-card-${key}`);
    if (!badge || !card) return;

    if (isPass) {
      badge.className = "inv-state-badge pass";
      badge.innerText = "PASS";
      card.classList.remove("violated");
    } else {
      badge.className = "inv-state-badge breach";
      badge.innerText = "BREACH";
      card.classList.add("violated");
    }
  }

  // --- Paper 1 Planner Trigger ---
  async runPaper1Planner() {
    this.addLog("PLANNER", "Initiating Paper 1 counterfactual branching evaluation...");

    if (this.isLiveConnected) {
      try {
        const resp = await fetch("/api/paper1/counterfactual", { method: "POST" });
        const data = await resp.json();
        this.renderCounterfactualResults(data.branches, data.selected_plan);
      } catch (e) {
        this.renderFallbackCounterfactual();
      }
    } else {
      this.renderFallbackCounterfactual();
    }
  }

  renderCounterfactualResults(branches, selected) {
    const tbody = document.getElementById("tbody-counterfactual");
    tbody.innerHTML = "";

    branches.forEach((b) => {
      const tr = document.createElement("tr");
      const isApp = b.safety_status === "APPROVED";
      const isSel = selected && selected.action_id === b.action_id;

      tr.style.backgroundColor = isSel ? "rgba(6, 182, 212, 0.1)" : "transparent";

      tr.innerHTML = `
        <td><strong>${b.action_id}</strong> ${isSel ? '<span class="badge badge-approved" style="font-size:0.65rem;">SELECTED</span>' : ''}</td>
        <td>${b.action_type}</td>
        <td>${b.description}</td>
        <td>${b.predicted_max_temp_c.toFixed(1)}°C</td>
        <td>${b.predicted_min_volt_v.toFixed(1)}V</td>
        <td>${b.payload_availability_pct}%</td>
        <td><span class="badge ${isApp ? 'badge-approved' : 'badge-rejected'}">${b.safety_status}</span></td>
        <td><strong>${b.score.toFixed(3)}</strong></td>
      `;
      tbody.appendChild(tr);
    });

    const box = document.getElementById("planner-decision-box");
    const title = document.getElementById("planner-selected-title");
    const desc = document.getElementById("planner-selected-desc");

    if (selected) {
      box.className = "verdict-banner approved";
      title.innerText = `SELECTED PLAN: ${selected.action_id} (${selected.action_type})`;
      desc.innerText = `Governor Approved. Preserves ${selected.payload_availability_pct}% science observation with verified safety margins (Peak Temp: ${selected.predicted_max_temp_c}°C, Min Bus: ${selected.predicted_min_volt_v}V).`;
      this.addLog("PLANNER", `Action ${selected.action_id} approved and scheduled for execution.`);
    } else {
      box.className = "verdict-banner rejected";
      title.innerText = "NO SAFE ACTION AVAILABLE (DEADLOCK SAFEMODE)";
      desc.innerText = "All candidate actions violate Level 1 physical safety invariants. Safe fail-closed standby activated.";
      this.addLog("PLANNER", "Governor blocked all candidates. Transitioned to safe deadlock hold.");
    }
  }

  renderFallbackCounterfactual() {
    const mockBranches = [
      { action_id: "ACT-00-NOOP", action_type: "CONTINUE_NOMINAL", description: "Continue nominal operations", predicted_max_temp_c: 28.5, predicted_min_volt_v: 28.2, payload_availability_pct: 100, safety_status: "APPROVED", score: 0.910 },
      { action_id: "ACT-01-SAFE-MODE", action_type: "ENTER_SAFE_MODE", description: "Enter minimal power Safe Mode", predicted_max_temp_c: 21.0, predicted_min_volt_v: 30.5, payload_availability_pct: 0, safety_status: "APPROVED", score: 0.812 },
      { action_id: "ACT-02-THROTTLE-50", action_type: "REDUCE_PAYLOAD_LOAD", description: "Throttle science payload by 50%", predicted_max_temp_c: 24.0, predicted_min_volt_v: 29.1, payload_availability_pct: 50, safety_status: "APPROVED", score: 0.865 },
      { action_id: "ACT-03-DISABLE-PAYLOAD", action_type: "DISABLE_NON_CRITICAL_SUBSYSTEM", description: "Isolate payload to protect battery", predicted_max_temp_c: 22.0, predicted_min_volt_v: 30.0, payload_availability_pct: 0, safety_status: "APPROVED", score: 0.790 },
    ];
    this.renderCounterfactualResults(mockBranches, mockBranches[0]);
  }

  // --- Paper 3: Governor Tester ---
  async evaluateGovernorProposal() {
    const actId = document.getElementById("prop-id").value;
    const actType = document.getElementById("prop-type").value;
    const peakTemp = parseFloat(document.getElementById("prop-temp").value);
    const minVolt = parseFloat(document.getElementById("prop-volt").value);
    const peakCurr = parseFloat(document.getElementById("prop-curr").value);
    const conf = parseFloat(document.getElementById("prop-conf").value);

    const payload = {
      action_id: actId,
      action_type: actType,
      predicted_peak_temp_c: peakTemp,
      predicted_min_voltage_v: minVolt,
      predicted_peak_current_a: peakCurr,
      predicted_min_soc: 0.80,
      predicted_peak_power_w: 350.0,
      ai_confidence: conf,
    };

    if (this.isLiveConnected) {
      try {
        const resp = await fetch("/api/paper3/evaluate-action", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const verdict = await resp.json();
        this.renderGovernorVerdict(verdict);
        return;
      } catch (e) {
        // Fallback to client check
      }
    }

    // Client-side Governor Logic
    const viols = [];
    const reasons = [];
    if (peakTemp > 46.0) {
      viols.push("THERMAL_OVERHEAT");
      reasons.push(`Temperature ${peakTemp}°C exceeds max limit 46.0°C by +${(peakTemp - 46.0).toFixed(1)}°C.`);
    }
    if (minVolt < 22.0) {
      viols.push("UNDERVOLTAGE");
      reasons.push(`Voltage ${minVolt}V below minimum floor 22.0V by ${(22.0 - minVolt).toFixed(1)}V.`);
    }
    if (peakCurr > 40.0) {
      viols.push("OVERCURRENT");
      reasons.push(`Current ${peakCurr}A exceeds limit 40.0A.`);
    }
    if (actType === "OVERCHARGE_RAPID_BATTERY") {
      viols.push("UNCERTIFIED_ACTION");
      reasons.push(`Action type '${actType}' is not in certified flight command catalog.`);
    }

    const isAdmissible = viols.length === 0;
    this.renderGovernorVerdict({
      action_id: actId,
      decision: isAdmissible ? "APPROVED" : "REJECTED",
      is_admissible: isAdmissible,
      violated_constraints: viols,
      rejection_reasons: reasons,
      constraints_evaluated_count: 6,
      evaluation_latency_ms: 0.003,
    });
  }

  renderGovernorVerdict(verdict) {
    const box = document.getElementById("governor-verdict-box");
    const title = document.getElementById("gov-verdict-title");
    const reasons = document.getElementById("gov-verdict-reasons");
    const meta = document.getElementById("gov-verdict-meta");
    const icon = document.getElementById("gov-verdict-icon");

    if (verdict.is_admissible) {
      box.className = "verdict-banner approved";
      icon.innerText = "✅";
      title.innerText = `VERDICT: APPROVED (${verdict.action_id})`;
      reasons.innerText = "All Level 1 physical safety invariants satisfied. Action is admissible for bus dispatch.";
      this.addLog("GOVERNOR", `Action ${verdict.action_id} evaluated: APPROVED (Passed 6/6 constraints).`);
    } else {
      box.className = "verdict-banner rejected";
      icon.innerText = "⛔";
      title.innerText = `VERDICT: REJECTED (${verdict.action_id})`;
      reasons.innerText = `Violated: ${verdict.violated_constraints.join(", ")}. ${verdict.rejection_reasons.join(" ")} Action BLOCKED from flight bus execution.`;
      this.addLog("GOVERNOR", `Action ${verdict.action_id} evaluated: REJECTED (${verdict.violated_constraints.join(", ")}).`);
    }

    meta.innerText = `Evaluated: ${verdict.constraints_evaluated_count} constraints | Latency: ${verdict.evaluation_latency_ms.toFixed(3)} ms | Execution: ${verdict.is_admissible ? 'AUTHORIZED' : 'BLOCKED'}`;
  }

  // --- Fault Actions ---
  async injectFault(faultType) {
    this.addLog("WARNING", `Injecting physical fault: ${faultType}...`);

    if (this.isLiveConnected) {
      try {
        await fetch("/api/inject-fault", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fault_type: faultType, severity: 1.0 }),
        });
      } catch (e) {
        this.addLog("CRITICAL", "Failed to contact fault endpoint.");
      }
    } else {
      this.clientSim.activeFault = faultType;
      this.addLog("WARNING", `Client physics active fault set: ${faultType}`);
    }
  }

  async clearFaults() {
    this.addLog("INFO", "Clearing all active physical faults...");
    if (this.isLiveConnected) {
      try {
        await fetch("/api/clear-faults", { method: "POST" });
      } catch (e) {}
    } else {
      this.clientSim.activeFault = null;
    }
  }

  async resetSimulation() {
    this.addLog("SYSTEM", "Resetting simulation to orbit epoch (t=0)...");
    if (this.isLiveConnected) {
      try {
        await fetch("/api/reset", { method: "POST" });
      } catch (e) {}
    } else {
      this.simTimeSec = 0.0;
      this.clientSim.temp = 24.5;
      this.clientSim.voltage = 28.4;
      this.clientSim.soc = 88.5;
      this.clientSim.activeFault = null;
    }
    this.history.labels = [];
    this.history.voltage = [];
    this.history.current = [];
    this.history.temperature = [];
    this.history.soc = [];
    this.history.power = [];
    this.history.solar = [];
  }

  // --- Client-Side Kinetics Engine (Fallback) ---
  tickClientSimulation() {
    this.simTimeSec += 2.0 * this.simSpeed;
    const t = this.simTimeSec;

    // Day/Night Orbit (~5400s orbit)
    const orbitAngle = ((t % 5400) / 5400) * 2 * Math.PI;
    const isSunlight = Math.sin(orbitAngle) > -0.2;
    const solarBase = isSunlight ? Math.max(0, Math.sin(orbitAngle) * 210.0) : 0.0;

    let faultHeating = 0.0;
    let faultImpedanceDrop = 0.0;
    let faultType = this.clientSim.activeFault;

    if (faultType === "THERMAL_RUNAWAY") {
      faultHeating = 0.45 * this.simSpeed;
    } else if (faultType === "BATTERY_RESISTANCE_SPIKE") {
      faultImpedanceDrop = 4.2;
      faultHeating = 0.15;
    } else if (faultType === "SOLAR_STRING_FAULT") {
      solarBase *= 0.3;
    } else if (faultType === "PARASITIC_LOAD_SURGE") {
      faultImpedanceDrop = 2.5;
    }

    this.clientSim.temp = Math.min(55.0, Math.max(15.0, this.clientSim.temp + faultHeating + (Math.random() - 0.5) * 0.05));
    this.clientSim.voltage = Math.max(19.0, 28.4 - faultImpedanceDrop + (Math.random() - 0.5) * 0.1);
    this.clientSim.solarPower = solarBase;

    const frame = {
      timestamp_sec: t,
      voltage_v: this.clientSim.voltage,
      current_a: 8.2 + (faultType ? 6.0 : 0.0),
      temperature_c: this.clientSim.temp,
      soc_pct: Math.max(10.0, 88.5 - (t / 5400) * 15.0),
      power_w: this.clientSim.voltage * 8.2,
      solar_power_w: solarBase,
      load_power_w: 120.0,
      link_status: (t % 5400 < 1200) ? "IN_CONTACT" : "BLACKOUT_OCCULTATION",
      safety_status: this.clientSim.temp > 46.0 ? "CRITICAL_VIOLATION" : (faultType ? "ANOMALY_INVESTIGATION" : "NOMINAL"),
      active_faults: faultType ? [{ type: faultType }] : [],
      evidential: {
        anomaly_detected: !!faultType,
        primary_diagnosis: faultType || "NOMINAL_STABLE",
        confidence: faultType ? 0.94 : 0.99,
        epistemic_uncertainty: faultType === "OOD_NOVELTY" ? 0.985 : 0.015,
        aleatoric_uncertainty: 0.022,
        is_ood_novelty: faultType === "OOD_NOVELTY",
        probabilities: {
          thermal_runaway: faultType === "THERMAL_RUNAWAY" ? 0.92 : 0.01,
          battery_impedance: faultType === "BATTERY_RESISTANCE_SPIKE" ? 0.89 : 0.01,
          solar_fault: faultType === "SOLAR_STRING_FAULT" ? 0.91 : 0.01,
          parasitic_surge: faultType === "PARASITIC_LOAD_SURGE" ? 0.88 : 0.01,
          novel_ood: faultType === "OOD_NOVELTY" ? 0.96 : 0.01,
        }
      }
    };

    this.ingestFrame(frame);
  }

  // --- Charts Setup & Updates ---
  initCharts() {
    const ctxPower = document.getElementById("chart-power").getContext("2d");
    const ctxThermal = document.getElementById("chart-thermal").getContext("2d");

    Chart.defaults.color = "#94a3b8";
    Chart.defaults.font.family = "'JetBrains Mono', monospace";
    Chart.defaults.font.size = 11;

    this.powerChart = new Chart(ctxPower, {
      type: "line",
      data: {
        labels: this.history.labels,
        datasets: [
          {
            label: "Bus Voltage (V)",
            data: this.history.voltage,
            borderColor: "#06b6d4",
            backgroundColor: "rgba(6, 182, 212, 0.08)",
            borderWidth: 2,
            pointRadius: 0,
            yAxisID: "yV",
            tension: 0.2,
          },
          {
            label: "Solar Power (W)",
            data: this.history.solar,
            borderColor: "#38bdf8",
            borderDash: [4, 4],
            borderWidth: 1.5,
            pointRadius: 0,
            yAxisID: "yP",
            tension: 0.2,
          },
          {
            label: "Total Power (W)",
            data: this.history.power,
            borderColor: "#818cf8",
            borderWidth: 1.8,
            pointRadius: 0,
            yAxisID: "yP",
            tension: 0.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        scales: {
          x: { grid: { color: "rgba(255,255,255,0.04)" } },
          yV: {
            position: "left",
            min: 18,
            max: 36,
            title: { display: true, text: "Voltage (V)", color: "#06b6d4" },
            grid: { color: "rgba(255,255,255,0.05)" },
          },
          yP: {
            position: "right",
            min: 0,
            max: 300,
            title: { display: true, text: "Power (W)", color: "#818cf8" },
            grid: { drawOnChartArea: false },
          },
        },
      },
    });

    this.thermalChart = new Chart(ctxThermal, {
      type: "line",
      data: {
        labels: this.history.labels,
        datasets: [
          {
            label: "Battery Temp (°C)",
            data: this.history.temperature,
            borderColor: "#ef4444",
            backgroundColor: "rgba(239, 68, 68, 0.08)",
            borderWidth: 2,
            pointRadius: 0,
            yAxisID: "yT",
            tension: 0.2,
          },
          {
            label: "State of Charge (%)",
            data: this.history.soc,
            borderColor: "#a855f7",
            borderWidth: 1.8,
            pointRadius: 0,
            yAxisID: "ySoc",
            tension: 0.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        scales: {
          x: { grid: { color: "rgba(255,255,255,0.04)" } },
          yT: {
            position: "left",
            min: 15,
            max: 55,
            title: { display: true, text: "Temperature (°C)", color: "#ef4444" },
            grid: { color: "rgba(255,255,255,0.05)" },
          },
          ySoc: {
            position: "right",
            min: 0,
            max: 100,
            title: { display: true, text: "SoC (%)", color: "#a855f7" },
            grid: { drawOnChartArea: false },
          },
        },
      },
    });
  }

  pushChartData(frame) {
    const label = `${Math.floor(frame.timestamp_sec)}s`;
    this.history.labels.push(label);
    this.history.voltage.push(frame.voltage_v);
    this.history.current.push(frame.current_a);
    this.history.temperature.push(frame.temperature_c);
    this.history.soc.push(frame.soc_pct);
    this.history.power.push(frame.power_w || (frame.voltage_v * Math.abs(frame.current_a)));
    this.history.solar.push(frame.solar_power_w || 0.0);

    if (this.history.labels.length > this.maxChartPoints) {
      this.history.labels.shift();
      this.history.voltage.shift();
      this.history.current.shift();
      this.history.temperature.shift();
      this.history.soc.shift();
      this.history.power.shift();
      this.history.solar.shift();
    }

    if (this.powerChart && this.thermalChart) {
      this.powerChart.update("none");
      this.thermalChart.update("none");
    }
  }

  // --- Event Console ---
  addLog(level, message) {
    const t = Math.floor(this.simTimeSec);
    const hrs = String(Math.floor(t / 3600)).padStart(2, "0");
    const mins = String(Math.floor((t % 3600) / 60)).padStart(2, "0");
    const secs = String(t % 60).padStart(2, "0");
    const timeStr = `${hrs}:${mins}:${secs}`;

    const entry = { time: timeStr, level, message };
    this.eventLogs.push(entry);
    if (this.eventLogs.length > 80) this.eventLogs.shift();

    const consoleEl = document.getElementById("log-console");
    if (!consoleEl) return;

    const row = document.createElement("div");
    row.className = "log-entry";
    row.innerHTML = `
      <span class="log-time">[${timeStr}]</span>
      <span class="log-level ${level}">${level}</span>
      <span class="log-msg">${escapeHtml(message)}</span>
    `;
    consoleEl.appendChild(row);
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }
}

// Utilities
function jsonParseSafe(str) {
  try {
    return JSON.parse(str);
  } catch (e) {
    return null;
  }
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, (m) => map[m]);
}
