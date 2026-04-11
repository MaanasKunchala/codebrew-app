import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGION_ID = 1
REGION_NAME = "West Arnhem Land"

COMMUNITIES = [
    ("Maningrida", 120, "difficult"),
    ("Gunbalanya", 70, "moderate"),
    ("Warruwi", 180, "difficult"),
    ("Jabiru", 40, "easy"),
    ("Milingimbi", 210, "difficult"),
    ("Ramingining", 190, "difficult"),
    ("Minjilang", 230, "difficult"),
    ("Outstation A", 95, "moderate"),
    ("Outstation B", 105, "difficult"),
    ("Croker Camp", 160, "difficult"),
]

SEASON_LOOKUP = {
    "Kudjewk": {"rain": 0.95, "humidity": 0.95},
    "Bangkerreng": {"rain": 0.75, "humidity": 0.70},
    "Yekke": {"rain": 0.35, "humidity": 0.40},
    "Wurrkeng": {"rain": 0.15, "humidity": 0.20},
    "Kurrung": {"rain": 0.10, "humidity": 0.35},
    "Kunumeleng": {"rain": 0.65, "humidity": 0.85},
}


def season_for_month(month: int) -> str:
    if month in (12, 1, 2, 3):
        return "Kudjewk"
    if month == 4:
        return "Bangkerreng"
    if month in (5, 6):
        return "Yekke"
    if month in (7, 8):
        return "Wurrkeng"
    if month in (9, 10):
        return "Kurrung"
    return "Kunumeleng"


def clamp(value, low, high):
    return max(low, min(high, value))


def weighted_choice(options):
    total = sum(options.values())
    r = random.random() * total
    upto = 0
    for key, weight in options.items():
        upto += weight
        if upto >= r:
            return key
    return list(options.keys())[-1]


def logistic(x):
    return 1 / (1 + math.exp(-x))


def noisy_count(mean_value):
    return max(0, int(round(random.gauss(mean_value, max(1.0, mean_value * 0.35)))))


def choose_rainfall(season_name):
    rain = SEASON_LOOKUP[season_name]["rain"]
    if rain > 0.8:
        return weighted_choice({"high": 0.70, "medium": 0.25, "low": 0.05})
    if rain > 0.55:
        return weighted_choice({"high": 0.45, "medium": 0.40, "low": 0.15})
    if rain > 0.25:
        return weighted_choice({"high": 0.15, "medium": 0.45, "low": 0.40})
    return weighted_choice({"high": 0.05, "medium": 0.25, "low": 0.70})


def choose_roaming(season_name, road_access):
    weights = {"low": 0.20, "medium": 0.45, "high": 0.35}
    if season_name in ("Kudjewk", "Kunumeleng"):
        weights["high"] += 0.10
    if road_access == "difficult":
        weights["high"] += 0.05
    return weighted_choice(weights)


def build_indicators(season_name, rainfall_level, roaming):
    indicators = []
    if season_name == "Kudjewk":
        indicators += ["monsoon_building", "flooded_ground", "mosquitoes_high"]
    elif season_name == "Bangkerreng":
        indicators += ["storm_tail", "wet_ground"]
    elif season_name == "Yekke":
        indicators += ["cooler_mornings", "surface_water_remaining"]
    elif season_name == "Wurrkeng":
        indicators += ["cool_dry", "low_humidity"]
    elif season_name == "Kurrung":
        indicators += ["hot_dry", "thunderclouds_building"]
    elif season_name == "Kunumeleng":
        indicators += ["humid_build_up", "afternoon_storms", "mosquitoes_rising"]

    if rainfall_level == "high":
        indicators.append("standing_water")
    if roaming == "high":
        indicators.append("dog_movement_high")

    return ", ".join(indicators)


