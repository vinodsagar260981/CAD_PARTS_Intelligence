from sqlalchemy import String, Integer, Float, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CADPartDB(Base):
    __tablename__ = "cad_parts"

    # -----------------------------
    # Basic CAD information
    # -----------------------------

    id: Mapped[int] = mapped_column(primary_key=True)

    part_id: Mapped[str] = mapped_column(String(100), unique=True)
    part_number: Mapped[str] = mapped_column(String(100))
    part_name: Mapped[str] = mapped_column(String(200))
    revision: Mapped[str] = mapped_column(String(20))
    material: Mapped[str] = mapped_column(String(100))
    manufacturing_process: Mapped[str] = mapped_column(String(100))
    units: Mapped[str] = mapped_column(String(20))

    # -----------------------------
    # Geometry
    # -----------------------------

    volume_mm3: Mapped[float] = mapped_column(Float)
    mass_kg: Mapped[float] = mapped_column(Float)
    surface_area_mm2: Mapped[float] = mapped_column(Float)

    bounding_length_mm: Mapped[float] = mapped_column(Float)
    bounding_width_mm: Mapped[float] = mapped_column(Float)
    bounding_height_mm: Mapped[float] = mapped_column(Float)

    # -----------------------------
    # Features
    # -----------------------------

    body_count: Mapped[int] = mapped_column(Integer)
    feature_count: Mapped[int] = mapped_column(Integer)
    hole_count: Mapped[int] = mapped_column(Integer)
    pocket_count: Mapped[int] = mapped_column(Integer)
    fillet_count: Mapped[int] = mapped_column(Integer)
    chamfer_count: Mapped[int] = mapped_column(Integer)

    # -----------------------------
    # Engineering
    # -----------------------------

    min_wall_thickness_mm: Mapped[float] = mapped_column(Float)
    max_wall_thickness_mm: Mapped[float] = mapped_column(Float)
    critical_hole_diameter_mm: Mapped[float] = mapped_column(Float)
    tolerance_mm: Mapped[float] = mapped_column(Float)

    # -----------------------------
    # PMI
    # -----------------------------

    dimension_count: Mapped[int] = mapped_column(Integer)
    gd_t_count: Mapped[int] = mapped_column(Integer)
    surface_finish_count: Mapped[int] = mapped_column(Integer)

    # -----------------------------
    # Lifecycle
    # -----------------------------

    lifecycle_status: Mapped[str] = mapped_column(String(50))
    usage_count: Mapped[int] = mapped_column(Integer)
    design_year: Mapped[int] = mapped_column(Integer)
    last_used_year: Mapped[int] = mapped_column(Integer)

    # -----------------------------
    # Business
    # -----------------------------

    estimated_manufacturing_cost: Mapped[float] = mapped_column(Float)
    estimated_replacement_cost: Mapped[float] = mapped_column(Float)
    standard_part: Mapped[bool] = mapped_column(Boolean)

    # -----------------------------
    # Reuse
    # -----------------------------

    approved_for_reuse: Mapped[bool] = mapped_column(Boolean)
    reuse_count: Mapped[int] = mapped_column(Integer)
    active_products: Mapped[int] = mapped_column(Integer)
    superseded_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    compatible_part_numbers: Mapped[list] = mapped_column(JSON)

    # -----------------------------
    # Design context
    # -----------------------------

    application: Mapped[str] = mapped_column(String(200))
    functional_category: Mapped[str] = mapped_column(String(100))
    load_type: Mapped[str] = mapped_column(String(100))
    criticality: Mapped[str] = mapped_column(String(50))
    environment: Mapped[str] = mapped_column(String(100))

    # -----------------------------
    # Findings relationship
    # -----------------------------

    findings: Mapped[list["CADFindingDB"]] = relationship(
        back_populates="part",
        cascade="all, delete-orphan"
    )


class CADFindingDB(Base):
    __tablename__ = "cad_findings"

    id: Mapped[int] = mapped_column(primary_key=True)

    part_id: Mapped[int] = mapped_column(
        ForeignKey("cad_parts.id")
    )

    finding_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)

    part: Mapped[CADPartDB] = relationship(
        back_populates="findings"
    )
class ProductDB(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[str] = mapped_column(String(100), unique=True)
    product_name: Mapped[str] = mapped_column(String(200))
    product_family: Mapped[str] = mapped_column(String(100))
    revision: Mapped[str] = mapped_column(String(20))
    lifecycle_status: Mapped[str] = mapped_column(String(50))

    usages: Mapped[list["PartUsageDB"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )


class PartUsageDB(Base):
    __tablename__ = "part_usages"

    id: Mapped[int] = mapped_column(primary_key=True)

    part_id: Mapped[int] = mapped_column(
        ForeignKey("cad_parts.id")
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id")
    )

    usage_role: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    part: Mapped[CADPartDB] = relationship()
    product: Mapped[ProductDB] = relationship(
        back_populates="usages"
    )