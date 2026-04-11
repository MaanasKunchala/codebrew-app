from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import sqlite3
from datetime import datetime
import joblib
import pandas as pd
from contextlib import asynccontextmanager
import sys
from fastapi import HTTPException

DB_PATH = Path(__file__).parent / "database" / "reports.db"
MODEL_PATH = Path(__file__).parent / "model" / "wrapped_XGB_model.joblib"
MODEL_DIR = Path(__file__).parent / "model"
if str(MODEL_DIR) not in sys.path:
    sys.path.append(str(MODEL_DIR))

ml_model = None


def load_ml_model():
    global ml_model
    ml_model = joblib.load(MODEL_PATH)
    print(f"ML model loaded from {MODEL_PATH}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_ml_model()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


"""
@app.get("/debug-model")
def debug_model():
    return {"model_type": str(type(ml_model)), "model_repr": str(ml_model)}
"""


def build_support_summary_from_values(
    num_puppies_seen: int,
    skin_issue_count: int,
    parasite_issue_count: int,
    rainfall_level: str,
):
    parasite_probability = min(0.95, 0.25 + parasite_issue_count * 0.08)
    scabies_probability = min(0.95, 0.20 + skin_issue_count * 0.08)
    followup_probability = min(0.95, 0.15 + num_puppies_seen * 0.04)

    main_support = "Parasite treatment"
    top_score = parasite_probability

    if scabies_probability > top_score:
        main_support = "Scabies treatment"
        top_score = scabies_probability

    if followup_probability > top_score:
        main_support = "Follow-up visit"
        top_score = followup_probability

    reasons = []
    if num_puppies_seen >= 5:
        reasons.append("High puppy numbers reported")
    if skin_issue_count >= 3:
        reasons.append("Multiple dogs with skin issues")
    if parasite_issue_count >= 3:
        reasons.append("Multiple parasite-related issues reported")
    if str(rainfall_level).lower() in ["high", "heavy"]:
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


def get_historical_treatment_trends(cursor, region_id: int, community_name: str):
    cursor.execute(
        """
        SELECT
            vv.visit_date,
            tr.treatment_category,
            tr.treatment_percentage
        FROM veterinary_visits vv
        JOIN treatment_records tr ON vv.id = tr.visit_id
        WHERE vv.region_id = ? AND vv.community_name = ?
        ORDER BY vv.visit_date ASC
    """,
        (region_id, community_name),
    )

    rows = cursor.fetchall()

    trends = {"parasite": [], "scabies": [], "desexing": []}

    cumulative = {"parasite": 0.0, "scabies": 0.0, "desexing": 0.0}

    for visit_date, category, pct in rows:
        if category not in trends:
            continue

        cumulative[category] = min(100.0, cumulative[category] + pct)

        trends[category].append(
            {
                "date": visit_date,
                "percentage": round(pct, 2),
                "cumulative_percentage": round(cumulative[category], 2),
            }
        )
    return trends


def estimate_desexing_projection(report, historical_trends):
    roaming_factor = {"low": 0.2, "medium": 0.5, "high": 1.0}.get(
        report.dog_roaming_level.lower(), 0.5
    )

    puppy_ratio = report.num_puppies_seen / max(report.num_dogs_seen, 1)
    months_since_last_visit_factor = min(
        1.0, 4 / 12
    )  # placeholder until this field is in runtime report
    previous_desexing_factor = 1.0

    if historical_trends["desexing"]:
        last_cumulative = historical_trends["desexing"][-1]["cumulative_percentage"]
        previous_desexing_factor = max(0.0, 1 - min(last_cumulative / 100, 1.0))

    current_prob = min(
        0.95,
        0.20
        + 0.40 * puppy_ratio
        + 0.20 * roaming_factor
        + 0.20 * months_since_last_visit_factor
        + 0.20 * previous_desexing_factor,
    )

    return {
        "3_months": round(min(0.95, current_prob + 0.05), 2),
        "6_months": round(min(0.95, current_prob + 0.10), 2),
        "9_months": round(min(0.95, current_prob + 0.15), 2),
        "12_months": round(min(0.95, current_prob + 0.20), 2),
    }


@app.get("/")
def root():
    return {"message": "WALDHeP backend running"}


@app.get("/latest-insight")
def get_latest_insight(region_name: str):
    conn = get_connection()
    cursor = conn.cursor()

    region_id = get_region_id_by_name(cursor, region_name)
    if region_id is None:
        conn.close()
        raise HTTPException(
            status_code=404, detail=f"Region '{region_name}' not found."
        )

    cursor.execute(
        """
        SELECT
            id,
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
        FROM community_reports
        WHERE region_id = ?
        ORDER BY datetime(report_date) DESC, id DESC
        LIMIT 1
        """,
        (region_id,),
    )

    report_row = cursor.fetchone()

    if not report_row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"No community reports found yet for region '{region_name}'.",
        )

    report_payload = {
        "report_id": report_row[0],
        "community_name": report_row[1],
        "region_name": region_name,
        "region_id": report_row[2],
        "report_date": report_row[3],
        "reporter_type": report_row[4],
        "local_season": report_row[5],
        "rainfall_level": report_row[6],
        "road_access": report_row[7],
        "seasonal_indicators": [
            item.strip() for item in (report_row[8] or "").split(",") if item.strip()
        ],
        "num_dogs_seen": report_row[9],
        "num_puppies_seen": report_row[10],
        "skin_issue_count": report_row[11],
        "parasite_issue_count": report_row[12],
        "recent_dog_deaths": report_row[13],
        "distance_to_clinic": report_row[14],
        "dog_roaming_level": report_row[15],
        "requested_help": bool(report_row[16]),
        "notes": report_row[17] or "",
    }

    cursor.execute(
        """
        SELECT
            parasite_3m,
            scabies_3m,
            followup_3m,
            parasite_6m,
            scabies_6m,
            followup_6m,
            parasite_9m,
            scabies_9m,
            followup_9m,
            parasite_12m,
            scabies_12m,
            followup_12m,
            desexing_3m,
            desexing_6m,
            desexing_9m,
            desexing_12m,
            created_at
        FROM ml_predictions
        WHERE report_id = ?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 1
        """,
        (report_payload["report_id"],),
    )

    ml_row = cursor.fetchone()

    ml_predictions = {}
    desexing_projection = {}

    if ml_row:
        ml_predictions = {
            "needs_parasite_treatment_3m": ml_row[0],
            "needs_scabies_treatment_3m": ml_row[1],
            "needs_followup_visit_3m": ml_row[2],
            "needs_parasite_treatment_6m": ml_row[3],
            "needs_scabies_treatment_6m": ml_row[4],
            "needs_followup_visit_6m": ml_row[5],
            "needs_parasite_treatment_9m": ml_row[6],
            "needs_scabies_treatment_9m": ml_row[7],
            "needs_followup_visit_9m": ml_row[8],
            "needs_parasite_treatment_12m": ml_row[9],
            "needs_scabies_treatment_12m": ml_row[10],
            "needs_followup_visit_12m": ml_row[11],
        }

        desexing_projection = {
            "3_months": ml_row[12],
            "6_months": ml_row[13],
            "9_months": ml_row[14],
            "12_months": ml_row[15],
        }
    else:
        historical_trends = get_historical_treatment_trends(
            cursor, region_id, report_payload["community_name"]
        )
        temp_report = type("TempReport", (), report_payload)
        desexing_projection = estimate_desexing_projection(
            temp_report, historical_trends
        )

    season_id = get_season_id(cursor, region_id, report_payload["local_season"])
    seasonal_guidance = (
        get_season_treatment_guidance(cursor, season_id) if season_id else []
    )
    historical_trends = get_historical_treatment_trends(
        cursor, region_id, report_payload["community_name"]
    )

    summary = build_support_summary_from_values(
        num_puppies_seen=report_payload["num_puppies_seen"],
        skin_issue_count=report_payload["skin_issue_count"],
        parasite_issue_count=report_payload["parasite_issue_count"],
        rainfall_level=report_payload["rainfall_level"],
    )

    conn.close()

    result_payload = {
        **summary,
        "ml_predictions": ml_predictions,
        "seasonal_guidance": seasonal_guidance,
        "historical_treatment_trends": historical_trends,
        "desexing_projection": desexing_projection,
    }

    return {
        "report": report_payload,
        "result": result_payload,
    }


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


