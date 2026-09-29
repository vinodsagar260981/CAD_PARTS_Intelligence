import json
from pathlib import Path

from app.database import SessionLocal
from app.models_db import CADPartDB, ProductDB, PartUsageDB


BASE_DIR = Path(__file__).resolve().parents[1]

PRODUCT_FILE = BASE_DIR / "data" / "products.json"
USAGE_FILE = BASE_DIR / "data" / "part_usages.json"


def load_products():
    db = SessionLocal()

    try:
        with open(PRODUCT_FILE, "r", encoding="utf-8") as file:
            products = json.load(file)

        with open(USAGE_FILE, "r", encoding="utf-8") as file:
            usages = json.load(file)

        for product_data in products:
            product = db.query(ProductDB).filter(
                ProductDB.product_id == product_data["product_id"]
            ).first()

            if not product:
                product = ProductDB(**product_data)
                db.add(product)
                db.flush()

        for usage_data in usages:
            part = db.query(CADPartDB).filter(
                CADPartDB.part_number == usage_data["part_number"]
            ).first()

            product = db.query(ProductDB).filter(
                ProductDB.product_id == usage_data["product_id"]
            ).first()

            if not part or not product:
                continue

            existing_usage = db.query(PartUsageDB).filter(
                PartUsageDB.part_id == part.id,
                PartUsageDB.product_id == product.id
            ).first()

            if not existing_usage:
                usage = PartUsageDB(
                    part_id=part.id,
                    product_id=product.id,
                    usage_role=usage_data["usage_role"],
                    quantity=usage_data["quantity"]
                )

                db.add(usage)

        db.commit()

        print("Products and part usage data loaded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    load_products()