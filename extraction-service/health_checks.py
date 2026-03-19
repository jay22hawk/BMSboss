"""
BMS Boss — Submission Health Check Engine

Automated validation that flags potential issues before MAP submission.
Can be triggered:
  - On submission status change (e.g., FORM_COMPLETE → EXCEL_GENERATED)
  - Manually by support staff via the diagnostics dashboard
  - As a pre-submit gate (BLOCKERs prevent Excel generation)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta
from models import BMSCalculatorInput, ExtractedBillData


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    BLOCKER = "BLOCKER"


@dataclass
class HealthCheckResult:
    check_code: str
    severity: Severity
    title: str
    detail: Optional[str] = None
    field_path: Optional[str] = None
    current_value: Optional[str] = None
    expected_range: Optional[str] = None


def run_all_checks(
    calc_input: BMSCalculatorInput,
    extraction: Optional[ExtractedBillData] = None,
) -> list[HealthCheckResult]:
    """Run all health checks and return a list of findings."""
    results: list[HealthCheckResult] = []

    results.extend(_check_building_sqft(calc_input))
    results.extend(_check_required_fields(calc_input))
    results.extend(_check_sequences(calc_input))
    results.extend(_check_affected_area_sqft(calc_input))
    results.extend(_check_incentive_cap(calc_input))
    results.extend(_check_high_incentive(calc_input))

    if extraction:
        results.extend(_check_extraction_confidence(extraction))
        results.extend(_check_bill_age(extraction))
        results.extend(_check_annual_usage_mismatch(extraction))

    return results


def has_blockers(results: list[HealthCheckResult]) -> bool:
    """Returns True if any BLOCKER-severity issues exist."""
    return any(r.severity == Severity.BLOCKER for r in results)


# ─── Individual Checks ───────────────────────────────────────────────────────

def _check_building_sqft(calc: BMSCalculatorInput) -> list[HealthCheckResult]:
    """BLOCKER: Building exceeds 300,000 sqft prescriptive limit."""
    if calc.total_building_sqft and calc.total_building_sqft > 300_000:
        return [HealthCheckResult(
            check_code="SQFT_EXCEEDS_LIMIT",
            severity=Severity.BLOCKER,
            title="Building exceeds 300,000 sqft prescriptive limit",
            detail=(
                f"Total building area is {calc.total_building_sqft:,.0f} sqft. "
                f"The Mass Save Prescriptive BMS program is limited to buildings "
                f"of 300,000 sqft or less. This submission cannot proceed."
            ),
            field_path="total_building_sqft",
            current_value=f"{calc.total_building_sqft:,.0f}",
            expected_range="1 – 300,000",
        )]
    return []


def _check_required_fields(calc: BMSCalculatorInput) -> list[HealthCheckResult]:
    """BLOCKER: Required calculator fields are missing."""
    missing = []
    if not calc.company_name:
        missing.append("company_name")
    if not calc.building_activity:
        missing.append("building_activity")
    if not calc.project_type:
        missing.append("project_type")
    if not calc.total_project_cost:
        missing.append("total_project_cost")
    if not calc.electric_account and not calc.gas_account:
        missing.append("electric_account or gas_account")
    if not calc.affected_areas:
        missing.append("affected_areas (at least one required)")

    if missing:
        return [HealthCheckResult(
            check_code="MISSING_REQUIRED_FIELDS",
            severity=Severity.BLOCKER,
            title="Required calculator fields are missing",
            detail=f"Missing fields: {', '.join(missing)}",
            field_path=", ".join(missing),
            current_value="empty",
            expected_range="Must be populated",
        )]
    return []


def _check_sequences(calc: BMSCalculatorInput) -> list[HealthCheckResult]:
    """ERROR: No sequences of operation selected for any area."""
    results = []
    for area in calc.affected_areas:
        seq_count = sum([
            area.seq_system_schedules,
            area.seq_optimal_start_stop,
            area.seq_reset_chilled_water,
            area.seq_reset_static_pressure,
            area.seq_reset_boiler_water,
            area.seq_demand_control_ventilation,
            area.seq_economizer_control,
            area.seq_reset_supply_air_temp,
            area.seq_reset_condenser_water,
        ])
        if seq_count == 0:
            results.append(HealthCheckResult(
                check_code="NO_SEQUENCES_SELECTED",
                severity=Severity.ERROR,
                title=f"No sequences selected for Area {area.area_number}",
                detail=(
                    f"Area {area.area_number}"
                    f"{f' ({area.area_description})' if area.area_description else ''} "
                    f"has zero sequences of operation. At least one sequence must be "
                    f"selected for the incentive calculation to produce a non-zero result."
                ),
                field_path=f"affected_areas[{area.area_number - 1}].seq_*",
                current_value="0",
                expected_range="≥ 1",
            ))
    return results


def _check_affected_area_sqft(calc: BMSCalculatorInput) -> list[HealthCheckResult]:
    """ERROR: Affected area has zero or missing square footage."""
    results = []
    for area in calc.affected_areas:
        if not area.project_affected_sqft or area.project_affected_sqft <= 0:
            results.append(HealthCheckResult(
                check_code="ZERO_AFFECTED_SQFT",
                severity=Severity.ERROR,
                title=f"Area {area.area_number} has no square footage",
                detail=(
                    f"Area {area.area_number} affected sqft is "
                    f"{area.project_affected_sqft or 'empty'}. "
                    f"This field is required for incentive calculation."
                ),
                field_path=f"affected_areas[{area.area_number - 1}].project_affected_sqft",
                current_value=str(area.project_affected_sqft),
                expected_range="> 0",
            ))
    return results


def _check_incentive_cap(calc: BMSCalculatorInput) -> list[HealthCheckResult]:
    """ERROR: Incentive would exceed 60% of project cost (usually auto-capped,
    but flags if the raw calculation is wildly out of range)."""
    if not calc.total_project_cost or calc.total_project_cost <= 0:
        return []

    # Quick estimate — actual calc is in excel_generator._estimate_incentive
    rates = {
        "Installation of New BMS": 0.10,
        "Add-On or Optimization of Sequences on Existing BMS": 0.05,
        "Subscription Based Control": 0.01,
    }
    rate = rates.get(calc.project_type.value if calc.project_type else "", 0.10)

    total_raw = 0
    for area in calc.affected_areas:
        seq_count = sum([
            area.seq_system_schedules, area.seq_optimal_start_stop,
            area.seq_reset_chilled_water, area.seq_reset_static_pressure,
            area.seq_reset_boiler_water, area.seq_demand_control_ventilation,
            area.seq_economizer_control, area.seq_reset_supply_air_temp,
            area.seq_reset_condenser_water,
        ])
        sqft = area.project_affected_sqft or 0
        total_raw += rate * seq_count * sqft

    cap = calc.total_project_cost * 0.60
    if total_raw > cap * 3:
        # Raw incentive is more than 3x the cap — something may be off
        return [HealthCheckResult(
            check_code="INCENTIVE_EXCEEDS_60_PCT",
            severity=Severity.WARNING,
            title="Raw incentive significantly exceeds project cost cap",
            detail=(
                f"Uncapped incentive would be ${total_raw:,.2f}, but the 60% cap "
                f"limits it to ${cap:,.2f}. The large gap may indicate the project "
                f"cost is understated or affected areas are overstated."
            ),
            field_path="incentive_estimate",
            current_value=f"${total_raw:,.2f} (uncapped)",
            expected_range=f"≤ ${cap:,.2f} (60% of ${calc.total_project_cost:,.2f})",
        )]
    return []


def _check_high_incentive(calc: BMSCalculatorInput) -> list[HealthCheckResult]:
    """INFO: Large incentive values should be reviewed."""
    # Placeholder — actual incentive is computed by excel_generator
    # This check would use the stored incentive_estimate from Submission
    return []


def _check_extraction_confidence(ext: ExtractedBillData) -> list[HealthCheckResult]:
    """WARNING: Bill extraction confidence below 80%."""
    if ext.confidence_score < 0.80:
        return [HealthCheckResult(
            check_code="LOW_EXTRACTION_CONFIDENCE",
            severity=Severity.WARNING,
            title="Bill extraction confidence below 80%",
            detail=(
                f"Extraction confidence is {ext.confidence_score:.0%}. "
                f"Some fields may be incorrect. Please review the extracted "
                f"data carefully and correct any errors."
            ),
            field_path="extraction_confidence",
            current_value=f"{ext.confidence_score:.0%}",
            expected_range="≥ 80%",
        )]
    return []


def _check_bill_age(ext: ExtractedBillData) -> list[HealthCheckResult]:
    """WARNING: Uploaded bill is older than 6 months."""
    if not ext.billing_period_end:
        return []

    try:
        # Try common date formats
        for fmt in ["%b %d, %Y", "%B %d, %Y", "%m/%d/%Y"]:
            try:
                end_date = datetime.strptime(ext.billing_period_end, fmt)
                break
            except ValueError:
                continue
        else:
            return []  # Couldn't parse the date

        if datetime.now() - end_date > timedelta(days=180):
            return [HealthCheckResult(
                check_code="BILL_AGE_EXCEEDED",
                severity=Severity.WARNING,
                title="Uploaded bill is older than 6 months",
                detail=(
                    f"Billing period ends {ext.billing_period_end}. "
                    f"Mass Save may require a more recent bill. Consider "
                    f"uploading an updated bill."
                ),
                field_path="billing_period_end",
                current_value=ext.billing_period_end,
                expected_range="Within last 6 months",
            )]
    except Exception:
        pass
    return []


def _check_annual_usage_mismatch(ext: ExtractedBillData) -> list[HealthCheckResult]:
    """WARNING: Annual usage doesn't match sum of monthly history."""
    if not ext.annual_usage_kwh or not ext.monthly_usage_history:
        return []

    history_sum = sum(m.kwh for m in ext.monthly_usage_history)
    if history_sum == 0:
        return []

    pct_diff = abs(ext.annual_usage_kwh - history_sum) / history_sum
    if pct_diff > 0.05:
        return [HealthCheckResult(
            check_code="ANNUAL_USAGE_MISMATCH",
            severity=Severity.WARNING,
            title="Annual usage doesn't match sum of monthly history",
            detail=(
                f"Annual usage is {ext.annual_usage_kwh:,.0f} kWh, but the "
                f"sum of monthly history is {history_sum:,.0f} kWh "
                f"(difference: {pct_diff:.1%}). Verify the correct value."
            ),
            field_path="annual_electric_kwh",
            current_value=f"{ext.annual_usage_kwh:,.0f} kWh",
            expected_range=f"Within 5% of {history_sum:,.0f} kWh",
        )]
    return []
