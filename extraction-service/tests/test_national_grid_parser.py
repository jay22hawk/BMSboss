"""
BMS Boss — Test: National Grid Parser
Tests the parser against simulated Murdock Middle High School bill text
based on data captured from Travis Zimmerman's sample bill.
"""

import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.national_grid import NationalGridParser
from models import ExtractedBillData, UtilitySponsor

# ─── Simulated bill text (based on Travis's sample) ─────────────────────────
# This matches the National Grid bill format as observed in the PDF preview

SAMPLE_BILL_TEXT_PAGE1 = """
nationalgrid

SERVICE FOR
MURDOCK MIDDLE HIGH
%SUPERINTENDENT OF SCHOOLS
32 ELMWOOD RD, POLE 10
WINCHENDON MA 01475

BILLING PERIOD
Jan 16, 2026 to Feb 13, 2026

ACCOUNT NUMBER
15022-63006

PLEASE PAY BY
No payment due

AMOUNT DUE
$ 0.00

ACCOUNT BALANCE
                        National Grid    Other Supplier
                        Services         Service          Adjustments       Total
Previous Balance        0.00             0.00             -31,532.82        -31,532.82
Payment(s) Received     - 0.00           - 0.00           - 0.00            - 0.00
Amount Past Due         0.00             0.00             -31,532.82        -31,532.82
Current Charges         5,915.98         7,611.78         -4,958.37         8,569.39
Amount Due              $ 5,915.98       $ 7,611.78       -$ 36,491.19      -$ 22,963.43

Enrollment Information
To enroll with a supplier or change to
another supplier, you will need the
following information about your account:
Loadzone WCMA
Acct No: 15022-63006 Cycle: 13, MURD

DETAIL OF CURRENT CHARGES
Delivery Services

Type of Service   Current Reading   Previous Reading   Difference  x  Meter     =  Total Usage
                                                                      Multiplier
Energy            44542  Actual     44333  Actual       209         300              62700 kWh
Peak              23282  Actual     23173  Actual       109         300              32700 kWh
Off Peak          21260  Actual     21160  Actual       100         300              30000 kWh
                                                        Total Energy                62700 kWh

Demand-kW
Peak                                        300         195.0 kW
Off Peak                                    300         174.0 kW

Demand-kVA
Peak                                        300         198.0 kVA
Off Peak                                    300         174.0 kVA

METER NUMBER 05083848    NEXT SCHEDULED READ DATE ON OR ABOUT Mar 19
SERVICE PERIOD Jan 16 - Feb 13   NUMBER OF DAYS IN PERIOD 28
RATE    Time-of-Use G-3  VOLTAGE DELIVERY LEVEL  0 - 2.2 kv

Electric Usage History
Month  kWh    Month  kWh
Feb 25 60300  Sep 25 60900
Mar 25 66900  Oct 25 70200
Apr 25 70800  Nov 25 66600
May 25 58500  Dec 25 69000
Jun 25 71400  Jan 26 63600
Jul 25 55500  Feb 26 62700
Aug 25 58800

Billed Demand Last 12 months
Minimum          153
Maximum          231
Average          202.25

DATE BILL ISSUED
Feb 13, 2026
"""

SAMPLE_BILL_TEXT_PAGE2 = """
nationalgrid

SERVICE FOR
MURDOCK MIDDLE HIGH
%SUPERINTENDENT OF SCHOOLS
32 ELMWOOD RD, POLE 10
WINCHENDON MA 01475

BILLING PERIOD
Jan 16, 2026 to Feb 13, 2026

Customer Charge                                         350.00
Dist Chg On Peak         0.01216  x  32700 kWh          397.64
Dist Chg Off Peak        0.00946  x  30000 kWh          283.80
Transition Charge       -0.00037  x  62700 kWh          -23.20
Transmission Charge      0.03832  x  62700 kWh        2,402.66
Distribution Demand Chg  10.48    x  195 kW/kVA       2,043.60
Energy Efficiency Chg   -0.00309  x  62700 kWh         -193.74
Renewable Energy Chg     0.0005   x  62700 kWh           31.35
Net Meter Recovery Off-Pk 0.00606 x  30000 kWh          181.80
Net Meter Recovery On-Pk  0.00606 x  32700 kWh          198.16
Distributed Solar Charge  0.00328 x  62700 kWh          205.66
Electric Vehicle Charge   0.00061 x  62700 kWh           38.25
                        Total Delivery Services      $ 5,915.98
"""

