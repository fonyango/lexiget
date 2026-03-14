import io
import os
import zipfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from .csv_export import export_batch_result_to_csvs
from .extractor import chunk_text, extract_text_from_pdf, rank_chunks
from .llm import extract_document_data

app = FastAPI(title="LexiGet")

SUPPORTED_DOCUMENT_TYPES = {
    "Invoice",
    "Receipt",
    "Delivery Note",
    "Contract",
}


@app.post("/extract_single")
async def extract_single(
    file: UploadFile = File(...),
    document_type: str = Form(...),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")

    if document_type not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document_type. Must be one of: {sorted(SUPPORTED_DOCUMENT_TYPES)}",
        )

    try:
        pdf_bytes = io.BytesIO(await file.read())
        text = extract_text_from_pdf(pdf_bytes)

        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No extractable text found in PDF",
            )

        chunks = chunk_text(text)
        ranked_chunks = rank_chunks(chunks)
        focused_text = "\n\n".join(ranked_chunks[:3])

        result = extract_document_data(
            text=focused_text,
            document_type=document_type,
        )

        single_record = {
            "processed_files": 1,
            "failed_files": 0,
            "results": [
                {
                    "filename": file.filename,
                    "result": result,
                }
            ],
            "errors": [],
        }

        csv_info = export_batch_result_to_csvs(single_record)

        summary_path = csv_info["summary_csv"]
        items_path = csv_info["items_csv"]
        errors_path = csv_info["errors_csv"]

        output_zip_buffer = io.BytesIO()

        with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(summary_path, "document_summary.csv")
            z.write(items_path, "document_items.csv")
            z.write(errors_path, "document_errors.csv")

        output_zip_buffer.seek(0)

        base_name = os.path.splitext(file.filename)[0]
        download_name = f"{base_name}_results.zip"

        return StreamingResponse(
            output_zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_extract")
async def batch_extract(
    zip_file: UploadFile = File(...),
    document_type: str = Form(...),
):
    if not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a ZIP file")

    if document_type not in SUPPORTED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported document_type. Must be one of: {sorted(SUPPORTED_DOCUMENT_TYPES)}",
        )

    zip_bytes = await zip_file.read()
    zip_buffer = io.BytesIO(zip_bytes)

    results = []
    errors = []

    with zipfile.ZipFile(zip_buffer, "r") as z:
        pdf_files = [
            f
            for f in z.namelist()
            if f.lower().endswith(".pdf")
            and not f.startswith("__MACOSX/")
            and not f.split("/")[-1].startswith("._")
        ]

        if not pdf_files:
            raise HTTPException(status_code=400, detail="No PDFs found in ZIP")

        for pdf_name in pdf_files:
            try:
                with z.open(pdf_name) as pdf_file:
                    pdf_bytes = io.BytesIO(pdf_file.read())
                    text = extract_text_from_pdf(pdf_bytes)

                    if not text or not text.strip():
                        raise ValueError("No extractable text found in PDF")

                    chunks = chunk_text(text)
                    ranked_chunks = rank_chunks(chunks)
                    focused_text = "\n\n".join(ranked_chunks[:3])

                    result = extract_document_data(
                        text=focused_text,
                        document_type=document_type,
                    )

                    results.append(
                        {
                            "filename": pdf_name,
                            "result": result,
                        }
                    )

            except Exception as e:
                errors.append(
                    {
                        "filename": pdf_name,
                        "error": str(e),
                    }
                )

    batch_record = {
        "processed_files": len(results),
        "failed_files": len(errors),
        "results": results,
        "errors": errors,
    }

    csv_info = export_batch_result_to_csvs(
        batch_result=batch_record, document_type=document_type
    )

    summary_path = csv_info["summary_csv"]
    items_path = csv_info["items_csv"]
    errors_path = csv_info["errors_csv"]

    output_zip_buffer = io.BytesIO()

    with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(summary_path, "document_summary.csv")
        z.write(items_path, "document_items.csv")
        z.write(errors_path, "document_errors.csv")

    output_zip_buffer.seek(0)

    base_name = os.path.splitext(zip_file.filename)[0]
    download_name = f"{base_name}_results.zip"

    return StreamingResponse(
        output_zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )
