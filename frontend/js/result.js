const saved = localStorage.getItem("waldhep_result");
const savedReport = localStorage.getItem("waldhep_last_report");

if (!saved) {
    document.body.innerHTML = `
    <main class="screen center">
        <section class="card">
        <h1>No result found</h1>
        <p class="subtext">Submit a report first.</p>
        <a class="primary-btn" href="report.html">Go to Report Form</a>
        </section>
    </main>
    `;
} else {
    const result = JSON.parse(saved);
    const report = savedReport ? JSON.parse(savedReport) : null;

    renderHeader(report);
    renderSummary(result);
    renderObservations(report);
    renderSeasonalGuidance(result.seasonal_guidance || []);
    renderForecast(result.ml_predictions || {});
    renderFundingSection(report, result);
    renderCharts(result);
}

function renderHeader(report) {
    const reportMeta = document.getElementById("reportMeta");

    const metaItems = [
        ["Region", report?.region_name || "Not available"],
        ["Community", report?.community_name || "Not available"],
        ["Role", formatRole(report?.reporter_type || "Not available")],
        ["Season", report?.local_season || "Not available"],
        ["Report Date", report?.report_date
            ? new Date(report.report_date).toLocaleString()
            : new Date().toLocaleString()]
    ];

    reportMeta.innerHTML = metaItems.map(([label, value]) => `
    <div class="report-meta-item">
        <span>${label}</span>
        <strong>${value}</strong>
    </div>
    `).join("");
}

function renderSummary(result) {
    document.getElementById("mainSupport").textContent = result.main_support || "Support assessment unavailable";
    document.getElementById("summaryConfidence").textContent =
        `Confidence: ${Math.round((result.confidence || 0) * 100)}%`;
    document.getElementById("summaryAction").textContent =
        result.recommended_action || "No recommended action available.";

    const reasons = result.reasons || [];
    document.getElementById("summaryReasons").innerHTML = `
    <p class="eyebrow">Key Drivers</p>
    <ul class="summary-reason-list">
        ${reasons.map(reason => `<li>${reason}</li>`).join("")}
    </ul>
    `;
}

function renderObservations(report) {
    const observationsGrid = document.getElementById("observationsGrid");

    const cards = [
        ["Dogs Seen", report?.num_dogs_seen ?? "—"],
        ["Puppies Seen", report?.num_puppies_seen ?? "—"],
        ["Skin Issues", report?.skin_issue_count ?? "—"],
        ["Parasite Issues", report?.parasite_issue_count ?? "—"],
        ["Dog Deaths", report?.recent_dog_deaths ?? "—"],
        ["Road Access", capitalize(report?.road_access || "—")]
    ];

    observationsGrid.innerHTML = cards.map(([label, value]) => `
    <div class="stat-card">
    <div class="stat-label">${label}</div>
    <div class="stat-value">${value}</div>
    </div>
`   ).join("");
}

function renderSeasonalGuidance(guidance) {
    const container = document.getElementById("seasonalGuidanceList");

    if (!guidance.length) {
        container.innerHTML = `<p class="subtext">No seasonal guidance available for this region and season.</p>`;
        return;
    }

    container.innerHTML = guidance.map(item => `
    <div class="guidance-card">
    <div class="guidance-top">
        <div class="guidance-title">${item.parasite}</div>
        <span class="risk-badge ${riskClass(item.risk_level)}">${item.risk_level || "Unknown Risk"}</span>
    </div>
    <div class="guidance-row"><strong>Treatment:</strong> ${item.treatment_name || "Not available"}</div>
    <div class="guidance-row"><strong>Ingredients:</strong> ${item.active_ingredients || "Not available"}</div>
    <div class="guidance-row"><strong>Why:</strong> ${item.trigger_notes || "Not available"}</div>
    <div class="guidance-row"><strong>Action:</strong> ${item.recommendation_notes || "Not available"}</div>
    </div>
    `).join("");
}

function renderForecast(mlPredictions) {
    const container = document.getElementById("forecastGrid");

    const horizons = [
        ["3 Months", "3m"],
        ["6 Months", "6m"],
        ["9 Months", "9m"],
        ["12 Months", "12m"]
    ];

    container.innerHTML = horizons.map(([title, suffix]) => `
    <div class="forecast-card">
        <h3>${title}</h3>
        <div class="forecast-item">
            <span>Parasite treatment</span>
            <span class="forecast-status ${statusClass(mlPredictions[`needs_parasite_treatment_${suffix}`])}">
            ${yesNo(mlPredictions[`needs_parasite_treatment_${suffix}`])}
            </span>
        </div>
        <div class="forecast-item">
            <span>Scabies treatment</span>
            <span class="forecast-status ${statusClass(mlPredictions[`needs_scabies_treatment_${suffix}`])}">
            ${yesNo(mlPredictions[`needs_scabies_treatment_${suffix}`])}
            </span>
        </div>
        <div class="forecast-item">
            <span>Follow-up visit</span>
            <span class="forecast-status ${statusClass(mlPredictions[`needs_followup_visit_${suffix}`])}">
            ${yesNo(mlPredictions[`needs_followup_visit_${suffix}`])}
            </span>
        </div>
    </div>
    `).join("");
}

