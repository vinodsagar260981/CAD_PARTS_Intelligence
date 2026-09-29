from app.models_db import CADPartDB


def similarity_score(source: CADPartDB, candidate: CADPartDB) -> float:
    scores = []

    # Geometry — 25%
    geometry_score = (
        numeric_similarity(source.volume_mm3, candidate.volume_mm3) +
        numeric_similarity(source.mass_kg, candidate.mass_kg) +
        numeric_similarity(source.surface_area_mm2, candidate.surface_area_mm2)
    ) / 3

    scores.append(geometry_score * 0.25)

    # Features — 20%
    feature_score = (
        numeric_similarity(source.feature_count, candidate.feature_count) +
        numeric_similarity(source.hole_count, candidate.hole_count) +
        numeric_similarity(source.pocket_count, candidate.pocket_count) +
        numeric_similarity(source.fillet_count, candidate.fillet_count) +
        numeric_similarity(source.chamfer_count, candidate.chamfer_count)
    ) / 5

    scores.append(feature_score * 0.20)

    # Material — 15%
    material_score = 1.0 if source.material == candidate.material else 0.0
    scores.append(material_score * 0.15)

    # Manufacturing — 15%
    manufacturing_score = (
        1.0
        if source.manufacturing_process == candidate.manufacturing_process
        else 0.0
    )

    scores.append(manufacturing_score * 0.15)

    # Engineering — 10%
    engineering_score = (
        numeric_similarity(
            source.min_wall_thickness_mm,
            candidate.min_wall_thickness_mm
        )
        +
        numeric_similarity(
            source.tolerance_mm,
            candidate.tolerance_mm
        )
    ) / 2

    scores.append(engineering_score * 0.10)

    # Design context — 15%
    context_values = [
        source.functional_category == candidate.functional_category,
        source.load_type == candidate.load_type,
        source.application == candidate.application,
        source.environment == candidate.environment
    ]

    context_score = sum(context_values) / len(context_values)

    scores.append(context_score * 0.15)

    return round(sum(scores) * 100, 2)


def numeric_similarity(value1: float, value2: float) -> float:
    if value1 == 0 and value2 == 0:
        return 1.0

    difference = abs(value1 - value2)
    maximum = max(abs(value1), abs(value2))

    return max(0.0, 1.0 - (difference / maximum))