SAMPLE_BILL_TEXT_PAGE3 = """
Supply Services
SUPPLIER SMARTESTENERGY US, LLC
333 WEST WASHINGTON STREET
SUITE 140
SYRACUSE, NY 13202
PHONE (800) 448-0995    ACCOUNT NO 1502263006

Electricity Supply       0.1214  x  62700 kWh        7,611.78
                        Total Supply Services        $ 7,611.78

Other Charges/Adjustments
Transfer of Remote Net Meter Credit                  -4,958.37
                Total Other Charges/Adjustments      -$ 4,958.37
"""

FULL_BILL_TEXT = SAMPLE_BILL_TEXT_PAGE1 + "\n\n" + SAMPLE_BILL_TEXT_PAGE2 + "\n\n" + SAMPLE_BILL_TEXT_PAGE3


def test_detection():
    """Test that the parser correctly identifies a National Grid bill."""
    parser = NationalGridParser()
    is_match, confidence = parser.detect(FULL_BILL_TEXT)

    assert is_match, "Should detect as National Grid bill"
    assert confidence >= 0.4, f"Confidence should be >= 0.4, got {confidence}"
    print(f"  Detection: match={is_match}, confidence={confidence:.2f}")


def test_extraction():
    """Test full extraction against known bill data."""
    parser = NationalGridParser()
    pages = [SAMPLE_BILL_TEXT_PAGE1, SAMPLE_BILL_TEXT_PAGE2, SAMPLE_BILL_TEXT_PAGE3]

    data = parser.extract(FULL_BILL_TEXT, pages)

    print(f"\n  === Extracted Data ===")
    print(f"  Sponsor: {data.utility_sponsor}")
    print(f"  Confidence: {data.confidence_score:.2f}")
    print(f"  Account: {data.account_number}")
    print(f"  Customer: {data.customer_name}")
    print(f"  Address: {data.service_address}")
    print(f"  City/State/Zip: {data.service_city}, {data.service_state} {data.service_zip}")
    print(f"  Billing Period: {data.billing_period_start} to {data.billing_period_end}")
    print(f"  Days in Period: {data.days_in_period}")
    print(f"  Bill Date: {data.bill_date}")
    print(f"  Rate: {data.rate_type}")
    print(f"  Meter: {data.meter_number}")
    print(f"  Meter Multiplier: {data.meter_multiplier}")
    print(f"  Load Zone: {data.load_zone}")
    print(f"  Voltage: {data.voltage_level}")
    print(f"  Total Energy: {data.total_energy_kwh} kWh")

    print(f"\n  Usage Readings:")
    for r in data.usage_readings:
        print(f"    {r.type_of_service}: {r.current_reading} - {r.previous_reading} "
              f"= {r.difference} x {r.multiplier} = {r.total_usage} kWh")

    print(f"\n  Demand kW: Peak={data.demand_kw.peak if data.demand_kw else 'N/A'}, "
          f"Off-Peak={data.demand_kw.off_peak if data.demand_kw else 'N/A'}")
    print(f"  Demand kVA: Peak={data.demand_kva.peak if data.demand_kva else 'N/A'}, "
          f"Off-Peak={data.demand_kva.off_peak if data.demand_kva else 'N/A'}")

    print(f"\n  12-Month Usage History ({len(data.monthly_usage_history)} months):")
    for m in data.monthly_usage_history:
        print(f"    {m.month}: {m.kwh:,.0f} kWh")
    print(f"  Annual Usage (sum): {data.annual_usage_kwh:,.0f} kWh")

    print(f"\n  Billed Demand (12mo): Min={data.billed_demand_min}, "
          f"Max={data.billed_demand_max}, Avg={data.billed_demand_avg}")

    print(f"\n  Charges:")
    print(f"    Delivery: ${data.total_delivery_charges:,.2f}" if data.total_delivery_charges else "    Delivery: N/A")
    print(f"    Supply: ${data.total_supply_charges:,.2f}" if data.total_supply_charges else "    Supply: N/A")
    print(f"    Other: -${data.total_other_charges:,.2f}" if data.total_other_charges else "    Other: N/A")

    print(f"\n  Supplier: {data.supplier_name}")
    print(f"  Supplier Account: {data.supplier_account}")

    # ─── Assertions ──────────────────────────────────────────────────────
    assert data.utility_sponsor == UtilitySponsor.NATIONAL_GRID
    assert data.account_number == "15022-63006", f"Expected 15022-63006, got {data.account_number}"
    assert data.customer_name == "MURDOCK MIDDLE HIGH", f"Got: {data.customer_name}"
    assert data.meter_number == "05083848", f"Got: {data.meter_number}"
    assert data.total_energy_kwh == 62700, f"Expected 62700, got {data.total_energy_kwh}"
    assert data.days_in_period == 28, f"Expected 28, got {data.days_in_period}"
    assert data.rate_type is not None and "G-3" in data.rate_type, f"Got: {data.rate_type}"
    assert data.meter_multiplier == 300, f"Expected 300, got {data.meter_multiplier}"

    # Demand checks
    assert data.demand_kw is not None
    assert data.demand_kw.peak == 195.0, f"Expected 195.0, got {data.demand_kw.peak}"
    assert data.demand_kw.off_peak == 174.0
    assert data.demand_kva.peak == 198.0
    assert data.demand_kva.off_peak == 174.0

    # Usage readings
    assert len(data.usage_readings) == 3, f"Expected 3 readings, got {len(data.usage_readings)}"

    # Monthly history
    assert len(data.monthly_usage_history) >= 12, \
        f"Expected >= 12 months, got {len(data.monthly_usage_history)}"

    # Annual usage should be sum of monthly
    expected_annual = sum(m.kwh for m in data.monthly_usage_history)
    assert data.annual_usage_kwh == expected_annual, \
        f"Annual {data.annual_usage_kwh} != sum {expected_annual}"

    # Charges
    assert data.total_delivery_charges == 5915.98, f"Got {data.total_delivery_charges}"
    assert data.total_supply_charges == 7611.78, f"Got {data.total_supply_charges}"

    print(f"\n  All assertions passed!")


