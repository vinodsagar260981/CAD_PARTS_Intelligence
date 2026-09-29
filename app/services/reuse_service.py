from app.models_db import CADPartDB


def evaluate_reuse(
    source_part: CADPartDB,
    candidate_part: CADPartDB,
    similarity_score: float
) -> dict:

    reasons = []
    warnings = []

    # -----------------------------
    # Similarity threshold
    # -----------------------------

    if similarity_score >= 80:
        reasons.append("High design similarity.")
    elif similarity_score >= 60:
        reasons.append("Moderate design similarity.")
    else:
        warnings.append("Low design similarity.")

    # -----------------------------
    # Reuse approval
    # -----------------------------

    if candidate_part.approved_for_reuse:
        reasons.append("Part is approved for reuse.")
    else:
        warnings.append("Part is not approved for reuse.")

    # -----------------------------
    # Lifecycle status
    # -----------------------------

    if candidate_part.lifecycle_status.lower() == "released":
        reasons.append("Candidate part is released.")
    else:
        warnings.append(
            f"Candidate lifecycle status is "
            f"{candidate_part.lifecycle_status}."
        )

    # -----------------------------
    # Superseded part
    # -----------------------------

    if candidate_part.superseded_by:
        warnings.append(
            f"Candidate has been superseded by "
            f"{candidate_part.superseded_by}."
        )

    # -----------------------------
    # Material
    # -----------------------------

    if source_part.material == candidate_part.material:
        reasons.append("Material is the same.")
    else:
        warnings.append(
            f"Material differs: "
            f"{source_part.material} vs "
            f"{candidate_part.material}."
        )

    # -----------------------------
    # Manufacturing process
    # -----------------------------

    if (
        source_part.manufacturing_process
        == candidate_part.manufacturing_process
    ):
        reasons.append("Manufacturing process is the same.")
    else:
        warnings.append(
            "Manufacturing process is different."
        )

    # -----------------------------
    # Design context
    # -----------------------------

    if (
        source_part.functional_category
        == candidate_part.functional_category
    ):
        reasons.append("Functional category matches.")
    else:
        warnings.append("Functional category differs.")

    if source_part.application == candidate_part.application:
        reasons.append("Application matches.")
    else:
        warnings.append("Application differs.")

    if source_part.load_type == candidate_part.load_type:
        reasons.append("Load type matches.")
    else:
        warnings.append("Load type differs.")

    # -----------------------------
    # Reuse decision
    # -----------------------------

    if (
        similarity_score >= 80
        and candidate_part.approved_for_reuse
        and candidate_part.lifecycle_status.lower() == "released"
        and candidate_part.superseded_by is None
    ):
        decision = "reuse_candidate"

    elif (
        similarity_score >= 60
        and candidate_part.approved_for_reuse
        and candidate_part.superseded_by is None
    ):
        decision = "engineering_review"

    else:
        decision = "do_not_reuse_without_review"

    return {
        "candidate_part_id": candidate_part.part_id,
        "candidate_part_number": candidate_part.part_number,
        "similarity_score": similarity_score,
        "decision": decision,
        "reasons": reasons,
        "warnings": warnings
    }