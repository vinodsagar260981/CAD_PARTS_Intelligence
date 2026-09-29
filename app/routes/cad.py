import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.cad_analyzer import analyze_cad_part
from app.services.llm_service import generate_engineering_review
from app.services.similarity_service import similarity_score
from app.services.reuse_service import evaluate_reuse
from app.services.llm_service import generate_reuse_review
from app.models_db import (
    CADPartDB,
    CADFindingDB,
    ProductDB,
    PartUsageDB
)
from app.models import CADPart, IntelligenceQuestion
from app.services.intelligence_service import get_part_intelligence
from app.models import CADPart, IntelligenceQuestion, AskRequest
from app.services.part_resolver import resolve_part
from app.services.intelligence_service import get_part_intelligence
from app.services.llm_service import generate_part_intelligence_review


router = APIRouter(prefix="/cad", tags=["CAD"])

BASE_DIR = Path(__file__).resolve().parents[2]
CAD_FILE = BASE_DIR / "data" / "cad_part.json"


def save_part_and_findings(part: CADPart, result: dict, db: Session):
    db_part = db.query(CADPartDB).filter(
        CADPartDB.part_id == part.part_id
    ).first()

    if db_part:
        # -----------------------------
        # Basic CAD information
        # -----------------------------

        db_part.part_number = part.part_number
        db_part.part_name = part.part_name
        db_part.revision = part.revision
        db_part.material = part.material
        db_part.manufacturing_process = part.manufacturing_process
        db_part.units = part.units

        # -----------------------------
        # Geometry
        # -----------------------------

        db_part.volume_mm3 = part.geometry.volume_mm3
        db_part.mass_kg = part.geometry.mass_kg
        db_part.surface_area_mm2 = part.geometry.surface_area_mm2

        db_part.bounding_length_mm = part.geometry.bounding_box.length_mm
        db_part.bounding_width_mm = part.geometry.bounding_box.width_mm
        db_part.bounding_height_mm = part.geometry.bounding_box.height_mm

        # -----------------------------
        # Features
        # -----------------------------

        db_part.body_count = part.features.body_count
        db_part.feature_count = part.features.feature_count
        db_part.hole_count = part.features.hole_count
        db_part.pocket_count = part.features.pocket_count
        db_part.fillet_count = part.features.fillet_count
        db_part.chamfer_count = part.features.chamfer_count

        # -----------------------------
        # Engineering
        # -----------------------------

        db_part.min_wall_thickness_mm = part.engineering.min_wall_thickness_mm
        db_part.max_wall_thickness_mm = part.engineering.max_wall_thickness_mm
        db_part.critical_hole_diameter_mm = part.engineering.critical_hole_diameter_mm
        db_part.tolerance_mm = part.engineering.tolerance_mm

        # -----------------------------
        # PMI
        # -----------------------------

        db_part.dimension_count = part.pmi.dimension_count
        db_part.gd_t_count = part.pmi.gd_t_count
        db_part.surface_finish_count = part.pmi.surface_finish_count

        # -----------------------------
        # Lifecycle
        # -----------------------------

        db_part.lifecycle_status = part.lifecycle.status
        db_part.usage_count = part.lifecycle.usage_count
        db_part.design_year = part.lifecycle.design_year
        db_part.last_used_year = part.lifecycle.last_used_year

        # -----------------------------
        # Business
        # -----------------------------

        db_part.estimated_manufacturing_cost = (
            part.business.estimated_manufacturing_cost
        )
        db_part.estimated_replacement_cost = (
            part.business.estimated_replacement_cost
        )
        db_part.standard_part = part.business.standard_part

        # -----------------------------
        # Reuse
        # -----------------------------

        db_part.approved_for_reuse = part.reuse.approved_for_reuse
        db_part.reuse_count = part.reuse.reuse_count
        db_part.active_products = part.reuse.active_products
        db_part.superseded_by = part.reuse.superseded_by
        db_part.compatible_part_numbers = part.reuse.compatible_part_numbers

        # -----------------------------
        # Design context
        # -----------------------------

        db_part.application = part.design_context.application
        db_part.functional_category = part.design_context.functional_category
        db_part.load_type = part.design_context.load_type
        db_part.criticality = part.design_context.criticality
        db_part.environment = part.design_context.environment

        # Remove previous findings
        db.query(CADFindingDB).filter(
            CADFindingDB.part_id == db_part.id
        ).delete()

    else:
        db_part = CADPartDB(
            # -----------------------------
            # Basic CAD information
            # -----------------------------

            part_id=part.part_id,
            part_number=part.part_number,
            part_name=part.part_name,
            revision=part.revision,
            material=part.material,
            manufacturing_process=part.manufacturing_process,
            units=part.units,

            # -----------------------------
            # Geometry
            # -----------------------------

            volume_mm3=part.geometry.volume_mm3,
            mass_kg=part.geometry.mass_kg,
            surface_area_mm2=part.geometry.surface_area_mm2,

            bounding_length_mm=part.geometry.bounding_box.length_mm,
            bounding_width_mm=part.geometry.bounding_box.width_mm,
            bounding_height_mm=part.geometry.bounding_box.height_mm,

            # -----------------------------
            # Features
            # -----------------------------

            body_count=part.features.body_count,
            feature_count=part.features.feature_count,
            hole_count=part.features.hole_count,
            pocket_count=part.features.pocket_count,
            fillet_count=part.features.fillet_count,
            chamfer_count=part.features.chamfer_count,

            # -----------------------------
            # Engineering
            # -----------------------------

            min_wall_thickness_mm=part.engineering.min_wall_thickness_mm,
            max_wall_thickness_mm=part.engineering.max_wall_thickness_mm,
            critical_hole_diameter_mm=part.engineering.critical_hole_diameter_mm,
            tolerance_mm=part.engineering.tolerance_mm,

            # -----------------------------
            # PMI
            # -----------------------------

            dimension_count=part.pmi.dimension_count,
            gd_t_count=part.pmi.gd_t_count,
            surface_finish_count=part.pmi.surface_finish_count,

            # -----------------------------
            # Lifecycle
            # -----------------------------

            lifecycle_status=part.lifecycle.status,
            usage_count=part.lifecycle.usage_count,
            design_year=part.lifecycle.design_year,
            last_used_year=part.lifecycle.last_used_year,

            # -----------------------------
            # Business
            # -----------------------------

            estimated_manufacturing_cost=(
                part.business.estimated_manufacturing_cost
            ),
            estimated_replacement_cost=(
                part.business.estimated_replacement_cost
            ),
            standard_part=part.business.standard_part,

            # -----------------------------
            # Reuse
            # -----------------------------

            approved_for_reuse=part.reuse.approved_for_reuse,
            reuse_count=part.reuse.reuse_count,
            active_products=part.reuse.active_products,
            superseded_by=part.reuse.superseded_by,
            compatible_part_numbers=part.reuse.compatible_part_numbers,

            # -----------------------------
            # Design context
            # -----------------------------

            application=part.design_context.application,
            functional_category=part.design_context.functional_category,
            load_type=part.design_context.load_type,
            criticality=part.design_context.criticality,
            environment=part.design_context.environment
        )

        db.add(db_part)
        db.flush()

    # -----------------------------
    # Save findings
    # -----------------------------

    for finding in result["findings"]:
        db.add(
            CADFindingDB(
                part_id=db_part.id,
                finding_type=finding["type"],
                severity=finding["severity"],
                message=finding["message"]
            )
        )

    db.commit()
    db.refresh(db_part)

    return db_part


