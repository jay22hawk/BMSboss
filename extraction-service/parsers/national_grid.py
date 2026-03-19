"""
BMS Boss — National Grid Bill Parser
Extracts structured data from National Grid electricity bill PDFs.

National Grid Bill Format (3+ pages):
  Page 1: Header (account, address, billing period), Account Balance,
          Detail of Current Charges (usage readings, demand), Usage History
  Page 2: Delivery Services charge detail
  Page 3: Supply Services, Other Charges/Adjustments
"""

import re
from typing import Optional, Tuple, List
from .base import BillParser
from models import (
    ExtractedBillData, MonthlyUsage, DemandReading, UsageReading,
    UtilitySponsor, BillType
)


class NationalGridParser(BillParser):
    """Parser for National Grid electric bills."""

    @property
    def sponsor_name(self) -> str:
        return "National Grid"

    def detect(self, text: str) -> Tuple[bool, float]:
        """Detect if this is a National Grid bill."""
        indicators = [
            ("nationalgrid" in text.lower().replace(" ", ""), 0.4),
            ("www.nationalgridus.com" in text.lower(), 0.3),
            ("ngrid.com" in text.lower(), 0.2),
            ("national grid services" in text.lower(), 0.1),
        ]
        score = sum(weight for match, weight in indicators if match)
        return (score >= 0.4, min(score, 1.0))

    def extract(self, text: str, pages_text: list[str]) -> ExtractedBillData:
        """Extract all fields from a National Grid electric bill."""
        data = ExtractedBillData(
            utility_sponsor=UtilitySponsor.NATIONAL_GRID,
            bill_type=BillType.ELECTRIC,
        )

        # Use page 1 for most extraction
        page1 = pages_text[0] if pages_text else text

        # Extract each section
        self._extract_header(page1, data)
        self._extract_account_info(text, data)
        self._extract_billing_period(page1, data)
        self._extract_rate_meter_info(page1, data)
        self._extract_usage_readings(page1, data)
        self._extract_demand(page1, data)
        self._extract_usage_history(page1, data)
        self._extract_billed_demand_history(page1, data)
        self._extract_charges(text, data)
        self._extract_supplier_info(text, data)

        # Calculate annual usage from history if available
        if data.monthly_usage_history:
            data.annual_usage_kwh = sum(m.kwh for m in data.monthly_usage_history)

        # Set confidence based on how many fields were extracted
        filled_fields = sum(1 for v in [
            data.account_number, data.customer_name, data.service_address,
            data.billing_period_start, data.total_energy_kwh, data.rate_type,
            data.meter_number, len(data.monthly_usage_history) > 0,
            data.demand_kw, data.total_delivery_charges,
        ] if v)
        data.confidence_score = min(filled_fields / 10.0, 1.0)

        return data

    # ─── Header Extraction ───────────────────────────────────────────────

    def _extract_header(self, text: str, data: ExtractedBillData):
        """Extract service address and customer name from bill header."""

        # SERVICE FOR pattern - National Grid bills have this header block
        # Format: SERVICE FOR\nCUSTOMER NAME\n%DEPT (optional)\nADDRESS\nCITY STATE ZIP
        service_for_match = re.search(
            r'SERVICE\s+FOR\s*\n'
            r'(.+?)(?:\n|$)'        # Customer/building name (line 1)
            r'(?:(.+?)(?:\n|$))?'   # Optional line 2 (dept, c/o, etc.)
            r'(?:(.+?)(?:\n|$))?'   # Optional line 3
            r'(?:(.+?)(?:\n|$))?',  # Optional line 4
            text, re.IGNORECASE
        )

        if service_for_match:
            lines = [g.strip() for g in service_for_match.groups() if g and g.strip()]
            if lines:
                data.customer_name = lines[0]

            # Find the address line (contains a number at start)
            for line in lines[1:]:
                if re.match(r'\d+\s', line):
                    data.service_address = line
                    break

            # Find city/state/zip line
            for line in lines:
                city_match = re.match(
                    r'([A-Z][A-Z\s]+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)',
                    line
                )
                if city_match:
                    data.service_city = city_match.group(1).strip()
                    data.service_state = city_match.group(2)
                    data.service_zip = city_match.group(3)
                    break

    # ─── Account Info ────────────────────────────────────────────────────

    def _extract_account_info(self, text: str, data: ExtractedBillData):
        """Extract account number."""
        # ACCOUNT NUMBER followed by the number
        # Format: ACCOUNT NUMBER\n15022-63006 or ACCOUNT NUMBER 15022-63006
        acct_match = re.search(
            r'ACCOUNT\s+NUMBER\s*[:\n]\s*(\d{5}-\d{5})',
            text, re.IGNORECASE
        )
        if acct_match:
            data.account_number = acct_match.group(1)
        else:
            # Try alternate format: Acct No: 15022-63006
            acct_match = re.search(
                r'Acct\s+No[:\s]+(\d{5}-\d{5})',
                text, re.IGNORECASE
            )
            if acct_match:
                data.account_number = acct_match.group(1)

    # ─── Billing Period ──────────────────────────────────────────────────

    def _extract_billing_period(self, text: str, data: ExtractedBillData):
        """Extract billing period dates."""
        # BILLING PERIOD\nJan 16, 2026 to Feb 13, 2026
        period_match = re.search(
            r'BILLING\s+PERIOD\s*\n?\s*'
            r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})\s+'
            r'to\s+'
            r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            text, re.IGNORECASE
        )
        if period_match:
            data.billing_period_start = period_match.group(1).strip()
            data.billing_period_end = period_match.group(2).strip()

        # SERVICE PERIOD Jan 16 - Feb 13
        svc_period_match = re.search(
            r'SERVICE\s+PERIOD\s+'
            r'([A-Za-z]+\s+\d{1,2})\s*-\s*([A-Za-z]+\s+\d{1,2})',
            text, re.IGNORECASE
        )
        if svc_period_match and not data.billing_period_start:
            data.billing_period_start = svc_period_match.group(1).strip()
            data.billing_period_end = svc_period_match.group(2).strip()

        # NUMBER OF DAYS IN PERIOD 28
        days_match = re.search(
            r'NUMBER\s+OF\s+DAYS\s+IN\s+PERIOD\s+(\d+)',
            text, re.IGNORECASE
        )
        if days_match:
            data.days_in_period = int(days_match.group(1))

        # DATE BILL ISSUED
        bill_date_match = re.search(
            r'DATE\s+BILL\s+ISSUED\s*\n?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            text, re.IGNORECASE
        )
        if bill_date_match:
            data.bill_date = bill_date_match.group(1).strip()

    # ─── Rate & Meter Info ───────────────────────────────────────────────

    def _extract_rate_meter_info(self, text: str, data: ExtractedBillData):
        """Extract rate type, meter number, voltage, load zone."""

        # RATE Time-of-Use G-3
        rate_match = re.search(
            r'RATE\s+(.+?)(?:\s+VOLTAGE|\n)',
            text, re.IGNORECASE
        )
        if rate_match:
            data.rate_type = rate_match.group(1).strip()

        # VOLTAGE DELIVERY LEVEL 0 - 2.2 kv
        voltage_match = re.search(
            r'VOLTAGE\s+DELIVERY\s+LEVEL\s+(.+?)(?:\n|$)',
            text, re.IGNORECASE
        )
        if voltage_match:
            data.voltage_level = voltage_match.group(1).strip()

        # METER NUMBER 05083848
        meter_match = re.search(
            r'METER\s+NUMBER\s+(\d+)',
            text, re.IGNORECASE
        )
        if meter_match:
            data.meter_number = meter_match.group(1)

        # Loadzone WCMA
        lz_match = re.search(
            r'Loadzone\s+(\w+)',
            text, re.IGNORECASE
        )
        if lz_match:
            data.load_zone = lz_match.group(1)

        # Cycle: 13
        cycle_match = re.search(
            r'Cycle[:\s]+(\d+)',
            text, re.IGNORECASE
        )
        if cycle_match:
            data.cycle = cycle_match.group(1)

    # ─── Usage Readings ──────────────────────────────────────────────────

    def _extract_usage_readings(self, text: str, data: ExtractedBillData):
        """Extract energy usage readings table (Energy, Peak, Off Peak)."""
        # Pattern: Type  CurrentReading Actual  PrevReading Actual  Diff  x  Mult  =  TotalUsage kWh
        # Energy   44542  Actual  44333  Actual  209  300  62700 kWh
        usage_pattern = re.compile(
            r'(Energy|Peak|Off\s*Peak)\s+'
            r'(\d+)\s+(?:Actual|Estimated)\s+'
            r'(\d+)\s+(?:Actual|Estimated)\s+'
            r'(\d+)\s+'
            r'(\d+)\s+'
            r'(\d+)\s*kWh',
            re.IGNORECASE
        )

        total_kwh = 0
        for match in usage_pattern.finditer(text):
            service_type = match.group(1).strip()
            reading = UsageReading(
                type_of_service=service_type,
                current_reading=float(match.group(2)),
                previous_reading=float(match.group(3)),
                difference=float(match.group(4)),
                multiplier=float(match.group(5)),
                total_usage=float(match.group(6)),
            )
            data.usage_readings.append(reading)
            total_kwh += reading.total_usage

        # Also look for Total Energy line
        total_match = re.search(
            r'Total\s+Energy\s+(\d[\d,]*)\s*kWh',
            text, re.IGNORECASE
        )
        if total_match:
            data.total_energy_kwh = float(total_match.group(1).replace(',', ''))
        elif total_kwh > 0:
            # Sum from Energy type only (Peak/OffPeak are subsets)
            energy_readings = [r for r in data.usage_readings
                             if r.type_of_service.lower() == 'energy']
            if energy_readings:
                data.total_energy_kwh = energy_readings[0].total_usage
            else:
                data.total_energy_kwh = total_kwh

        # Extract meter multiplier from usage table
        if data.usage_readings:
            data.meter_multiplier = data.usage_readings[0].multiplier

    # ─── Demand ──────────────────────────────────────────────────────────

    def _extract_demand(self, text: str, data: ExtractedBillData):
        """Extract demand kW and kVA readings."""

        # Demand-kW section
        # Peak  300  195.0 kW
        # Off Peak  300  174.0 kW
        kw_section = re.search(
            r'Demand-kW\s*\n(.*?)(?=Demand-kVA|$)',
            text, re.IGNORECASE | re.DOTALL
        )

        if kw_section:
            section_text = kw_section.group(1)
            peak_match = re.search(r'Peak\s+(\d+)\s+([\d.]+)\s*kW', section_text)
            offpeak_match = re.search(r'Off\s*Peak\s+(\d+)\s+([\d.]+)\s*kW', section_text)

            data.demand_kw = DemandReading(
                peak=float(peak_match.group(2)) if peak_match else None,
                off_peak=float(offpeak_match.group(2)) if offpeak_match else None,
                multiplier=float(peak_match.group(1)) if peak_match else None,
            )

        # Demand-kVA section
        kva_section = re.search(
            r'Demand-kVA\s*\n(.*?)(?=METER\s+NUMBER|SERVICE\s+PERIOD|$)',
            text, re.IGNORECASE | re.DOTALL
        )

        if kva_section:
            section_text = kva_section.group(1)
            peak_match = re.search(r'Peak\s+(\d+)\s+([\d.]+)\s*kVA', section_text)
            offpeak_match = re.search(r'Off\s*Peak\s+(\d+)\s+([\d.]+)\s*kVA', section_text)

            data.demand_kva = DemandReading(
                peak=float(peak_match.group(2)) if peak_match else None,
                off_peak=float(offpeak_match.group(2)) if offpeak_match else None,
                multiplier=float(peak_match.group(1)) if peak_match else None,
            )

    # ─── 12-Month Usage History ──────────────────────────────────────────

    def _extract_usage_history(self, text: str, data: ExtractedBillData):
        """Extract the Electric Usage History table (12 months)."""
        # Format: Month kWh  Month kWh (two columns side by side)
        # Feb 25 60300  Sep 25 60900
        # Mar 25 66900  Oct 25 70200

        history_section = re.search(
            r'Electric\s+Usage\s+History\s*\n'
            r'Month\s+kWh\s+Month\s+kWh\s*\n'
            r'(.*?)(?=Billed\s+Demand|$)',
            text, re.IGNORECASE | re.DOTALL
        )

        if history_section:
            section_text = history_section.group(1)
            # Match pairs: MonthYY  NNNNN  MonthYY  NNNNN
            pair_pattern = re.compile(
                r'([A-Za-z]{3})\s+(\d{2})\s+(\d+)\s+'
                r'([A-Za-z]{3})\s+(\d{2})\s+(\d+)'
            )
            for match in pair_pattern.finditer(section_text):
                data.monthly_usage_history.append(MonthlyUsage(
                    month=f"{match.group(1)} {match.group(2)}",
                    kwh=float(match.group(3))
                ))
                data.monthly_usage_history.append(MonthlyUsage(
                    month=f"{match.group(4)} {match.group(5)}",
                    kwh=float(match.group(6))
                ))
        else:
            # Try single-column format
            single_pattern = re.compile(
                r'([A-Za-z]{3})\s+(\d{2})\s+(\d{3,})'
            )
            in_history = False
            for line in text.split('\n'):
                if 'electric usage history' in line.lower():
                    in_history = True
                    continue
                if in_history:
                    match = single_pattern.search(line)
                    if match:
                        data.monthly_usage_history.append(MonthlyUsage(
                            month=f"{match.group(1)} {match.group(2)}",
                            kwh=float(match.group(3))
                        ))
                    elif 'billed demand' in line.lower() or 'meter number' in line.lower():
                        break

    # ─── Billed Demand History ───────────────────────────────────────────

    def _extract_billed_demand_history(self, text: str, data: ExtractedBillData):
        """Extract billed demand last 12 months summary."""
        min_match = re.search(r'Minimum\s+([\d.]+)', text)
        max_match = re.search(r'Maximum\s+([\d.]+)', text)
        avg_match = re.search(r'Average\s+([\d.]+)', text)

        if min_match:
            data.billed_demand_min = float(min_match.group(1))
        if max_match:
            data.billed_demand_max = float(max_match.group(1))
        if avg_match:
            data.billed_demand_avg = float(avg_match.group(1))

    # ─── Charges ─────────────────────────────────────────────────────────

    def _extract_charges(self, text: str, data: ExtractedBillData):
        """Extract charge totals."""
        delivery_match = re.search(
            r'Total\s+Delivery\s+Services\s+\$?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if delivery_match:
            data.total_delivery_charges = float(delivery_match.group(1).replace(',', ''))

        supply_match = re.search(
            r'Total\s+Supply\s+Services\s+\$?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if supply_match:
            data.total_supply_charges = float(supply_match.group(1).replace(',', ''))

        other_match = re.search(
            r'Total\s+Other\s+Charges/Adjustments\s+[-\$\s]*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if other_match:
            data.total_other_charges = float(other_match.group(1).replace(',', ''))

        amount_match = re.search(
            r'Amount\s+Due\s*[►▶]?\s+[-\$]?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if amount_match:
            data.amount_due = float(amount_match.group(1).replace(',', ''))

    # ─── Supplier Info ───────────────────────────────────────────────────

    def _extract_supplier_info(self, text: str, data: ExtractedBillData):
        """Extract supplier/generation service provider info."""
        # Match: SUPPLIER SMARTESTENERGY US, LLC (the supplier name on the same line)
        # but NOT: "Other Supplier" from the account balance table header
        supplier_match = re.search(
            r'(?:^|\n)\s*SUPPLIER\s+([A-Z][A-Za-z\s,\.]+(?:LLC|INC|CORP|CO|LP)?)',
            text, re.IGNORECASE
        )
        if supplier_match:
            data.supplier_name = supplier_match.group(1).strip()

        supplier_acct_match = re.search(
            r'ACCOUNT\s+NO\s+([\d]+)',
            text, re.IGNORECASE
        )
        if supplier_acct_match:
            data.supplier_account = supplier_acct_match.group(1)

    # ─── Validation ──────────────────────────────────────────────────────

    def validate(self, data: ExtractedBillData) -> list[str]:
        """National Grid specific validation."""
        warnings = super().validate(data)

        # Cross-check: total energy should match sum of usage readings
        if data.total_energy_kwh and data.usage_readings:
            energy_readings = [r for r in data.usage_readings
                             if r.type_of_service.lower() == 'energy']
            if energy_readings:
                expected = energy_readings[0].total_usage
                if abs(data.total_energy_kwh - expected) > 1:
                    warnings.append(
                        f"Total energy ({data.total_energy_kwh} kWh) doesn't match "
                        f"Energy reading ({expected} kWh)"
                    )

        # Verify account number format (National Grid: XXXXX-XXXXX)
        if data.account_number and not re.match(r'\d{5}-\d{5}', data.account_number):
            warnings.append(f"Account number '{data.account_number}' doesn't match expected format XXXXX-XXXXX")

        return warnings
