ROLE_ACCESS_MAP = {
    "finance_team": ["finance", "general"],
    "hr_team": ["hr", "general"],
    "c_level": ["finance", "hr", "general"],
    "employee": ["general"],
}


def get_allowed_collections(role: str) -> list[str]:
    return ROLE_ACCESS_MAP.get(role, ["general"])
