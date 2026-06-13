"""Seed data for the WM 2026 prototype.

The group/team composition, match numbers and kick-off times follow the
official FIFA match schedule PDF released after the final draw. Kick-off times
are stored as Eastern Time because that is how FIFA publishes the schedule; the
Flask app displays them converted to Germany/Berlin summer time.
"""

TEAMS = [
    # code, name, group, position, deterministic rank fallback
    ("MEX", "Mexiko", "A", 1, 15), ("RSA", "Südafrika", "A", 2, 55), ("KOR", "Korea Republic", "A", 3, 23), ("CZE", "Tschechien", "A", 4, 31),
    ("CAN", "Kanada", "B", 1, 28), ("BIH", "Bosnien und Herzegowina", "B", 2, 70), ("QAT", "Katar", "B", 3, 53), ("SUI", "Schweiz", "B", 4, 17),
    ("BRA", "Brasilien", "C", 1, 5), ("MAR", "Marokko", "C", 2, 12), ("HAI", "Haiti", "C", 3, 83), ("SCO", "Schottland", "C", 4, 45),
    ("USA", "USA", "D", 1, 16), ("PAR", "Paraguay", "D", 2, 48), ("AUS", "Australien", "D", 3, 24), ("TUR", "Türkei", "D", 4, 27),
    ("GER", "Deutschland", "E", 1, 9), ("CUW", "Curaçao", "E", 2, 75), ("CIV", "Côte d’Ivoire", "E", 3, 41), ("ECU", "Ecuador", "E", 4, 30),
    ("NED", "Niederlande", "F", 1, 7), ("JPN", "Japan", "F", 2, 20), ("SWE", "Schweden", "F", 3, 35), ("TUN", "Tunesien", "F", 4, 49),
    ("BEL", "Belgien", "G", 1, 8), ("EGY", "Ägypten", "G", 2, 34), ("IRN", "Iran", "G", 3, 21), ("NZL", "Neuseeland", "G", 4, 88),
    ("ESP", "Spanien", "H", 1, 2), ("CPV", "Cabo Verde", "H", 2, 68), ("KSA", "Saudi-Arabien", "H", 3, 59), ("URU", "Uruguay", "H", 4, 14),
    ("FRA", "Frankreich", "I", 1, 3), ("SEN", "Senegal", "I", 2, 18), ("IRQ", "Irak", "I", 3, 58), ("NOR", "Norwegen", "I", 4, 33),
    ("ARG", "Argentinien", "J", 1, 1), ("ALG", "Algerien", "J", 2, 36), ("AUT", "Österreich", "J", 3, 26), ("JOR", "Jordanien", "J", 4, 62),
    ("POR", "Portugal", "K", 1, 6), ("COL", "Kolumbien", "K", 2, 13), ("UZB", "Usbekistan", "K", 3, 61), ("COD", "DR Kongo", "K", 4, 56),
    ("ENG", "England", "L", 1, 4), ("CRO", "Kroatien", "L", 2, 11), ("GHA", "Ghana", "L", 3, 64), ("PAN", "Panama", "L", 4, 52),
]

TEAM_FLAGS = {
    "MEX": "🇲🇽", "RSA": "🇿🇦", "KOR": "🇰🇷", "CZE": "🇨🇿",
    "CAN": "🇨🇦", "BIH": "🇧🇦", "QAT": "🇶🇦", "SUI": "🇨🇭",
    "BRA": "🇧🇷", "MAR": "🇲🇦", "HAI": "🇭🇹", "SCO": "🏴",
    "USA": "🇺🇸", "PAR": "🇵🇾", "AUS": "🇦🇺", "TUR": "🇹🇷",
    "GER": "🇩🇪", "CUW": "🇨🇼", "CIV": "🇨🇮", "ECU": "🇪🇨",
    "NED": "🇳🇱", "JPN": "🇯🇵", "SWE": "🇸🇪", "TUN": "🇹🇳",
    "BEL": "🇧🇪", "EGY": "🇪🇬", "IRN": "🇮🇷", "NZL": "🇳🇿",
    "ESP": "🇪🇸", "CPV": "🇨🇻", "KSA": "🇸🇦", "URU": "🇺🇾",
    "FRA": "🇫🇷", "SEN": "🇸🇳", "IRQ": "🇮🇶", "NOR": "🇳🇴",
    "ARG": "🇦🇷", "ALG": "🇩🇿", "AUT": "🇦🇹", "JOR": "🇯🇴",
    "POR": "🇵🇹", "COL": "🇨🇴", "UZB": "🇺🇿", "COD": "🇨🇩",
    "ENG": "🏴", "CRO": "🇭🇷", "GHA": "🇬🇭", "PAN": "🇵🇦",
}


