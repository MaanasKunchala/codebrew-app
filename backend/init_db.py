import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "reports.db"


def create_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS regions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        state TEXT,
        notes TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS seasons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        approx_months TEXT,
        temperature_range TEXT,
        source TEXT,
        notes TEXT,
        FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE CASCADE,
        UNIQUE(region_id, name)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS season_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season_id INTEGER NOT NULL,
        observation_type TEXT NOT NULL,
        observation_text TEXT NOT NULL,
        FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE CASCADE
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS parasites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        parasite_group TEXT,
        notes TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        treatment_name TEXT NOT NULL,
        active_ingredients TEXT,
        treatment_type TEXT,
        notes TEXT,
        UNIQUE(treatment_name, active_ingredients)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS season_parasite_treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        season_id INTEGER NOT NULL,
        parasite_id INTEGER NOT NULL,
        treatment_id INTEGER NOT NULL,
        risk_level TEXT,
        trigger_notes TEXT,
        recommendation_notes TEXT,
        FOREIGN KEY (season_id) REFERENCES seasons(id) ON DELETE CASCADE,
        FOREIGN KEY (parasite_id) REFERENCES parasites(id) ON DELETE CASCADE,
        FOREIGN KEY (treatment_id) REFERENCES treatments(id) ON DELETE CASCADE,
        UNIQUE(season_id, parasite_id, treatment_id)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS community_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        community_name TEXT NOT NULL,
        region_id INTEGER,
        report_date TEXT NOT NULL,
        reporter_type TEXT NOT NULL,
        local_season TEXT,
        rainfall_level TEXT,
        road_access TEXT,
        seasonal_indicators_text TEXT,
        num_dogs_seen INTEGER NOT NULL,
        num_puppies_seen INTEGER NOT NULL,
        skin_issue_count INTEGER NOT NULL,
        parasite_issue_count INTEGER NOT NULL,
        recent_dog_deaths INTEGER NOT NULL,
        distance_to_clinic INTEGER NOT NULL,
        dog_roaming_level TEXT NOT NULL,
        requested_help INTEGER NOT NULL DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS ml_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER NOT NULL,
        horizon_months INTEGER NOT NULL,
        predicted_parasite_id INTEGER,
        predicted_treatment_id INTEGER,
        predicted_probability REAL NOT NULL,
        predicted_risk_level TEXT,
        recommended_action TEXT,
        top_reason_1 TEXT,
        top_reason_2 TEXT,
        top_reason_3 TEXT,
        model_version TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (report_id) REFERENCES community_reports(id) ON DELETE CASCADE,
        FOREIGN KEY (predicted_parasite_id) REFERENCES parasites(id) ON DELETE SET NULL,
        FOREIGN KEY (predicted_treatment_id) REFERENCES treatments(id) ON DELETE SET NULL
    )
    """
    )

    conn.commit()


def seed_basic_data(conn: sqlite3.Connection):
    cursor = conn.cursor()

    cursor.execute(
        """
    INSERT OR IGNORE INTO regions (name, state, notes)
    VALUES (?, ?, ?)
    """,
        ("West Arnhem Land", "NT", "Starter region for prototype"),
    )

    conn.commit()


def main():
    conn = create_connection()
    create_tables(conn)
    seed_basic_data(conn)
    conn.close()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    main()
