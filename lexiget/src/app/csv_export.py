import csv
import os

SUMMARY_COLUMNS = {
    "Invoice": [
        "filename",
        "invoice_number",
        "invoice_date",
        "currency",
        "total_amount",
        "seller_name",
        "seller_address_street",
        "seller_address_city",
        "seller_address_state",
        "seller_address_zipcode",
        "seller_address_phone",
        "seller_address_email",
        "buyer_name",
        "buyer_address_street",
        "buyer_address_city",
        "buyer_address_state",
        "buyer_address_zipcode",
        "buyer_address_phone",
        "buyer_address_email",
        "payment_details_bank_name",
        "payment_details_account_number",
        "payment_details_ifsc_code",
        "payment_details_payment_method",
        "terms_and_conditions",
    ],
    "Receipt": [
        "filename",
        "receipt_number",
        "receipt_date",
        "currency",
        "total_amount",
        "merchant_name",
        "merchant_address_street",
        "merchant_address_city",
        "merchant_address_state",
        "merchant_address_zipcode",
        "merchant_address_phone",
        "merchant_address_email",
        "payment_details_bank_name",
        "payment_details_account_number",
        "payment_details_ifsc_code",
        "payment_details_payment_method",
        "tax",
    ],
    "Delivery Note": [
        "filename",
        "delivery_note_number",
        "delivery_date",
        "reference_number",
        "supplier_name",
        "supplier_address_street",
        "supplier_address_city",
        "supplier_address_state",
        "supplier_address_zipcode",
        "customer_name",
        "customer_address_street",
        "customer_address_city",
        "customer_address_state",
        "customer_address_zipcode",
        "delivery_address_street",
        "delivery_address_city",
        "delivery_address_state",
        "delivery_address_zipcode",
        "transport_details",
    ],
    "Contract": [
        "filename",
        "contract_title",
        "contract_number",
        "effective_date",
        "expiry_date",
        "obligations",
        "payment_terms",
        "termination_clause",
        "governing_law",
    ],
}


ITEM_COLUMNS = {
    "Invoice": [
        "filename",
        "invoice_number",
        "item_index",
        "item_name",
        "item_unit_cost",
        "item_quantity",
        "item_amount",
        "item_discount",
        "item_tax",
        "item_total",
    ],
    "Receipt": [
        "filename",
        "receipt_number",
        "item_index",
        "item_name",
        "item_unit_cost",
        "item_quantity",
        "item_amount",
        "item_discount",
        "item_tax",
        "item_total",
    ],
    "Delivery Note": [
        "filename",
        "delivery_note_number",
        "item_index",
        "item_name",
        "item_quantity",
        "item_unit",
        "item_description",
    ],
    "Contract": ["filename"],
}


ERROR_COLUMNS = ["filename", "error"]


def flatten_dict(data, parent_key=""):
    flat = {}

    for key, value in data.items():
        new_key = f"{parent_key}_{key}" if parent_key else key

        if isinstance(value, dict):
            flat.update(flatten_dict(value, new_key))
        elif isinstance(value, list):
            continue
        else:
            flat[new_key] = value

    return flat


def reorder_columns(rows, preferred_columns):
    found = set()
    for row in rows:
        found.update(row.keys())

    ordered = [col for col in preferred_columns if col in found]
    extras = sorted(col for col in found if col not in ordered)

    return ordered + extras


def write_csv(rows, path, preferred_columns):
    headers = reorder_columns(rows, preferred_columns) if rows else preferred_columns

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        if rows:
            writer.writerows(rows)


def build_summary_rows(batch_result):
    rows = []

    for entry in batch_result.get("results", []):
        filename = entry.get("filename")
        result = entry.get("result", {})

        row = flatten_dict(result)
        row["filename"] = filename
        rows.append(row)

    return rows


def build_item_rows(batch_result, document_type):
    rows = []

    id_field_map = {
        "Invoice": "invoice_number",
        "Receipt": "receipt_number",
        "Delivery Note": "delivery_note_number",
    }

    id_field = id_field_map.get(document_type)

    for entry in batch_result.get("results", []):
        filename = entry.get("filename")
        result = entry.get("result", {})
        items = result.get("items", [])

        if not isinstance(items, list):
            continue

        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue

            row = {
                "filename": filename,
                "item_index": idx,
            }

            if id_field:
                row[id_field] = result.get(id_field)

            for k, v in item.items():
                row[f"item_{k}"] = v

            rows.append(row)

    return rows


def build_error_rows(batch_result):
    return batch_result.get("errors", [])


def export_batch_result_to_csvs(batch_result, document_type, output_dir="exports"):
    os.makedirs(output_dir, exist_ok=True)

    summary_rows = build_summary_rows(batch_result)
    item_rows = build_item_rows(batch_result, document_type)
    error_rows = build_error_rows(batch_result)

    summary_path = os.path.join(output_dir, "document_summary.csv")
    items_path = os.path.join(output_dir, "document_items.csv")
    errors_path = os.path.join(output_dir, "document_errors.csv")

    write_csv(
        summary_rows, summary_path, SUMMARY_COLUMNS.get(document_type, ["filename"])
    )
    write_csv(item_rows, items_path, ITEM_COLUMNS.get(document_type, ["filename"]))
    write_csv(error_rows, errors_path, ERROR_COLUMNS)

    return {
        "summary_csv": summary_path,
        "items_csv": items_path,
        "errors_csv": errors_path,
    }
