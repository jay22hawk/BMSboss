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

        # Use page 2 for delivery line items, page 3 for supply
        page2 = pages_text[1] if len(pages_text) > 1 else ''
        page3 = pages_text[2] if len(pages_text) > 2 else ''

        # Extract each section
        self._extract_header(page1, data)
        self._extract_account_info(text, data)
        self._extract_billing_period(text, data)  # Use full text to find year on later pages
        self._extract_rate_meter_info(page1, data)
        self._extract_usage_readings(page1, data)
        self._extract_demand(page1, data)
        self._extract_usage_history(page1, data)
        self._extract_billed_demand_history(page1, data)
        self._extract_charges(text, data)
        self._extract_supplier_info(text, data)
        self._extract_mailing_address(page1, data)
        self._extract_delivery_line_items(page2, data)
        self._extract_supply_rate(page3 or text, data)

        # Calculate annual usage from last 12 months of history
        if data.monthly_usage_history:
            # If we have 13 months (overlapping start/end month), use last 12
            history = data.monthly_usage_history
            if len(history) > 12:
                history = history[-12:]
            data.annual_usage_kwh = sum(m.kwh for m in history)

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

        # SERVICE FOR block - grab multiple lines after it
        service_for_match = re.search(
            r'SERVICE\s+FOR\s*(?:BILLING)?\s*(?:PERIOD)?\s*(?:PAGE\s+\d+\s+(?:Of|of)\s+\d+)?\s*\n'
            r'(.+?)(?:\n|$)'        # Customer/building name (line 1)
            r'(?:(.+?)(?:\n|$))?'   # Optional line 2 (dept, c/o, etc.)
            r'(?:(.+?)(?:\n|$))?'   # Optional line 3
            r'(?:(.+?)(?:\n|$))?',  # Optional line 4
            text, re.IGNORECASE
        )

        # If that didn't work, try the simpler pattern for scanned bills
        if not service_for_match:
            service_for_match = re.search(
                r'SERVICE\s+FOR[^\n]*\n'
                r'(?:nationalgrid[^\n]*\n)?'
                r'(.+?)(?:\n|$)'
                r'(?:(.+?)(?:\n|$))?'
                r'(?:(.+?)(?:\n|$))?'
                r'(?:(.+?)(?:\n|$))?',
                text, re.IGNORECASE
            )

        if service_for_match:
            lines = [g.strip() for g in service_for_match.groups() if g and g.strip()]
            # Filter out noise: dates, page numbers, account info that may have leaked in
            lines = [l for l in lines if not re.match(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d', l)
                     and 'ACCOUNT NUMBER' not in l.upper()
                     and 'BILLING PERIOD' not in l.upper()
                     and 'nationalgrid' not in l.lower()]

            if lines:
                data.customer_name = lines[0]

            # Check for care-of line (starts with % or c/o)
            for line in lines[1:]:
                if line.startswith('%') or line.upper().startswith('C/O'):
                    data.customer_care_of = line
                    break

            # Find the address line (contains a number at start)
            for line in lines[1:]:
                if re.match(r'\d+\s', line):
                    data.service_address = line
                    break

            # Find city/state/zip line - handle OCR merging like "WINCHENDONMA01475"
            for line in lines:
                # Standard format: CITY STATE ZIP
                city_match = re.match(
                    r'([A-Z][A-Z\s]+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)',
                    line
                )
                if city_match:
                    data.service_city = city_match.group(1).strip()
                    data.service_state = city_match.group(2)
                    data.service_zip = city_match.group(3)
                    break

                # OCR-merged format: WINCHENDONMA01475
                merged_match = re.match(
                    r'([A-Z]+?)(MA|CT|NH|RI|VT|ME|NY|NJ)\s*(\d{5}(?:-?\d{4})?)',
                    line
                )
                if merged_match:
                    data.service_city = merged_match.group(1).strip()
                    data.service_state = merged_match.group(2)
                    data.service_zip = merged_match.group(3)
                    break

        # If city/state/zip still not found, scan full text for merged pattern near top
        if not data.service_city:
            for line in text.split('\n')[:20]:
                line = line.strip()
                merged = re.match(
                    r'([A-Z]{3,}?)(MA|CT|NH|RI|VT|ME|NY|NJ)\s*(\d{5}(?:-?\d{4})?)\s*$',
                    line
                )
                if merged:
                    data.service_city = merged.group(1).strip()
                    data.service_state = merged.group(2)
                    data.service_zip = merged.group(3)
                    break
                std = re.match(
                    r'([A-Z][A-Z\s]{2,}?)\s+(MA|CT|NH|RI|VT|ME|NY|NJ)\s+(\d{5}(?:-\d{4})?)',
                    line
                )
                if std and len(std.group(1).strip()) > 2:
                    data.service_city = std.group(1).strip()
                    data.service_state = std.group(2)
                    data.service_zip = std.group(3)
                    break

    # ─── Account Info ────────────────────────────────────────────────────

    def _extract_account_info(self, text: str, data: ExtractedBillData):
        """Extract account number."""
        # Try multiple patterns - OCR can garble the label
        patterns = [
            r'ACCOUNT\s+NUMBER\s*[:\n]\s*(\d{5}-\d{5})',
            r'Acct\s+No[:\s]+(\d{5}-\d{5})',
            # Standalone pattern: look for the XXXXX-XXXXX format near top of page
            r'(\d{5}-\d{5})\s+(?:No\s+payment|Please\s+pay)',
            # AcctNo: in enrollment section
            r'AcctNo[:\s]+(\d{5}-\d{5})',
        ]
        for pattern in patterns:
            acct_match = re.search(pattern, text, re.IGNORECASE)
            if acct_match:
                data.account_number = acct_match.group(1)
                break

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

        # DATE BILL ISSUED - may have newline between label and date
        bill_date_patterns = [
            r'DATE\s+BILL\s+ISSUED\s*\n?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'BILL\s+ISSUED\s*\n\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        ]
        for pattern in bill_date_patterns:
            bill_date_match = re.search(pattern, text, re.IGNORECASE)
            if bill_date_match:
                data.bill_date = bill_date_match.group(1).strip()
                break

        # If billing period only got short form (e.g. "Jan 16"), try to get the year
        # Search full text (all pages) for the full date format
        if data.billing_period_start and not re.search(r'\d{4}', data.billing_period_start):
            # Handle OCR quirks: "Feb 13,2026" (no space before year)
            full_period = re.search(
                r'([A-Za-z]+\s+\d{1,2},?\s*\d{4})\s+to\s+([A-Za-z]+\s+\d{1,2},?\s*\d{4})',
                text, re.IGNORECASE
            )
            if full_period:
                data.billing_period_start = full_period.group(1).strip()
                data.billing_period_end = full_period.group(2).strip()

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
        """Extract the Electric Usage History table (12 months).
        Handles OCR quirks: merged month names (Jun25), mixed-in demand data on same lines.
        """
        # Find the section start
        history_start = re.search(r'Electric\s+Usage\s+History', text, re.IGNORECASE)
        if not history_start:
            return

        # Get text from history section to end of billed demand or similar marker
        section_text = text[history_start.start():]
        end_match = re.search(r'Billed\s+Demand|METER\s+NUMBER', section_text, re.IGNORECASE)
        if end_match:
            section_text = section_text[:end_match.start()]

        # Pattern for month-year-kwh entries
        # Handles both "Feb 25 60300" and "Jun25 71400" (no space between month and year)
        entry_pattern = re.compile(
            r'([A-Za-z]{3})\s?(\d{2})\s+(\d{4,6})'
        )

        seen_months = set()
        for match in entry_pattern.finditer(section_text):
            month_str = f"{match.group(1)} {match.group(2)}"
            kwh_val = float(match.group(3))

            # Skip if this looks like a meter reading (5+ digits starting with 2xxxx, 4xxxx)
            if kwh_val > 100000:
                continue
            # Skip duplicates
            if month_str in seen_months:
                continue

            seen_months.add(month_str)
            data.monthly_usage_history.append(MonthlyUsage(
                month=month_str,
                kwh=kwh_val
            ))

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
        """Extract charge totals. Handles OCR quirks like 'Servici' for 'Services'."""
        # Delivery total - OCR may render "Services" as "Servici" or "Servic"
        delivery_match = re.search(
            r'Total\s+Delivery\s+Servic\w*\s+\$?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if delivery_match:
            data.total_delivery_charges = float(delivery_match.group(1).replace(',', ''))

        # Supply total
        supply_match = re.search(
            r'Total\s+Supply\s+Servic\w*\s+\$?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if supply_match:
            data.total_supply_charges = float(supply_match.group(1).replace(',', ''))

        # Other charges - OCR may render "-$" as "•$" or "-$ " or "·$"
        other_match = re.search(
            r'Total\s+Other\s+Charges/?Adjustments\s+[•·\-\$\s]*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if other_match:
            data.total_other_charges = float(other_match.group(1).replace(',', ''))

        # Amount due
        amount_match = re.search(
            r'Amount\s+Due\s*[►▶>]?\s+[-\$]?\s*([\d,]+\.?\d*)',
            text, re.IGNORECASE
        )
        if amount_match:
            data.amount_due = float(amount_match.group(1).replace(',', ''))

    # ─── Supplier Info ───────────────────────────────────────────────────

    def _extract_supplier_info(self, text: str, data: ExtractedBillData):
        """Extract supplier/generation service provider info."""
        # Match SUPPLIER on its own line or "SUPPLIER NAME" pattern
        # Avoid matching "Supplier Service Charges" from the explanation text
        supplier_match = re.search(
            r'SUPPLIER\s+([A-Z][A-Z\s,\.]+(?:LLC|INC|CORP|CO|LP))',
            text
        )
        if supplier_match:
            name = supplier_match.group(1).strip()
            # Filter out false positives from explanation sections
            if 'Charges' not in name and 'Service' not in name and len(name) > 3:
                data.supplier_name = name

        supplier_acct_match = re.search(
            r'ACCOUNT\s+NO\s+([\d]+)',
            text, re.IGNORECASE
        )
        if supplier_acct_match:
            data.supplier_account = supplier_acct_match.group(1)

        # Supplier phone: PHONE (800) 448-0995
        phone_match = re.search(
            r'PHONE\s+\((\d{3})\)\s*(\d{3})-?(\d{4})',
            text, re.IGNORECASE
        )
        if phone_match:
            data.supplier_phone = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"

    # ─── Mailing Address ──────────────────────────────────────────────

    def _extract_mailing_address(self, text: str, data: ExtractedBillData):
        """Extract mailing/correspondence address from payment return section."""
        # Look for the mailing block near bottom of page 1:
        # MURDOCK MIDDLE HIGH
        # %SUPERINTENDANT OF SCHOOLS
        # 175 GROVE ST
        # WINCHENDON MA 01475-1162
        mail_match = re.search(
            r'(?:AUTO[^\n]*\n)'
            r'(?:[^\n]*barcode[^\n]*\n)?'
            r'(?:[|lI\.]+[^\n]*\n)?'
            r'\s*([A-Z][A-Z\s]+)\n'
            r'\s*(%[^\n]+)\n'
            r'\s*(\d+[^\n]+?)\s+(\d{6})\n'
            r'\s*(\w+)(?:\s*)(MA|CT|NH|RI|VT|ME|NY)\s*(\d{5}(?:-\d{4})?)',
            text, re.IGNORECASE
        )
        if mail_match:
            data.mailing_name = mail_match.group(1).strip()
            data.mailing_address = mail_match.group(3).strip()
            data.mailing_city = mail_match.group(5).strip()
            data.mailing_state = mail_match.group(6).strip()
            data.mailing_zip = mail_match.group(7).strip()
        else:
            # Simpler fallback: look for street address after customer name pattern near bottom
            street_match = re.search(
                r'([A-Z][A-Z\s]+(?:SCHOOL|HIGH|MIDDLE|ELEMENTARY|CENTER|OFFICE|BUILDING))\s*\n'
                r'(?:%[^\n]+\n)?'
                r'\s*(\d+\s+[A-Z\s]+(?:ST|AVE|RD|DR|LN|BLVD|WAY|CT|PL))\b[^\n]*\n'
                r'\s*(\w+?)(?:\s*)(MA|CT|NH|RI|VT|ME|NY)\s*(\d{5}(?:-\d{4})?)',
                text, re.IGNORECASE
            )
            if street_match:
                data.mailing_name = street_match.group(1).strip()
                data.mailing_address = street_match.group(2).strip()
                data.mailing_city = street_match.group(3).strip()
                data.mailing_state = street_match.group(4).strip()
                data.mailing_zip = street_match.group(5).strip()

    # ─── Delivery Line Items ──────────────────────────────────────────

    def _extract_delivery_line_items(self, page2_text: str, data: ExtractedBillData):
        """Extract individual delivery charge line items from page 2."""
        if not page2_text:
            return

        # Pattern: charge_name  rate x quantity unit  amount
        # e.g.: Dist Chg On Peak  0.01216 x 32700 kWh  397.64
        line_pattern = re.compile(
            r'([\w\s-]+?)\s+'
            r'([\d.-]+)\s+x\s+([\d,]+)\s*(kWh|kW/kVA|kW)\s+'
            r'([\d,.-]+)',
        )

        for match in line_pattern.finditer(page2_text):
            name = match.group(1).strip()
            rate = float(match.group(2))
            quantity = float(match.group(3).replace(',', ''))
            unit = match.group(4)
            amount = float(match.group(5).replace(',', ''))
            data.delivery_line_items.append({
                'name': name,
                'rate': rate,
                'quantity': quantity,
                'unit': unit,
                'amount': amount,
            })

        # Also grab Customer Charge (flat fee, no rate x quantity)
        cust_charge = re.search(r'Customer\s+Charge\s+([\d,]+\.?\d*)', page2_text)
        if cust_charge:
            data.delivery_line_items.insert(0, {
                'name': 'Customer Charge',
                'rate': None,
                'quantity': None,
                'unit': None,
                'amount': float(cust_charge.group(1).replace(',', '')),
            })

    # ─── Supply Rate ──────────────────────────────────────────────────

    def _extract_supply_rate(self, text: str, data: ExtractedBillData):
        """Extract the electricity supply rate ($/kWh)."""
        # Electricity Supply  0.1214 x 62700 kWh  7,611.78
        rate_match = re.search(
            r'Electricity\s+Supply\s+([\d.]+)\s+x\s+([\d,]+)\s*kWh',
            text, re.IGNORECASE
        )
        if rate_match:
            data.electricity_supply_rate = float(rate_match.group(1))

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
