"""Manager ingredient inventory, batches, waste, and history."""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_UP

import pymysql
from flask import (
    abort,
    flash,
    g,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    url_for,
)

from .reviewed_excel_import import read_reviewed_table

BASE_UNITS = ("kg", "g", "l", "ml", "pcs", "packs", "trays")
WASTE_REASONS = ("Expired", "Spoiled", "Damaged", "Preparation Waste", "Other")


def normalize_unit(value):
    return str(value or "").strip().lower()


def valid_unit(value):
    return 1 <= len(value) <= 40 and not any(ord(char) < 32 for char in value)


def install_ingredient_inventory(app, get_db, business_required, validate_csrf):
    trash_schema_ready = False

    def ensure_ingredient_trash_schema():
        nonlocal trash_schema_ready
        if trash_schema_ready:
            return
        database = get_db()
        with database.cursor() as cursor:
            cursor.execute(
                """SELECT COLUMN_NAME FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='ingredients'
                     AND COLUMN_NAME IN ('trashed_at','purged_at','status_before_trash')"""
            )
            existing = {row["COLUMN_NAME"] for row in cursor.fetchall()}
            if "trashed_at" not in existing:
                cursor.execute("ALTER TABLE ingredients ADD COLUMN trashed_at DATETIME NULL AFTER status")
            if "purged_at" not in existing:
                cursor.execute("ALTER TABLE ingredients ADD COLUMN purged_at DATETIME NULL AFTER trashed_at")
            if "status_before_trash" not in existing:
                cursor.execute("ALTER TABLE ingredients ADD COLUMN status_before_trash VARCHAR(20) NULL AFTER purged_at")
        trash_schema_ready = True

    def cleanup_expired_ingredient_trash(business_id):
        database = get_db()
        with database.cursor() as cursor:
            cursor.execute(
                """SELECT ingredient_id FROM ingredients
                   WHERE business_id=%s AND trashed_at IS NOT NULL AND purged_at IS NULL
                     AND trashed_at<=DATE_SUB(NOW(),INTERVAL 30 DAY)""",
                (business_id,),
            )
            expired_ids = [row["ingredient_id"] for row in cursor.fetchall()]
        for ingredient_id in expired_ids:
            try:
                with database.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM ingredients WHERE ingredient_id=%s AND business_id=%s",
                        (ingredient_id, business_id),
                    )
            except pymysql.err.IntegrityError:
                with database.cursor() as cursor:
                    cursor.execute(
                        """UPDATE ingredients SET purged_at=NOW(),status='Inactive'
                           WHERE ingredient_id=%s AND business_id=%s""",
                        (ingredient_id, business_id),
                    )

    def manager_business(database):
        with database.cursor() as cursor:
            cursor.execute(
                """SELECT business_id, business_name, business_type, created_at
                   FROM businesses WHERE user_id=%s""",
                (g.user["user_id"],),
            )
            owner = cursor.fetchone()
        if owner is None:
            abort(403, description="Your account has no linked business.")
        return owner

    def positive_decimal(value, label):
        try:
            number = Decimal(str(value).strip())
            if (
                not number.is_finite()
                or number <= 0
                or number > Decimal("99999999999.999")
                or number != number.quantize(Decimal("0.001"))
            ):
                raise ValueError
            return number
        except (InvalidOperation, ValueError):
            raise ValueError(f"Enter a valid {label} greater than zero.")

    def nonnegative_decimal(value, label):
        try:
            number = Decimal(str(value).strip())
            if (
                not number.is_finite()
                or number < 0
                or number > Decimal("99999999999.999")
                or number != number.quantize(Decimal("0.001"))
            ):
                raise ValueError
            return number
        except (InvalidOperation, ValueError):
            raise ValueError(f"Enter a valid {label} of zero or more.")

    @app.route("/business/ingredient-inventory/export")
    @business_required
    def export_ingredients():
        from io import BytesIO
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from flask import send_file
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill

        database = get_db()
        owner = manager_business(database)
        ensure_ingredient_trash_schema()
        with database.cursor() as cursor:
            cursor.execute(
                """SELECT i.ingredient_name,i.base_unit,i.low_stock_threshold,
                          COALESCE(SUM(CASE WHEN b.expiration_date IS NULL
                            OR b.expiration_date>=CURDATE()
                            THEN b.remaining_quantity ELSE 0 END),0) AS current_stock
                   FROM ingredients i
                   LEFT JOIN inventory_batches b ON b.ingredient_id=i.ingredient_id
                   WHERE i.business_id=%s AND i.status='Active'
                     AND i.trashed_at IS NULL AND i.purged_at IS NULL
                   GROUP BY i.ingredient_id ORDER BY i.ingredient_name""",
                (owner["business_id"],),
            )
            rows = cursor.fetchall()
        if not rows:
            flash("There are no ingredients to export.", "ingredient_error")
            return redirect(url_for("ingredient_inventory"))

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Ingredients"
        sheet.append(["Ingredient", "Unit", "Current stock", "Low-stock level"])
        for row in rows:
            sheet.append([row["ingredient_name"], row["base_unit"], row["current_stock"], row["low_stock_threshold"]])
            sheet.cell(sheet.max_row, 1).data_type = "s"
            sheet.cell(sheet.max_row, 2).data_type = "s"
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="3B5F49")
        for column, width in (("A", 34), ("B", 14), ("C", 20), ("D", 20)):
            sheet.column_dimensions[column].width = width
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        output = BytesIO()
        workbook.save(output)
        workbook.close()
        output.seek(0)
        stamp = datetime.now(ZoneInfo("Asia/Manila")).strftime("%Y-%m-%d")
        return send_file(
            output,
            as_attachment=True,
            download_name=f"foodcast-ingredients-{stamp}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    @app.route("/business/ingredient-inventory/import", methods=["GET", "POST"])
    @business_required
    def import_ingredients():
        request.max_content_length = 6 * 1024 * 1024
        database = get_db()
        owner = manager_business(database)
        ensure_ingredient_trash_schema()
        errors = []
        review_rows = None

        if request.method == "POST":
            validate_csrf()
            action = request.form.get("action", "upload")
            if action == "upload":
                try:
                    review_rows = read_reviewed_table(
                        request.files.get("file"),
                        ("name", "unit", "low-stock threshold"),
                        "ingredient",
                    )
                except ValueError as error:
                    errors = [str(error)]
            elif action == "save":
                try:
                    count = int(request.form.get("row_count", "0"))
                    if not 1 <= count <= 500:
                        raise ValueError("Review between 1 and 500 rows.")
                    review_rows = []
                    clean_rows = []
                    seen = set()
                    for index in range(count):
                        row = {
                            "source": request.form.get(f"source_{index}", str(index + 2)),
                            "include": request.form.get(f"include_{index}") == "yes",
                            "name": request.form.get(f"name_{index}", "").strip(),
                            "unit": normalize_unit(request.form.get(f"unit_{index}", "")),
                            "low-stock threshold": request.form.get(
                                f"threshold_{index}", ""
                            ).strip(),
                        }
                        review_rows.append(row)
                        if not row["include"]:
                            continue
                        if not 1 <= len(row["name"]) <= 100:
                            errors.append(f"Row {row['source']}: enter an ingredient name of 1–100 characters.")
                        if not valid_unit(row["unit"]):
                            errors.append(f"Row {row['source']}: choose a valid measurement unit.")
                        try:
                            threshold = nonnegative_decimal(
                                row["low-stock threshold"], "low-stock level"
                            )
                        except ValueError as error:
                            errors.append(f"Row {row['source']}: {error}")
                            continue
                        key = row["name"].casefold()
                        if key in seen:
                            errors.append(f"Row {row['source']}: this ingredient is duplicated in the file.")
                        seen.add(key)
                        clean_rows.append((row["name"], row["unit"], threshold))

                    if not any(row["include"] for row in review_rows):
                        raise ValueError("Select at least one ingredient row to import.")
                    if errors:
                        raise ValueError("Correct the listed rows before importing.")

                    database.begin()
                    with database.cursor() as cursor:
                        cursor.execute(
                            """SELECT ingredient_name FROM ingredients
                               WHERE business_id=%s FOR UPDATE""",
                            (owner["business_id"],),
                        )
                        existing_names = {
                            row["ingredient_name"].casefold()
                            for row in cursor.fetchall()
                        }
                        if existing_names.intersection(seen):
                            raise ValueError(
                                "An ingredient with one of these names already exists."
                            )
                        cursor.executemany(
                            """INSERT INTO ingredients (
                                   business_id, ingredient_name, base_unit,
                                   low_stock_threshold, status
                               ) VALUES (%s,%s,%s,%s,'Active')""",
                            [
                                (owner["business_id"], name, unit, threshold)
                                for name, unit, threshold in clean_rows
                            ],
                        )
                    database.commit()
                    flash(f"{len(clean_rows)} ingredients imported. No stock was added.", "ingredient_success")
                    return redirect(url_for("ingredient_inventory"))
                except (ValueError, TypeError) as error:
                    database.rollback()
                    if not errors:
                        errors = [str(error)]
                except pymysql.MySQLError:
                    database.rollback()
                    app.logger.exception("Ingredient import failed.")
                    errors = ["The ingredient import could not be saved."]
            else:
                errors = ["Choose a valid import action."]

        return render_template(
            "business/import_ingredients.html",
            business=owner,
            base_units=BASE_UNITS,
            review_rows=review_rows,
            errors=errors,
        )

    @app.route("/business/ingredient-inventory", methods=["GET", "POST"])
    @business_required
    def ingredient_inventory():
        database = get_db()
        owner = manager_business(database)
        ensure_ingredient_trash_schema()
        cleanup_expired_ingredient_trash(owner["business_id"])

        if request.method == "POST":
            validate_csrf()
            action = request.form.get("action", "").strip()
            try:
                database.begin()
                with database.cursor() as cursor:
                    if action == "add_ingredient":
                        name = request.form.get("ingredient_name", "").strip()
                        unit = normalize_unit(request.form.get("base_unit", ""))
                        threshold = nonnegative_decimal(
                            request.form.get("low_stock_threshold", ""),
                            "low-stock level",
                        )
                        if not 1 <= len(name) <= 100:
                            raise ValueError("Enter an ingredient name.")
                        if not valid_unit(unit):
                            raise ValueError("Select a valid measurement unit.")
                        cursor.execute(
                            """INSERT INTO ingredients (
                                   business_id, ingredient_name, base_unit,
                                   low_stock_threshold, status
                               ) VALUES (%s, %s, %s, %s, 'Active')""",
                            (owner["business_id"], name, unit, threshold),
                        )
                        success = f"{name} was added to Ingredient Inventory."

                    elif action == "edit_ingredient":
                        ingredient_id = int(request.form.get("ingredient_id", ""))
                        name = request.form.get("ingredient_name", "").strip()
                        unit = normalize_unit(request.form.get("base_unit", ""))
                        threshold = nonnegative_decimal(
                            request.form.get("low_stock_threshold", ""),
                            "low-stock level",
                        )
                        if not 1 <= len(name) <= 100:
                            raise ValueError("Enter an ingredient name.")
                        if not valid_unit(unit):
                            raise ValueError("Select a valid measurement unit.")
                        cursor.execute(
                            """UPDATE ingredients
                               SET ingredient_name=%s, base_unit=%s,
                                   low_stock_threshold=%s
                               WHERE ingredient_id=%s AND business_id=%s""",
                            (name, unit, threshold, ingredient_id,
                             owner["business_id"]),
                        )
                        if cursor.rowcount != 1:
                            raise ValueError("That ingredient is unavailable.")
                        success = f"{name} was updated."

                    elif action == "archive_ingredients":
                        ingredient_ids = {
                            int(value)
                            for value in request.form.getlist("ingredient_id")
                            if value.strip().isdigit() and int(value) > 0
                        }
                        if not ingredient_ids:
                            raise ValueError("Select at least one ingredient to archive.")
                        placeholders = ", ".join(["%s"] * len(ingredient_ids))
                        cursor.execute(
                            f"""UPDATE ingredients
                                SET status='Inactive'
                                WHERE business_id=%s
                                  AND status='Active'
                                  AND ingredient_id IN ({placeholders})""",
                            (owner["business_id"], *sorted(ingredient_ids)),
                        )
                        if cursor.rowcount == 0:
                            raise ValueError("The selected ingredients are unavailable.")
                        success = (
                            f"{cursor.rowcount} ingredient"
                            f"{'s were' if cursor.rowcount != 1 else ' was'} archived. "
                            "Inventory history was kept."
                        )

                    elif action == "delete_ingredients":
                        ingredient_ids = {
                            int(value)
                            for value in request.form.getlist("ingredient_id")
                            if value.strip().isdigit() and int(value) > 0
                        }
                        if not ingredient_ids:
                            raise ValueError("Select at least one ingredient to delete.")
                        placeholders = ", ".join(["%s"] * len(ingredient_ids))
                        cursor.execute(
                            f"""SELECT ingredient_id FROM ingredients
                                WHERE business_id=%s
                                  AND trashed_at IS NULL
                                  AND ingredient_id IN ({placeholders})
                                FOR UPDATE""",
                            (owner["business_id"], *sorted(ingredient_ids)),
                        )
                        if {row["ingredient_id"] for row in cursor.fetchall()} != ingredient_ids:
                            raise ValueError("One or more selected ingredients are unavailable.")
                        cursor.execute(
                            f"""UPDATE ingredients
                                SET status_before_trash=status,status='Inactive',
                                    trashed_at=NOW(),purged_at=NULL
                                WHERE business_id=%s AND trashed_at IS NULL
                                  AND ingredient_id IN ({placeholders})""",
                            (owner["business_id"], *sorted(ingredient_ids)),
                        )
                        success = (
                            f"{len(ingredient_ids)} ingredient"
                            f"{'s were' if len(ingredient_ids) != 1 else ' was'} moved to Trash."
                        )

                    elif action == "restore_ingredient":
                        ingredient_id = int(request.form.get("ingredient_id", ""))
                        cursor.execute(
                            """UPDATE ingredients
                               SET status=COALESCE(status_before_trash,'Active'),
                                   trashed_at=NULL,purged_at=NULL,status_before_trash=NULL
                               WHERE ingredient_id=%s AND business_id=%s
                                 AND trashed_at IS NOT NULL AND purged_at IS NULL""",
                            (ingredient_id, owner["business_id"]),
                        )
                        if cursor.rowcount != 1:
                            raise ValueError("That ingredient is no longer in Trash.")
                        success = "The ingredient was restored."

                    elif action == "permanently_delete_ingredient":
                        ingredient_id = int(request.form.get("ingredient_id", ""))
                        cursor.execute(
                            """DELETE FROM ingredients
                               WHERE ingredient_id=%s AND business_id=%s
                                 AND trashed_at IS NOT NULL""",
                            (ingredient_id, owner["business_id"]),
                        )
                        if cursor.rowcount != 1:
                            raise ValueError("That ingredient is no longer in Trash.")
                        success = "The ingredient was permanently deleted."

                    elif action == "permanently_delete_ingredients":
                        ingredient_ids = {
                            int(value)
                            for value in request.form.getlist("ingredient_id")
                            if value.strip().isdigit() and int(value) > 0
                        }
                        if not ingredient_ids or len(ingredient_ids) > 200:
                            raise ValueError(
                                "Select between 1 and 200 ingredients to permanently delete."
                            )
                        placeholders = ", ".join(["%s"] * len(ingredient_ids))
                        selected_ids = tuple(sorted(ingredient_ids))
                        cursor.execute(
                            f"""SELECT ingredient_id FROM ingredients
                                WHERE business_id=%s AND trashed_at IS NOT NULL
                                  AND purged_at IS NULL
                                  AND ingredient_id IN ({placeholders})
                                FOR UPDATE""",
                            (owner["business_id"], *selected_ids),
                        )
                        found_ids = {row["ingredient_id"] for row in cursor.fetchall()}
                        if found_ids != ingredient_ids:
                            raise ValueError(
                                "One or more selected ingredients are no longer in Trash."
                            )
                        cursor.execute(
                            f"""DELETE FROM ingredients
                                WHERE business_id=%s AND trashed_at IS NOT NULL
                                  AND ingredient_id IN ({placeholders})""",
                            (owner["business_id"], *selected_ids),
                        )
                        success = (
                            f"{len(ingredient_ids)} ingredient(s) were permanently deleted."
                        )

                    elif action == "receive_stock":
                        ingredient_id = int(request.form.get("ingredient_id", ""))
                        quantity = positive_decimal(
                            request.form.get("quantity", ""), "quantity"
                        )
                        received_date = date.fromisoformat(
                            request.form.get("received_date", "")
                        )
                        expiration_text = request.form.get("expiration_date", "").strip()
                        expiration_date = (
                            date.fromisoformat(expiration_text)
                            if expiration_text else None
                        )
                        if expiration_date and expiration_date < received_date:
                            raise ValueError(
                                "Expiration date cannot be before the received date."
                            )
                        cursor.execute(
                            """SELECT ingredient_name
                               FROM ingredients
                               WHERE ingredient_id=%s AND business_id=%s
                                 AND status='Active' FOR UPDATE""",
                            (ingredient_id, owner["business_id"]),
                        )
                        ingredient = cursor.fetchone()
                        if ingredient is None:
                            raise ValueError("Select an active ingredient.")
                        cursor.execute(
                            """SELECT COALESCE(SUM(remaining_quantity), 0) AS total
                               FROM inventory_batches WHERE ingredient_id=%s""",
                            (ingredient_id,),
                        )
                        previous = cursor.fetchone()["total"]
                        cursor.execute(
                            """INSERT INTO inventory_batches (
                                   ingredient_id, quantity_received,
                                   remaining_quantity, received_date,
                                   expiration_date, recorded_by
                               ) VALUES (%s, %s, %s, %s, %s, %s)""",
                            (ingredient_id, quantity, quantity, received_date,
                             expiration_date, g.user["user_id"]),
                        )
                        batch_id = cursor.lastrowid
                        cursor.execute(
                            """INSERT INTO inventory_transactions (
                                   ingredient_id, batch_id, transaction_type,
                                   quantity, previous_quantity, new_quantity,
                                   user_id, notes
                               ) VALUES (%s, %s, 'RECEIVED', %s, %s, %s, %s, %s)""",
                            (ingredient_id, batch_id, quantity, previous,
                             previous + quantity, g.user["user_id"],
                             "Stock received"),
                        )
                        success = f"Stock received for {ingredient['ingredient_name']}."

                    elif action == "record_waste":
                        ingredient_id = int(request.form.get("ingredient_id", ""))
                        quantity = positive_decimal(
                            request.form.get("quantity", ""), "waste quantity"
                        )
                        reason = request.form.get("reason", "").strip()
                        notes = request.form.get("notes", "").strip()
                        if reason not in WASTE_REASONS:
                            raise ValueError("Select a valid waste reason.")
                        if len(notes) > 255:
                            raise ValueError("Notes cannot exceed 255 characters.")
                        cursor.execute(
                            """SELECT ingredient_name
                               FROM ingredients
                               WHERE ingredient_id=%s AND business_id=%s
                               FOR UPDATE""",
                            (ingredient_id, owner["business_id"]),
                        )
                        ingredient = cursor.fetchone()
                        if ingredient is None:
                            raise ValueError("Select one of your ingredients.")
                        cursor.execute(
                            """SELECT batch_id, remaining_quantity
                               FROM inventory_batches
                               WHERE ingredient_id=%s AND remaining_quantity > 0
                               ORDER BY
                                 CASE WHEN expiration_date IS NULL THEN 1 ELSE 0 END,
                                 expiration_date, received_date, batch_id
                               FOR UPDATE""",
                            (ingredient_id,),
                        )
                        batches = cursor.fetchall()
                        available = sum(
                            (row["remaining_quantity"] for row in batches),
                            Decimal("0"),
                        )
                        if quantity > available:
                            raise ValueError(
                                f"Only {available} is available. Waste cannot exceed stock."
                            )
                        remaining = quantity
                        running_total = available
                        for batch in batches:
                            if remaining <= 0:
                                break
                            deducted = min(remaining, batch["remaining_quantity"])
                            new_batch_quantity = batch["remaining_quantity"] - deducted
                            cursor.execute(
                                """UPDATE inventory_batches
                                   SET remaining_quantity=%s WHERE batch_id=%s""",
                                (new_batch_quantity, batch["batch_id"]),
                            )
                            cursor.execute(
                                """INSERT INTO inventory_transactions (
                                       ingredient_id, batch_id, transaction_type,
                                       quantity, previous_quantity, new_quantity,
                                       user_id, notes
                                   ) VALUES (%s, %s, 'WASTE', %s, %s, %s, %s, %s)""",
                                (ingredient_id, batch["batch_id"], deducted,
                                 running_total, running_total - deducted,
                                 g.user["user_id"],
                                 f"{reason}: {notes}".rstrip(": ")),
                            )
                            running_total -= deducted
                            remaining -= deducted
                        success = f"Waste recorded for {ingredient['ingredient_name']}."
                    elif action == "adjust_stock":
                        ingredient_id = int(request.form.get("ingredient_id", ""))
                        actual_quantity = nonnegative_decimal(
                            request.form.get("actual_quantity", ""),
                            "actual quantity",
                        )
                        reason = request.form.get("adjustment_reason", "").strip()
                        notes = request.form.get("notes", "").strip()
                        expiration_text = request.form.get(
                            "adjustment_expiration_date", ""
                        ).strip()
                        expiration_date = (
                            date.fromisoformat(expiration_text)
                            if expiration_text else None
                        )
                        allowed_reasons = (
                            "Physical Count Correction",
                            "Starting Balance Correction",
                            "Data Entry Correction",
                            "Other",
                        )
                        if reason not in allowed_reasons:
                            raise ValueError("Select a valid adjustment reason.")
                        if len(notes) > 255:
                            raise ValueError("Notes cannot exceed 255 characters.")
                        if expiration_date and expiration_date < date.today():
                            raise ValueError("Expiration date cannot be before today.")

                        cursor.execute(
                            """SELECT ingredient_name, base_unit
                               FROM ingredients
                               WHERE ingredient_id=%s AND business_id=%s
                                 AND status='Active'
                               FOR UPDATE""",
                            (ingredient_id, owner["business_id"]),
                        )
                        ingredient = cursor.fetchone()
                        if ingredient is None:
                            raise ValueError("Select an active ingredient.")
                        cursor.execute(
                            """SELECT batch_id, remaining_quantity
                               FROM inventory_batches
                               WHERE ingredient_id=%s
                                 AND remaining_quantity>0
                                 AND (expiration_date IS NULL
                                      OR expiration_date>=CURDATE())
                               ORDER BY
                                 CASE WHEN expiration_date IS NULL THEN 1 ELSE 0 END,
                                 expiration_date, received_date, batch_id
                               FOR UPDATE""",
                            (ingredient_id,),
                        )
                        batches = cursor.fetchall()
                        current_quantity = sum(
                            (batch["remaining_quantity"] for batch in batches),
                            Decimal("0"),
                        )
                        difference = actual_quantity - current_quantity
                        if difference == 0:
                            raise ValueError(
                                "The actual quantity already matches Foodcast."
                            )
                        adjustment_notes = (
                            f"{reason}: {notes}" if notes else reason
                        )
                        if difference < 0:
                            remaining = -difference
                            running_total = current_quantity
                            for batch in batches:
                                if remaining <= 0:
                                    break
                                deducted = min(
                                    remaining, batch["remaining_quantity"]
                                )
                                cursor.execute(
                                    """UPDATE inventory_batches
                                       SET remaining_quantity=remaining_quantity-%s
                                       WHERE batch_id=%s""",
                                    (deducted, batch["batch_id"]),
                                )
                                cursor.execute(
                                    """INSERT INTO inventory_transactions (
                                           ingredient_id, batch_id,
                                           transaction_type, quantity,
                                           previous_quantity, new_quantity,
                                           user_id, notes
                                       ) VALUES (%s,%s,'ADJUSTMENT',%s,%s,%s,%s,%s)""",
                                    (
                                        ingredient_id, batch["batch_id"],
                                        deducted, running_total,
                                        running_total-deducted,
                                        g.user["user_id"], adjustment_notes,
                                    ),
                                )
                                running_total -= deducted
                                remaining -= deducted
                        else:
                            cursor.execute(
                                """INSERT INTO inventory_batches (
                                       ingredient_id, quantity_received,
                                       remaining_quantity, received_date,
                                       expiration_date, recorded_by
                                   ) VALUES (%s,%s,%s,CURDATE(),%s,%s)""",
                                (
                                    ingredient_id, difference, difference,
                                    expiration_date, g.user["user_id"],
                                ),
                            )
                            batch_id = cursor.lastrowid
                            cursor.execute(
                                """INSERT INTO inventory_transactions (
                                       ingredient_id, batch_id,
                                       transaction_type, quantity,
                                       previous_quantity, new_quantity,
                                       user_id, notes
                                   ) VALUES (%s,%s,'ADJUSTMENT',%s,%s,%s,%s,%s)""",
                                (
                                    ingredient_id, batch_id, difference,
                                    current_quantity, actual_quantity,
                                    g.user["user_id"], adjustment_notes,
                                ),
                            )
                        success = (
                            f"{ingredient['ingredient_name']} was adjusted from "
                            f"{current_quantity} to {actual_quantity} "
                            f"{ingredient['base_unit']}."
                        )
                    else:
                        raise ValueError("Choose an inventory action.")
                database.commit()
                if action == "add_ingredient":
                    flash("Ingredient added", "ingredient_added")
                    flash("", "reopen_add_ingredient")
                    return redirect(url_for("ingredient_inventory"))
                flash(success, "ingredient_success")
            except (ValueError, TypeError) as error:
                database.rollback()
                flash(str(error), "ingredient_error")
            except pymysql.err.IntegrityError as error:
                database.rollback()
                if error.args[0] == 1062:
                    flash("That ingredient already exists.", "ingredient_error")
                elif action in (
                    "delete_ingredients",
                    "permanently_delete_ingredient",
                    "permanently_delete_ingredients",
                ):
                    flash(
                        "An ingredient with stock, recipe, production, or inventory history cannot be deleted.",
                        "ingredient_error",
                    )
                else:
                    app.logger.exception("Ingredient inventory update failed.")
                    flash("The inventory update could not be saved.", "ingredient_error")
            except pymysql.MySQLError:
                database.rollback()
                app.logger.exception("Ingredient inventory update failed.")
                flash("The inventory update could not be saved.", "ingredient_error")
            if action == "add_ingredient":
                flash("", "reopen_add_ingredient")
            return redirect(url_for("ingredient_inventory"))

        search = request.args.get("search", "").strip()[:100]
        with database.cursor() as cursor:
            cursor.execute(
                """SELECT DISTINCT LOWER(base_unit) AS base_unit FROM ingredients
                   WHERE business_id=%s ORDER BY base_unit""",
                (owner["business_id"],),
            )
            saved_units = [row["base_unit"] for row in cursor.fetchall()]
        ingredient_units = tuple(dict.fromkeys((*BASE_UNITS, *saved_units)))
        with database.cursor() as cursor:
            cursor.execute(
                """SELECT
                       i.ingredient_id, i.ingredient_name, i.base_unit,
                       i.low_stock_threshold, i.status, i.created_at,
                       COALESCE(SUM(CASE
                           WHEN (b.expiration_date IS NULL OR b.expiration_date >= CURDATE())
                           THEN b.remaining_quantity ELSE 0 END), 0) AS usable_stock,
                       COALESCE(SUM(CASE
                           WHEN b.expiration_date < CURDATE()
                           THEN b.remaining_quantity ELSE 0 END), 0) AS expired_stock,
                       MIN(CASE
                           WHEN b.remaining_quantity > 0 AND b.expiration_date >= CURDATE()
                           THEN b.expiration_date END) AS nearest_expiration
                   FROM ingredients AS i
                   LEFT JOIN inventory_batches AS b
                     ON b.ingredient_id=i.ingredient_id
                   WHERE i.business_id=%s
                     AND i.status='Active'
                     AND i.trashed_at IS NULL AND i.purged_at IS NULL
                   GROUP BY i.ingredient_id
                   ORDER BY i.ingredient_name""",
                (owner["business_id"],),
            )
            ingredients = cursor.fetchall()

            cursor.execute(
                """SELECT ingredient_id,ingredient_name,trashed_at,
                          GREATEST(0,30-DATEDIFF(NOW(),trashed_at)) AS days_remaining
                   FROM ingredients
                   WHERE business_id=%s AND trashed_at IS NOT NULL AND purged_at IS NULL
                   ORDER BY trashed_at DESC""",
                (owner["business_id"],),
            )
            trashed_ingredients = cursor.fetchall()

            cursor.execute(
                """SELECT ingredient_id, ingredient_name, base_unit
                   FROM ingredients
                   WHERE business_id=%s AND status='Active'
                   ORDER BY ingredient_name""",
                (owner["business_id"],),
            )
            ingredient_choices = cursor.fetchall()

            cursor.execute(
                """SELECT b.batch_id, b.quantity_received, b.remaining_quantity,
                          b.received_date, b.expiration_date,
                          i.ingredient_name, i.base_unit
                   FROM inventory_batches AS b
                   INNER JOIN ingredients AS i ON i.ingredient_id=b.ingredient_id
                   WHERE i.business_id=%s AND i.trashed_at IS NULL
                     AND i.purged_at IS NULL AND b.remaining_quantity > 0
                   ORDER BY COALESCE(b.expiration_date, '9999-12-31'),
                            b.received_date, b.batch_id
                   LIMIT 100""",
                (owner["business_id"],),
            )
            batches = cursor.fetchall()

            cursor.execute(
                """SELECT COUNT(*) AS open_batch_count
                   FROM inventory_batches AS b
                   INNER JOIN ingredients AS i ON i.ingredient_id=b.ingredient_id
                   WHERE i.business_id=%s AND i.trashed_at IS NULL
                     AND i.purged_at IS NULL AND b.remaining_quantity > 0""",
                (owner["business_id"],),
            )
            open_batch_count = cursor.fetchone()["open_batch_count"]

            cursor.execute(
                """SELECT t.inventory_transaction_id, t.transaction_type,
                          t.quantity, t.new_quantity, t.notes, t.created_at,
                          i.ingredient_name, i.base_unit, u.username, u.role
                   FROM inventory_transactions AS t
                   INNER JOIN ingredients AS i ON i.ingredient_id=t.ingredient_id
                   INNER JOIN users AS u ON u.user_id=t.user_id
                   WHERE i.business_id=%s AND i.trashed_at IS NULL
                     AND i.purged_at IS NULL
                   ORDER BY t.inventory_transaction_id DESC LIMIT 100""",
                (owner["business_id"],),
            )
            history = cursor.fetchall()
            for entry in history:
                username = entry["username"] or ""
                if username.lower().startswith("cashier"):
                    entry["display_name"] = "Staff"
                elif entry["role"] == "Manager":
                    entry["display_name"] = owner["business_name"]
                else:
                    entry["display_name"] = username.replace("_", " ").title()

            cursor.execute(
                """SELECT fr.forecast_run_id,
                          MIN(fpd.forecast_date) AS requirement_date
                   FROM forecast_runs AS fr
                   INNER JOIN forecast_product_days AS fpd
                     ON fpd.forecast_run_id=fr.forecast_run_id
                   WHERE fr.business_id=%s
                     AND fr.forecast_run_id=(
                       SELECT MAX(forecast_run_id)
                       FROM forecast_runs WHERE business_id=%s
                     )
                     AND fpd.forecast_date>=CURDATE()
                   GROUP BY fr.forecast_run_id""",
                (owner['business_id'], owner['business_id']),
            )
            forecast_info = cursor.fetchone()
            requirements_by_ingredient = {}
            unconfigured_forecast_products = []
            if forecast_info:
                cursor.execute(
                    """SELECT r.ingredient_id,
                              SUM(
                                COALESCE(
                                  adjustment.adjusted_quantity,
                                  fpd.predicted_quantity
                                ) * r.quantity_required
                                / r.recipe_yield
                              ) AS required_quantity
                       FROM forecast_product_days AS fpd
                       INNER JOIN products AS p
                         ON p.product_id=fpd.product_id
                       LEFT JOIN forecast_adjustments AS adjustment
                         ON adjustment.forecast_product_day_id=
                            fpd.forecast_product_day_id
                       INNER JOIN product_recipes AS r
                         ON r.product_id=p.product_id
                       INNER JOIN ingredients AS i
                         ON i.ingredient_id=r.ingredient_id
                        AND i.business_id=p.business_id
                       WHERE fpd.forecast_run_id=%s
                         AND fpd.forecast_date=%s
                         AND p.business_id=%s
                         AND p.status='Active'
                       GROUP BY r.ingredient_id""",
                    (
                        forecast_info['forecast_run_id'],
                        forecast_info['requirement_date'],
                        owner['business_id'],
                    ),
                )
                requirements_by_ingredient = {
                    row['ingredient_id']: row['required_quantity']
                    for row in cursor.fetchall()
                }

                cursor.execute(
                    """SELECT p.product_name
                       FROM forecast_product_days AS fpd
                       INNER JOIN products AS p
                         ON p.product_id=fpd.product_id
                       LEFT JOIN product_recipes AS r
                         ON r.product_id=p.product_id
                       WHERE fpd.forecast_run_id=%s
                         AND fpd.forecast_date=%s
                         AND p.business_id=%s
                         AND p.status='Active'
                         AND fpd.predicted_quantity > 0
                       GROUP BY p.product_id,p.product_name
                       HAVING COUNT(r.recipe_id)=0
                       ORDER BY p.product_name""",
                    (
                        forecast_info['forecast_run_id'],
                        forecast_info['requirement_date'],
                        owner['business_id'],
                    ),
                )
                unconfigured_forecast_products = [
                    row['product_name'] for row in cursor.fetchall()
                ]

        today = date.today()
        recommendations = []
        for ingredient in ingredients:
            stock = ingredient["usable_stock"]
            threshold = ingredient["low_stock_threshold"]
            expiry = ingredient["nearest_expiration"]
            if stock <= 0:
                ingredient["stock_label"] = "Out of Stock"
                ingredient["stock_class"] = "danger"
                ingredient["summary_class"] = "low"
            elif stock <= threshold:
                ingredient["stock_label"] = "Running Low"
                ingredient["stock_class"] = "warning"
                ingredient["summary_class"] = "low"
            elif expiry and (expiry - today).days <= 7:
                ingredient["stock_label"] = "Expires Soon"
                ingredient["stock_class"] = "warning"
                ingredient["summary_class"] = "expiring"
            else:
                ingredient["stock_label"] = "Enough Stock"
                ingredient["stock_class"] = "good"
                ingredient["summary_class"] = "enough"

            required = requirements_by_ingredient.get(
                ingredient['ingredient_id'], Decimal('0')
            )
            required = required.quantize(
                Decimal('0.001'), rounding=ROUND_UP
            )
            shortage = max(required - stock, Decimal('0'))
            threshold_gap = max(
                ingredient['low_stock_threshold'] - stock,
                Decimal('0'),
            )
            restock_quantity = max(shortage, threshold_gap)
            ingredient['forecast_required'] = required
            ingredient['forecast_shortage'] = shortage
            ingredient['restock_quantity'] = restock_quantity

            if restock_quantity > 0:
                if shortage > 0:
                    reason = 'Not enough for the next forecast'
                else:
                    reason = 'Stock is below the running-low level'
                recommendations.append({
                    'ingredient_name': ingredient['ingredient_name'],
                    'base_unit': ingredient['base_unit'],
                    'available': stock,
                    'required': required,
                    'restock_quantity': restock_quantity,
                    'reason': reason,
                })

        return render_template(
            "business/ingredient_inventory.html",
            business=owner,
            ingredients=ingredients,
            trashed_ingredients=trashed_ingredients,
            batches=batches,
            history=history,
            ingredient_choices=ingredient_choices,
            open_batch_count=open_batch_count,
            base_units=ingredient_units,
            waste_reasons=WASTE_REASONS,
            adjustment_reasons=(
                "Physical Count Correction",
                "Starting Balance Correction",
                "Data Entry Correction",
                "Other",
            ),
            search=search,
            today=today.isoformat(),
            reopen_add_ingredient=bool(
                get_flashed_messages(category_filter=["reopen_add_ingredient"])
            ),
            ingredient_added=bool(
                get_flashed_messages(category_filter=["ingredient_added"])
            ),
            forecast_info=forecast_info,
            recommendations=recommendations,
            unconfigured_forecast_products=unconfigured_forecast_products,
        )



