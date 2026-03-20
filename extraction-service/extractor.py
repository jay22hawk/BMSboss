"""
BMS Boss — Bill Extraction Service
Main extraction logic: takes a PDF, auto-detects the utility sponsor,
extracts structured data, and returns validated results.
"""

import pdfplumber
from typing import Optional
from pathlib import Path
from models import ExtractedBillData, ExtractionResponse
from parsers import NationalGridParser, EversourceParser
from parsers.base import BillParser


# Registry of available parsers
PARSERS: list[BillParser] = [
    NationalGridParser(),
    EversourceParser(),
    # Future: LibertyParser(), UnitilParser(), etc.
]


def extract_bill(pdf_path: str) -> ExtractionResponse:
    """
    Extract structured data from a utility bill PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        ExtractionResponse with extracted data, errors, and warnings
    """
    errors = []
    warnings = []

    # Step 1: Extract text from PDF
    try:
        full_text, pages_text = _extract_pdf_text(pdf_path)
    except Exception as e:
        return ExtractionResponse(
            success=False,
            errors=[f"Failed to read PDF: {str(e)}"]
        )

    if not full_text.strip():
        return ExtractionResponse(
            success=False,
            errors=["PDF appears to be empty or image-only (no extractable text). "
                   "Scanned bills may require OCR preprocessing."]
        )

    # Step 2: Auto-detect utility sponsor
    parser, confidence = _detect_sponsor(full_text)

    if not parser:
        return ExtractionResponse(
            success=False,
            errors=["Could not identify the utility company. "
                   "Currently supported: National Grid. "
                   "Please verify the PDF is a utility energy bill."]
        )

    if confidence < 0.6:
        warnings.append(
            f"Low confidence ({confidence:.0%}) detecting {parser.sponsor_name}. "
            f"Please verify the extracted data."
        )

    # Step 3: Extract structured data
    try:
        data = parser.extract(full_text, pages_text)
    except Exception as e:
        return ExtractionResponse(
            success=False,
            errors=[f"Extraction failed for {parser.sponsor_name}: {str(e)}"]
        )

    # Step 4: Validate
    validation_warnings = parser.validate(data)
    warnings.extend(validation_warnings)

    return ExtractionResponse(
        success=True,
        data=data,
        warnings=warnings,
    )


def _extract_pdf_text(pdf_path: str) -> tuple[str, list[str]]:
    """Extract text from PDF using pdfplumber."""
    pages_text = []
    full_text_parts = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
            full_text_parts.append(text)

    full_text = "\n\n".join(full_text_parts)
    return full_text, pages_text


def _detect_sponsor(text: str) -> tuple[Optional[BillParser], float]:
    """Auto-detect which utility sponsor the bill is from."""
    best_parser = None
    best_confidence = 0.0

    for parser in PARSERS:
        is_match, confidence = parser.detect(text)
        if is_match and confidence > best_confidence:
            best_parser = parser
            best_confidence = confidence

    return best_parser, best_confidence