function renderFundingSection(report, result) {
    const fundingSection = document.getElementById("fundingSection");
    const ml = result.ml_predictions || {};
    const guidanceCount = (result.seasonal_guidance || []).length;

    const likelyFutureNeed =
        (ml.needs_parasite_treatment_3m ? 1 : 0) +
        (ml.needs_scabies_treatment_3m ? 1 : 0) +
        (ml.needs_followup_visit_3m ? 1 : 0);

    let urgency = "Moderate";
    if ((report?.recent_dog_deaths || 0) >= 2 || likelyFutureNeed >= 3) urgency = "High";
    if ((report?.parasite_issue_count || 0) <= 2 && (report?.skin_issue_count || 0) <= 2) urgency = "Low";

    fundingSection.innerHTML = `
    <p><strong>Operational urgency:</strong> ${urgency}</p>
    <p><strong>Immediate planning implication:</strong> This report indicates a likely need for targeted veterinary outreach, especially where seasonal and observed conditions align with known parasite or skin-related treatment pressures.</p>
    <p><strong>Evidence basis:</strong> ${guidanceCount} seasonal guidance record(s), current field observations, historical treatment trends, and projected future treatment needs.</p>
    <p><strong>Suggested use in funding/reporting:</strong> This output can support prioritisation of outreach timing, medication planning, staffing allocation, and justification for follow-up investment in communities showing repeated or elevated treatment demand.</p>
    `;
}

function renderCharts(result) {
    const trends = result.historical_treatment_trends || {
        parasite: [],
        scabies: [],
        desexing: []
    };

    const ml = result.ml_predictions || {};
    const desexingProjection = result.desexing_projection || {};

    createTreatmentChart(
        "parasiteChart",
        "Parasite",
        trends.parasite || [],
        [
            ["3 Months", ml.needs_parasite_treatment_3m],
            ["6 Months", ml.needs_parasite_treatment_6m],
            ["9 Months", ml.needs_parasite_treatment_9m],
            ["12 Months", ml.needs_parasite_treatment_12m]
        ]
    );

    createTreatmentChart(
        "scabiesChart",
        "Scabies",
        trends.scabies || [],
        [
            ["3 Months", ml.needs_scabies_treatment_3m],
            ["6 Months", ml.needs_scabies_treatment_6m],
            ["9 Months", ml.needs_scabies_treatment_9m],
            ["12 Months", ml.needs_scabies_treatment_12m]
        ]
    );

    createDesexingChart(
        "desexingChart",
        trends.desexing || [],
        desexingProjection
    );
}

function createTreatmentChart(canvasId, label, historical, projectedFlags) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const historicalLabels = historical.map(item => item.date);
    const historicalData = historical.map(item => item.cumulative_percentage);

    const lastValue = historicalData.length ? historicalData[historicalData.length - 1] : 0;

    const projectedLabels = projectedFlags.map(item => item[0]);
    let running = lastValue;
    const projectedData = projectedFlags.map(item => {
        running += item[1] ? 8 : 2;
        return running;
    });

    new Chart(ctx, {
        type: "line",
        data: {
            labels: [...historicalLabels, ...projectedLabels],
            datasets: [
                {
                    label: `${label} Historical`,
                    data: [...historicalData, ...new Array(projectedLabels.length).fill(null)],
                    borderWidth: 2,
                    tension: 0.25
                },
                {
                    label: `${label} Projected`,
                    data: [...new Array(historicalLabels.length).fill(null), ...projectedData],
                    borderDash: [6, 6],
                    borderWidth: 2,
                    tension: 0.25
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom"
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Cumulative Treatment %"
                    }
                }
            }
        }
    });
}

function createDesexingChart(canvasId, historical, projection) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    const historicalLabels = historical.map(item => item.date);
    const historicalData = historical.map(item => item.cumulative_percentage);

    const lastValue = historicalData.length ? historicalData[historicalData.length - 1] : 0;

    const projectedLabels = ["3 Months", "6 Months", "9 Months", "12 Months"];
    const projectedData = [
        lastValue + ((projection["3_months"] || 0) * 10),
        lastValue + ((projection["6_months"] || 0) * 10),
        lastValue + ((projection["9_months"] || 0) * 10),
        lastValue + ((projection["12_months"] || 0) * 10)
    ];

    new Chart(ctx, {
        type: "line",
        data: {
            labels: [...historicalLabels, ...projectedLabels],
            datasets: [
                {
                    label: "Desexing Historical",
                    data: [...historicalData, ...new Array(projectedLabels.length).fill(null)],
                    borderWidth: 2,
                    tension: 0.25
                },
                {
                    label: "Desexing Projected",
                    data: [...new Array(historicalLabels.length).fill(null), ...projectedData],
                    borderDash: [6, 6],
                    borderWidth: 2,
                    tension: 0.25
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom"
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Cumulative Treatment %"
                    }
                }
            }
        }
    });
}

function formatRole(role) {
    if (!role) return "Not available";
    if (role === "waldhep_staff") return "WALDHeP Staff";
    if (role === "veterinarian") return "Veterinarian";
    if (role === "ranger") return "Ranger";
    return role;
}

function capitalize(text) {
    if (!text || typeof text !== "string") return text;
    return text.charAt(0).toUpperCase() + text.slice(1);
}

function yesNo(value) {
    return value === 1 ? "Yes" : "No";
}

function statusClass(value) {
    return value === 1 ? "status-yes" : "status-no";
}

function riskClass(level) {
    if (!level) return "";
    const normalized = level.toLowerCase();
    if (normalized === "high") return "risk-high";
    if (normalized === "medium") return "risk-medium";
    if (normalized === "low") return "risk-low";
    return "";
}

const printBtn = document.getElementById("printPdfBtn");

if (printBtn) {
    printBtn.addEventListener("click", () => {
        window.print();
    });
}