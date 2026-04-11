import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "reports.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS veterinary_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_id INTEGER NOT NULL,
        community_name TEXT NOT NULL,
        visit_date TEXT NOT NULL,
        visit_type TEXT,
        notes TEXT,
        FOREIGN KEY (region_id) REFERENCES regions(id)
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS treatment_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        visit_id INTEGER NOT NULL,
        treatment_category TEXT NOT NULL,
        dogs_treated_count INTEGER NOT NULL,
        estimated_total_dogs INTEGER NOT NULL,
        treatment_percentage REAL NOT NULL,
        notes TEXT,
        FOREIGN KEY (visit_id) REFERENCES veterinary_visits(id) ON DELETE CASCADE
    )
    """
    )

    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_veterinary_visits_region_community_date
    ON veterinary_visits(region_id, community_name, visit_date)
    """
    )

    cursor.execute(
        """
    CREATE INDEX IF NOT EXISTS idx_treatment_records_visit_category
    ON treatment_records(visit_id, treatment_category)
    """
    )

    conn.commit()
    conn.close()
    print("Treatment history tables added successfully.")


if __name__ == "__main__":
    main()
