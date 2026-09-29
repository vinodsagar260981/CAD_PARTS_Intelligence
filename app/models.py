from pydantic import BaseModel


class BoundingBox(BaseModel):
    length_mm: float
    width_mm: float
    height_mm: float


class Geometry(BaseModel):
    volume_mm3: float
    mass_kg: float
    surface_area_mm2: float
    bounding_box: BoundingBox


class Features(BaseModel):
    body_count: int
    feature_count: int
    hole_count: int
    pocket_count: int
    fillet_count: int
    chamfer_count: int


class Engineering(BaseModel):
    min_wall_thickness_mm: float
    max_wall_thickness_mm: float
    critical_hole_diameter_mm: float
    tolerance_mm: float


class PMI(BaseModel):
    dimension_count: int
    gd_t_count: int
    surface_finish_count: int


class Lifecycle(BaseModel):
    status: str
    usage_count: int
    design_year: int
    last_used_year: int


class Business(BaseModel):
    estimated_manufacturing_cost: float
    estimated_replacement_cost: float
    standard_part: bool


class Reuse(BaseModel):
    approved_for_reuse: bool
    reuse_count: int
    active_products: int
    superseded_by: str | None
    compatible_part_numbers: list[str]


class DesignContext(BaseModel):
    application: str
    functional_category: str
    load_type: str
    criticality: str
    environment: str


class CADPart(BaseModel):
    part_id: str
    part_number: str
    part_name: str
    revision: str
    material: str
    manufacturing_process: str
    units: str

    geometry: Geometry
    features: Features
    engineering: Engineering
    pmi: PMI

    lifecycle: Lifecycle
    business: Business
    reuse: Reuse
    design_context: DesignContext
    
class IntelligenceQuestion(BaseModel):
    question: str
    
class AskRequest(BaseModel):
    question: str