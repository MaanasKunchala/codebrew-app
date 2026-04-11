console.log("futureInsights.js loaded");

const form = document.getElementById("futureInsightsForm");
const regionSelect = document.getElementById("future_region_name");
const message = document.getElementById("futureInsightsMessage");

async function loadRegions() {
    try {
        const response = await fetch("http://127.0.0.1:8000/regions");
        const regions = await response.json();

        regionSelect.innerHTML = '<option value="">Select</option>';

        regions.forEach(region => {
            const option = document.createElement("option");
            option.value = region.name;
            option.textContent = region.name;
            regionSelect.appendChild(option);
        });
    } catch (error) {
        console.error("Failed to load regions:", error);
        regionSelect.innerHTML = '<option value="">Could not load regions</option>';
    }
}

loadRegions();

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);
    const regionName = formData.get("region_name");

    if (!regionName) {
        message.textContent = "Please select a region.";
        return;
    }

    message.textContent = "Loading latest insight...";

    try {
        const response = await fetch(
            `http://127.0.0.1:8000/latest-insight?region_name=${encodeURIComponent(regionName)}`
        );

        const data = await response.json();
        console.log("Latest insight response:", data);

        if (!response.ok) {
            message.textContent = data.detail || "Could not fetch latest insight.";
            return;
        }

        localStorage.setItem("waldhep_last_report", JSON.stringify(data.report));
        localStorage.setItem("waldhep_result", JSON.stringify(data.result));

        window.location.href = "result.html";
    } catch (error) {
        console.error("Request failed:", error);
        message.textContent = "Failed to retrieve latest insight. Check backend and console.";
    }
});