def team_flag(code: str | None) -> str:
    return TEAM_FLAGS.get(code or "", "")

TEAM_FLAG_CODES = {
    "MEX": "mx", "RSA": "za", "KOR": "kr", "CZE": "cz",
    "CAN": "ca", "BIH": "ba", "QAT": "qa", "SUI": "ch",
    "BRA": "br", "MAR": "ma", "HAI": "ht", "SCO": "gb-sct",
    "USA": "us", "PAR": "py", "AUS": "au", "TUR": "tr",
    "GER": "de", "CUW": "cw", "CIV": "ci", "ECU": "ec",
    "NED": "nl", "JPN": "jp", "SWE": "se", "TUN": "tn",
    "BEL": "be", "EGY": "eg", "IRN": "ir", "NZL": "nz",
    "ESP": "es", "CPV": "cv", "KSA": "sa", "URU": "uy",
    "FRA": "fr", "SEN": "sn", "IRQ": "iq", "NOR": "no",
    "ARG": "ar", "ALG": "dz", "AUT": "at", "JOR": "jo",
    "POR": "pt", "COL": "co", "UZB": "uz", "COD": "cd",
    "ENG": "gb-eng", "CRO": "hr", "GHA": "gh", "PAN": "pa",
}


def team_flag_url(code: str | None) -> str:
    flag_code = TEAM_FLAG_CODES.get(code or "")
    if not flag_code:
        return ""
    return f"https://flagcdn.com/w40/{flag_code}.png"


GROUP_MATCHES = [
    # match_no, group, home, away
    (1,"A","MEX","RSA"),(2,"A","KOR","CZE"),(25,"A","CZE","RSA"),(28,"A","MEX","KOR"),(53,"A","CZE","MEX"),(54,"A","RSA","KOR"),
    (3,"B","CAN","BIH"),(8,"B","QAT","SUI"),(26,"B","SUI","BIH"),(27,"B","CAN","QAT"),(51,"B","SUI","CAN"),(52,"B","BIH","QAT"),
    (5,"C","HAI","SCO"),(7,"C","BRA","MAR"),(29,"C","BRA","HAI"),(30,"C","SCO","MAR"),(49,"C","SCO","BRA"),(50,"C","MAR","HAI"),
    (4,"D","USA","PAR"),(6,"D","AUS","TUR"),(31,"D","TUR","PAR"),(32,"D","USA","AUS"),(59,"D","TUR","USA"),(60,"D","PAR","AUS"),
    (9,"E","CIV","ECU"),(10,"E","GER","CUW"),(33,"E","GER","CIV"),(34,"E","ECU","CUW"),(55,"E","CUW","CIV"),(56,"E","ECU","GER"),
    (11,"F","NED","JPN"),(12,"F","SWE","TUN"),(35,"F","NED","SWE"),(36,"F","TUN","JPN"),(57,"F","JPN","SWE"),(58,"F","TUN","NED"),
    (16,"G","BEL","EGY"),(15,"G","IRN","NZL"),(39,"G","BEL","IRN"),(40,"G","NZL","EGY"),(63,"G","EGY","IRN"),(64,"G","NZL","BEL"),
    (13,"H","KSA","URU"),(14,"H","ESP","CPV"),(37,"H","URU","CPV"),(38,"H","ESP","KSA"),(65,"H","CPV","KSA"),(66,"H","URU","ESP"),
    (17,"I","FRA","SEN"),(18,"I","IRQ","NOR"),(41,"I","NOR","SEN"),(42,"I","FRA","IRQ"),(61,"I","NOR","FRA"),(62,"I","SEN","IRQ"),
    (19,"J","ARG","ALG"),(20,"J","AUT","JOR"),(43,"J","ARG","AUT"),(44,"J","JOR","ALG"),(69,"J","ALG","AUT"),(70,"J","JOR","ARG"),
    (23,"K","POR","COD"),(24,"K","UZB","COL"),(47,"K","POR","UZB"),(48,"K","COL","COD"),(71,"K","COL","POR"),(72,"K","COD","UZB"),
    (21,"L","GHA","PAN"),(22,"L","ENG","CRO"),(45,"L","ENG","GHA"),(46,"L","PAN","CRO"),(67,"L","PAN","ENG"),(68,"L","CRO","GHA"),
]