@app.get("/local-seasons")
def get_local_seasons():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, name
        FROM seasons
        ORDER BY name
    """
    )
    rows = cursor.fetchall()
    conn.close()

    return [{"id": row[0], "name": row[1]} for row in rows]


"""
def build_model_input(report: Report):
    conn = get_connection()
    cursor = conn.cursor()
    region_id = get_region_id_by_name(cursor, report.region_name)
    data = {
        "community_name": [report.community_name],
        "region_id": [region_id],
        "local_season": [report.local_season],
        "rainfall_level": [report.rainfall_level],
        "road_access": [report.road_access],
        "seasonal_indicators_text": [", ".join(report.seasonal_indicators)],
        "num_dogs_seen": [report.num_dogs_seen],
        "num_puppies_seen": [report.num_puppies_seen],
        "skin_issue_count": [report.skin_issue_count],
        "parasite_issue_count": [report.parasite_issue_count],
        "recent_dog_deaths": [report.recent_dog_deaths],
        "distance_to_clinic": [report.distance_to_clinic],
        "dog_roaming_level": [report.dog_roaming_level],
        "requested_help": [1 if report.requested_help else 0],
        "months_since_last_visit": [4],  # placeholder for now
    }
    return pd.DataFrame(data)
"""

"""
@app.get("/debug-predict")
def debug_predict():
    conn = get_connection()
    cursor = conn.cursor()

    region_id = get_region_id_by_name(cursor, "West Arnhem Land")

    sample = pd.DataFrame(
        [
            {
                "community_name": "Maningrida",
                "region_id": region_id,
                "local_season": "Kudjewk",
                "rainfall_level": "high",
                "road_access": "difficult",
                "num_dogs_seen": 24,
                "num_puppies_seen": 7,
                "skin_issue_count": 4,
                "parasite_issue_count": 5,
                "recent_dog_deaths": 1,
                "distance_to_clinic": 120,
                "dog_roaming_level": "high",
                "requested_help": 1,
            }
        ]
    )

    conn.close()

    result = {}

    try:
        pred = ml_model.predict(sample)
        result["predict"] = pred.to_dict(orient="records")
    except Exception as e:
        result["predict_error"] = str(e)

    return result