@router.post("/analyze")
def analyze_part(part: CADPart, db: Session = Depends(get_db)):
    result = analyze_cad_part(part)

    save_part_and_findings(part, result, db)

    return result


@router.get("/analyze-file")
def analyze_cad_file(db: Session = Depends(get_db)):
    with open(CAD_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    results = []

    for part_data in data:
        part = CADPart(**part_data)

        result = analyze_cad_part(part)

        save_part_and_findings(
            part,
            result,
            db
        )

        results.append(result)

    return {
        "part_count": len(results),
        "parts": results
    }


@router.get("/parts/{part_id}")
def get_part(part_id: str, db: Session = Depends(get_db)):
    part = db.query(CADPartDB).filter(
        CADPartDB.part_id == part_id
    ).first()

    if not part:
        raise HTTPException(
            status_code=404,
            detail="CAD part not found"
        )

    findings = db.query(CADFindingDB).filter(
        CADFindingDB.part_id == part.id
    ).all()

    return {
        # -----------------------------
        # Basic CAD information
        # -----------------------------

        "part_id": part.part_id,
        "part_number": part.part_number,
        "part_name": part.part_name,
        "revision": part.revision,
        "material": part.material,
        "image_url": f"/images/{part.part_number}.png",
        "manufacturing_process": part.manufacturing_process,
        "units": part.units,

        # -----------------------------
        # Geometry
        # -----------------------------

        "geometry": {
            "volume_mm3": part.volume_mm3,
            "mass_kg": part.mass_kg,
            "surface_area_mm2": part.surface_area_mm2,
            "bounding_box": {
                "length_mm": part.bounding_length_mm,
                "width_mm": part.bounding_width_mm,
                "height_mm": part.bounding_height_mm
            }
        },

        # -----------------------------
        # Features
        # -----------------------------

        "features": {
            "body_count": part.body_count,
            "feature_count": part.feature_count,
            "hole_count": part.hole_count,
            "pocket_count": part.pocket_count,
            "fillet_count": part.fillet_count,
            "chamfer_count": part.chamfer_count
        },

        # -----------------------------
        # Engineering
        # -----------------------------

        "engineering": {
            "min_wall_thickness_mm": part.min_wall_thickness_mm,
            "max_wall_thickness_mm": part.max_wall_thickness_mm,
            "critical_hole_diameter_mm": part.critical_hole_diameter_mm,
            "tolerance_mm": part.tolerance_mm
        },

        # -----------------------------
        # PMI
        # -----------------------------

        "pmi": {
            "dimension_count": part.dimension_count,
            "gd_t_count": part.gd_t_count,
            "surface_finish_count": part.surface_finish_count
        },

        # -----------------------------
        # Lifecycle
        # -----------------------------

        "lifecycle": {
            "status": part.lifecycle_status,
            "usage_count": part.usage_count,
            "design_year": part.design_year,
            "last_used_year": part.last_used_year
        },

        # -----------------------------
        # Business
        # -----------------------------

        "business": {
            "estimated_manufacturing_cost": part.estimated_manufacturing_cost,
            "estimated_replacement_cost": part.estimated_replacement_cost,
            "standard_part": part.standard_part
        },

        # -----------------------------
        # Reuse
        # -----------------------------

        "reuse": {
            "approved_for_reuse": part.approved_for_reuse,
            "reuse_count": part.reuse_count,
            "active_products": part.active_products,
            "superseded_by": part.superseded_by,
            "compatible_part_numbers": part.compatible_part_numbers
        },

        # -----------------------------
        # Design context
        # -----------------------------

        "design_context": {
            "application": part.application,
            "functional_category": part.functional_category,
            "load_type": part.load_type,
            "criticality": part.criticality,
            "environment": part.environment
        },

        # -----------------------------
        # Inspection findings
        # -----------------------------

        "findings": [
            {
                "type": finding.finding_type,
                "severity": finding.severity,
                "message": finding.message
            }
            for finding in findings
        ]
    }

@router.get("/parts/{part_id}/similar")
def get_similar_parts(
    part_id: str,
    db: Session = Depends(get_db)
):
    source_part = db.query(CADPartDB).filter(
        CADPartDB.part_id == part_id
    ).first()

    if not source_part:
        raise HTTPException(
            status_code=404,
            detail="CAD part not found"
        )

    candidates = db.query(CADPartDB).filter(
        CADPartDB.part_id != part_id
    ).all()

    results = []

    for candidate in candidates:
        score = similarity_score(source_part, candidate)

        results.append({
            "part_id": candidate.part_id,
            "part_number": candidate.part_number,
            "part_name": candidate.part_name,
            "similarity_score": score,
            "approved_for_reuse": candidate.approved_for_reuse,
            "manufacturing_process": candidate.manufacturing_process,
            "material": candidate.material
        })

    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return {
        "source_part": part_id,
        "similar_parts": results
    }
    
@router.get("/parts/{part_id}/reuse")
def get_reuse_candidates(
    part_id: str,
    db: Session = Depends(get_db)
):
    source_part = db.query(CADPartDB).filter(
        CADPartDB.part_id == part_id
    ).first()

    if not source_part:
        raise HTTPException(
            status_code=404,
            detail="CAD part not found"
        )

    candidates = db.query(CADPartDB).filter(
        CADPartDB.part_id != part_id
    ).all()

    results = []

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

        results.append(reuse_result)

    results.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return {
        "source_part": {
            "part_id": source_part.part_id,
            "part_number": source_part.part_number,
            "part_name": source_part.part_name
        },
        "reuse_candidates": results
    }
    
@router.post("/parts/{part_id}/reuse-review")
def reuse_review(
    part_id: str,
    db: Session = Depends(get_db)
):
    source_part = db.query(CADPartDB).filter(
        CADPartDB.part_id == part_id
    ).first()

    if not source_part:
        raise HTTPException(
            status_code=404,
            detail="CAD part not found"
        )

    candidates = db.query(CADPartDB).filter(
        CADPartDB.part_id != part_id
    ).all()

    reuse_candidates = []

    for candidate in candidates:
        score = similarity_score(
            source_part,
            candidate
        )

        result = evaluate_reuse(
            source_part,
            candidate,
            score
        )

        reuse_candidates.append(result)

    reuse_candidates.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    source_data = {
        "part_id": source_part.part_id,
        "part_number": source_part.part_number,
        "part_name": source_part.part_name,
        "material": source_part.material,
        "manufacturing_process": source_part.manufacturing_process,
        "functional_category": source_part.functional_category,
        "application": source_part.application,
        "load_type": source_part.load_type,
        "criticality": source_part.criticality
    }

    review = generate_reuse_review(
        source_data,
        reuse_candidates
    )

    return {
        "source_part": source_data,
        "reuse_candidates": reuse_candidates,
        "engineering_review": review
    }

@router.get("/parts/{part_id}/where-used")
def get_where_used(part_id: str, db: Session = Depends(get_db)):
    part = db.query(CADPartDB).filter(
        CADPartDB.part_id == part_id
    ).first()

    if not part:
        raise HTTPException(
            status_code=404,
            detail="CAD part not found"
        )

    usages = db.query(PartUsageDB).filter(
        PartUsageDB.part_id == part.id
    ).all()

    return {
        "part_id": part.part_id,
        "part_number": part.part_number,
        "where_used": [
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
    }

@router.get("/parts/{part_id}/intelligence")
def get_part_intelligence_route(
    part_id: str,
    db: Session = Depends(get_db)
):
    intelligence = get_part_intelligence(
        part_id=part_id,
        db=db
    )

    if not intelligence:
        raise HTTPException(
            status_code=404,
            detail="CAD part not found"
        )

    return intelligence

@router.post("/parts/{part_id}/intelligence-review")
def generate_part_intelligence(
    part_id: str,
    request: IntelligenceQuestion,
    db: Session = Depends(get_db)
):
    intelligence = get_part_intelligence(
        part_id=part_id,
        db=db
    )

    review = generate_part_intelligence_review(
        question=request.question,
        intelligence=intelligence
    )

    return {
        "part_id": part_id,
        "question": request.question,
        "engineering_review": review
    }


@router.post("/ask")
def ask_engineering(
    request: AskRequest,
    db: Session = Depends(get_db)
):
    resolved = resolve_part(
        question=request.question,
        db=db
    )

    if resolved["status"] == "not_found":
        return {
            "status": "not_found",
            "question": request.question,
            "message": "I could not identify a CAD part from your question."
        }

    if resolved["status"] == "ambiguous":
        return {
            "status": "ambiguous",
            "question": request.question,
            "message": "Multiple CAD parts may match your question.",
            "parts": [
                {
                    "part_id": part.part_id,
                    "part_number": part.part_number,
                    "part_name": part.part_name
                }
                for part in resolved["parts"]
            ]
        }

    part = resolved["part"]

    intelligence = get_part_intelligence(
        part_id=part.part_id,
        db=db
    )

    review = generate_part_intelligence_review(
        question=request.question,
        intelligence=intelligence
    )

    return {
        "status": "resolved",
        "part": {
            "part_id": part.part_id,
            "part_number": part.part_number,
            "part_name": part.part_name
        },
        "question": request.question,
        "engineering_review": review
    }