# Knock-out references are resolved dynamically by the engine.
KNOCKOUT_MATCHES = [
    # match_no, phase, home_ref, away_ref
    (73,"r32","2A","2B"),(74,"r32","1E","3ABCDF"),(75,"r32","1F","2C"),(76,"r32","1C","2F"),
    (77,"r32","1I","3CDFGH"),(78,"r32","2E","2I"),(79,"r32","1A","3CEFHI"),(80,"r32","1L","3EHIJK"),
    (81,"r32","1D","3BEFIJ"),(82,"r32","1G","3AEHIJ"),(83,"r32","2K","2L"),(84,"r32","1H","2J"),
    (85,"r32","1B","3EFGIJ"),(86,"r32","1J","2H"),(87,"r32","1K","3DEIJL"),(88,"r32","2D","2G"),
    (89,"r16","W74","W77"),(90,"r16","W73","W75"),(91,"r16","W76","W78"),(92,"r16","W79","W80"),
    (93,"r16","W83","W84"),(94,"r16","W81","W82"),(95,"r16","W86","W88"),(96,"r16","W85","W87"),
    (97,"qf","W89","W90"),(98,"qf","W93","W94"),(99,"qf","W91","W92"),(100,"qf","W95","W96"),
    (101,"sf","W97","W98"),(102,"sf","W99","W100"),
    (103,"third","L101","L102"),(104,"final","W101","W102"),
]

