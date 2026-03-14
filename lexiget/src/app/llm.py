import json

import ollama

from .schemas import (ContractSchema, DeliveryNoteSchema, InvoiceSchema,
                      ReceiptSchema)

PROMPT_TEMPLATES = {
    "Invoice": """
Extract invoice data.
Use the schema exactly.
Do not guess or invent values.
Use null for missing scalar fields.
Use [] for missing lists.
Return JSON only.
""",
    "Receipt": """
Extract receipt data.
Use the schema exactly.
Do not guess or invent values.
Use null for missing scalar fields.
Use [] for missing lists.
Return JSON only.
""",
    "Delivery Note": """
Extract delivery note data.
Use the schema exactly.
Do not guess or invent values.
Use null for missing scalar fields.
Use [] for missing lists.
Return JSON only.
""",
    "Contract": """
Extract contract data.
Use the schema exactly.
Do not guess or invent values.
Use null for missing scalar fields.
Use [] for missing lists.
Return JSON only.
""",
}

SCHEMA_MAP = {
    "Invoice": InvoiceSchema,
    "Receipt": ReceiptSchema,
    "Delivery Note": DeliveryNoteSchema,
    "Contract": ContractSchema,
}


EXAMPLE_OUTPUTS = {
    "Invoice": {
        "invoice_number": None,
        "invoice_date": None,
        "currency": None,
        "total_amount": None,
        "seller": {
            "name": None,
            "address": {
                "street": None,
                "city": None,
                "state": None,
                "zipcode": None,
                "phone": None,
                "email": None,
            },
        },
        "buyer": {
            "name": None,
            "address": {
                "street": None,
                "city": None,
                "state": None,
                "zipcode": None,
                "phone": None,
                "email": None,
            },
        },
        "payment_details": {
            "bank_name": None,
            "account_number": None,
            "ifsc_code": None,
            "payment_method": None,
        },
        "items": [
            {
                "name": None,
                "unit_cost": None,
                "quantity": None,
                "amount": None,
                "discount": None,
                "tax": None,
                "total": None,
            }
        ],
        "terms_and_conditions": None,
    }
}


def extract_document_data(text: str, document_type: str):
    schema_class = SCHEMA_MAP.get(document_type)
    prompt_template = PROMPT_TEMPLATES.get(document_type)

    if not schema_class or not prompt_template:
        return {"parse_error": f"Unsupported document_type: {document_type}"}

    schema_example = schema_class.model_json_schema()

    example_output = EXAMPLE_OUTPUTS.get(document_type)

    full_prompt = f"""
        You are an AI assistant for structured document extraction.

        Follow the instructions exactly.
        Return valid JSON only.
        Do not include markdown.
        Do not include explanations.
        Do not add extra keys not present in the schema.

        Instructions:
        {prompt_template}

        Target JSON schema:
        {json.dumps(schema_example, indent=2)}

        Example output format:
        {json.dumps(example_output, indent=2)}

        Document Text:
        {text}
        """

    response = ollama.chat(
        model="mistral", messages=[{"role": "user", "content": full_prompt}]
    )

    content = response["message"]["content"].strip()
    content = content.replace("```json", "").replace("```", "").strip()

    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError:
        return {"raw_output": content, "parse_error": "Model did not return valid JSON"}

    try:
        validated = schema_class.model_validate(raw_data)
        return validated.model_dump()
    except Exception as e:
        return {"raw_output": raw_data, "validation_error": str(e)}
