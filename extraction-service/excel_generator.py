"""
BMS Boss — Excel Generator
Generates a completed Prescriptive BMS Calculator .xlsx file
matching the Mass Save 2026 V1.0 format.

Cell mapping is based on the "User Inputs and Savings" sheet.
Orange cells = user input fields.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from pathlib import Path
from models import BMSCalculatorInput, ExtractedBillData, GenerationResponse


# ─── Cell Mapping ────────────────────────────────────────────────────────────
# Maps BMSCalculatorInput fields to Excel cell references on "User Inputs and Savings" sheet

SHEET_NAME = "User Inputs and Savings"

# Header section (rows 3-10)
CELL_MAP_HEADER = {
    "company_name": "C4",
    "company_address": "C5",       # Street portion
    "company_street": "D5",        # Street column
    "company_city": "F5",          # City column
    "customer_contact_name": "C6",
    "customer_phone": "D6",
    "pa_technical_rep": "C7",
    "pa_tech_rep_phone": "C8",
    "application_number": "F8",
    "electric_account": "C9",
    "gas_account": "C10",
    "gas_pa": "G3",                # Gas PA name
    "electric_pa": "G4",           # Electric PA name
}

# Building Energy Use Intensity (rows 17-21)
CELL_MAP_BUILDING = {
    "building_activity": "C17",     # Dropdown: Select Principal building activity
    "heating_fuel": "C18",          # Dropdown: Non-Electric Heating Fuel
    "total_building_sqft": "C19",   # Total Building Area (sqft)
    "annual_electric_kwh": "C20",   # Annual electric usage (kWh)
    "annual_fuel_usage": "C21",     # Annual fuel usage
}

# Control System Information (rows 30-35)
CELL_MAP_CONTROL = {
    "project_type": "C30",          # Dropdown: Proposed Control activity
    "demand_response": "C31",       # Dropdown: Yes/No
    "bms_manufacturer": "B33",      # BMS Manufacturer and Product
    "bms_product_type": "D33",      # Product type
    "total_project_cost": "C34",    # Total Proposed Project Cost
    "notes": "C35",                 # Notes/explanation
}

# Subscription fields (rows 37-44)
CELL_MAP_SUBSCRIPTION = {
    "subscription_product": "B38",
    "subscription_first_year_hardware": "C39",
    "subscription_previous_incentive": "C40",
    "subscription_years": "C41",
    "subscription_install_cost": "C42",
    "subscription_annual_fee": "C43",
    "subscription_notes": "C44",
}

# Affected Areas - column mapping per area number
AREA_COLUMNS = {
    1: "C",  # Area 1
    2: "D",  # Area 2
    3: "E",  # Area 3
    4: "F",  # Area 4
    5: "G",  # Area 5
}

# Area field rows
AREA_ROWS = {
    "project_affected_sqft": 49,
    "area_description": 50,
    "is_new_equipment": 54,
    "ventilation_type": 55,
    "primary_heating": 56,
    "primary_cooling": 57,
    "terminal_units": 58,
    "secondary_heating_to_hp": 59,
    # Sequences of Operation
    "seq_system_schedules": 61,
    "seq_optimal_start_stop": 62,
    "seq_reset_chilled_water": 63,
    "seq_reset_static_pressure": 64,
    "seq_reset_boiler_water": 65,
    "seq_demand_control_ventilation": 66,
    "seq_economizer_control": 67,
    "seq_reset_supply_air_temp": 68,
    "seq_reset_condenser_water": 69,
    # Optimization sequences
    "opt_cooling": 71,
    "opt_ventilation": 72,
    "opt_heating": 73,
}


def generate_calculator(
    calculator_input: BMSCalculatorInput,
    output_path: str,
    template_path: str = None,
) -> GenerationResponse:
    """
    Generate a completed Prescriptive BMS Calculator Excel file.

    Args:
        calculator_input: All form data to populate
        output_path: Where to save the generated .xlsx
        template_path: Optional path to the original BMS Calculator template.
                      If provided, populates the actual template.
                      If not, creates a standalone data sheet.

    Returns:
        GenerationResponse with file path and any warnings
    """
    warnings = []

    try:
        if template_path and Path(template_path).exists():
            wb = openpyxl.load_workbook(template_path)
            ws = wb[SHEET_NAME]
            _populate_template(ws, calculator_input, warnings)
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = SHEET_NAME
            _create_standalone_sheet(ws, calculator_input, warnings)

        # Save
        wb.save(output_path)

        # Calculate incentive estimate
        incentive = _estimate_incentive(calculator_input)
        if incentive:
            warnings.append(f"Estimated incentive: ${incentive:,.2f} (subject to PA review)")

        return GenerationResponse(
            success=True,
            file_path=output_path,
            incentive_estimate=incentive,
        )

    except Exception as e:
        return GenerationResponse(
            success=False,
            errors=[f"Excel generation failed: {str(e)}"],
        )


def _populate_template(ws, data: BMSCalculatorInput, warnings: list):
    """Populate an existing BMS Calculator template."""

    # Header fields
    for field, cell in CELL_MAP_HEADER.items():
        value = getattr(data, field, None)
        if value is not None:
            ws[cell] = value

    # Building fields
    for field, cell in CELL_MAP_BUILDING.items():
        value = getattr(data, field, None)
        if value is not None:
            # For enums, use the value string
            ws[cell] = value.value if hasattr(value, 'value') else value

    # Control system fields
    field_map = {
        "project_type": "C30",
        "demand_response_curtailment": "C31",
        "bms_manufacturer": "B33",
        "bms_product_type": "D33",
        "total_project_cost": "C34",
        "notes": "C35",
    }
    for field, cell in field_map.items():
        value = getattr(data, field, None)
        if value is not None:
            ws[cell] = value.value if hasattr(value, 'value') else value

    # Subscription fields
    for field, cell in CELL_MAP_SUBSCRIPTION.items():
        value = getattr(data, field, None)
        if value is not None:
            ws[cell] = value

    # Affected Areas
    for area in data.affected_areas:
        col = AREA_COLUMNS.get(area.area_number)
        if not col:
            continue

        for field, row in AREA_ROWS.items():
            value = getattr(area, field, None)
            if value is not None:
                cell = f"{col}{row}"
                ws[cell] = value.value if hasattr(value, 'value') else value


def _create_standalone_sheet(ws, data: BMSCalculatorInput, warnings: list):
    """Create a standalone sheet with all calculator data (no template)."""

    # Styles
    header_font = Font(name="Arial", size=14, bold=True)
    section_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    section_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    label_font = Font(name="Arial", size=10)
    value_font = Font(name="Arial", size=10, bold=True)
    input_fill = PatternFill(start_color="FCD5B4", end_color="FCD5B4", fill_type="solid")

    # Title
    ws.merge_cells("A1:G1")
    ws["A1"] = "BMS Boss — Prescriptive BMS Calculator Data Export"
    ws["A1"].font = header_font

    ws.merge_cells("A2:G2")
    ws["A2"] = "Generated data for Mass Save Prescriptive BMS Calculator (2026 V1.0)"
    ws["A2"].font = Font(name="Arial", size=9, italic=True)

    row = 4

    # ─── Section: Company Information ────────────────────────────────────
    row = _write_section_header(ws, row, "Company / Account Information", section_font, section_fill)

    company_fields = [
        ("Company Name", data.company_name),
        ("Company Address", data.company_address),
        ("City", data.company_city),
        ("Customer Contact", data.customer_contact_name),
        ("Phone", data.customer_phone),
        ("PA Technical Rep", data.pa_technical_rep),
        ("Application #", data.application_number),
        ("Electric Account", data.electric_account),
        ("Gas Account", data.gas_account),
        ("Electric PA", data.electric_pa),
        ("Gas PA", data.gas_pa),
    ]
    row = _write_field_rows(ws, row, company_fields, label_font, value_font, input_fill)

    row += 1

    # ─── Section: Building Energy Use Intensity ──────────────────────────
    row = _write_section_header(ws, row, "Building Energy Use Intensity", section_font, section_fill)

    building_fields = [
        ("Principal Building Activity", data.building_activity.value if data.building_activity else None),
        ("Non-Electric Heating Fuel", data.heating_fuel.value if data.heating_fuel else None),
        ("Total Building Area (sqft)", data.total_building_sqft),
        ("Annual Electric Usage (kWh)", data.annual_electric_kwh),
        ("Annual Fuel Usage", data.annual_fuel_usage),
    ]
    row = _write_field_rows(ws, row, building_fields, label_font, value_font, input_fill)

    row += 1

    # ─── Section: Control System Information ─────────────────────────────
    row = _write_section_header(ws, row, "Control System Information", section_font, section_fill)

    control_fields = [
        ("Proposed Control Activity", data.project_type.value if data.project_type else None),
        ("Demand Response Curtailment", data.demand_response_curtailment),
        ("BMS Manufacturer & Product", data.bms_manufacturer),
        ("Total Proposed Project Cost", f"${data.total_project_cost:,.2f}" if data.total_project_cost else None),
        ("Notes", data.notes),
    ]
    row = _write_field_rows(ws, row, control_fields, label_font, value_font, input_fill)

    row += 1

    # ─── Section: Affected Areas ─────────────────────────────────────────
    row = _write_section_header(ws, row, "Affected Areas & Sequences of Operation", section_font, section_fill)

    if data.affected_areas:
        # Header row
        headers = ["Field"] + [f"Area {a.area_number}" for a in data.affected_areas]
        for col_idx, header in enumerate(headers):
            cell = ws.cell(row=row, column=col_idx + 1, value=header)
            cell.font = Font(name="Arial", size=10, bold=True)
        row += 1

        area_field_labels = [
            ("project_affected_sqft", "Affected Area (sqft)"),
            ("area_description", "Description"),
            ("ventilation_type", "Ventilation System"),
            ("primary_heating", "Primary Heating"),
            ("primary_cooling", "Primary Cooling"),
            ("terminal_units", "Terminal Units"),
            ("seq_system_schedules", "Seq: System Schedules"),
            ("seq_optimal_start_stop", "Seq: Optimal Start/Stop"),
            ("seq_reset_chilled_water", "Seq: Reset Chilled Water Temp"),
            ("seq_reset_static_pressure", "Seq: Reset Static Pressure"),
            ("seq_reset_boiler_water", "Seq: Reset Boiler Water Temp"),
            ("seq_demand_control_ventilation", "Seq: Demand Control Ventilation"),
            ("seq_economizer_control", "Seq: Economizer Control"),
            ("seq_reset_supply_air_temp", "Seq: Reset Supply Air Temp"),
            ("seq_reset_condenser_water", "Seq: Reset Condenser Water Temp"),
        ]

        for field_name, label in area_field_labels:
            ws.cell(row=row, column=1, value=label).font = label_font
            for col_idx, area in enumerate(data.affected_areas):
                value = getattr(area, field_name, None)
                if value is not None:
                    display = value.value if hasattr(value, 'value') else value
                    cell = ws.cell(row=row, column=col_idx + 2, value=display)
                    cell.font = value_font
                    cell.fill = input_fill
            row += 1

    # Set column widths
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 25
    for col in ['C', 'D', 'E', 'F', 'G']:
        ws.column_dimensions[col].width = 20

    warnings.append("Standalone data export generated. For full calculator functionality, "
                    "use with the official Prescriptive BMS Calculator template.")


def _write_section_header(ws, row, title, font, fill):
    """Write a section header row."""
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    cell = ws.cell(row=row, column=1, value=title)
    cell.font = font
    cell.fill = fill
    return row + 1


def _write_field_rows(ws, row, fields, label_font, value_font, input_fill):
    """Write label-value pairs."""
    for label, value in fields:
        ws.cell(row=row, column=1, value=label).font = label_font
        if value is not None:
            cell = ws.cell(row=row, column=2, value=value)
            cell.font = value_font
            cell.fill = input_fill
        row += 1
    return row


def _estimate_incentive(data: BMSCalculatorInput) -> float:
    """
    Estimate the incentive based on project type, affected area, and sequences.
    Formula: Incentive Rate × Number of Eligible Sequences × Area Affected
    Capped at 60% of total project costs.
    """
    if not data.affected_areas:
        return 0.0

    # Incentive rates per sequence per sqft
    rates = {
        "Installation of New BMS": 0.10,
        "Add-On or Optimization of Sequences on Existing BMS": 0.05,
        "Subscription Based Control": 0.01,  # per pre-paid year
    }

    rate = 0.0
    if data.project_type:
        rate = rates.get(data.project_type.value, 0.0)

    total_incentive = 0.0
    for area in data.affected_areas:
        sqft = area.project_affected_sqft or 0
        sequences = sum([
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
        total_incentive += rate * sequences * sqft

    # Cap at 60% of project costs
    if data.total_project_cost and data.total_project_cost > 0:
        cap = data.total_project_cost * 0.60
        total_incentive = min(total_incentive, cap)

    return total_incentive


def merge_bill_data_to_calculator(
    bill_data: ExtractedBillData,
    calculator_input: BMSCalculatorInput
) -> BMSCalculatorInput:
    """
    Merge extracted bill data into calculator input fields.
    Bill data populates auto-fillable fields; manual fields are preserved.
    """
    if bill_data.customer_name and not calculator_input.company_name:
        calculator_input.company_name = bill_data.customer_name

    if bill_data.service_address and not calculator_input.company_address:
        calculator_input.company_address = bill_data.service_address

    if bill_data.service_city and not calculator_input.company_city:
        calculator_input.company_city = bill_data.service_city

    if bill_data.account_number and not calculator_input.electric_account:
        calculator_input.electric_account = bill_data.account_number

    if bill_data.annual_usage_kwh and not calculator_input.annual_electric_kwh:
        calculator_input.annual_electric_kwh = bill_data.annual_usage_kwh

    # Set the electric PA based on the bill sponsor
    if bill_data.utility_sponsor:
        calculator_input.electric_pa = bill_data.utility_sponsor.value

    return calculator_input
