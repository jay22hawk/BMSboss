// ─── Enums (matching Python models) ─────────────────────────────────────────

export enum UtilitySponsor {
  NATIONAL_GRID = "National Grid",
  EVERSOURCE = "Eversource",
  LIBERTY = "Liberty",
  CAPE_LIGHT = "Cape Light Compact",
  BERKSHIRE_GAS = "Berkshire Gas",
  UNITIL = "Unitil",
}

export enum BillType {
  ELECTRIC = "Electric",
  GAS = "Gas",
}

export enum ProjectType {
  NEW_BMS = "Installation of New BMS",
  UPGRADE_EXISTING = "Add-On or Optimization of Sequences on Existing BMS",
  SUBSCRIPTION = "Subscription Based Control",
}

export enum BuildingActivity {
  EDUCATION_K12 = "Education - K through 12",
  EDUCATION_COLLEGE = "Education - College/University",
  OFFICE = "Office",
  RETAIL = "Retail - Standalone",
  RETAIL_STRIP = "Retail - Strip Mall",
  HEALTHCARE_OUTPATIENT = "Healthcare - Outpatient",
  HEALTHCARE_INPATIENT = "Healthcare - Inpatient",
  LODGING = "Lodging",
  WAREHOUSE = "Warehouse",
  WORSHIP = "Worship",
  ASSEMBLY = "Assembly",
  FOOD_SERVICE = "Food Service",
  FOOD_SALES = "Food Sales",
  LABORATORY = "Laboratory",
  OTHER = "Other",
}

export enum HeatingFuel {
  NATURAL_GAS = "Natural Gas",
  OIL = "#2 Oil",
  PROPANE = "Propane",
  ELECTRIC = "Electric",
  NONE = "None",
}

export enum VentilationType {
  CV_AIR_HANDLER = "CV Air Handler",
  CV_DOAS = "CV DOAS",
  VAV_AHU = "VAV AHU",
  VAV_DOAS = "VAV DOAS",
  NA = "N/A or Not Controlled in Project",
}

export enum HeatingSystemType {
  CONDENSING_BOILER = "Condensing Boiler",
  STANDARD_BOILER = "Standard Boiler",
  HYDRONIC_BOILER = "Hydronic Boiler",
  FURNACE = "Furnace",
  ELECTRIC_RESISTANCE = "Electric Resistance (AHU or Terminal Units)",
  AIR_SOURCE_HEAT_PUMP = "Air Source Heat Pump",
  VRF_VRV = "VRF or VRV System",
  WATER_SOURCE_HP = "Water Source Heat Pump with Boiler",
  DIRECT_EXPANSION = "Direct Expansion (ASHP, VRF, GSHP, AWHP)",
  NA = "N/A or Not Controlled in Project",
}

export enum CoolingSystemType {
  DIRECT_EXPANSION = "Direct Expansion (AC, ASHP, VRF, GSHP, AWHP)",
  CHILLER = "Chiller",
  NA = "N/A or Not Controlled in Project",
}

export enum TerminalUnitType {
  VAV_BOX = "VAV Box",
  FAN_COIL = "Fan Coil Unit (FCU)",
  UNIT_VENTILATOR = "Unit Ventilator",
  PTAC = "PTAC",
  NA = "N/A or Not Controlled in Project",
}

// ─── Data Interfaces ────────────────────────────────────────────────────────

export interface MonthlyUsage {
  month: string;
  kwh: number;
}

export interface DemandReading {
  peak: number | null;
  off_peak: number | null;
  multiplier: number | null;
}

export interface UsageReading {
  type_of_service: string;
  current_reading: number;
  previous_reading: number;
  difference: number;
  multiplier: number;
  total_usage: number;
}

export interface ExtractedBillData {
  utility_sponsor: UtilitySponsor;
  bill_type: BillType;
  confidence_score: number;
  account_number: string | null;
  meter_number: string | null;
  service_address: string | null;
  service_city: string | null;
  service_state: string | null;
  service_zip: string | null;
  customer_name: string | null;
  billing_period_start: string | null;
  billing_period_end: string | null;
  bill_date: string | null;
  days_in_period: number | null;
  rate_type: string | null;
  voltage_level: string | null;
  meter_multiplier: number | null;
  load_zone: string | null;
  total_energy_kwh: number | null;
  usage_readings: UsageReading[];
  demand_kw: DemandReading | null;
  demand_kva: DemandReading | null;
  monthly_usage_history: MonthlyUsage[];
  annual_usage_kwh: number | null;
  billed_demand_min: number | null;
  billed_demand_max: number | null;
  billed_demand_avg: number | null;
  total_delivery_charges: number | null;
  total_supply_charges: number | null;
  total_other_charges: number | null;
  amount_due: number | null;
  supplier_name: string | null;
  supplier_account: string | null;
}

