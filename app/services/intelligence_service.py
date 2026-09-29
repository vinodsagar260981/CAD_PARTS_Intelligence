from sqlalchemy.orm import Session

from app.models_db import CADPartDB, PartUsageDB
from app.services.similarity_service import similarity_score
from app.services.reuse_service import evaluate_reuse


def build_part_intelligence(
    source_part: CADPartDB,
    where_used: list,
    similar_parts: list,
    reuse_candidates: list
) -> dict:

    future_development_candidates = []

    for candidate in reuse_candidates:
        if candidate["decision"] in {
            "reuse_candidate",
            "engineering_review"
        }:
            future_development_candidates.append({
                "part_id": candidate["candidate_part_id"],
                "part_number": candidate["candidate_part_number"],
                "similarity_score": candidate["similarity_score"],
                "decision": candidate["decision"],
                "engineering_review": [
                    "Verify functional requirements.",
                    "Verify material compatibility.",
                    "Verify manufacturing process compatibility.",
                    "Verify dimensional and tolerance requirements.",
                    "Verify load and application requirements.",
                    "Review lifecycle and reuse status."
                ]
            })

    return {
        "part": {
            "part_id": source_part.part_id,
            "part_number": source_part.part_number,
            "part_name": source_part.part_name,
            "revision": source_part.revision,
            "material": source_part.material,
            "manufacturing_process": source_part.manufacturing_process,
            "functional_category": source_part.functional_category,
            "application": source_part.application,
            "load_type": source_part.load_type,
            "criticality": source_part.criticality,
            "environment": source_part.environment,
            "lifecycle_status": source_part.lifecycle_status,
            "usage_count": source_part.usage_count,
            "reuse_count": source_part.reuse_count,
            "active_products": source_part.active_products,
            "approved_for_reuse": source_part.approved_for_reuse
        },

        "where_used": where_used,

        "similar_parts": similar_parts,

        "reuse_candidates": reuse_candidates,

        "future_development_candidates": future_development_candidates
    }
    
def get_part_intelligence(part_id: str, db: Session) -> dict:

    source_part = db.query(CADPartDB).filter(
        CADPartDB.part_id == part_id
    ).first()

    if not source_part:
        return None # type: ignore

    # ---------------------------------------------------------
    # WHERE USED
    # ---------------------------------------------------------

    usages = db.query(PartUsageDB).filter(
        PartUsageDB.part_id == source_part.id
    ).all()

    where_used = [
        {
            "product_id": usage.product.product_id,
            "product_name": usage.product.product_name,
            "product_family": usage.product.product_family,
            "product_revision": usage.product.revision,
            "lifecycle_status": usage.product.lifecycle_status,
            "usage_role": usage.usage_role,
            "quantity": usage.quantity
        }
        for usage in usages
    ]

    # ---------------------------------------------------------
    # SIMILAR PARTS
    # ---------------------------------------------------------

    candidates = db.query(CADPartDB).filter(
        CADPartDB.id != source_part.id
    ).all()

    similar_parts = []

    for candidate in candidates:

        score = similarity_score(
            source_part,
            candidate
        )

        similar_parts.append({
            "part_id": candidate.part_id,
            "part_number": candidate.part_number,
            "part_name": candidate.part_name,
            "similarity_score": score,
            "material": candidate.material,
            "manufacturing_process": candidate.manufacturing_process,
            "functional_category": candidate.functional_category,
            "application": candidate.application,
            "load_type": candidate.load_type,
            "criticality": candidate.criticality,
            "approved_for_reuse": candidate.approved_for_reuse,
            "lifecycle_status": candidate.lifecycle_status,
            "reuse_count": candidate.reuse_count,
            "active_products": candidate.active_products
        })

    similar_parts.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    # ---------------------------------------------------------
    # REUSE CANDIDATES
    # ---------------------------------------------------------

    reuse_candidates = []

    for candidate in candidates:

        score = similarity_score(
            source_part,
            candidate
        )

        reuse_result = evaluate_reuse(
            source_part,
            candidate,
            score
        )

        reuse_result.update({
            "part_name": candidate.part_name,
            "material": candidate.material,
            "manufacturing_process": candidate.manufacturing_process,
            "functional_category": candidate.functional_category,
            "application": candidate.application,
            "load_type": candidate.load_type,
            "criticality": candidate.criticality,
            "lifecycle_status": candidate.lifecycle_status,
            "reuse_count": candidate.reuse_count,
            "active_products": candidate.active_products
        })

        reuse_candidates.append(reuse_result)

    reuse_candidates.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return build_part_intelligence(
        source_part=source_part,
        where_used=where_used,
        similar_parts=similar_parts,
        reuse_candidates=reuse_candidates
    )