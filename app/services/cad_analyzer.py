from app.models import CADPart


def analyze_cad_part(part: CADPart) -> dict:
    findings = []

    # 1. Minimum wall thickness
    wall = part.engineering.min_wall_thickness_mm

    if wall < 3.0:
        findings.append({
            "type": "wall_thickness",
            "severity": "high",
            "message": f"Minimum wall thickness is {wall} mm. Review structural and manufacturing feasibility."
        })
    elif wall < 4.0:
        findings.append({
            "type": "wall_thickness",
            "severity": "medium",
            "message": f"Minimum wall thickness is {wall} mm. Manufacturing review recommended."
        })

    # 2. Tolerance
    tolerance = part.engineering.tolerance_mm

    if tolerance < 0.05:
        findings.append({
            "type": "tolerance",
            "severity": "high",
            "message": f"Tolerance is {tolerance} mm. Tight manufacturing control may be required."
        })
    elif tolerance == 0.05:
        findings.append({
            "type": "tolerance",
            "severity": "medium",
            "message": f"Tolerance is {tolerance} mm. Verify whether this tolerance is required for all applicable features."
        })

    # 3. Hole count
    holes = part.features.hole_count

    if holes > 10:
        findings.append({
            "type": "manufacturing_complexity",
            "severity": "medium",
            "message": f"Part contains {holes} holes. Review machining complexity."
        })

    # 4. Feature count
    features = part.features.feature_count

    if features > 25:
        findings.append({
            "type": "feature_complexity",
            "severity": "medium",
            "message": f"Part contains {features} features. Review model complexity and manufacturing effort."
        })

    # 5. GD&T
    gd_t = part.pmi.gd_t_count

    if gd_t > 10:
        findings.append({
            "type": "gd_t_complexity",
            "severity": "medium",
            "message": f"Part contains {gd_t} GD&T requirements. Review inspection complexity."
        })

    # 6. Surface finish
    surface_finish = part.pmi.surface_finish_count

    if surface_finish > 5:
        findings.append({
            "type": "surface_finish",
            "severity": "medium",
            "message": f"Part contains {surface_finish} surface-finish requirements. Review manufacturing and inspection requirements."
        })

    # Count findings
    high_count = sum(
        1 for finding in findings
        if finding["severity"] == "high"
    )

    medium_count = sum(
        1 for finding in findings
        if finding["severity"] == "medium"
    )

    # Overall status
    if high_count > 0:
        status = "review_required"
    elif medium_count > 0:
        status = "engineering_review"
    else:
        status = "no_major_issues"

    return {
        "part_id": part.part_id,
        "part_number": part.part_number,
        "part_name": part.part_name,
        "status": status,
        "finding_count": len(findings),
        "findings": findings
    }