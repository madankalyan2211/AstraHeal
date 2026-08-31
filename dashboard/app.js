/**
 * AstraHeal Mission Dashboard Client Logic
 */

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const response = await fetch("data.json");
    if (!response.ok) {
      throw new Error(`Failed to load data.json: ${response.statusText}`);
    }
    const data = await response.json();
    initDashboard(data);
  } catch (err) {
    console.error("Error loading dashboard data:", err);
    // Fallback static load if served via file:// protocol
    loadFallbackData();
  }
});

function initDashboard(data) {
  // 1. Populate Metric Highlights
  const tLen = data.telemetry.timestamps_sec.length;
  const lastIdx = tLen - 1;

  document.getElementById("val-voltage").innerHTML = `${data.telemetry.voltage_v[lastIdx]} <span class="unit">V</span>`;
  document.getElementById("val-current").innerHTML = `${data.telemetry.current_a[lastIdx]} <span class="unit">A</span>`;
  document.getElementById("val-temp").innerHTML = `${data.telemetry.temperature_c[lastIdx]} <span class="unit">°C</span>`;
  document.getElementById("val-soc").innerHTML = `${data.telemetry.soc_pct[lastIdx]} <span class="unit">%</span>`;

  // 2. Populate Intelligence
  document.getElementById("val-epistemic").innerText = data.intelligence.epistemic_uncertainty.toFixed(3);
  document.getElementById("bar-epistemic").style.width = `${data.intelligence.epistemic_uncertainty * 100}%`;
  
  document.getElementById("val-aleatoric").innerText = data.intelligence.aleatoric_uncertainty.toFixed(3);
  document.getElementById("bar-aleatoric").style.width = `${Math.min(100, data.intelligence.aleatoric_uncertainty * 100)}%`;

  // 3. Populate Counterfactual Table
  const tbody = document.getElementById("counterfactual-tbody");
  tbody.innerHTML = "";
  
  data.counterfactual_actions.forEach(action => {
    const tr = document.createElement("tr");
    const isApproved = action.safety_status === "APPROVED";
    const badgeClass = isApproved ? "badge-approved" : "badge-rejected";

    tr.innerHTML = `
      <td><strong>${action.action_id}</strong></td>
      <td>${action.action_type}</td>
      <td>${action.predicted_max_temp_c.toFixed(1)}°C</td>
      <td>${action.predicted_min_volt_v.toFixed(1)}V</td>
      <td>${action.payload_availability_pct}%</td>
      <td><span class="${badgeClass}">${action.safety_status}</span></td>
      <td><strong>${action.score.toFixed(3)}</strong></td>
    `;
    tbody.appendChild(tr);
  });

  // 4. Render Telemetry Charts
  renderTelemetryChart(data.telemetry);
}

function renderTelemetryChart(telemetry) {
  const ctx = document.getElementById("telemetryChart").getContext("2d");
  
  // Format timestamps into minutes
  const labels = telemetry.timestamps_sec.map(t => (t / 60).toFixed(0) + "m");

  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Bus Voltage (V)",
          data: telemetry.voltage_v,
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.05)",
          borderWidth: 1.8,
          pointRadius: 0,
          yAxisID: "yVoltage"
        },
        {
          label: "Battery Temp (°C)",
          data: telemetry.temperature_c,
          borderColor: "#ef4444",
          backgroundColor: "transparent",
          borderWidth: 1.8,
          pointRadius: 0,
          yAxisID: "yTemp"
        },
        {
          label: "Battery SoC (%)",
          data: telemetry.soc_pct,
          borderColor: "#8b5cf6",
          backgroundColor: "transparent",
          borderWidth: 1.8,
          pointRadius: 0,
          yAxisID: "ySoc"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#9ca3af", font: { family: "Inter", size: 10 } }
        },
        yVoltage: {
          type: "linear",
          position: "left",
          min: 20,
          max: 35,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#06b6d4", font: { family: "Inter", size: 10 } },
          title: { display: true, text: "Voltage (V)", color: "#06b6d4", font: { size: 10 } }
        },
        yTemp: {
          type: "linear",
          position: "right",
          min: 0,
          max: 60,
          grid: { display: false },
          ticks: { color: "#ef4444", font: { family: "Inter", size: 10 } },
          title: { display: true, text: "Temp (°C)", color: "#ef4444", font: { size: 10 } }
        },
        ySoc: {
          type: "linear",
          position: "right",
          min: 0,
          max: 100,
          grid: { display: false },
          ticks: { color: "#8b5cf6", font: { family: "Inter", size: 10 } },
          title: { display: true, text: "SoC (%)", color: "#8b5cf6", font: { size: 10 } }
        }
      }
    }
  });
}

function loadFallbackData() {
  console.log("Loading offline fallback state...");
}
