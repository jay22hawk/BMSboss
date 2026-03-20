"""
BMS Boss — Data Models
Dataclass models for bill extraction, BMS calculator data, and API responses.

NOTE: These use Python dataclasses for portability. When deploying with FastAPI,
these can be converted to Pydantic models by changing the base class.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from enum import Enum
from datetime import date


# ─── Enums ───────────────────────────────────────────────────────────────────

class UtilitySponsor(str, Enum):
    NATIONAL_GRID = "National Grid"
    EVERSOURCE = "Eversource"
    LIBERTY = "Liberty"
    CAPE_LIGHT = "Cape Light Compact"
    BERKSHIRE_GAS = "Berkshire Gas"
    UNITIL = "Unitil"


class BillType(str, Enum):
    ELECTRIC = "Electric"
    GAS = "Gas"


class ProjectType(str, Enum):
    NEW_BMS = "Installation of New BMS"
    UPGRADE_EXISTING = "Add-On or Optimization of Sequences on Existing BMS"
    SUBSCRIPTION = "Subscription Based Control"


class BuildingActivity(str, Enum):
    EDUCATION_K12 = "Education - K through 12"
    EDUCATION_COLLEGE = "Education - College/University"
    OFFICE = "Office"
    RETAIL = "Retail - Standalone"
    RETAIL_STRIP = "Retail - Strip Mall"
    HEALTHCARE_OUTPATIENT = "Healthcare - Outpatient"
    HEALTHCARE_INPATIENT = "Healthcare - Inpatient"
    LODGING = "Lodging"
    WAREHOUSE = "Warehouse"
    WORSHIP = "Worship"
    ASSEMBLY = "Assembly"
    FOOD_SERVICE = "Food Service"
    FOOD_SALES = "Food Sales"
    LABORATORY = "Laboratory"
    OTHER = "Other"


class HeatingFuel(str, Enum):
    NATURAL_GAS = "Natural Gas"
    OIL = "#2 Oil"
    PROPANE = "Propane"
    ELECTRIC = "Electric"
    NONE = "None"


class VentilationType(str, Enum):
    CV_AIR_HANDLER = "CV Air Handler"
    CV_DOAS = "CV DOAS"
    VAV_AHU = "VAV AHU"
    VAV_DOAS = "VAV DOAS"
    NA = "N/A or Not Controlled in Project"


class HeatingSystemType(str, Enum):
    CONDENSING_BOILER = "Condensing Boiler"
    STANDARD_BOILER = "Standard Boiler"
    HYDRONIC_BOILER = "Hydronic Boiler"
    FURNACE = "Furnace"
    ELECTRIC_RESISTANCE = "Electric Resistance (AHU or Terminal Units)"
    AIR_SOURCE_HEAT_PUMP = "Air Source Heat Pump"
    VRF_VRV = "VRF or VRV System"
    WATER_SOURCE_HP = "Water Source Heat Pump with Boiler"
    DIRECT_EXPANSION = "Direct Expansion (ASHP, VRF, GSHP, AWHP)"
    NA = "N/A or Not Controlled in Project"


class CoolingSystemType(str, Enum):
    DIRECT_EXPANSION = "Direct Expansion (AC, ASHP, VRF, GSHP, AWHP)"
    CHILLER = "Chiller"
    NA = "N/A or Not Controlled in Project"


class TerminalUnitType(str, Enum):
    VAV_BOX = "VAV Box"
    FAN_COIL = "Fan Coil Unit (FCU)"
    UNIT_VENTILATOR = "Unit Ventilator"
    PTAC = "PTAC"
    NA = "N/A or Not Controlled in Project"


# ─── Extracted Bill Data ─────────────────────────────────────────────────────

@dataclass
class MonthlyUsage:
    """Monthly kWh usage from bill history."""
    month: str = ""          # e.g., 'Feb 25'
    kwh: float = 0.0


@dataclass
class DemandReading:
    """Demand readings (kW or kVA)."""
    peak: Optional[float] = None
    off_peak: Optional[float] = None
    multiplier: Optional[float] = None


@dataclass
class UsageReading:
    """Meter usage readings."""
    type_of_service: str = ""    # Energy, Peak, or Off Peak
    current_reading: float = 0
    previous_reading: float = 0
    difference: float = 0
    multiplier: float = 1
    total_usage: float = 0


@dataclass
class ExtractedBillData:
    """Data extracted from a utility energy bill PDF."""

    # Source info
    utility_sponsor: UtilitySponsor = UtilitySponsor.NATIONAL_GRID
    bill_type: BillType = BillType.ELECTRIC
    confidence_score: float = 0.0

    # Account & Service Info
    account_number: Optional[str] = None
    meter_number: Optional[str] = None
    service_address: Optional[str] = None
    service_city: Optional[str] = None
    service_state: Optional[str] = None
    service_zip: Optional[str] = None
    customer_name: Optional[str] = None
    customer_care_of: Optional[str] = None       # e.g., "%SUPERINTENDANT OF SCHOOLS"

    # Mailing Address (from payment return section)
    mailing_name: Optional[str] = None
    mailing_address: Optional[str] = None
    mailing_city: Optional[str] = None
    mailing_state: Optional[str] = None
    mailing_zip: Optional[str] = None

    # Billing Period
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None
    bill_date: Optional[str] = None
    days_in_period: Optional[int] = None

    # Rate & Meter Info
    rate_type: Optional[str] = None
    voltage_level: Optional[str] = None
    meter_multiplier: Optional[float] = None
    load_zone: Optional[str] = None
    cycle: Optional[str] = None

    # Usage Data
    usage_readings: List[UsageReading] = field(default_factory=list)
    total_energy_kwh: Optional[float] = None

    # Demand Data
    demand_kw: Optional[DemandReading] = None
    demand_kva: Optional[DemandReading] = None

    # 12-Month History
    monthly_usage_history: List[MonthlyUsage] = field(default_factory=list)
    annual_usage_kwh: Optional[float] = None

    # Billed Demand History
    billed_demand_min: Optional[float] = None
    billed_demand_max: Optional[float] = None
    billed_demand_avg: Optional[float] = None

    # Charges (reference data)
    total_delivery_charges: Optional[float] = None
    total_supply_charges: Optional[float] = None
    total_other_charges: Optional[float] = None
    amount_due: Optional[float] = None

    # Supply Info
    supplier_name: Optional[str] = None
    supplier_account: Optional[str] = None
    supplier_phone: Optional[str] = None
    supplier_address: Optional[str] = None
    electricity_supply_rate: Optional[float] = None  # $/kWh

    # Delivery Charge Line Items
    delivery_line_items: List[Dict] = field(default_factory=list)  # [{name, rate, quantity, unit, amount}]


# ─── BMS Calculator Input ────────────────────────────────────────────────────

@dataclass
class AffectedArea:
    """One of up to 5 affected building areas."""
    area_number: int = 1
    project_affected_sqft: Optional[float] = None
    area_description: Optional[str] = None
    is_new_equipment: Optional[str] = None        # Unknown, Yes, No
    ventilation_type: Optional[VentilationType] = None
    primary_heating: Optional[HeatingSystemType] = None
    primary_cooling: Optional[CoolingSystemType] = None
    terminal_units: Optional[TerminalUnitType] = None
    secondary_heating_to_hp: Optional[HeatingSystemType] = None

    # Sequences of Operation (1 = implement, 0 = skip)
    seq_system_schedules: int = 0
    seq_optimal_start_stop: int = 0
    seq_reset_chilled_water: int = 0
    seq_reset_static_pressure: int = 0
    seq_reset_boiler_water: int = 0
    seq_demand_control_ventilation: int = 0
    seq_economizer_control: int = 0
    seq_reset_supply_air_temp: int = 0
    seq_reset_condenser_water: int = 0

    # Subscription optimization sequences
    opt_cooling: int = 0
    opt_ventilation: int = 0
    opt_heating: int = 0


@dataclass
class BMSCalculatorInput:
    """Complete input for generating the Prescriptive BMS Calculator .xlsx."""

    # Company / Contact Info
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_street: Optional[str] = None
    company_city: Optional[str] = None
    customer_contact_name: Optional[str] = None
    customer_phone: Optional[str] = None
    pa_technical_rep: Optional[str] = None
    pa_tech_rep_phone: Optional[str] = None
    application_number: Optional[str] = None
    electric_account: Optional[str] = None
    gas_account: Optional[str] = None
    gas_pa: Optional[str] = "Eversource Gas"
    electric_pa: Optional[str] = "Eversource"

    # Building Energy Use Intensity
    building_activity: Optional[BuildingActivity] = None
    heating_fuel: Optional[HeatingFuel] = None
    total_building_sqft: Optional[float] = None
    annual_electric_kwh: Optional[float] = None
    annual_fuel_usage: Optional[float] = None

    # Control System Information
    project_type: Optional[ProjectType] = None
    demand_response_curtailment: Optional[str] = None    # Yes or No
    bms_manufacturer: Optional[str] = None
    bms_product_type: Optional[str] = None
    total_project_cost: Optional[float] = None
    notes: Optional[str] = None

    # Subscription fields (if applicable)
    subscription_product: Optional[str] = None
    subscription_first_year_hardware: Optional[int] = None
    subscription_previous_incentive: Optional[str] = None
    subscription_years: Optional[int] = None
    subscription_install_cost: Optional[float] = None
    subscription_annual_fee: Optional[float] = None
    subscription_notes: Optional[str] = None

    # Affected Areas (up to 5)
    affected_areas: List[AffectedArea] = field(default_factory=list)

    def model_dump(self):
        """Compatibility method for API serialization."""
        import dataclasses
        return dataclasses.asdict(self)


# ─── API Response Models ─────────────────────────────────────────────────────

@dataclass
class ExtractionResponse:
    """API response for bill extraction."""
    success: bool = False
    data: Optional[ExtractedBillData] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def model_dump(self):
        """Compatibility method for API serialization."""
        import dataclasses
        return dataclasses.asdict(self)


@dataclass
class GenerationResponse:
    """API response for Excel generation."""
    success: bool = False
    file_path: Optional[str] = None
    incentive_estimate: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
