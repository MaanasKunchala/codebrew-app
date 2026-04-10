import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database" / "reports.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_region_id(cursor, region_name):
    cursor.execute("SELECT id FROM regions WHERE name = ?", (region_name,))
    row = cursor.fetchone()
    return row[0] if row else None


def insert_season(
    cursor, region_id, name, approx_months, temperature_range, source="", notes=""
):
    cursor.execute(
        """
        INSERT OR IGNORE INTO seasons (
            region_id, name, approx_months, temperature_range, source, notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (region_id, name, approx_months, temperature_range, source, notes),
    )


def get_season_id(cursor, region_id, season_name):
    cursor.execute(
        """
        SELECT id FROM seasons
        WHERE region_id = ? AND name = ?
    """,
        (region_id, season_name),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def insert_observation(cursor, season_id, observation_type, observation_text):
    cursor.execute(
        """
        SELECT id FROM season_observations
        WHERE season_id = ? AND observation_type = ? AND observation_text = ?
    """,
        (season_id, observation_type, observation_text),
    )
    if cursor.fetchone():
        return

    cursor.execute(
        """
        INSERT INTO season_observations (
            season_id, observation_type, observation_text
        )
        VALUES (?, ?, ?)
    """,
        (season_id, observation_type, observation_text),
    )


def insert_parasite(cursor, name, parasite_group="", notes=""):
    cursor.execute("SELECT id FROM parasites WHERE name = ?", (name,))
    if cursor.fetchone():
        return

    cursor.execute(
        """
        INSERT INTO parasites (name, parasite_group, notes)
        VALUES (?, ?, ?)
    """,
        (name, parasite_group, notes),
    )


def get_parasite_id(cursor, parasite_name):
    cursor.execute("SELECT id FROM parasites WHERE name = ?", (parasite_name,))
    row = cursor.fetchone()
    return row[0] if row else None


def insert_treatment(
    cursor, treatment_name, active_ingredients="", treatment_type="", notes=""
):
    cursor.execute(
        """
        SELECT id FROM treatments
        WHERE treatment_name = ? AND active_ingredients = ?
    """,
        (treatment_name, active_ingredients),
    )
    if cursor.fetchone():
        return

    cursor.execute(
        """
        INSERT INTO treatments (
            treatment_name, active_ingredients, treatment_type, notes
        )
        VALUES (?, ?, ?, ?)
    """,
        (treatment_name, active_ingredients, treatment_type, notes),
    )


def get_treatment_id(cursor, treatment_name, active_ingredients=""):
    cursor.execute(
        """
        SELECT id FROM treatments
        WHERE treatment_name = ? AND active_ingredients = ?
    """,
        (treatment_name, active_ingredients),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def link_season_parasite_treatment(
    cursor,
    season_id,
    parasite_id,
    treatment_id,
    risk_level,
    trigger_notes="",
    recommendation_notes="",
):
    cursor.execute(
        """
        SELECT id FROM season_parasite_treatments
        WHERE season_id = ? AND parasite_id = ? AND treatment_id = ?
    """,
        (season_id, parasite_id, treatment_id),
    )
    if cursor.fetchone():
        return

    cursor.execute(
        """
        INSERT INTO season_parasite_treatments (
            season_id, parasite_id, treatment_id, risk_level, trigger_notes, recommendation_notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (
            season_id,
            parasite_id,
            treatment_id,
            risk_level,
            trigger_notes,
            recommendation_notes,
        ),
    )


def main():
    conn = get_connection()
    cursor = conn.cursor()

    region_name = "West Arnhem Land"
    region_id = get_region_id(cursor, region_name)

    if region_id is None:
        print(f"Region '{region_name}' not found.")
        conn.close()
        return

    seasons_data = [
        {
            "name": "Kudjewk",
            "months": "Dec - Mar",
            "temp": "24-34C",
            "source": "csiro | kakadu | Willie's walkabouts",
            "notes": "Wet season / monsoon period",
            "observations": [
                ("weather", "Moonsoon and heavy rains"),
                ("weather", "thunderstorm, heavy rain, flooding"),
                ("weather", "hot and humid"),
                ("weather", "lush and green, abundance of water sources"),
                (
                    "weather",
                    "averages to raining 2 days out of 3 + a little more than 6 hrs of sun daily",
                ),
                ("weather", "avg min: 24"),
                ("weather", "lowest min: 20"),
                ("weather", "avg max: 33.5"),
                ("weather", "max max: 38"),
                ("resource", "abundance of fruits"),
                ("resource", "eggs and stranded animals for food"),
                ("resource", "explosion of plant and animal life"),
                ("key_note", "speargrass growth"),
                ("key_note", "Wet season data"),
                (
                    "key_note",
                    "reference: https://www.ntvet.com.au/news/category/parasites-worms",
                ),
                ("key_note", "reference: https://theveterinarian.com.au/?p=3451"),
                (
                    "key_note",
                    "reference: https://allpetsvet.com.au/blog/2013/03/28/fleas-and-ticks-in-the-northern-territory/",
                ),
                (
                    "key_note",
                    "reference: http://thetopendermagazine.org.au/post/all-recommendations-for-dogs-and-cats-in-the-top-end",
                ),
            ],
            "risks": [
                {
                    "parasite": "Hookworms",
                    "group": "Internal",
                    "treatment_name": "tick repellents, ehrlichia antibiotics",
                    "active_ingredients": "tick repellents, ehrlichia antibiotics",
                    "treatment_type": "Imported spreadsheet recommendation",
                    "risk": "High",
                    "trigger": "Moonsoon and heavy rains; abundance of fruits",
                    "recommendation": "Filia | tick repellents, ehrlichia antibiotics",
                },
                {
                    "parasite": "Brown dog tick",
                    "group": "External",
                    "treatment_name": "Fipronil products (EFFIPRO, My Flea Guard, Pestigon, Eliminall Fleatix, Frontline Spray, Frontline Plus), fipronil + amitraz (Certifect), fipronil + cyphenothrin (Frontline Tritak, Parastar Plus), permethrin products (Advantix, Bayvantic, Defend, Vectra 3D, etc.), permethrin + imidacloprid (Dominal Max, Advantix), permethrin + indoxacarb (Activyl Tick Plus), flumethrin (Bayticol), pyriprole (Prac-Tic), amitraz + metaflumizone (Pro Meris Duo), etofenprox products.",
                    "active_ingredients": "Fipronil products (EFFIPRO, My Flea Guard, Pestigon, Eliminall Fleatix, Frontline Spray, Frontline Plus), fipronil + amitraz (Certifect), fipronil + cyphenothrin (Frontline Tritak, Parastar Plus), permethrin products (Advantix, Bayvantic, Defend, Vectra 3D, etc.), permethrin + imidacloprid (Dominal Max, Advantix), permethrin + indoxacarb (Activyl Tick Plus), flumethrin (Bayticol), pyriprole (Prac-Tic), amitraz + metaflumizone (Pro Meris Duo), etofenprox products.",
                    "treatment_type": "Tick control",
                    "risk": "High",
                    "trigger": "thunderstorm, heavy rain, flooding; eggs and stranded animals for food",
                    "recommendation": "broad spectrum wormer",
                },
                {
                    "parasite": "Toxocara spp. (roundworms)",
                    "group": "Internal",
                    "treatment_name": "broad spectrum wormer/parasite protection",
                    "active_ingredients": "broad spectrum wormer/parasite protection",
                    "treatment_type": "Worming",
                    "risk": "High",
                    "trigger": "hot and humid; explosion of plant and animal life; speargrass growth",
                    "recommendation": "broad spectrum wormer/parasite protection",
                },
                {
                    "parasite": "fleas (Ctenocephalides felis)",
                    "group": "External",
                    "treatment_name": "Fipronil products (EFFIPRO, My Flea Guard, Pestigon, Eliminall Fleatix, Frontline Spray), fipronil + S-methoprene (Frontline Plus), fipronil + cyphenothrin (Frontline Tritak, Parastar Plus), permethrin products, permethrin + pyriproxyfen (Duogard, Duowin), permethrin + imidacloprid (Advantix, Dominal Max), etofenprox products (Biospot, Zodiac, Ovitrol X-Tend), pyrethrins (Ovitrol Plus, Adams Flea & Tick Spray), pyrethrin + permethrin (Duocide LA), phenothrin + methoprene (Hartz Ultragard Pro), First Shield Trio, Simple Guard 3, K9 Advantix II.",
                    "active_ingredients": "Fipronil products (EFFIPRO, My Flea Guard, Pestigon, Eliminall Fleatix, Frontline Spray), fipronil + S-methoprene (Frontline Plus), fipronil + cyphenothrin (Frontline Tritak, Parastar Plus), permethrin products, permethrin + pyriproxyfen (Duogard, Duowin), permethrin + imidacloprid (Advantix, Dominal Max), etofenprox products (Biospot, Zodiac, Ovitrol X-Tend), pyrethrins (Ovitrol Plus, Adams Flea & Tick Spray), pyrethrin + permethrin (Duocide LA), phenothrin + methoprene (Hartz Ultragard Pro), First Shield Trio, Simple Guard 3, K9 Advantix II.",
                    "treatment_type": "Flea control",
                    "risk": "High",
                    "trigger": "lush and green, abundance of water sources; Wet season data",
                    "recommendation": "flea tablets/spray on",
                },
                {
                    "parasite": "spirometra (tapeworm)",
                    "group": "Internal",
                    "treatment_name": "worming",
                    "active_ingredients": "worming",
                    "treatment_type": "Tapeworm treatment",
                    "risk": "Medium",
                    "trigger": "averages to raining 2 days out of 3 + a little more than 6 hrs of sun daily",
                    "recommendation": "worming",
                },
                {
                    "parasite": "heartworm (from mosquitos)",
                    "group": "Internal",
                    "treatment_name": "monthly tablet/annual injection",
                    "active_ingredients": "monthly tablet/annual injection",
                    "treatment_type": "Heartworm prevention",
                    "risk": "High",
                    "trigger": "avg max: 33.5",
                    "recommendation": "monthly tablet/annual injection",
                },
            ],
        },
        {
            "name": "Bangkerreng",
            "months": "Apr",
            "temp": "23-34C",
            "source": "csiro | kakadu | kakudu tourism",
            "notes": "Knock-em-down storms / transition out of wet season",
            "observations": [
                ("weather", '"knock-em-down" storms (Nakurl)'),
                ("weather", "clear skies, flood recede + streams clear"),
                ("weather", "early days: violent/windy storms"),
                (
                    "weather",
                    "Manbedje yirridjdja (the early spear grass). Manbedje duwa (the later spear grass) is now green and growing until barra (the later rains).",
                ),
                ("resource", "speargrass (early/late) flattening/growth"),
                ("resource", "magpie goose eggs collection, fishing"),
                ("resource", "fruiting plants, young animals"),
                ("resource", "--> flattens speargrass"),
            ],
            "risks": [
                {
                    "parasite": "Hookworms",
                    "group": "Internal",
                    "treatment_name": "Filia",
                    "active_ingredients": "Filia",
                    "treatment_type": "Worming",
                    "risk": "High",
                    "trigger": '"knock-em-down" storms (Nakurl); speargrass (early/late) flattening/growth',
                    "recommendation": "Filia",
                },
                {
                    "parasite": "Brown dog tick",
                    "group": "External",
                    "treatment_name": "General monitoring / not specified in sheet",
                    "active_ingredients": "General monitoring / not specified in sheet",
                    "treatment_type": "Tick control",
                    "risk": "Medium",
                    "trigger": "magpie goose eggs collection, fishing",
                    "recommendation": "No explicit treatment listed in sheet",
                },
                {
                    "parasite": "Toxocara spp. (roundworms)",
                    "group": "Internal",
                    "treatment_name": "General monitoring / not specified in sheet",
                    "active_ingredients": "General monitoring / not specified in sheet",
                    "treatment_type": "Worming",
                    "risk": "Medium",
                    "trigger": "clear skies, flood recede + streams clear; fruiting plants, young animals",
                    "recommendation": "No explicit treatment listed in sheet",
                },
                {
                    "parasite": "fleas (Ctenocephalides felis)",
                    "group": "External",
                    "treatment_name": "General monitoring / not specified in sheet",
                    "active_ingredients": "General monitoring / not specified in sheet",
                    "treatment_type": "Flea control",
                    "risk": "Medium",
                    "trigger": "early days: violent/windy storms; --> flattens speargrass",
                    "recommendation": "No explicit treatment listed in sheet",
                },
                {
                    "parasite": "spirometra (tapeworm)",
                    "group": "Internal",
                    "treatment_name": "General monitoring / not specified in sheet",
                    "active_ingredients": "General monitoring / not specified in sheet",
                    "treatment_type": "Tapeworm treatment",
                    "risk": "Medium",
                    "trigger": "Manbedje yirridjdja (the early spear grass). Manbedje duwa (the later spear grass) is now green and growing until barra (the later rains).",
                    "recommendation": "No explicit treatment listed in sheet",
                },
                {
                    "parasite": "heartworm (from mosquitos)",
                    "group": "Internal",
                    "treatment_name": "General monitoring / not specified in sheet",
                    "active_ingredients": "General monitoring / not specified in sheet",
                    "treatment_type": "Heartworm prevention",
                    "risk": "Medium",
                    "trigger": "Residual mosquito activity after wet season",
                    "recommendation": "No explicit treatment listed in sheet",
                },
            ],
        },
        {
            "name": "Yekke",
            "months": "May to Mid Jun",
            "temp": "21-33C",
            "source": "https://www.bamurruplains.com/wp-content/uploads/2023/05/BamurruPlains_Seasonality.pdf | https://www.csiro.au/en/research/indigenous-science/Indigenous-knowledge/Calendars/Ngurrungurrudjba",
            "notes": "Generally the 'season of life'",
            "observations": [
                ("weather", "Cool but still (less) humid"),
                ("weather", "Warm and dry"),
                ("weather", "Generally cloudless"),
                ("weather", "dry winds blow from south-east"),
                ("resource", "Yellow-green fruits of Anmorlak"),
                ("resource", "Flowering Darwin woollybutt"),
                ("resource", "Lots of dragonflies"),
                ("resource", "Flowering of Manbarndarr and Mandjedj"),
                ("resource", "Covered with water lilies"),
                (
                    "resource",
                    "Andjalen flowers, provides nectar for birds, possums, flying foxes",
                ),
                ("key_note", "Generally the 'season of life'"),
                ("key_note", "Many species teach their young how to navigate"),
                ("key_note", "Aboriginal start 'patchburning'"),
            ],
            "risks": [
                {
                    "parasite": "Strongyles",
                    "group": "Internal",
                    "treatment_name": "Fenbendazole, Ivermectin",
                    "active_ingredients": "Fenbendazole, Ivermectin",
                    "treatment_type": "Worming",
                    "risk": "Medium",
                    "trigger": "Cool but still (less) humid; Yellow-green fruits of Anmorlak; Generally the 'season of life'",
                    "recommendation": "Maanas",
                },
                {
                    "parasite": "Hookworms",
                    "group": "Internal",
                    "treatment_name": "Pyrantel, Febantel, Oxibendazole",
                    "active_ingredients": "Pyrantel, Febantel, Oxibendazole",
                    "treatment_type": "Worming",
                    "risk": "Medium",
                    "trigger": "Warm and dry; Many species teach their young how to navigate",
                    "recommendation": "Pyrantel, Febantel, Oxibendazole",
                },
                {
                    "parasite": "Roundworms",
                    "group": "Internal",
                    "treatment_name": "fenbendazole, pyrantel, or milbemycin",
                    "active_ingredients": "fenbendazole, pyrantel, or milbemycin",
                    "treatment_type": "Worming",
                    "risk": "Medium",
                    "trigger": "Generally cloudless; Flowering Darwin woollybutt",
                    "recommendation": "fenbendazole, pyrantel, or milbemycin",
                },
                {
                    "parasite": "Dog heartworms",
                    "group": "Internal",
                    "treatment_name": "melarsomine",
                    "active_ingredients": "melarsomine",
                    "treatment_type": "Heartworm treatment",
                    "risk": "Medium",
                    "trigger": "dry winds blow from south-east; Aboriginal start 'patchburning'",
                    "recommendation": "melarsomine",
                },
                {
                    "parasite": "Ticks (Cattle tick, bush tick)",
                    "group": "External",
                    "treatment_name": "General monitoring / not specified in sheet",
                    "active_ingredients": "General monitoring / not specified in sheet",
                    "treatment_type": "Tick control",
                    "risk": "Medium",
                    "trigger": "Lots of dragonflies",
                    "recommendation": "No explicit treatment listed in sheet",
                },
                {
                    "parasite": "Giardia",
                    "group": "Internal",
                    "treatment_name": "fenbendazole (Panacur) or metronidazole (Flagyl)",
                    "active_ingredients": "fenbendazole (Panacur) or metronidazole (Flagyl)",
                    "treatment_type": "Protozoal treatment",
                    "risk": "Medium",
                    "trigger": "Flowering of Manbarndarr and Mandjedj",
                    "recommendation": "fenbendazole (Panacur) or metronidazole (Flagyl)",
                },
                {
                    "parasite": "Cryptosporidiosis",
                    "group": "Internal",
                    "treatment_name": "Azithromycin, Paromomycin, Tylosin",
                    "active_ingredients": "Azithromycin, Paromomycin, Tylosin",
                    "treatment_type": "Protozoal treatment",
                    "risk": "Medium",
                    "trigger": "Covered with water lilies",
                    "recommendation": "Azithromycin, Paromomycin, Tylosin",
                },
            ],
        },
        {
            "name": "Wurrkeng",
            "months": "Mid Jun to Mid Aug",
            "temp": "17-32C",
            "source": "https://www.bamurruplains.com/wp-content/uploads/2023/05/BamurruPlains_Seasonality.pdf | https://www.csiro.au/en/research/indigenous-science/Indigenous-knowledge/Calendars/Ngurrungurrudjba",
            "notes": "Cold weather (the coldest time)",
            "observations": [
                ("weather", "Cold weather (the coldest time)"),
                ("weather", "Low humidity"),
                ("weather", "Daytime temps rise to 30C, nightime falls to 17C"),
                ("resource", "Seeds of Wurrmarninj"),
                ("resource", "Andem roots in water"),
                ("key_note", "Magpie Geese and other waterbirds crowd the billabongs"),
                ("key_note", "Most creeks stop flowing"),
                ("key_note", "Insects and small animals escape patchburning flames"),
                ("key_note", "Birds of prey patrol fire lines"),
                (
                    "key_note",
                    "Many flowering - like Mandjalen, Manbordokorr and Mandadjek",
                ),
                ("key_note", "Native bees are busy"),
                ("key_note", "Kumoken crocodiles lay eggs on creek banks"),
                ("key_note", "Maanas"),
            ],
            "risks": [],
        },
        {
            "name": "Kurrung",
            "months": "Mid-August to mid-October.",
            "temp": "23°C – 37°C",
            "source": "https://www.furlifevet.com.au/creepy-summer-risks/#:~:text=Dogs%2C%20Pets%2C%20Summer%20Pets,found%20on%20dogs%20in%20Australia. | https://www.youtube.com/shorts/NRCX6MaIrkw | https://vets4pets.com.au/pet-advice/know-your-parasites/#:~:text=Ticks,respiratory%20distress%20and%20secondary%20infections.",
            "notes": "Hot dry season before Kunumeleng build-up",
            "observations": [
                ("weather", "Hot Dry"),
                (
                    "weather",
                    "‘goose time’ but also time for local Aboriginal people to hunt file snakes and long-necked turtles.",
                ),
                (
                    "weather",
                    "flowering of many plants, such as the Syzgium forte (Manboyberre) and Syzgium suborbiculare (Mandjarduk).",
                ),
                ("weather", "Mahbilil (the saltwater wind) blows in the evenings"),
                (
                    "weather",
                    "Whirly whirlies, known as Nadjurlum, are common during this time.",
                ),
                (
                    "weather",
                    "Towards the end of the season, thunderclouds begin to build in the sky, signaling the transition to the Kunumeleng pre-monsoon season.",
                ),
            ],
            "risks": [
                {
                    "parasite": "Paralysis Ticks (Ixodes holocyclus)",
                    "group": "External",
                    "treatment_name": "Fipronil; fipronil + amitraz; fipronil + cyphenothrin; permethrin; permethrin + imidacloprid; permethrin + pyriproxyfen; permethrin + indoxacarb; flumethrin; amitraz + metaflumizone; pyriprole; etofenprox",
                    "active_ingredients": "Fipronil; fipronil + amitraz; fipronil + cyphenothrin; permethrin; permethrin + imidacloprid; permethrin + pyriproxyfen; permethrin + indoxacarb; flumethrin; amitraz + metaflumizone; pyriprole; etofenprox",
                    "treatment_type": "Tick control",
                    "risk": "High",
                    "trigger": "Hot Dry",
                    "recommendation": "Kunal Dewani",
                },
                {
                    "parasite": "Fleas",
                    "group": "External",
                    "treatment_name": "Fipronil; fipronil + S-methoprene; fipronil + cyphenothrin; permethrin; permethrin + pyriproxyfen; permethrin + imidacloprid; etofenprox; pyrethrins; pyrethrin + permethrin; phenothrin + methoprene; permethrin + dinotefuran + pyriproxyfen; permethrin + pyriproxyfen + imidacloprid",
                    "active_ingredients": "Fipronil; fipronil + S-methoprene; fipronil + cyphenothrin; permethrin; permethrin + pyriproxyfen; permethrin + imidacloprid; etofenprox; pyrethrins; pyrethrin + permethrin; phenothrin + methoprene; permethrin + dinotefuran + pyriproxyfen; permethrin + pyriproxyfen + imidacloprid",
                    "treatment_type": "Flea control",
                    "risk": "Medium",
                    "trigger": "‘goose time’ but also time for local Aboriginal people to hunt file snakes and long-necked turtles.",
                    "recommendation": "Flea treatment during hot dry period",
                },
                {
                    "parasite": "Mites (Mange)",
                    "group": "Skin",
                    "treatment_name": "Amitraz is the main active for mange mites; fipronil + amitraz and amitraz + metaflumizone may help in some cases. Flumethrin and pyrethroid products are generally not first-line for mange.",
                    "active_ingredients": "Amitraz is the main active for mange mites; fipronil + amitraz and amitraz + metaflumizone may help in some cases. Flumethrin and pyrethroid products are generally not first-line for mange.",
                    "treatment_type": "Mange treatment",
                    "risk": "Medium",
                    "trigger": "flowering of many plants, such as the Syzgium forte (Manboyberre) and Syzgium suborbiculare (Mandjarduk).",
                    "recommendation": "Amitraz-focused mange control",
                },
                {
                    "parasite": "Bush Ticks",
                    "group": "External",
                    "treatment_name": "Fipronil; fipronil + amitraz; fipronil + cyphenothrin; permethrin products; flumethrin; pyriprole; amitraz + metaflumizone; etofenprox",
                    "active_ingredients": "Fipronil; fipronil + amitraz; fipronil + cyphenothrin; permethrin products; flumethrin; pyriprole; amitraz + metaflumizone; etofenprox",
                    "treatment_type": "Tick control",
                    "risk": "Medium",
                    "trigger": "Mahbilil (the saltwater wind) blows in the evenings",
                    "recommendation": "Tick control",
                },
                {
                    "parasite": "Heartworm",
                    "group": "Internal",
                    "treatment_name": "Milbemycin oxime; Moxidectin",
                    "active_ingredients": "Milbemycin oxime; Moxidectin",
                    "treatment_type": "Heartworm prevention",
                    "risk": "Medium",
                    "trigger": "Whirly whirlies, known as Nadjurlum, are common during this time.",
                    "recommendation": "Milbemycin oxime; Moxidectin",
                },
                {
                    "parasite": "Hookworms (during transition to Kunumeleng season)",
                    "group": "Internal",
                    "treatment_name": "Pyrantel (as embonate/pamoate); Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime; Levamisole hydrochloride; Moxidectin; Emodepside",
                    "active_ingredients": "Pyrantel (as embonate/pamoate); Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime; Levamisole hydrochloride; Moxidectin; Emodepside",
                    "treatment_type": "Worming",
                    "risk": "High",
                    "trigger": "Towards the end of the season, thunderclouds begin to build in the sky, signaling the transition to the Kunumeleng pre-monsoon season.",
                    "recommendation": "Broad-spectrum deworming before wet build-up",
                },
                {
                    "parasite": "Roundworms (common in puppies)",
                    "group": "Internal",
                    "treatment_name": "Pyrantel (as embonate/pamoate); Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime; Nitroscanate; Levamisole hydrochloride; Moxidectin; Emodepside",
                    "active_ingredients": "Pyrantel (as embonate/pamoate); Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime; Nitroscanate; Levamisole hydrochloride; Moxidectin; Emodepside",
                    "treatment_type": "Worming",
                    "risk": "Medium",
                    "trigger": "Common in puppies during seasonal transition",
                    "recommendation": "Broad-spectrum puppy deworming",
                },
                {
                    "parasite": "Tapeworms (scooting)",
                    "group": "Internal",
                    "treatment_name": "Praziquantel; Epsiprantel; Niclosamide; Nitroscanate; Fenbendazole; Flubendazole",
                    "active_ingredients": "Praziquantel; Epsiprantel; Niclosamide; Nitroscanate; Fenbendazole; Flubendazole",
                    "treatment_type": "Tapeworm treatment",
                    "risk": "Medium",
                    "trigger": "Scooting / intestinal tapeworm signs",
                    "recommendation": "Tapeworm treatment",
                },
                {
                    "parasite": "Whipworm (Bloody darrhea -> dehydration)",
                    "group": "Internal",
                    "treatment_name": "Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime",
                    "active_ingredients": "Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime",
                    "treatment_type": "Worming",
                    "risk": "Medium",
                    "trigger": "Bloody darrhea -> dehydration",
                    "recommendation": "Whipworm treatment",
                },
            ],
        },
        {
            "name": "Kunumeleng",
            "months": "Mid-October to late December.",
            "temp": "24°C – 37°C",
            "source": "Spreadsheet seasonal notes",
            "notes": "Pre-monsoon season / build-up",
            "observations": [
                ("weather", "Humidity builds"),
                (
                    "weather",
                    "kunngol (clouds) and kunmayorrk (wind) gather together from all directions",
                ),
                (
                    "weather",
                    "the pre-monsoon season, with hot weather that becomes increasingly humid.",
                ),
                ("weather", "It can last from a few weeks to several months."),
                (
                    "weather",
                    "Thunderstorms build in the afternoons and showers bring green to the dry land.",
                ),
                (
                    "weather",
                    "As the streams begin to run, acidic water from the floodplains can kill fish in billabongs with low oxygen levels.",
                ),
                (
                    "weather",
                    "Barramundi move from the waterholes to the estuaries to breed, and waterbirds spread out with the increased surface water and plant growth.",
                ),
                (
                    "weather",
                    "Kunumeleng was when Aboriginal people traditionally moved camp from the floodplains to the Stone Country to shelter from the coming monsoon",
                ),
                (
                    "weather",
                    "Namarrkon kamayhmayhke (lightning flashes) tell us that the Ngalmangiyi and Kedjebe are moving closer to the bank and are easier to collect.",
                ),
            ],
            "risks": [
                {
                    "parasite": "Brown Dog Ticks (Rhipicephalus sanguineus) (thrive in hot, humid environments)",
                    "group": "External",
                    "treatment_name": "Fipronil, Amitraz, Permethrin, Cyphenothrin, Flumethrin, Pyriprole, Indoxacarb",
                    "active_ingredients": "Fipronil, Amitraz, Permethrin, Cyphenothrin, Flumethrin, Pyriprole, Indoxacarb",
                    "treatment_type": "Tick control",
                    "risk": "High",
                    "trigger": "Humidity builds",
                    "recommendation": "Kunal",
                },
                {
                    "parasite": "Fleas (intense itching and potentially leading to flea allergy dermatitis)",
                    "group": "External",
                    "treatment_name": "Fipronil, S-methoprene, Permethrin, Pyriproxyfen, Imidacloprid, Cyphenothrin, Dinotefuran, Etofenprox, Pyrethrins, Phenothrin",
                    "active_ingredients": "Fipronil, S-methoprene, Permethrin, Pyriproxyfen, Imidacloprid, Cyphenothrin, Dinotefuran, Etofenprox, Pyrethrins, Phenothrin",
                    "treatment_type": "Flea control",
                    "risk": "High",
                    "trigger": "kunngol (clouds) and kunmayorrk (wind) gather together from all directions",
                    "recommendation": "Flea control during humid build-up",
                },
                {
                    "parasite": "Sarcoptic mange (Scabies) (Highly contagious, causing intense itching and loss of hair, and can be transmitted to humans)",
                    "group": "Skin",
                    "treatment_name": "Amitraz, Fipronil, Metaflumizone",
                    "active_ingredients": "Amitraz, Fipronil, Metaflumizone",
                    "treatment_type": "Mange treatment",
                    "risk": "High",
                    "trigger": "the pre-monsoon season, with hot weather that becomes increasingly humid.",
                    "recommendation": "Scabies treatment",
                },
                {
                    "parasite": "Demodectic mange ( Affects dogs when their immune system is compromised)",
                    "group": "Skin",
                    "treatment_name": "Amitraz, Metaflumizone",
                    "active_ingredients": "Amitraz, Metaflumizone",
                    "treatment_type": "Mange treatment",
                    "risk": "Medium",
                    "trigger": "It can last from a few weeks to several months.",
                    "recommendation": "Demodectic mange treatment",
                },
                {
                    "parasite": "Ehrlichiosis (Ehrlichia canis) ( A serious, often fatal disease spread by the brown dog tick, now established in the Northern Territory. It causes fever, bleeding disorders, and lethargy. )",
                    "group": "Other",
                    "treatment_name": "Fipronil, Amitraz, Permethrin, Flumethrin, Pyriprole, Cyphenothrin, Indoxacarb",
                    "active_ingredients": "Fipronil, Amitraz, Permethrin, Flumethrin, Pyriprole, Cyphenothrin, Indoxacarb",
                    "treatment_type": "Tick-borne disease control",
                    "risk": "High",
                    "trigger": "Thunderstorms build in the afternoons and showers bring green to the dry land.",
                    "recommendation": "Brown dog tick control to reduce ehrlichiosis risk",
                },
                {
                    "parasite": "Heartworm (Dirofilaria immitis) (Transmitted by mosquitoes, which are highly active in the humid Kunumeleng season)",
                    "group": "Internal",
                    "treatment_name": "Milbemycin oxime; Moxidectin",
                    "active_ingredients": "Milbemycin oxime; Moxidectin",
                    "treatment_type": "Heartworm prevention",
                    "risk": "High",
                    "trigger": "As the streams begin to run, acidic water from the floodplains can kill fish in billabongs with low oxygen levels.",
                    "recommendation": "Heartworm prevention",
                },
                {
                    "parasite": "Hookworms (Ancylostoma caninum) (These are particularly dangerous during the wet season because the larvae require moisture to hatch and thrive in the environment. They cause significant blood loss, weight loss, pain, and death in puppies and older dogs.)",
                    "group": "Internal",
                    "treatment_name": "Pyrantel (as embonate/pamoate); Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime; Levamisole hydrochloride; Moxidectin; Emodepside",
                    "active_ingredients": "Pyrantel (as embonate/pamoate); Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime; Levamisole hydrochloride; Moxidectin; Emodepside",
                    "treatment_type": "Worming",
                    "risk": "High",
                    "trigger": "Barramundi move from the waterholes to the estuaries to breed, and waterbirds spread out with the increased surface water and plant growth.",
                    "recommendation": "Prioritise hookworm treatment",
                },
                {
                    "parasite": "Whipworm (Trichuris vulpis): Highly prevalent in Aboriginal community dogs, causing chronic infections.",
                    "group": "Internal",
                    "treatment_name": "Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime",
                    "active_ingredients": "Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime",
                    "treatment_type": "Worming",
                    "risk": "High",
                    "trigger": "Kunumeleng was when Aboriginal people traditionally moved camp from the floodplains to the Stone Country to shelter from the coming monsoon",
                    "recommendation": "Whipworm treatment",
                },
                {
                    "parasite": "Roundworms & Tapeworms: Common intestinal parasites. Spirometra tapeworms are also found in this region, often transmitted to dogs by eating lizards and frogs",
                    "group": "Internal",
                    "treatment_name": "Pyrantel (as embonate/pamoate); Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime; Nitroscanate; Levamisole hydrochloride; Moxidectin; Emodepside",
                    "active_ingredients": "Pyrantel (as embonate/pamoate); Febantel; Oxibendazole; Fenbendazole; Flubendazole; Milbemycin oxime; Nitroscanate; Levamisole hydrochloride; Moxidectin; Emodepside",
                    "treatment_type": "Worming",
                    "risk": "Medium",
                    "trigger": "Namarrkon kamayhmayhke (lightning flashes) tell us that the Ngalmangiyi and Kedjebe are moving closer to the bank and are easier to collect.",
                    "recommendation": "Broad-spectrum intestinal parasite control",
                },
                {
                    "parasite": "Tapeworms (general; e.g. Dipylidium, Taenia)",
                    "group": "Internal",
                    "treatment_name": "Praziquantel; Epsiprantel; Niclosamide; Nitroscanate; Fenbendazole; Flubendazole",
                    "active_ingredients": "Praziquantel; Epsiprantel; Niclosamide; Nitroscanate; Fenbendazole; Flubendazole",
                    "treatment_type": "Tapeworm treatment",
                    "risk": "Medium",
                    "trigger": "General tapeworm burden",
                    "recommendation": "Tapeworm treatment",
                },
                {
                    "parasite": "Spirometra tapeworms",
                    "group": "Internal",
                    "treatment_name": "Praziquantel; Nitroscanate; Fenbendazole",
                    "active_ingredients": "Praziquantel; Nitroscanate; Fenbendazole",
                    "treatment_type": "Tapeworm treatment",
                    "risk": "Medium",
                    "trigger": "Spirometra risk in region",
                    "recommendation": "Spirometra treatment",
                },
            ],
        },
    ]

    for season in seasons_data:
        insert_season(
            cursor,
            region_id=region_id,
            name=season["name"],
            approx_months=season["months"],
            temperature_range=season["temp"],
            source=season["source"],
            notes=season["notes"],
        )

        season_id = get_season_id(cursor, region_id, season["name"])

        for obs_type, obs_text in season["observations"]:
            insert_observation(cursor, season_id, obs_type, obs_text)

        for risk in season["risks"]:
            insert_parasite(
                cursor, risk["parasite"], risk["group"], "Seeded from spreadsheet"
            )
            insert_treatment(
                cursor,
                risk["treatment_name"],
                risk["active_ingredients"],
                risk["treatment_type"],
                "Seeded from spreadsheet",
            )

            parasite_id = get_parasite_id(cursor, risk["parasite"])
            treatment_id = get_treatment_id(
                cursor, risk["treatment_name"], risk["active_ingredients"]
            )

            link_season_parasite_treatment(
                cursor,
                season_id=season_id,
                parasite_id=parasite_id,
                treatment_id=treatment_id,
                risk_level=risk["risk"],
                trigger_notes=risk["trigger"],
                recommendation_notes=risk["recommendation"],
            )

    conn.commit()
    conn.close()
    print(
        "All six seasons, observations, parasites, and treatments seeded successfully."
    )


if __name__ == "__main__":
    main()