def test_validation():
    """Test validation catches issues."""
    parser = NationalGridParser()
    pages = [SAMPLE_BILL_TEXT_PAGE1, SAMPLE_BILL_TEXT_PAGE2, SAMPLE_BILL_TEXT_PAGE3]

    data = parser.extract(FULL_BILL_TEXT, pages)
    warnings = parser.validate(data)

    print(f"\n  Validation warnings ({len(warnings)}):")
    for w in warnings:
        print(f"    - {w}")


def test_excel_generation():
    """Test generating an Excel file with extracted + manual data."""
    from excel_generator import generate_calculator, merge_bill_data_to_calculator
    from models import BMSCalculatorInput, AffectedArea, ProjectType, BuildingActivity, HeatingFuel, VentilationType, HeatingSystemType, CoolingSystemType

    parser = NationalGridParser()
    pages = [SAMPLE_BILL_TEXT_PAGE1, SAMPLE_BILL_TEXT_PAGE2, SAMPLE_BILL_TEXT_PAGE3]
    bill_data = parser.extract(FULL_BILL_TEXT, pages)

    # Create calculator input with manual fields for Murdock Middle High
    calc_input = BMSCalculatorInput(
        # These will be auto-filled from bill data
        company_name=None,
        electric_account=None,
        annual_electric_kwh=None,

        # Manual entry fields
        building_activity=BuildingActivity.EDUCATION_K12,
        heating_fuel=HeatingFuel.NATURAL_GAS,
        total_building_sqft=340706,          # Full building
        annual_fuel_usage=None,              # Would need gas bill
        project_type=ProjectType.NEW_BMS,
        demand_response_curtailment="No",
        bms_manufacturer="Tridium Niagara N4",
        total_project_cost=100000,
        electric_pa="National Grid",

        # Affected areas - project covers half the school
        affected_areas=[
            AffectedArea(
                area_number=1,
                project_affected_sqft=170353,    # Half of 340706
                area_description="Main Building - East Wing",
                ventilation_type=VentilationType.CV_AIR_HANDLER,
                primary_heating=HeatingSystemType.CONDENSING_BOILER,
                primary_cooling=CoolingSystemType.DIRECT_EXPANSION,
                seq_system_schedules=1,
                seq_optimal_start_stop=1,
                seq_reset_chilled_water=1,
                seq_reset_static_pressure=1,
                seq_reset_boiler_water=1,
                seq_demand_control_ventilation=1,
                seq_economizer_control=1,
            ),
        ],
    )

    # Merge bill data into calculator input
    calc_input = merge_bill_data_to_calculator(bill_data, calc_input)

    print(f"\n  === Merged Calculator Input ===")
    print(f"  Company: {calc_input.company_name}")
    print(f"  Address: {calc_input.company_address}")
    print(f"  Electric Account: {calc_input.electric_account}")
    print(f"  Annual Electric: {calc_input.annual_electric_kwh:,.0f} kWh")
    print(f"  Building Type: {calc_input.building_activity.value}")
    print(f"  Total sqft: {calc_input.total_building_sqft:,.0f}")
    print(f"  Project Type: {calc_input.project_type.value}")
    print(f"  Project Cost: ${calc_input.total_project_cost:,.2f}")

    # Generate Excel
    output_path = str(Path(__file__).parent.parent / "outputs" / "test_calculator_output.xlsx")
    Path(output_path).parent.mkdir(exist_ok=True)

    result = generate_calculator(calc_input, output_path)

    print(f"\n  === Excel Generation ===")
    print(f"  Success: {result.success}")
    print(f"  File: {result.file_path}")
    print(f"  Incentive Estimate: ${result.incentive_estimate:,.2f}" if result.incentive_estimate else "  Incentive: N/A")
    for w in result.warnings:
        print(f"    Warning: {w}")

    assert result.success, f"Generation failed: {result.errors}"
    assert result.incentive_estimate is not None
    assert result.incentive_estimate > 0

    # The incentive for 7 sequences x 170,353 sqft x $0.10/seq/sqft = $119,247.10
    # Capped at 60% of $100,000 = $60,000
    expected_cap = 100000 * 0.60
    assert result.incentive_estimate == expected_cap, \
        f"Expected incentive capped at ${expected_cap:,.2f}, got ${result.incentive_estimate:,.2f}"

    print(f"\n  Incentive correctly capped at 60% of project cost: ${result.incentive_estimate:,.2f}")
    print(f"  (Uncapped would be: ${0.10 * 7 * 170353:,.2f})")
    print(f"\n  All Excel generation tests passed!")


# ─── Run Tests ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("BMS Boss — National Grid Parser Tests")
    print("Test Data: Murdock Middle High School, Winchendon MA")
    print("=" * 60)

    print("\n[1] Testing sponsor detection...")
    test_detection()

    print("\n[2] Testing bill extraction...")
    test_extraction()

    print("\n[3] Testing validation...")
    test_validation()

    print("\n[4] Testing Excel generation with merged data...")
    test_excel_generation()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
