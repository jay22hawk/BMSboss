"""
BMS Boss — Base Bill Parser
Abstract base class for utility bill parsers. Each sponsor implements this interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
from models import ExtractedBillData


class BillParser(ABC):
    """Base class for utility bill parsers."""

    @property
    @abstractmethod
    def sponsor_name(self) -> str:
        """Name of the utility sponsor this parser handles."""
        ...

    @abstractmethod
    def detect(self, text: str) -> Tuple[bool, float]:
        """
        Detect if this parser can handle the given bill text.
        Returns (is_match, confidence_score).
        """
        ...

    @abstractmethod
    def extract(self, text: str, pages_text: list[str]) -> ExtractedBillData:
        """
        Extract structured data from bill text.
        Args:
            text: Full text of the PDF
            pages_text: List of text per page
        Returns:
            ExtractedBillData with all extracted fields
        """
        ...

    def validate(self, data: ExtractedBillData) -> list[str]:
        """
        Validate extracted data and return list of warnings.
        Override in subclasses for sponsor-specific validation.
        """
        warnings = []

        if not data.account_number:
            warnings.append("Account number not found")
        if not data.customer_name:
            warnings.append("Customer name not found")
        if not data.service_address:
            warnings.append("Service address not found")
        if not data.total_energy_kwh:
            warnings.append("Total energy usage not found")
        if len(data.monthly_usage_history) < 12:
            warnings.append(
                f"Only {len(data.monthly_usage_history)} months of usage history found (12 expected)"
            )
        if data.annual_usage_kwh and data.annual_usage_kwh <= 0:
            warnings.append("Annual usage is zero or negative")

        return warnings
