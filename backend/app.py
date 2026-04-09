from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Report(BaseModel):
    community_name: str
    reporter_type: str
    local_season: str
    rainfall_level: str
    road_access: str
    seasonal_indicators: List[
        str
    ]  # needs to simplified, probably boolean question for each weather/seasonal challenge
    num_dogs_seen: int
    num_puppies_seen: int
    skin_issue_count: int
    parasite_issue_count: int
    dog_roaming_level: str
    requested_help: bool
    recent_dog_deaths: int
    distance_to_clinic: int
    notes: Optional[str] = ""


@app.get("/")
def root():
    return {"message": "WALDHeP backend running"}


@app.post("/submit-report")
def submit_report(report: Report):
    # fake prediction for now
    parasite_probability = min(0.95, 0.25 + report.parasite_issue_count * 0.08)
    scabies_probability = min(0.95, 0.20 + report.skin_issue_count * 0.08)
    followup_probability = min(0.95, 0.15 + report.num_puppies_seen * 0.04)

    main_support = "Parasite treatment"
    top_score = parasite_probability

    if scabies_probability > top_score:
        main_support = "Scabies treatment"
        top_score = scabies_probability

    if followup_probability > top_score:
        main_support = "Follow-up visit"
        top_score = followup_probability

    reasons = []
    if report.num_puppies_seen >= 5:
        reasons.append("High puppy numbers reported")
    if report.skin_issue_count >= 3:
        reasons.append("Multiple dogs with skin issues")
    if report.parasite_issue_count >= 3:
        reasons.append("Multiple parasite-related issues reported")
    if report.rainfall_level.lower() in ["high", "heavy"]:
        reasons.append("Seasonal conditions may increase health risk")

    if not reasons:
        reasons.append("General community report pattern suggests monitoring")

    return {
        "main_support": main_support,
        "confidence": round(top_score, 2),
        "predictions": {
            "parasite_treatment": round(parasite_probability, 2),
            "scabies_treatment": round(scabies_probability, 2),
            "followup_visit": round(followup_probability, 2),
        },
        "reasons": reasons,
        "recommended_action": "Review report and schedule community follow-up if needed.",
    }
