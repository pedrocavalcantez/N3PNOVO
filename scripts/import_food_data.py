import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from app import create_app, db
from app.models import FoodData
from config import Config


def import_food_data(clear_existing=False, show_progress=True, filename="food.xlsx"):
    """
    Import food data from Excel file into the food_data table.

    Args:
        clear_existing (bool): If True, delete all existing food data before importing
        show_progress (bool): If True, show progress messages
    """
    app = create_app()
    with app.app_context():
        try:
            # Get Excel file path from config or use default
            excel_path = os.path.join(Config.BASE_DIR, "data", filename)
            if not os.path.exists(excel_path):
                # Try relative path
                excel_path = os.path.join("data", filename)
                if not os.path.exists(excel_path):
                    raise FileNotFoundError(f"Excel file not found at: {excel_path}")

            if show_progress:
                print(f"Reading Excel file: {excel_path}")

            # Read Excel file
            df = pd.read_excel(excel_path)

            if show_progress:
                print(f"Found {len(df)} rows in Excel file")
                print("\nAvailable columns in Excel file:")
                print(df.columns.tolist())
                print()

            # Clear existing data if requested
            if clear_existing:
                if show_progress:
                    existing_count = FoodData.query.count()
                    print(f"Clearing {existing_count} existing food records...")
                FoodData.query.delete()
                db.session.commit()

            # Validate required fields first
            required_fields = [
                "identificador",
                "alimento",
                "Quantidade",
                "Calorias",
                "Proteínas",
                "Carboidratos",
                "Gorduras",
            ]
            missing_fields = [
                field for field in required_fields if field not in df.columns
            ]
            if missing_fields:
                raise ValueError(f"Missing required columns: {missing_fields}")

            # Get existing codes from database (if not clearing)
            existing_codes = set()
            if not clear_existing:
                if show_progress:
                    print("Checking for existing food codes in database...")
                existing_foods = FoodData.query.with_entities(FoodData.code).all()
                existing_codes = {code[0] for code in existing_foods}
                if show_progress:
                    print(f"Found {len(existing_codes)} existing food codes")

            # Import new data
            imported_count = 0
            skipped_count = 0
            error_count = 0
            batch_size = 100
            batch_codes = set()  # Track codes in current batch to avoid duplicates
            all_used_codes = (
                existing_codes.copy()
            )  # Track all codes used in this import

            for index, row in df.iterrows():
                try:
                    # Get and validate data - use code EXACTLY as it appears in Excel
                    code = str(row["identificador"]).strip()
                    name = str(row["alimento"]).strip()

                    # Check for empty values
                    if not code or not name:
                        if show_progress:
                            print(f"  Skipping row {index + 1}: Empty code or name")
                        skipped_count += 1
                        continue

                    # Code is used exactly as-is from Excel - NO modifications, NO truncation

                    # Validate name length (max 100 characters)
                    if len(name) > 100:
                        if show_progress:
                            print(
                                f"  Warning: Name '{name[:50]}...' is too long, truncating..."
                            )
                        name = name[:100]

                    # Check for duplicates in current batch
                    if code in batch_codes:
                        if show_progress:
                            print(
                                f"  Skipping row {index + 1}: Duplicate code '{code}' in current batch"
                            )
                        skipped_count += 1
                        continue

                    # Check if food with this code already exists in database
                    if code in existing_codes:
                        if show_progress:
                            print(
                                f"  Skipping row {index + 1}: Code '{code}' already exists in database"
                            )
                        skipped_count += 1
                        continue

                    # Convert numeric fields, handle NaN values
                    quantity = (
                        float(row["Quantidade"]) if pd.notna(row["Quantidade"]) else 0.0
                    )
                    calories = (
                        float(row["Calorias"]) if pd.notna(row["Calorias"]) else 0.0
                    )
                    proteins = (
                        float(row["Proteínas"]) if pd.notna(row["Proteínas"]) else 0.0
                    )
                    carbs = (
                        float(row["Carboidratos"])
                        if pd.notna(row["Carboidratos"])
                        else 0.0
                    )
                    fats = float(row["Gorduras"]) if pd.notna(row["Gorduras"]) else 0.0

                    # Create food record
                    food = FoodData(
                        code=code,
                        name=name,
                        quantity=quantity,
                        calories=calories,
                        proteins=proteins,
                        carbs=carbs,
                        fats=fats,
                    )
                    db.session.add(food)
                    batch_codes.add(code)
                    all_used_codes.add(code)  # Track this code as used
                    imported_count += 1

                    # Commit in batches to avoid large transactions and catch errors early
                    if imported_count % batch_size == 0:
                        try:
                            db.session.commit()
                            batch_codes.clear()  # Clear batch codes after successful commit
                            if show_progress:
                                print(
                                    f"  Committed batch: {imported_count} records imported so far..."
                                )
                        except Exception as e:
                            db.session.rollback()
                            # Remove failed codes from batch tracking and all_used_codes
                            for failed_code in batch_codes:
                                all_used_codes.discard(failed_code)
                            batch_codes.clear()
                            raise e

                except Exception as e:
                    error_count += 1
                    if show_progress:
                        print(f"  Error on row {index + 1}: {str(e)}")
                    # Don't add to batch_codes if there was an error
                    continue

            # Commit remaining changes
            try:
                db.session.commit()
                if show_progress and imported_count % batch_size != 0:
                    print(f"  Committed final batch: {imported_count} records imported")
            except Exception as e:
                db.session.rollback()
                raise e

            # Print summary
            print("\n" + "=" * 60)
            print("IMPORT SUMMARY")
            print("=" * 60)
            print(f"Successfully imported: {imported_count} records")
            if skipped_count > 0:
                print(f"Skipped: {skipped_count} records")
            if error_count > 0:
                print(f"Errors: {error_count} records")
            print("=" * 60)
            print("Food data import completed!")

            # Verify import
            total_in_db = FoodData.query.count()
            print(f"Total food records in database: {total_in_db}")

        except FileNotFoundError as e:
            print(f"ERROR: {str(e)}")
            print(
                "\nPlease make sure the food.xlsx file exists in the 'data' directory."
            )
        except Exception as e:
            db.session.rollback()
            print(f"\nERROR importing food data: {str(e)}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    import_food_data(clear_existing=True, filename="food.xlsx")
    import_food_data(clear_existing=False, filename="export.xlsx")
