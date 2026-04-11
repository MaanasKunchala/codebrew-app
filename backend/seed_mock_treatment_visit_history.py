import sqlite3
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

DB_PATH = Path(__file__).parent / "database" / "reports.db"

REGION_NAME = "West Arnhem Land"

COMMUNITIES = [
    ("Maningrida", 120, "difficult", 950),
    ("Gunbalanya", 70, "moderate", 700),
    ("Warruwi", 180, "difficult", 620),
    ("Jabiru", 40, "easy", 480),
    ("Milingimbi", 210, "difficult", 760),
    ("Ramingining", 190, "difficult", 810),
    ("Minjilang", 230, "difficult", 540),
    ("Outstation A", 95, "moderate", 430),
    ("Outstation B", 105, "difficult", 520),
    ("Croker Camp", 160, "difficult", 600),
]

SEASON_BY_MONTH = {
    1: "Kudjewk",
    2: "Kudjewk",
    3: "Kudjewk",
    4: "Bangkerreng",
    5: "Yekke",
    6: "Yekke",
    7: "Wurrkeng",
    8: "Wurrkeng",
    9: "Kurrung",
    10: "Kurrung",
    11: "Kunumeleng",
    12: "Kudjewk",
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_region_id(cursor, region_name):
    cursor.execute("SELECT id FROM regions WHERE name = ?", (region_name,))
    row = cursor.fetchone()
    return row[0] if row else None


def treatment_pct_for_category(category, season_name, road_access):
    if category == "parasite":
        base = {
            "Kudjewk": 16,
            "Bangkerreng": 13,
            "Yekke": 9,
            "Wurrkeng": 6,
            "Kurrung": 8,
            "Kunumeleng": 14,
        }[season_name]
    elif category == "scabies":
        base = {
            "Kudjewk": 7,
            "Bangkerreng": 6,
            "Yekke": 5,
            "Wurrkeng": 4,
            "Kurrung": 5,
            "Kunumeleng": 8,
        }[season_name]
    elif category == "desexing":
        base = {
            "Kudjewk": 4,
            "Bangkerreng": 5,
            "Yekke": 6,
            "Wurrkeng": 7,
            "Kurrung": 6,
            "Kunumeleng": 5,
        }[season_name]
    else:
        base = 5

    if road_access == "difficult":
        base -= 1.0
    elif road_access == "easy":
        base += 1.0

    return max(1.0, base + random.uniform(-1.5, 1.5))


def main():
    conn = get_connection()
    cursor = conn.cursor()

    region_id = get_region_id(cursor, REGION_NAME)
    if region_id is None:
        print(f"Region '{REGION_NAME}' not found.")
        conn.close()
        return

    # optional cleanup so reseeding doesn't duplicate
    cursor.execute("DELETE FROM treatment_records")
    cursor.execute("DELETE FROM veterinary_visits")

    start_date = date(2022, 1, 15)
    end_date = date(2026, 3, 15)

    for community_name, distance_to_clinic, road_access, est_total_dogs in COMMUNITIES:
        current = start_date + timedelta(days=random.randint(0, 25))

        while current <= end_date:
            season_name = SEASON_BY_MONTH[current.month]

            visit_type = random.choice(
                ["routine outreach", "seasonal response visit", "follow-up visit"]
            )

            visit_notes = f"Mock historical visit during {season_name}"

            cursor.execute(
                """
                INSERT INTO veterinary_visits (
                    region_id,
                    community_name,
                    visit_date,
                    visit_type,
                    notes
                )
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    region_id,
                    community_name,
                    current.isoformat(),
                    visit_type,
                    visit_notes,
                ),
            )

            visit_id = cursor.lastrowid

            for category in ["parasite", "scabies", "desexing"]:
                pct = treatment_pct_for_category(category, season_name, road_access)

                if category == "desexing":
                    # desexing is usually lower-volume than broad parasite treatment
                    dogs_treated = max(
                        0,
                        int(
                            round(
                                est_total_dogs
                                * (pct / 100.0)
                                * random.uniform(0.6, 0.9)
                            )
                        ),
                    )
                else:
                    dogs_treated = max(
                        0,
                        int(
                            round(
                                est_total_dogs
                                * (pct / 100.0)
                                * random.uniform(0.8, 1.1)
                            )
                        ),
                    )

                dogs_treated = min(dogs_treated, est_total_dogs)

                cursor.execute(
                    """
                    INSERT INTO treatment_records (
                        visit_id,
                        treatment_category,
                        dogs_treated_count,
                        estimated_total_dogs,
                        treatment_percentage,
                        notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        visit_id,
                        category,
                        dogs_treated,
                        est_total_dogs,
                        round((dogs_treated / est_total_dogs) * 100, 2),
                        f"Mock {category} treatment history",
                    ),
                )

            current += timedelta(days=random.randint(75, 130))

    conn.commit()
    conn.close()
    print("Mock veterinary visit history seeded successfully.")


if __name__ == "__main__":
    main()
