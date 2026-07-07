import re


def contains_pii(text: str) -> bool:
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"\d{3}[-.]?\d{3}[-.]?\d{4}"
    ssn_pattern = r"\d{3}-\d{2}-\d{4}"
    if re.search(email_pattern, text):
        return True
    if re.search(phone_pattern, text):
        return True
    if re.search(ssn_pattern, text):
        return True
    return False


BLOCKED_TOPICS = ["weather", "sports", "politics", "celebrity", "movie"]


def is_out_of_scope(query: str) -> bool:
    lower_query = query.lower()
    for topic in BLOCKED_TOPICS:
        if topic in lower_query:
            return True
    return False