# Official kick-off metadata. Values are Eastern Time (ET), matching FIFA's
# schedule PDF. IMPORTANT: date_et is the calendar date in Eastern Time, not
# necessarily the venue-local date. For late matches in western host cities,
# the ET date can already be the following day. The UI converts these values
# to Europe/Berlin time.
# broadcast: conservative German Free-TV status. Exact ARD/ZDF split is only
# known for some games; unknown free-TV selections remain editable here.
MATCH_INFO = {
    1: {"date_et": "2026-06-11", "time_et": "15:00", "broadcast": "ZDF"},
    2: {"date_et": "2026-06-11", "time_et": "22:00", "broadcast": "Free-TV offen / MagentaTV"},
    3: {"date_et": "2026-06-12", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    4: {"date_et": "2026-06-12", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    5: {"date_et": "2026-06-13", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    6: {"date_et": "2026-06-14", "time_et": "00:00", "broadcast": "Free-TV offen / MagentaTV"},
    7: {"date_et": "2026-06-13", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    8: {"date_et": "2026-06-13", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    9: {"date_et": "2026-06-14", "time_et": "19:00", "broadcast": "Free-TV offen / MagentaTV"},
    10: {"date_et": "2026-06-14", "time_et": "13:00", "broadcast": "ARD"},
    11: {"date_et": "2026-06-14", "time_et": "16:00", "broadcast": "Free-TV offen / MagentaTV"},
    12: {"date_et": "2026-06-14", "time_et": "22:00", "broadcast": "Free-TV offen / MagentaTV"},
    13: {"date_et": "2026-06-15", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    14: {"date_et": "2026-06-15", "time_et": "12:00", "broadcast": "Free-TV offen / MagentaTV"},
    15: {"date_et": "2026-06-15", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    16: {"date_et": "2026-06-15", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    17: {"date_et": "2026-06-16", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    18: {"date_et": "2026-06-16", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    19: {"date_et": "2026-06-16", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    20: {"date_et": "2026-06-17", "time_et": "00:00", "broadcast": "Free-TV offen / MagentaTV"},
    21: {"date_et": "2026-06-17", "time_et": "19:00", "broadcast": "Free-TV offen / MagentaTV"},
    22: {"date_et": "2026-06-17", "time_et": "16:00", "broadcast": "Free-TV offen / MagentaTV"},
    23: {"date_et": "2026-06-17", "time_et": "13:00", "broadcast": "Free-TV offen / MagentaTV"},
    24: {"date_et": "2026-06-17", "time_et": "22:00", "broadcast": "Free-TV offen / MagentaTV"},
    25: {"date_et": "2026-06-18", "time_et": "12:00", "broadcast": "Free-TV offen / MagentaTV"},
    26: {"date_et": "2026-06-18", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    27: {"date_et": "2026-06-18", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    28: {"date_et": "2026-06-18", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    29: {"date_et": "2026-06-19", "time_et": "20:30", "broadcast": "Free-TV offen / MagentaTV"},
    30: {"date_et": "2026-06-19", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    31: {"date_et": "2026-06-19", "time_et": "23:00", "broadcast": "Free-TV offen / MagentaTV"},
    32: {"date_et": "2026-06-19", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    33: {"date_et": "2026-06-20", "time_et": "16:00", "broadcast": "ZDF"},
    34: {"date_et": "2026-06-20", "time_et": "20:00", "broadcast": "Free-TV offen / MagentaTV"},
    35: {"date_et": "2026-06-20", "time_et": "13:00", "broadcast": "Free-TV offen / MagentaTV"},
    36: {"date_et": "2026-06-21", "time_et": "00:00", "broadcast": "Free-TV offen / MagentaTV"},
    37: {"date_et": "2026-06-21", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    38: {"date_et": "2026-06-21", "time_et": "12:00", "broadcast": "Free-TV offen / MagentaTV"},
    39: {"date_et": "2026-06-21", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    40: {"date_et": "2026-06-21", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    41: {"date_et": "2026-06-22", "time_et": "20:00", "broadcast": "Free-TV offen / MagentaTV"},
    42: {"date_et": "2026-06-22", "time_et": "17:00", "broadcast": "Free-TV offen / MagentaTV"},
    43: {"date_et": "2026-06-22", "time_et": "13:00", "broadcast": "Free-TV offen / MagentaTV"},
    44: {"date_et": "2026-06-22", "time_et": "23:00", "broadcast": "Free-TV offen / MagentaTV"},
    45: {"date_et": "2026-06-23", "time_et": "16:00", "broadcast": "Free-TV offen / MagentaTV"},
    46: {"date_et": "2026-06-23", "time_et": "19:00", "broadcast": "Free-TV offen / MagentaTV"},
    47: {"date_et": "2026-06-23", "time_et": "13:00", "broadcast": "Free-TV offen / MagentaTV"},
    48: {"date_et": "2026-06-23", "time_et": "22:00", "broadcast": "Free-TV offen / MagentaTV"},
    49: {"date_et": "2026-06-24", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    50: {"date_et": "2026-06-24", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    51: {"date_et": "2026-06-24", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    52: {"date_et": "2026-06-24", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    53: {"date_et": "2026-06-24", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    54: {"date_et": "2026-06-24", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    55: {"date_et": "2026-06-25", "time_et": "16:00", "broadcast": "Free-TV offen / MagentaTV"},
    56: {"date_et": "2026-06-25", "time_et": "16:00", "broadcast": "ARD"},
    57: {"date_et": "2026-06-25", "time_et": "19:00", "broadcast": "Free-TV offen / MagentaTV"},
    58: {"date_et": "2026-06-25", "time_et": "19:00", "broadcast": "Free-TV offen / MagentaTV"},
    59: {"date_et": "2026-06-25", "time_et": "22:00", "broadcast": "Free-TV offen / MagentaTV"},
    60: {"date_et": "2026-06-25", "time_et": "22:00", "broadcast": "Free-TV offen / MagentaTV"},
    61: {"date_et": "2026-06-26", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    62: {"date_et": "2026-06-26", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    63: {"date_et": "2026-06-26", "time_et": "23:00", "broadcast": "Free-TV offen / MagentaTV"},
    64: {"date_et": "2026-06-26", "time_et": "23:00", "broadcast": "Free-TV offen / MagentaTV"},
    65: {"date_et": "2026-06-26", "time_et": "20:00", "broadcast": "Free-TV offen / MagentaTV"},
    66: {"date_et": "2026-06-26", "time_et": "20:00", "broadcast": "Free-TV offen / MagentaTV"},
    67: {"date_et": "2026-06-27", "time_et": "17:00", "broadcast": "Free-TV offen / MagentaTV"},
    68: {"date_et": "2026-06-27", "time_et": "17:00", "broadcast": "Free-TV offen / MagentaTV"},
    69: {"date_et": "2026-06-27", "time_et": "22:00", "broadcast": "Free-TV offen / MagentaTV"},
    70: {"date_et": "2026-06-27", "time_et": "22:00", "broadcast": "Free-TV offen / MagentaTV"},
    71: {"date_et": "2026-06-27", "time_et": "19:30", "broadcast": "Free-TV offen / MagentaTV"},
    72: {"date_et": "2026-06-27", "time_et": "19:30", "broadcast": "Free-TV offen / MagentaTV"},
    73: {"date_et": "2026-06-28", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    74: {"date_et": "2026-06-29", "time_et": "16:30", "broadcast": "Free-TV offen / MagentaTV"},
    75: {"date_et": "2026-06-29", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    76: {"date_et": "2026-06-29", "time_et": "13:00", "broadcast": "Free-TV offen / MagentaTV"},
    77: {"date_et": "2026-06-30", "time_et": "17:00", "broadcast": "Free-TV offen / MagentaTV"},
    78: {"date_et": "2026-06-30", "time_et": "13:00", "broadcast": "Free-TV offen / MagentaTV"},
    79: {"date_et": "2026-06-30", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    80: {"date_et": "2026-07-01", "time_et": "12:00", "broadcast": "Free-TV offen / MagentaTV"},
    81: {"date_et": "2026-07-01", "time_et": "20:00", "broadcast": "Free-TV offen / MagentaTV"},
    82: {"date_et": "2026-07-01", "time_et": "16:00", "broadcast": "Free-TV offen / MagentaTV"},
    83: {"date_et": "2026-07-02", "time_et": "19:00", "broadcast": "Free-TV offen / MagentaTV"},
    84: {"date_et": "2026-07-02", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    85: {"date_et": "2026-07-02", "time_et": "23:00", "broadcast": "Free-TV offen / MagentaTV"},
    86: {"date_et": "2026-07-03", "time_et": "18:00", "broadcast": "Free-TV offen / MagentaTV"},
    87: {"date_et": "2026-07-03", "time_et": "21:30", "broadcast": "Free-TV offen / MagentaTV"},
    88: {"date_et": "2026-07-03", "time_et": "14:00", "broadcast": "Free-TV offen / MagentaTV"},
    89: {"date_et": "2026-07-04", "time_et": "17:00", "broadcast": "Free-TV offen / MagentaTV"},
    90: {"date_et": "2026-07-04", "time_et": "13:00", "broadcast": "Free-TV offen / MagentaTV"},
    91: {"date_et": "2026-07-05", "time_et": "16:00", "broadcast": "Free-TV offen / MagentaTV"},
    92: {"date_et": "2026-07-05", "time_et": "20:00", "broadcast": "Free-TV offen / MagentaTV"},
    93: {"date_et": "2026-07-06", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    94: {"date_et": "2026-07-06", "time_et": "20:00", "broadcast": "Free-TV offen / MagentaTV"},
    95: {"date_et": "2026-07-07", "time_et": "12:00", "broadcast": "Free-TV offen / MagentaTV"},
    96: {"date_et": "2026-07-07", "time_et": "16:00", "broadcast": "Free-TV offen / MagentaTV"},
    97: {"date_et": "2026-07-09", "time_et": "16:00", "broadcast": "Free-TV offen / MagentaTV"},
    98: {"date_et": "2026-07-10", "time_et": "15:00", "broadcast": "Free-TV offen / MagentaTV"},
    99: {"date_et": "2026-07-11", "time_et": "17:00", "broadcast": "Free-TV offen / MagentaTV"},
    100: {"date_et": "2026-07-11", "time_et": "21:00", "broadcast": "Free-TV offen / MagentaTV"},
    101: {"date_et": "2026-07-14", "time_et": "15:00", "broadcast": "Free-TV ARD/ZDF"},
    102: {"date_et": "2026-07-15", "time_et": "15:00", "broadcast": "Free-TV ARD/ZDF"},
    103: {"date_et": "2026-07-18", "time_et": "17:00", "broadcast": "Free-TV offen / MagentaTV"},
    104: {"date_et": "2026-07-19", "time_et": "15:00", "broadcast": "ZDF"},
}

DEFAULT_SETTINGS = {
    "prediction_lock_at": "2026-06-11T19:00:00Z",
    "score_exact_group": "3",
    "score_outcome_group": "1",
    "score_goal_diff_bonus": "1",
    "score_reaches_r32": "1",
    "score_reaches_r16": "2",
    "score_reaches_qf": "3",
    "score_reaches_sf": "4",
    "score_reaches_final": "6",
    "score_champion": "10",
}


def seed_database(db, models):
    Team, Match, Setting = models.Team, models.Match, models.Setting

    # Upsert instead of only inserting once, so prototype seed corrections can be
    # applied to an existing local database without deleting users/predictions.
    for code, name, group_id, pos, rank in TEAMS:
        team = Team.query.get(code)
        if team is None:
            team = Team(code=code)
            db.session.add(team)
        team.name = name
        team.group_id = group_id
        team.group_pos = pos
        team.fifa_rank = rank

    for match_no, group_id, home, away in GROUP_MATCHES:
        match = Match.query.get(match_no)
        if match is None:
            match = Match(match_no=match_no)
            db.session.add(match)
        match.phase = "group"
        match.group_id = group_id
        match.home_team_code = home
        match.away_team_code = away
        match.home_ref = home
        match.away_ref = away

    for match_no, phase, home_ref, away_ref in KNOCKOUT_MATCHES:
        match = Match.query.get(match_no)
        if match is None:
            match = Match(match_no=match_no)
            db.session.add(match)
        match.phase = phase
        match.group_id = None
        match.home_ref = home_ref
        match.away_ref = away_ref
        match.home_team_code = None
        match.away_team_code = None

    for key, value in DEFAULT_SETTINGS.items():
        setting = Setting.query.get(key)
        if setting is None:
            db.session.add(Setting(key=key, value=value))
        elif key.startswith("score_"):
            # Scoring rules are part of the prototype definition, so keep
            # existing local databases aligned when the prototype is upgraded.
            setting.value = value
    db.session.commit()
