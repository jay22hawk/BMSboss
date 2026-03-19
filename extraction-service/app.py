"""
BMS Boss — FastAPI Extraction Service
API endpoints for bill extraction and Excel generation.
"""

import os
import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from models import (
    BMSCalculatorInput, ExtractionResponse, GenerationResponse,
    ExtractedBillData
)
from extractor import extract_bill
from excel_generator import (
    generate_calculator, merge_bill_data_to_calculator
)

app = FastAPI(
    title="BMS Boss — Extraction Service",
    description="PDF bill extraction and BMS Calculator Excel generation",
    version="0.1.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temp directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "bms-boss-extraction"}


@app.post("/extract", response_model=ExtractionResponse)
async def extract_bill_endpoint(file: UploadFile = File(...)):
    """
    Upload a utility bill PDF and extract structured data.
    Returns auto-detected sponsor, account info, usage, demand, etc.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are accepted")

    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Extract
        result = extract_bill(str(file_path))
        return result

    finally:
        # Clean up
        if file_path.exists():
            file_path.unlink()


@app.post("/generate", response_model=GenerationResponse)
async def generate_excel_endpoint(calculator_input: BMSCalculatorInput):
    """
    Generate a completed Prescriptive BMS Calculator Excel file
    from the provided form data.
    """
    file_id = str(uuid.uuid4())
    output_path = OUTPUT_DIR / f"BMS_Calculator_{file_id}.xlsx"

    result = generate_calculator(
        calculator_input=calculator_input,
        output_path=str(output_path),
    )

    return result


@app.post("/extract-and-merge")
async def extract_and_merge_endpoint(
    file: UploadFile = File(...),
):
    """
    Upload a bill PDF, extract data, and return a pre-populated
    BMSCalculatorInput with auto-filled fields from the bill.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are accepted")

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.pdf"

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        extraction = extract_bill(str(file_path))

        if not extraction.success or not extraction.data:
            return {
                "success": False,
                "extraction": extraction.model_dump(),
                "calculator_input": None,
            }

        # Create calculator input with auto-filled fields from bill
        calculator_input = BMSCalculatorInput()
        calculator_input = merge_bill_data_to_calculator(
            extraction.data, calculator_input
        )

        return {
            "success": True,
            "extraction": extraction.model_dump(),
            "calculator_input": calculator_input.model_dump(),
        }

    finally:
        if file_path.exists():
            file_path.unlink()


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download a generated Excel file."""
    file_path = OUTPUT_DIR / f"BMS_Calculator_{file_id}.xlsx"
    if not file_path.exists():
        raise HTTPException(404, "File not found")

    return FileResponse(
        path=str(file_path),
        filename=f"Prescriptive_BMS_Calculator_{file_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