export interface AffectedArea {
  area_number: number;
  project_affected_sqft: number | null;
  area_description: string | null;
  is_new_equipment: string | null;
  ventilation_type: VentilationType | null;
  primary_heating: HeatingSystemType | null;
  primary_cooling: CoolingSystemType | null;
  terminal_units: TerminalUnitType | null;
  secondary_heating_to_hp: HeatingSystemType | null;
  seq_system_schedules: number;
  seq_optimal_start_stop: number;
  seq_reset_chilled_water: number;
  seq_reset_static_pressure: number;
  seq_reset_boiler_water: number;
  seq_demand_control_ventilation: number;
  seq_economizer_control: number;
  seq_reset_supply_air_temp: number;
  seq_reset_condenser_water: number;
  opt_cooling: number;
  opt_ventilation: number;
  opt_heating: number;
}

export interface BMSCalculatorInput {
  company_name: string | null;
  company_address: string | null;
  company_city: string | null;
  electric_account: string | null;
  gas_account: string | null;
  electric_pa: string | null;
  gas_pa: string | null;
  customer_contact_name: string | null;
  customer_phone: string | null;
  building_activity: BuildingActivity | null;
  heating_fuel: HeatingFuel | null;
  total_building_sqft: number | null;
  annual_electric_kwh: number | null;
  annual_fuel_usage: number | null;
  project_type: ProjectType | null;
  demand_response_curtailment: string | null;
  bms_manufacturer: string | null;
  total_project_cost: number | null;
  notes: string | null;
  affected_areas: AffectedArea[];
}

// ─── API Responses ──────────────────────────────────────────────────────────

export interface ExtractionResponse {
  success: boolean;
  data: ExtractedBillData | null;
  errors: string[];
  warnings: string[];
}

export interface GenerationResponse {
  success: boolean;
  file_path: string | null;
  incentive_estimate: number | null;
  errors: string[];
  warnings: string[];
}

export interface ExtractAndMergeResponse {
  success: boolean;
  extraction: ExtractionResponse;
  calculator_input: BMSCalculatorInput | null;
}

// ─── Auth, Roles & Permissions ──────────────────────────────────────────────

export enum UserRole {
  PLATFORM_ADMIN = "PLATFORM_ADMIN",
  PLATFORM_SUPPORT = "PLATFORM_SUPPORT",
  CLIENT_ADMIN = "CLIENT_ADMIN",
  CLIENT_USER = "CLIENT_USER",
  CLIENT_VIEWER = "CLIENT_VIEWER",
  CLIENT_BILLING = "CLIENT_BILLING",
}

export enum Permission {
  // Submission lifecycle
  SUBMISSION_CREATE = "SUBMISSION_CREATE",
  SUBMISSION_READ = "SUBMISSION_READ",
  SUBMISSION_EDIT = "SUBMISSION_EDIT",
  SUBMISSION_DELETE = "SUBMISSION_DELETE",
  SUBMISSION_GENERATE_EXCEL = "SUBMISSION_GENERATE_EXCEL",
  SUBMISSION_DOWNLOAD = "SUBMISSION_DOWNLOAD",

  // Bill upload & extraction
  BILL_UPLOAD = "BILL_UPLOAD",
  BILL_RERUN_EXTRACTION = "BILL_RERUN_EXTRACTION",

  // Customer / Location management
  CUSTOMER_CREATE = "CUSTOMER_CREATE",
  CUSTOMER_READ = "CUSTOMER_READ",
  CUSTOMER_EDIT = "CUSTOMER_EDIT",
  CUSTOMER_DELETE = "CUSTOMER_DELETE",
  LOCATION_CREATE = "LOCATION_CREATE",
  LOCATION_READ = "LOCATION_READ",
  LOCATION_EDIT = "LOCATION_EDIT",
  LOCATION_DELETE = "LOCATION_DELETE",

  // Client management (platform-level)
  CLIENT_CREATE = "CLIENT_CREATE",
  CLIENT_READ = "CLIENT_READ",
  CLIENT_EDIT = "CLIENT_EDIT",
  CLIENT_DEACTIVATE = "CLIENT_DEACTIVATE",

  // User management
  USER_INVITE = "USER_INVITE",
  USER_READ = "USER_READ",
  USER_EDIT = "USER_EDIT",
  USER_DEACTIVATE = "USER_DEACTIVATE",

  // Billing & payments
  BILLING_VIEW = "BILLING_VIEW",
  BILLING_MANAGE = "BILLING_MANAGE",