*/
"""


def get_ml_predictions(report: Report, region_id: int):
    model_input = pd.DataFrame(
        [
            {
                "community_name": report.community_name,
                "region_id": region_id,
                "local_season": report.local_season,
                "rainfall_level": report.rainfall_level,
                "road_access": report.road_access,
                "num_dogs_seen": report.num_dogs_seen,
                "num_puppies_seen": report.num_puppies_seen,
                "skin_issue_count": report.skin_issue_count,
                "parasite_issue_count": report.parasite_issue_count,
                "recent_dog_deaths": report.recent_dog_deaths,
                "distance_to_clinic": report.distance_to_clinic,
                "dog_roaming_level": report.dog_roaming_level,
                "requested_help": 1 if report.requested_help else 0,
            }
        ]
    )

    prediction_df = ml_model.predict(model_input)

    return prediction_df.iloc[0].to_dict()


@app.post("/submit-report")
def submit_report(report: Report):
    conn = get_connection()
    cursor = conn.cursor()

    region_id = get_region_id_by_name(cursor, report.region_name)

    ml_predictions = get_ml_predictions(report, region_id)

    season_id = (
        get_season_id(cursor, region_id, report.local_season) if region_id else None
    )
    seasonal_guidance = (
        get_season_treatment_guidance(cursor, season_id) if season_id else []
    )

    historical_trends = get_historical_treatment_trends(
        cursor, region_id, report.community_name
    )

    desexing_projection = estimate_desexing_projection(report, historical_trends)

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
    cursor.execute(
        """
    INSERT INTO ml_predictions (
        report_id,
        parasite_3m,
        scabies_3m,
        followup_3m,
        parasite_6m,
        scabies_6m,
        followup_6m,
        parasite_9m,
        scabies_9m,
        followup_9m,
        parasite_12m,
        scabies_12m,
        followup_12m,
        desexing_3m,
        desexing_6m,
        desexing_9m,
        desexing_12m,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            report_id,
            ml_predictions["needs_parasite_treatment_3m"],
            ml_predictions["needs_scabies_treatment_3m"],
            ml_predictions["needs_followup_visit_3m"],
            ml_predictions["needs_parasite_treatment_6m"],
            ml_predictions["needs_scabies_treatment_6m"],
            ml_predictions["needs_followup_visit_6m"],
            ml_predictions["needs_parasite_treatment_9m"],
            ml_predictions["needs_scabies_treatment_9m"],
            ml_predictions["needs_followup_visit_9m"],
            ml_predictions["needs_parasite_treatment_12m"],
            ml_predictions["needs_scabies_treatment_12m"],
            ml_predictions["needs_followup_visit_12m"],
            desexing_projection["3_months"],
            desexing_projection["6_months"],
            desexing_projection["9_months"],
            desexing_projection["12_months"],
            report_date,
        ),
    )
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
        "region_name": report.region_name,
        "main_support": main_support,
        "confidence": round(top_score, 2),
        "predictions": {
            "parasite_treatment": round(parasite_probability, 2),
            "scabies_treatment": round(scabies_probability, 2),
            "followup_visit": round(followup_probability, 2),
        },
        "ml_predictions": ml_predictions,
        "reasons": reasons,
        "recommended_action": "Review report and schedule community follow-up if needed.",
        "seasonal_guidance": seasonal_guidance,
        "historical_treatment_trends": historical_trends,
        "desexing_projection": desexing_projection,
    }