def main():
    rows = []
    report_id = 1

    start_date = date(2022, 1, 1)
    end_date = date(2025, 12, 31)

    for community_name, distance_to_clinic, road_access in COMMUNITIES:
        base_dog_population = random.randint(400, 1200)
        current = date(2022, 1, random.randint(1, 20))
        months_since_last_visit = random.randint(1, 4)

        while current <= end_date:
            season_name = season_for_month(current.month)
            rainfall_level = choose_rainfall(season_name)
            roaming = choose_roaming(season_name, road_access)
            humidity = SEASON_LOOKUP[season_name]["humidity"]

            num_dogs_seen = clamp(
                noisy_count(base_dog_population * random.uniform(0.05, 0.14)), 20, 180
            )

            puppy_multiplier = {
                "Kudjewk": 1.25,
                "Bangkerreng": 1.05,
                "Yekke": 0.90,
                "Wurrkeng": 0.75,
                "Kurrung": 0.85,
                "Kunumeleng": 1.15,
            }[season_name]

            num_puppies_seen = clamp(
                noisy_count((num_dogs_seen * 0.12) * puppy_multiplier), 0, 40
            )

            wet_boost = (
                1
                if rainfall_level == "high"
                else 0.5 if rainfall_level == "medium" else 0.1
            )

            skin_issue_count = clamp(
                noisy_count(2 + humidity * 4 + (0.8 if roaming == "high" else 0)), 0, 25
            )

            parasite_issue_count = clamp(
                noisy_count(2 + wet_boost * 5 + (1.0 if num_puppies_seen > 10 else 0)),
                0,
                30,
            )

            recent_dog_deaths = clamp(
                noisy_count(
                    0.2 + parasite_issue_count * 0.05 + skin_issue_count * 0.03
                ),
                0,
                8,
            )

            requested_help = (
                1
                if (
                    parasite_issue_count >= 7
                    or skin_issue_count >= 6
                    or recent_dog_deaths >= 2
                    or months_since_last_visit >= 5
                )
                else 0
            )

            indicators = build_indicators(season_name, rainfall_level, roaming)

            # probability model
            access_penalty = (
                0.25
                if road_access == "difficult"
                else 0.10 if road_access == "moderate" else 0.0
            )
            distance_penalty = min(0.30, distance_to_clinic / 1000.0)
            puppy_signal = num_puppies_seen / 18.0
            parasite_signal = parasite_issue_count / 10.0
            skin_signal = skin_issue_count / 9.0
            death_signal = recent_dog_deaths / 3.0
            help_signal = 0.35 if requested_help else 0.0
            visit_signal = months_since_last_visit / 5.0

            p_parasite_3 = logistic(
                -1.2
                + parasite_signal
                + puppy_signal
                + wet_boost * 0.8
                + access_penalty
                + help_signal
                + visit_signal * 0.5
            )
            p_scabies_3 = logistic(
                -1.4
                + skin_signal
                + humidity * 0.8
                + access_penalty
                + death_signal * 0.3
                + help_signal
            )
            p_followup_3 = logistic(
                -1.0
                + parasite_signal * 0.4
                + skin_signal * 0.4
                + death_signal * 0.5
                + help_signal
                + access_penalty
                + distance_penalty
                + visit_signal * 0.7
            )

            p_parasite_6 = logistic(
                -1.0
                + parasite_signal * 0.7
                + puppy_signal * 0.5
                + wet_boost * 0.7
                + visit_signal * 0.4
                + distance_penalty
            )
            p_scabies_6 = logistic(
                -1.15 + skin_signal * 0.75 + humidity * 0.65 + access_penalty + 0.1
            )
            p_followup_6 = logistic(
                -0.85
                + parasite_signal * 0.35
                + skin_signal * 0.35
                + distance_penalty
                + access_penalty
                + visit_signal * 0.5
                + help_signal * 0.7
            )

            p_parasite_9 = logistic(
                -0.9
                + parasite_signal * 0.55
                + puppy_signal * 0.45
                + wet_boost * 0.55
                + distance_penalty
                + 0.15
            )
            p_scabies_9 = logistic(
                -1.05 + skin_signal * 0.60 + humidity * 0.55 + access_penalty + 0.15
            )
            p_followup_9 = logistic(
                -0.75
                + parasite_signal * 0.3
                + skin_signal * 0.3
                + distance_penalty
                + access_penalty
                + visit_signal * 0.45
                + 0.1
            )

            p_parasite_12 = logistic(
                -0.85
                + parasite_signal * 0.45
                + puppy_signal * 0.35
                + wet_boost * 0.45
                + distance_penalty
                + 0.20
            )
            p_scabies_12 = logistic(
                -1.0 + skin_signal * 0.50 + humidity * 0.45 + access_penalty + 0.2
            )
            p_followup_12 = logistic(
                -0.65
                + parasite_signal * 0.25
                + skin_signal * 0.25
                + distance_penalty
                + access_penalty
                + visit_signal * 0.4
                + 0.15
            )

            def label(p):
                return 1 if random.random() < p else 0

            rows.append(
                {
                    "report_id": report_id,
                    "community_name": community_name,
                    "region_id": REGION_ID,
                    "report_date": current.isoformat(),
                    "reporter_type": weighted_choice(
                        {"ranger": 0.75, "waldhep_staff": 0.15, "veterinarian": 0.10}
                    ),
                    "local_season": season_name,
                    "rainfall_level": rainfall_level,
                    "road_access": road_access,
                    "seasonal_indicators_text": indicators,
                    "num_dogs_seen": num_dogs_seen,
                    "num_puppies_seen": num_puppies_seen,
                    "skin_issue_count": skin_issue_count,
                    "parasite_issue_count": parasite_issue_count,
                    "recent_dog_deaths": recent_dog_deaths,
                    "distance_to_clinic": distance_to_clinic,
                    "dog_roaming_level": roaming,
                    "requested_help": requested_help,
                    "notes": "Synthetic ranger field report",
                    "months_since_last_visit": months_since_last_visit,
                    "needs_parasite_treatment_3m": label(p_parasite_3),
                    "needs_scabies_treatment_3m": label(p_scabies_3),
                    "needs_followup_visit_3m": label(p_followup_3),
                    "needs_parasite_treatment_6m": label(p_parasite_6),
                    "needs_scabies_treatment_6m": label(p_scabies_6),
                    "needs_followup_visit_6m": label(p_followup_6),
                    "needs_parasite_treatment_9m": label(p_parasite_9),
                    "needs_scabies_treatment_9m": label(p_scabies_9),
                    "needs_followup_visit_9m": label(p_followup_9),
                    "needs_parasite_treatment_12m": label(p_parasite_12),
                    "needs_scabies_treatment_12m": label(p_scabies_12),
                    "needs_followup_visit_12m": label(p_followup_12),
                }
            )

            current += timedelta(days=random.randint(25, 40))
            months_since_last_visit = clamp(
                months_since_last_visit + random.choice([0, 1, 1, 2]), 1, 9
            )
            if requested_help and random.random() < 0.35:
                months_since_last_visit = 1

            report_id += 1

    rows = sorted(rows, key=lambda r: r["report_date"])
    split_index = int(len(rows) * 0.8)
    train_rows = rows[:split_index]
    test_rows = rows[split_index:]

    def write_csv(path, data):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)

    write_csv(OUTPUT_DIR / "mock_training_dataset_full.csv", rows)
    write_csv(OUTPUT_DIR / "mock_training_dataset_train.csv", train_rows)
    write_csv(OUTPUT_DIR / "mock_training_dataset_test.csv", test_rows)

    print(f"Full rows: {len(rows)}")
    print(f"Train rows: {len(train_rows)}")
    print(f"Test rows: {len(test_rows)}")
    print(f"Saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
