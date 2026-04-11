from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import sqlite3
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = Path(__file__).parent / "database" / "reports.db"


class RegionCreate(BaseModel):
    name: str
    state: Optional[str] = ""
    notes: Optional[str] = ""


class Report(BaseModel):
    community_name: str
    region_name: str
    reporter_type: str
    local_season: str
    rainfall_level: str
    road_access: str
    seasonal_indicators: List[str]
    num_dogs_seen: int
    num_puppies_seen: int
    skin_issue_count: int
    parasite_issue_count: int
    dog_roaming_level: str
    recent_dog_deaths: int
    distance_to_clinic: int
    requested_help: bool
    notes: Optional[str] = ""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@app.post("/regions")
def create_region(region: RegionCreate):
    conn = get_connection()
    cursor = conn.cursor()

    # Check if region already exists
    cursor.execute(
        "SELECT id, name, state, notes FROM regions WHERE LOWER(name) = LOWER(?)",
        (region.name,),
    )
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {
            "id": existing[0],
            "name": existing[1],
            "state": existing[2],
            "notes": existing[3],
            "message": "Region already exists",
        }

    cursor.execute(
        """
        INSERT INTO regions (name, state, notes)
        VALUES (?, ?, ?)
    """,
        (region.name, region.state, region.notes),
    )

    region_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": region_id,
        "name": region.name,
        "state": region.state,
        "notes": region.notes,
        "message": "Region created successfully",
    }


def get_region_id_by_name(cursor, region_name: str):
    cursor.execute("SELECT id FROM regions WHERE name = ?", (region_name,))
    row = cursor.fetchone()
    return row[0] if row else None


def get_season_id(cursor, region_id: int, season_name: str):
    cursor.execute(
        """
        SELECT id
        FROM seasons
        WHERE region_id = ? AND LOWER(name) = LOWER(?)
    """,
        (region_id, season_name),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_season_treatment_guidance(cursor, season_id: int):
    cursor.execute(
        """
        SELECT
            p.name AS parasite_name,
            t.treatment_name,
            t.active_ingredients,
            spt.risk_level,
            spt.trigger_notes,
            spt.recommendation_notes
        FROM season_parasite_treatments spt
        JOIN parasites p ON spt.parasite_id = p.id
        JOIN treatments t ON spt.treatment_id = t.id
        WHERE spt.season_id = ?
    """,
        (season_id,),
    )
    rows = cursor.fetchall()

    guidance = []
    for row in rows:
        guidance.append(
            {
                "parasite": row[0],
                "treatment_name": row[1],
                "active_ingredients": row[2],
                "risk_level": row[3],
                "trigger_notes": row[4],
                "recommendation_notes": row[5],
            }
        )

    return guidance


@app.get("/")
def root():
    return {"message": "WALDHeP backend running"}


@app.get("/regions")
def get_regions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name
        FROM regions
        ORDER BY name
    """
    )
    rows = cursor.fetchall()
    conn.close()

    return [{"id": row[0], "name": row[1]} for row in rows]


@app.post("/submit-report")
def submit_report(report: Report):
    conn = get_connection()
    cursor = conn.cursor()

    region_id = get_region_id_by_name(cursor, report.region_name)
    season_id = (
        get_season_id(cursor, region_id, report.local_season) if region_id else None
    )
    seasonal_guidance = (
        get_season_treatment_guidance(cursor, season_id) if season_id else []
    )

    seasonal_indicators_text = ", ".join(report.seasonal_indicators)
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO community_reports (
            community_name,
            region_id,
            report_date,
            reporter_type,
            local_season,
            rainfall_level,
            road_access,
            seasonal_indicators_text,
            num_dogs_seen,
            num_puppies_seen,
            skin_issue_count,
            parasite_issue_count,
            recent_dog_deaths,
            distance_to_clinic,
            dog_roaming_level,
            requested_help,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            report.community_name,
            region_id,
            report_date,
            report.reporter_type,
            report.local_season,
            report.rainfall_level,
            report.road_access,
            seasonal_indicators_text,
            report.num_dogs_seen,
            report.num_puppies_seen,
            report.skin_issue_count,
            report.parasite_issue_count,
            report.recent_dog_deaths,
            report.distance_to_clinic,
            report.dog_roaming_level,
            1 if report.requested_help else 0,
            report.notes,
        ),
    )

    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

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
        "report_id": report_id,
        "main_support": main_support,
        "confidence": round(top_score, 2),
        "predictions": {
            "parasite_treatment": round(parasite_probability, 2),
            "scabies_treatment": round(scabies_probability, 2),
            "followup_visit": round(followup_probability, 2),
        },
        "reasons": reasons,
        "recommended_action": "Review report and schedule community follow-up if needed.",
        "seasonal_guidance": seasonal_guidance,
    }
