from sqlalchemy.orm import Session
from app.models_db import CADPartDB


def resolve_part(question: str, db: Session) -> dict:
    question_lower = question.lower()
    parts = db.query(CADPartDB).all()

    # ---------------------------------------------------------
    # 1. Exact part number
    # ---------------------------------------------------------

    for part in parts:
        if part.part_number.lower() in question_lower:
            return {
                "status": "resolved",
                "part": part
            }

    # ---------------------------------------------------------
    # 2. Exact full part name
    # ---------------------------------------------------------

    name_matches = [
        part
        for part in parts
        if part.part_name.lower() in question_lower
    ]

    if len(name_matches) == 1:
        return {
            "status": "resolved",
            "part": name_matches[0]
        }

    if len(name_matches) > 1:
        return {
            "status": "ambiguous",
            "parts": name_matches
        }

    # ---------------------------------------------------------
    # 3. Generic category words
    # ---------------------------------------------------------

    category_matches = []

    for part in parts:
        category = part.functional_category.lower()

        if category in question_lower:
            category_matches.append(part)

    if len(category_matches) == 1:
        return {
            "status": "resolved",
            "part": category_matches[0]
        }

    if len(category_matches) > 1:
        return {
            "status": "ambiguous",
            "parts": category_matches
        }

    # ---------------------------------------------------------
    # 4. Common engineering keywords
    # ---------------------------------------------------------

    keywords = []

    if "bracket" in question_lower:
        keywords.append("bracket")

    if "shaft" in question_lower:
        keywords.append("shaft")

    if "cover" in question_lower:
        keywords.append("cover")

    if "plate" in question_lower:
        keywords.append("plate")

    if "flange" in question_lower:
        keywords.append("flange")

    if "housing" in question_lower:
        keywords.append("housing")

    if "spacer" in question_lower:
        keywords.append("spacer")

    matches = []

    for part in parts:
        part_text = (
            f"{part.part_number} "
            f"{part.part_name} "
            f"{part.functional_category}"
        ).lower()

        if any(keyword in part_text for keyword in keywords):
            matches.append(part)

    if len(matches) == 1:
        return {
            "status": "resolved",
            "part": matches[0]
        }

    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "parts": matches
        }

    # ---------------------------------------------------------
    # 5. Nothing found
    # ---------------------------------------------------------

    return {
        "status": "not_found"
    }