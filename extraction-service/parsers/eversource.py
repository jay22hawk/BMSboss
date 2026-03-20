"""
BMS Boss — Eversource Bill Parser
Handles Eversource electric and gas bills for Massachusetts.

Eversource is one of the major utility providers in Mass Save territory,
serving both electric and gas customers. This parser supports:
  - Eversource Electric bills
  - Eversource Gas bills (separate account/bill from electric)

Status: STUB — detection logic implemented, extraction is scaffolded
        for future development once sample bills are available.
"""

import re
from typing import Tuple
from models import ExtractedBillData, UtilitySponsor, MonthlyUsage
from parsers.base import BillParser


class EversourceParser(BillParser):
    """Parser for Eversource electric and gas bills."""

    @property
    def sponsor_name(self) -> str:
        return "Eversource"

    def detect(self, text: str) -> Tuple[bool, float]:
        """
        Detect if this is an Eversource bill.

        Eversource bills typically contain:
          - "Eversource" or "EVERSOURCE" branding
          - "NSTAR" (legacy name, still appears on some bills)
          - Account format: typically 51-XXX-XXXXX-X or similar
        """
        confidence = 0.0
        text_upper = text.upper()

        # Strong indicators
        if "EVERSOURCE" in text_upper:
            confidence += 0.6
        if "EVERSOURCE ENERGY" in text_upper:
            confidence += 0.2

        # Legacy branding (NSTAR was acquired by Eversource)
        if "NSTAR" in text_upper and "EVERSOURCE" not in text_upper:
            confidence += 0.4

        # Eversource-specific patterns
        if re.search(r'eversource\.com', text, re.IGNORECASE):
            confidence += 0.15
        if re.search(r'Account\s+Number.*\d{2}-\d{3}-\d{5}', text):
            confidence += 0.1

        # Bill type indicators
        if re.search(r'(Electric|Gas)\s+Service', text, re.IGNORECASE):
            confidence += 0.05

        # Negative signals — if National Grid is prominent, this isn't Eversource
        if "NATIONAL GRID" in text_upper:
            confidence -= 0.5

        is_match = confidence >= 0.5
        return is_match, min(confidence, 1.0)

    def extract(self, text: str, pages_text: list[str]) -> ExtractedBillData:
        """
        Extract structured data from an Eversource bill.

        NOTE: This is a scaffold. Once we have sample Eversource bills,
        the extraction methods below will be fleshed out with the actual
        field positions and regex patterns for Eversource's bill layout.
        """
        data = ExtractedBillData()
        data.utility_sponsor = UtilitySponsor.EVERSOURCE

        # Determine bill type (electric vs gas)
        is_gas = bool(re.search(r'Gas\s+Service|Natural\s+Gas|Therms', text, re.IGNORECASE))
        data.bill_type_raw = "gas" if is_gas else "electric"

        # ── Header / Customer Info ──────────────────────────────────
        self._extract_header(text, data)
        self._extract_account_info(text, data)

        # ── Billing Period ──────────────────────────────────────────
        self._extract_billing_period(text, data)

        # ── Usage ───────────────────────────────────────────────────
        if is_gas:
            self._extract_gas_usage(text, data)
        else:
            self._extract_electric_usage(text, data)
            self._extract_usage_history(text, data)

        # ── Charges ─────────────────────────────────────────────────
        self._extract_charges(text, data)

        # ── Supplier Info ───────────────────────────────────────────
        self._extract_supplier_info(text, data)

        return data

    # ── Stub extraction methods ─────────────────────────────────────

    def _extract_header(self, text: str, data: ExtractedBillData):
        """Extract customer name and service address from Eversource bill."""
        # TODO: Implement once sample bill layout is known.
        # Eversource bills typically have customer info in the upper portion,
        # with a service address section distinct from mailing address.
        pass

    def _extract_account_info(self, text: str, data: ExtractedBillData):
        """Extract account number(s) from Eversource bill."""
        # Eversource account format: XX-XXX-XXXXX-X
        match = re.search(r'Account\s*(?:Number|#|No\.?)[:\s]*(\d{2}-\d{3}-\d{5}-\d)', text)
        if match:
            data.account_number = match.group(1)

    def _extract_billing_period(self, text: str, data: ExtractedBillData):
        """Extract billing period dates."""
        # TODO: Implement — Eversource typically shows "Service from MM/DD/YY to MM/DD/YY"
        period = re.search(
            r'Service\s+(?:from|period)\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(?:to|-)\s+(\d{1,2}/\d{1,2}/\d{2,4})',
            text, re.IGNORECASE,
        )
        if period:
            data.billing_period_start = period.group(1)
            data.billing_period_end = period.group(2)

    def _extract_electric_usage(self, text: str, data: ExtractedBillData):
        """Extract current period electric usage (kWh)."""
        # TODO: Implement once layout is known
        kwh_match = re.search(r'(\d[\d,]+)\s*kWh', text)
        if kwh_match:
            data.total_energy_kwh = float(kwh_match.group(1).replace(',', ''))

    def _extract_gas_usage(self, text: str, data: ExtractedBillData):
        """Extract gas usage in therms."""
        # TODO: Eversource gas bills show usage in therms
        # We'll need to store this as annual_fuel_usage in the calculator
        therm_match = re.search(r'(\d[\d,]+)\s*(?:therms|Therms)', text)
        if therm_match:
            data.total_energy_kwh = float(therm_match.group(1).replace(',', ''))

    def _extract_usage_history(self, text: str, data: ExtractedBillData):
        """Extract monthly usage history chart/table data."""
        # TODO: Implement — Eversource bills include a bar chart or table
        # with 13 months of usage history
        pass

    def _extract_charges(self, text: str, data: ExtractedBillData):
        """Extract charge breakdowns (delivery, supply, total)."""
        # TODO: Implement once bill layout is confirmed
        # Eversource bills separate delivery services from supplier services

        # Total amount due
        total = re.search(r'(?:Total|Amount)\s+(?:Due|Charges)[:\s]*\$?([\d,]+\.\d{2})', text, re.IGNORECASE)
        if total:
            data.total_amount_due = float(total.group(1).replace(',', ''))

    def _extract_supplier_info(self, text: str, data: ExtractedBillData):
        """Extract competitive supplier info if customer has one."""
        # TODO: Implement — similar structure to National Grid
        pass

    def validate(self, data: ExtractedBillData) -> list[str]:
        """Eversource-specific validation."""
        warnings = super().validate(data)

        if data.bill_type_raw == "gas" and not data.total_energy_kwh:
            warnings.append("Gas usage (therms) not found — check bill format")

        return warnings
