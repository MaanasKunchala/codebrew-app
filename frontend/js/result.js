const resultContent = document.getElementById("resultContent");
const saved = localStorage.getItem("waldhep_result");

if (!saved) {
    resultContent.innerHTML = "<p>No result found.</p>";
} else {
    const data = JSON.parse(saved);

    resultContent.innerHTML = `
    <div class="result-block">
        <p class="eyebrow">Main Predicted Support</p>
        <h2>${data.main_support}</h2>
        <p><strong>Confidence:</strong> ${Math.round(data.confidence * 100)}%</p>
    </div>

    <div class="result-block">
        <p class="eyebrow">Probabilities</p>
        <p>Parasite treatment: ${Math.round(data.predictions.parasite_treatment * 100)}%</p>
        <p>Scabies treatment: ${Math.round(data.predictions.scabies_treatment * 100)}%</p>
        <p>Follow-up visit: ${Math.round(data.predictions.followup_visit * 100)}%</p>
    </div>

    <div class="result-block">
        <p class="eyebrow">Why</p>
        <ul>
            ${data.reasons.map(reason => `<li>${reason}</li>`).join("")}
        </ul>
    </div>

    <div class="result-block">
        <p class="eyebrow">Recommended Action</p>
        <p>${data.recommended_action}</p>
    </div>
`;
}