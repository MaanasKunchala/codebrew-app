console.log("report.js loaded");

const form = document.getElementById("reportForm");

const regionSelect = document.getElementById("region_name");

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

    console.log("Raw recent_dog_deaths:", formData.get("recent_dog_deaths"));
    console.log("Raw distance_to_clinic:", formData.get("distance_to_clinic"));
    console.log("Raw num_dogs_seen:", formData.get("num_dogs_seen"));
    console.log("Raw num_puppies_seen:", formData.get("num_puppies_seen"));
    console.log("Raw skin_issue_count:", formData.get("skin_issue_count"));
    console.log("Raw parasite_issue_count:", formData.get("parasite_issue_count"));

    const indicatorsRaw = formData.get("seasonal_indicators") || "";
    const seasonalIndicators = indicatorsRaw
        .split(",")
        .map(item => item.trim())
        .filter(item => item.length > 0);

    const payload = {
        community_name: formData.get("community_name"),
        region_name: formData.get("region_name"),
        reporter_type: formData.get("reporter_type"),
        local_season: formData.get("local_season"),
        rainfall_level: formData.get("rainfall_level"),
        road_access: formData.get("road_access"),
        seasonal_indicators: seasonalIndicators,
        num_dogs_seen: Number(formData.get("num_dogs_seen")),
        num_puppies_seen: Number(formData.get("num_puppies_seen")),
        skin_issue_count: Number(formData.get("skin_issue_count")),
        parasite_issue_count: Number(formData.get("parasite_issue_count")),
        dog_roaming_level: formData.get("dog_roaming_level"),
        recent_dog_deaths: Number(formData.get("recent_dog_deaths")),
        distance_to_clinic: Number(formData.get("distance_to_clinic")),
        requested_help: formData.get("requested_help") === "on",
        notes: formData.get("notes") || ""
    };

    /*
    const payload = {
        community_name: "Maningrida",
        reporter_type: "community_member",
        local_season: "early_wet",
        rainfall_level: "high",
        road_access: "difficult",
        seasonal_indicators: ["first rains", "flowering trees"],
        num_dogs_seen: 20,
        num_puppies_seen: 5,
        skin_issue_count: 3,
        parasite_issue_count: 4,
        dog_roaming_level: "high",
        recent_dog_deaths: 1,
        distance_to_clinic: 120,
        requested_help: true,
        notes: "Several dogs scratching"
    };
    */

    localStorage.setItem("waldhep_last_report", JSON.stringify(payload));

    console.log("Payload being sent:", payload);

    try {
        for (const [key, value] of Object.entries(payload)) {
            if (value === null || value === undefined || Number.isNaN(value)) {
                console.error("Invalid payload field:", key, value);
                alert(`Invalid field detected: ${key}`);
                return;
            }
        }
        const response = await fetch("http://127.0.0.1:8000/submit-report", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        console.log("Backend response:", result);

        if (!response.ok) {
            alert("Backend validation failed. Open browser console.");
            return;
        }

        localStorage.setItem("waldhep_result", JSON.stringify(result));
        window.location.href = "result.html";
    } catch (error) {
        console.error("Request failed:", error);
        alert("Submission failed. Check console and backend terminal.");
    }
});