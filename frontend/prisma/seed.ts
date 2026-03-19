/**
 * BMS Boss — Database Seed
 * Populates the default role → permission mappings.
 *
 * Run with: npx prisma db seed
 * Configure in package.json: "prisma": { "seed": "npx ts-node prisma/seed.ts" }
 */

import { PrismaClient, UserRole, Permission } from "@prisma/client";

const prisma = new PrismaClient();

// ─── Default Permissions per Role ────────────────────────────────────────────

const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
  // Full platform access
  PLATFORM_ADMIN: Object.values(Permission),

  // Cross-tenant read + diagnostics, no billing management
  PLATFORM_SUPPORT: [
    Permission.SUBMISSION_READ,
    Permission.SUBMISSION_DOWNLOAD,
    Permission.BILL_RERUN_EXTRACTION,
    Permission.CUSTOMER_READ,
    Permission.LOCATION_READ,
    Permission.CLIENT_READ,
    Permission.USER_READ,
    Permission.SUPPORT_VIEW_ANY_TENANT,
    Permission.SUPPORT_VIEW_EXTRACTION_DIAGNOSTICS,
    Permission.SUPPORT_IMPERSONATE,
    Permission.SUPPORT_RERUN_EXTRACTION,
    Permission.SUPPORT_ADD_NOTES,
    Permission.AUDIT_LOG_VIEW,
    Permission.AUDIT_LOG_VIEW_ALL,
  ],

  // Full access within their tenant
  CLIENT_ADMIN: [
    Permission.SUBMISSION_CREATE,
    Permission.SUBMISSION_READ,
    Permission.SUBMISSION_EDIT,
    Permission.SUBMISSION_DELETE,
    Permission.SUBMISSION_GENERATE_EXCEL,
    Permission.SUBMISSION_DOWNLOAD,
    Permission.BILL_UPLOAD,
    Permission.CUSTOMER_CREATE,
    Permission.CUSTOMER_READ,
    Permission.CUSTOMER_EDIT,
    Permission.CUSTOMER_DELETE,
    Permission.LOCATION_CREATE,
    Permission.LOCATION_READ,
    Permission.LOCATION_EDIT,
    Permission.LOCATION_DELETE,
    Permission.USER_INVITE,
    Permission.USER_READ,
    Permission.USER_EDIT,
    Permission.USER_DEACTIVATE,
    Permission.BILLING_VIEW,
    Permission.BILLING_MANAGE,
    Permission.AUDIT_LOG_VIEW,
  ],

  // Create and edit submissions, manage customers/locations
  CLIENT_USER: [
    Permission.SUBMISSION_CREATE,
    Permission.SUBMISSION_READ,
    Permission.SUBMISSION_EDIT,
    Permission.SUBMISSION_GENERATE_EXCEL,
    Permission.SUBMISSION_DOWNLOAD,
    Permission.BILL_UPLOAD,
    Permission.CUSTOMER_CREATE,
    Permission.CUSTOMER_READ,
    Permission.CUSTOMER_EDIT,
    Permission.LOCATION_CREATE,
    Permission.LOCATION_READ,
    Permission.LOCATION_EDIT,
  ],

  // Read-only: view everything but change nothing
  CLIENT_VIEWER: [
    Permission.SUBMISSION_READ,
    Permission.SUBMISSION_DOWNLOAD,
    Permission.CUSTOMER_READ,
    Permission.LOCATION_READ,
  ],

  // Billing access only — no submission or customer data
  CLIENT_BILLING: [
    Permission.BILLING_VIEW,
    Permission.BILLING_MANAGE,
    Permission.USER_READ,
  ],
};

// ─── Health Check Definitions ────────────────────────────────────────────────

const HEALTH_CHECK_DEFINITIONS = [
  {
    code: "SQFT_EXCEEDS_LIMIT",
    title: "Building exceeds 300,000 sqft prescriptive limit",
    severity: "BLOCKER",
    field: "total_building_sqft",
    expectedRange: "1 – 300,000",
  },
  {
    code: "LOW_EXTRACTION_CONFIDENCE",
    title: "Bill extraction confidence below 80%",
    severity: "WARNING",
    field: "extraction_confidence",
    expectedRange: "0.80 – 1.00",
  },
  {
    code: "INCENTIVE_EXCEEDS_60_PCT",
    title: "Incentive estimate exceeds 60% of project cost",
    severity: "ERROR",
    field: "incentive_estimate",
    expectedRange: "≤ 60% of total_project_cost",
  },
  {
    code: "MISSING_REQUIRED_FIELDS",
    title: "Required calculator fields are missing",
    severity: "BLOCKER",
    field: null,
    expectedRange: null,
  },
  {
    code: "NO_SEQUENCES_SELECTED",
    title: "No sequences of operation selected for any area",
    severity: "ERROR",
    field: "affected_areas.*.seq_*",
    expectedRange: "≥ 1 sequence per area",
  },
  {
    code: "ZERO_AFFECTED_SQFT",
    title: "Affected area has zero square footage",
    severity: "ERROR",
    field: "affected_areas.*.affected_sqft",
    expectedRange: "> 0",
  },
  {
    code: "BILL_AGE_EXCEEDED",
    title: "Uploaded bill is older than 6 months",
    severity: "WARNING",
    field: "billing_period_end",
    expectedRange: "Within last 6 months",
  },
  {
    code: "ANNUAL_USAGE_MISMATCH",
    title: "Annual usage doesn't match sum of monthly history",
    severity: "WARNING",
    field: "annual_electric_kwh",
    expectedRange: "Within 5% of monthly sum",
  },
  {
    code: "HIGH_INCENTIVE_VALUE",
    title: "Estimated incentive exceeds $200,000",
    severity: "INFO",
    field: "incentive_estimate",
    expectedRange: "Review recommended for large incentives",
  },
];

// ─── Seed Function ───────────────────────────────────────────────────────────

async function main() {
  console.log("Seeding BMS Boss database...\n");

  // 1. Seed role permissions
  console.log("Seeding role permissions...");
  let count = 0;
  for (const [role, permissions] of Object.entries(ROLE_PERMISSIONS)) {
    for (const permission of permissions) {
      await prisma.rolePermission.upsert({
        where: {
          role_permission: {
            role: role as UserRole,
            permission: permission,
          },
        },
        update: {},
        create: {
          role: role as UserRole,
          permission: permission,
        },
      });
      count++;
    }
  }
  console.log(`  Created ${count} role-permission mappings across ${Object.keys(ROLE_PERMISSIONS).length} roles.\n`);

  // 2. Log health check definitions (these are enforced in app code, not DB)
  console.log("Health check definitions (enforced in application layer):");
  for (const check of HEALTH_CHECK_DEFINITIONS) {
    console.log(`  [${check.severity}] ${check.code}: ${check.title}`);
  }

  console.log("\nSeed complete.");
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
