/**
 * BMS Boss — Permission Utilities
 *
 * Client-side permission checking. The source of truth is the server
 * (Prisma role_permissions + user_permission_overrides), but this module
 * provides fast UI-level checks to hide/disable elements the user can't use.
 *
 * The AuthUser object returned by the session API includes a resolved
 * `permissions: Permission[]` array that already accounts for role defaults
 * and per-user overrides, so we just check membership.
 */

import { Permission, UserRole, type AuthUser } from "@/types";

// ─── Core Check ──────────────────────────────────────────────────────────────

/** Returns true if the user has a specific permission. */
export function hasPermission(user: AuthUser, permission: Permission): boolean {
  return user.permissions.includes(permission);
}

/** Returns true if the user has ALL of the listed permissions. */
export function hasAllPermissions(
  user: AuthUser,
  permissions: Permission[],
): boolean {
  return permissions.every((p) => user.permissions.includes(p));
}

/** Returns true if the user has ANY of the listed permissions. */
export function hasAnyPermission(
  user: AuthUser,
  permissions: Permission[],
): boolean {
  return permissions.some((p) => user.permissions.includes(p));
}

// ─── Role Helpers ────────────────────────────────────────────────────────────

/** True if user is a platform-level role (admin or support). */
export function isPlatformUser(user: AuthUser): boolean {
  return [UserRole.PLATFORM_ADMIN, UserRole.PLATFORM_SUPPORT].includes(
    user.role,
  );
}

/** True if user can modify data (not a viewer or billing-only role). */
export function canModifyData(user: AuthUser): boolean {
  return hasAnyPermission(user, [
    Permission.SUBMISSION_CREATE,
    Permission.SUBMISSION_EDIT,
  ]);
}

/** True if user can access support/diagnostics tools. */
export function canAccessSupportTools(user: AuthUser): boolean {
  return hasAnyPermission(user, [
    Permission.SUPPORT_VIEW_ANY_TENANT,
    Permission.SUPPORT_VIEW_EXTRACTION_DIAGNOSTICS,
    Permission.SUPPORT_IMPERSONATE,
  ]);
}

/** True if user can view billing information. */
export function canViewBilling(user: AuthUser): boolean {
  return hasPermission(user, Permission.BILLING_VIEW);
}

// ─── UI Visibility Helpers ───────────────────────────────────────────────────

/** Returns the navigation items visible to this user. */
export function getVisibleNavItems(user: AuthUser) {
  const items: { label: string; href: string; icon?: string }[] = [];

  // Dashboard — everyone sees this
  items.push({ label: "Dashboard", href: "/" });

  // New Submission — only users who can create
  if (hasPermission(user, Permission.SUBMISSION_CREATE)) {
    items.push({ label: "New Submission", href: "/submissions/new" });
  }

  // Submissions list — anyone who can read
  if (hasPermission(user, Permission.SUBMISSION_READ)) {
    items.push({ label: "Submissions", href: "/submissions" });
  }

  // Customers — anyone who can read customers
  if (hasPermission(user, Permission.CUSTOMER_READ)) {
    items.push({ label: "Customers", href: "/customers" });
  }

  // Billing — billing roles
  if (hasPermission(user, Permission.BILLING_VIEW)) {
    items.push({ label: "Billing", href: "/billing" });
  }

  // Support tools — platform support/admin
  if (canAccessSupportTools(user)) {
    items.push({ label: "Support", href: "/support" });
  }

  // Audit log
  if (hasAnyPermission(user, [Permission.AUDIT_LOG_VIEW, Permission.AUDIT_LOG_VIEW_ALL])) {
    items.push({ label: "Audit Log", href: "/audit" });
  }

  // User management
  if (hasPermission(user, Permission.USER_INVITE)) {
    items.push({ label: "Users", href: "/users" });
  }

  return items;
}

// ─── Submission Action Helpers ───────────────────────────────────────────────

/** Returns which actions the user can take on a submission. */
export function getSubmissionActions(user: AuthUser) {
  return {
    canView: hasPermission(user, Permission.SUBMISSION_READ),
    canEdit: hasPermission(user, Permission.SUBMISSION_EDIT),
    canDelete: hasPermission(user, Permission.SUBMISSION_DELETE),
    canGenerateExcel: hasPermission(user, Permission.SUBMISSION_GENERATE_EXCEL),
    canDownload: hasPermission(user, Permission.SUBMISSION_DOWNLOAD),
    canUploadBill: hasPermission(user, Permission.BILL_UPLOAD),
    canRerunExtraction: hasPermission(user, Permission.BILL_RERUN_EXTRACTION),
  };
}
