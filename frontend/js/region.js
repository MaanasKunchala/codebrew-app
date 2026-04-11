console.log("region.js loaded");

const regionForm = document.getElementById("regionForm");
const regionMessage = document.getElementById("regionMessage");

regionForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(regionForm);

    const payload = {
        name: formData.get("name")?.trim(),
        state: formData.get("state")?.trim() || "",
        notes: formData.get("notes")?.trim() || ""
    };

    console.log("Region payload:", payload);

    if (!payload.name) {
        regionMessage.textContent = "Region name is required.";
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/regions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();
        console.log("Backend response:", result);

        if (!response.ok) {
            regionMessage.textContent = result.detail || "Failed to save region.";
            return;
        }

        regionMessage.textContent = `Region saved: ${result.name}`;
        regionForm.reset();
    } catch (error) {
        console.error("Request failed:", error);
        regionMessage.textContent = "Submission failed. Check backend is running.";
    }
});