  // Support & diagnostics
  SUPPORT_VIEW_ANY_TENANT = "SUPPORT_VIEW_ANY_TENANT",
  SUPPORT_VIEW_EXTRACTION_DIAGNOSTICS = "SUPPORT_VIEW_EXTRACTION_DIAGNOSTICS",
  SUPPORT_IMPERSONATE = "SUPPORT_IMPERSONATE",
  SUPPORT_RERUN_EXTRACTION = "SUPPORT_RERUN_EXTRACTION",
  SUPPORT_ADD_NOTES = "SUPPORT_ADD_NOTES",

  // Audit
  AUDIT_LOG_VIEW = "AUDIT_LOG_VIEW",
  AUDIT_LOG_VIEW_ALL = "AUDIT_LOG_VIEW_ALL",
}

export interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
  clientId: string | null;
  permissions: Permission[];
  isImpersonating?: boolean;
  impersonationSessionId?: string;
}

// ─── Audit Log ──────────────────────────────────────────────────────────────

export enum AuditAction {
  USER_LOGIN = "USER_LOGIN",
  USER_LOGOUT = "USER_LOGOUT",
  SUBMISSION_CREATED = "SUBMISSION_CREATED",
  SUBMISSION_UPDATED = "SUBMISSION_UPDATED",
  SUBMISSION_FIELD_CHANGED = "SUBMISSION_FIELD_CHANGED",
  SUBMISSION_STATUS_CHANGED = "SUBMISSION_STATUS_CHANGED",
  SUBMISSION_DELETED = "SUBMISSION_DELETED",
  BILL_UPLOADED = "BILL_UPLOADED",
  EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED",
  EXTRACTION_RERUN = "EXTRACTION_RERUN",
  EXCEL_GENERATED = "EXCEL_GENERATED",
  EXCEL_DOWNLOADED = "EXCEL_DOWNLOADED",
  USER_ROLE_CHANGED = "USER_ROLE_CHANGED",
  USER_PERMISSION_OVERRIDE_SET = "USER_PERMISSION_OVERRIDE_SET",
  IMPERSONATION_STARTED = "IMPERSONATION_STARTED",
  IMPERSONATION_ENDED = "IMPERSONATION_ENDED",
  SUPPORT_NOTE_ADDED = "SUPPORT_NOTE_ADDED",
  HEALTH_CHECK_RUN = "HEALTH_CHECK_RUN",
}

export interface AuditLogEntry {
  id: string;
  performedBy: { id: string; name: string | null; email: string };
  action: AuditAction;
  clientId: string | null;
  targetType: string | null;
  targetId: string | null;
  previousValue: Record<string, unknown> | null;
  newValue: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  impersonationSessionId: string | null;
  createdAt: string;
}

// ─── Support & Diagnostics ──────────────────────────────────────────────────

export enum HealthCheckSeverity {
  INFO = "INFO",
  WARNING = "WARNING",
  ERROR = "ERROR",
  BLOCKER = "BLOCKER",
}

export enum HealthCheckStatus {
  OPEN = "OPEN",
  ACKNOWLEDGED = "ACKNOWLEDGED",
  RESOLVED = "RESOLVED",
  DISMISSED = "DISMISSED",
}

export interface SubmissionHealthCheck {
  id: string;
  submissionId: string;
  checkCode: string;
  severity: HealthCheckSeverity;
  status: HealthCheckStatus;
  title: string;
  detail: string | null;
  fieldPath: string | null;
  currentValue: string | null;
  expectedRange: string | null;
  resolvedById: string | null;
  resolvedAt: string | null;
  resolutionNote: string | null;
  createdAt: string;
}

export interface SupportNote {
  id: string;
  author: { id: string; name: string | null };
  clientId: string | null;
  submissionId: string | null;
  content: string;
  isPinned: boolean;
  createdAt: string;
}

export interface ImpersonationSession {
  id: string;
  impersonator: { id: string; name: string | null; email: string };
  impersonated: { id: string; name: string | null; email: string };
  reason: string;
  startedAt: string;
  endedAt: string | null;
  isActive: boolean;
}

export interface ExtractionRerun {
  id: string;
  billUploadId: string;
  triggeredBy: string;
  parserVersion: string;
  previousConfidence: number;
  newConfidence: number;
  fieldsChanged: string[] | null;
  accepted: boolean | null;
  createdAt: string;
  reviewedAt: string | null;
}

// ─── Client Activity Summary (Support View) ─────────────────────────────────

export interface ClientActivitySummary {
  clientId: string;
  companyName: string;
  totalUsers: number;
  activeUsers: number;
  lastLoginAt: string | null;
  totalSubmissions: number;
  submissionsThisMonth: number;
  draftSubmissions: number;
  failedExtractions: number;
  openHealthChecks: number;
  openSupportNotes: number;
}

// ─── Wizard State ───────────────────────────────────────────────────────────

export type WizardStep =
  | "upload"
  | "review-extraction"
  | "building-info"
  | "project-info"
  | "affected-areas"
  | "review-submit";
