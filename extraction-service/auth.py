"""
BMS Boss — Authentication and Authorization
Handles user registration, login, session management, and role-based access control.

Uses:
  - hashlib + secrets for password hashing (stdlib, no bcrypt dependency)
  - Token-based sessions stored in SQLite
  - Subscription-aware middleware for tier enforcement
"""

import hashlib
import secrets
import json
from datetime import datetime, timedelta
from database import get_db, generate_id, now_iso, row_to_dict


# ═══════════════════════════════════════════════════════════════
# Password Hashing (PBKDF2 — stdlib, no external deps)
# ═══════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2-SHA256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100_000)
    return f"{salt}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        salt, key_hex = stored_hash.split('$')
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100_000)
        return key.hex() == key_hex
    except (ValueError, AttributeError):
        return False


# ═══════════════════════════════════════════════════════════════
# Vendor Registration
# ═══════════════════════════════════════════════════════════════

def register_vendor(
    company_name: str,
    admin_name: str,
    admin_email: str,
    admin_password: str,
    company_address: str = None,
    company_city: str = None,
    company_state: str = 'MA',
    company_zip: str = None,
    company_phone: str = None,
) -> dict:
    """
    Register a new vendor account with an admin user.
    Returns the vendor and user records, plus a session token.
    """
    conn = get_db()

    # Check if email already exists
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (admin_email,)).fetchone()
    if existing:
        conn.close()
        return {"success": False, "error": "An account with this email already exists"}

    vendor_id = generate_id()
    user_id = generate_id()
    trial_end = (datetime.utcnow() + timedelta(days=30)).isoformat()

    try:
        # Create vendor (tenant)
        conn.execute("""
            INSERT INTO vendors (id, name, address, city, state, zip, phone, email,
                               subscription_tier, subscription_status, trial_ends_at,
                               max_projects_per_month, max_users, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'trial', 'trialing', ?, 3, 1, ?, ?)
        """, (vendor_id, company_name, company_address, company_city, company_state,
              company_zip, company_phone, admin_email, trial_end, now_iso(), now_iso()))

        # Create admin user
        conn.execute("""
            INSERT INTO users (id, vendor_id, email, name, password_hash, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 'admin', 1, ?)
        """, (user_id, vendor_id, admin_email, admin_name, hash_password(admin_password), now_iso()))

        conn.commit()

        # Create session
        token = create_session(conn, user_id, vendor_id)
        conn.commit()

        vendor = row_to_dict(conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone())
        user = row_to_dict(conn.execute("SELECT id, vendor_id, email, name, role FROM users WHERE id = ?", (user_id,)).fetchone())

        conn.close()
        return {
            "success": True,
            "vendor": vendor,
            "user": user,
            "token": token,
            "trial_ends_at": trial_end,
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# Login / Logout
# ═══════════════════════════════════════════════════════════════

def login(email: str, password: str) -> dict:
    """Authenticate a user and return a session token."""
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)
    ).fetchone()

    if not user or not verify_password(password, user['password_hash']):
        conn.close()
        return {"success": False, "error": "Invalid email or password"}

    # Update last login
    conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_iso(), user['id']))

    # Create session
    token = create_session(conn, user['id'], user['vendor_id'])
    conn.commit()

    # Get vendor info
    vendor = row_to_dict(conn.execute("SELECT * FROM vendors WHERE id = ?", (user['vendor_id'],)).fetchone())

    conn.close()
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user['role'],
            "vendor_id": user['vendor_id'],
        },
        "vendor": vendor,
    }


def logout(token: str) -> bool:
    """Invalidate a session token."""
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return True


# ═══════════════════════════════════════════════════════════════
# Session Management
# ═══════════════════════════════════════════════════════════════

def create_session(conn, user_id: str, vendor_id: str, hours: int = 24) -> str:
    """Create a session token. Returns the token string."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(hours=hours)).isoformat()
    conn.execute(
        "INSERT INTO sessions (token, user_id, vendor_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?)",
        (token, user_id, vendor_id, now_iso(), expires)
    )
    return token


def validate_session(token: str) -> dict:
    """
    Validate a session token and return user + vendor context.
    Returns None if invalid or expired.
    """
    if not token:
        return None

    conn = get_db()

    session = conn.execute("""
        SELECT s.*, u.email, u.name, u.role, u.is_active,
               v.name as vendor_name, v.subscription_tier, v.subscription_status,
               v.max_projects_per_month, v.max_users, v.trial_ends_at
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        JOIN vendors v ON s.vendor_id = v.id
        WHERE s.token = ? AND s.expires_at > ?
    """, (token, now_iso())).fetchone()

    conn.close()

    if not session or not session['is_active']:
        return None

    return {
        "user_id": session['user_id'],
        "vendor_id": session['vendor_id'],
        "email": session['email'],
        "name": session['name'],
        "role": session['role'],
        "vendor_name": session['vendor_name'],
        "subscription_tier": session['subscription_tier'],
        "subscription_status": session['subscription_status'],
        "max_projects_per_month": session['max_projects_per_month'],
        "max_users": session['max_users'],
    }


# ═══════════════════════════════════════════════════════════════
# Subscription Enforcement
# ═══════════════════════════════════════════════════════════════

TIER_LIMITS = {
    'trial':        {'projects_per_month': 3,  'users': 1},
    'starter':      {'projects_per_month': 5,  'users': 1},
    'professional': {'projects_per_month': 20, 'users': 3},
    'enterprise':   {'projects_per_month': 999, 'users': 10},
}


def check_subscription_access(session_ctx: dict, action: str = "read") -> dict:
    """
    Check if the current subscription allows the requested action.

    Args:
        session_ctx: The validated session context from validate_session()
        action: "read", "create_project", "invite_user", "upload_bill"

    Returns:
        {"allowed": True} or {"allowed": False, "reason": "..."}
    """
    status = session_ctx.get('subscription_status', 'canceled')

    # Read-only access is always allowed (even for canceled accounts)
    if action == "read":
        return {"allowed": True}

    # Write actions require active or trialing subscription
    if status == 'canceled' or status == 'unpaid':
        return {
            "allowed": False,
            "reason": "Your subscription is inactive. Please update your billing to continue."
        }

    # Check tier-specific limits for project creation
    if action == "create_project":
        tier = session_ctx.get('subscription_tier', 'trial')
        limit = TIER_LIMITS.get(tier, {}).get('projects_per_month', 0)
        count = _count_projects_this_month(session_ctx['vendor_id'])
        if count >= limit:
            return {
                "allowed": False,
                "reason": f"You've reached your monthly project limit ({limit} projects on the {tier} plan). Upgrade your plan to create more."
            }

    if action == "invite_user":
        tier = session_ctx.get('subscription_tier', 'trial')
        limit = TIER_LIMITS.get(tier, {}).get('users', 0)
        count = _count_users(session_ctx['vendor_id'])
        if count >= limit:
            return {
                "allowed": False,
                "reason": f"You've reached your user limit ({limit} users on the {tier} plan). Upgrade your plan to add more team members."
            }

    return {"allowed": True}


def _count_projects_this_month(vendor_id: str) -> int:
    """Count projects created this month for a vendor."""
    conn = get_db()
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0).isoformat()
    count = conn.execute("""
        SELECT COUNT(*) as cnt FROM projects p
        JOIN buildings b ON p.building_id = b.id
        JOIN clients c ON b.client_id = c.id
        WHERE c.vendor_id = ? AND p.created_at >= ?
    """, (vendor_id, first_of_month)).fetchone()['cnt']
    conn.close()
    return count


def _count_users(vendor_id: str) -> int:
    """Count active users for a vendor."""
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE vendor_id = ? AND is_active = 1",
        (vendor_id,)
    ).fetchone()['cnt']
    conn.close()
    return count


# ═══════════════════════════════════════════════════════════════
# Stripe Integration Stubs
# ═══════════════════════════════════════════════════════════════

def create_stripe_customer(vendor_id: str, email: str, name: str) -> str:
    """
    Create a Stripe customer for a vendor.
    STUB: In production, this calls stripe.Customer.create() and returns the ID.
    For now, generates a mock ID.
    """
    mock_stripe_id = f"cus_mock_{vendor_id[:12]}"
    conn = get_db()
    conn.execute(
        "UPDATE vendors SET stripe_customer_id = ? WHERE id = ?",
        (mock_stripe_id, vendor_id)
    )
    conn.commit()
    conn.close()
    return mock_stripe_id


def handle_stripe_webhook(event_type: str, data: dict) -> dict:
    """
    Handle incoming Stripe webhook events.
    STUB: In production, this verifies the webhook signature and processes events.
    """
    handlers = {
        'checkout.session.completed': _handle_checkout_completed,
        'invoice.paid': _handle_invoice_paid,
        'invoice.payment_failed': _handle_payment_failed,
        'customer.subscription.updated': _handle_subscription_updated,
        'customer.subscription.deleted': _handle_subscription_deleted,
    }
    handler = handlers.get(event_type)
    if handler:
        return handler(data)
    return {"handled": False, "reason": f"Unhandled event type: {event_type}"}


def _handle_checkout_completed(data: dict) -> dict:
    """Process successful checkout — activate subscription."""
    # In production: extract customer_id and subscription details from data
    return {"handled": True, "action": "subscription_activated"}


def _handle_invoice_paid(data: dict) -> dict:
    """Process successful payment — confirm active subscription."""
    return {"handled": True, "action": "payment_confirmed"}


def _handle_payment_failed(data: dict) -> dict:
    """Process failed payment — set status to past_due."""
    return {"handled": True, "action": "marked_past_due"}


def _handle_subscription_updated(data: dict) -> dict:
    """Process subscription change — update tier."""
    return {"handled": True, "action": "tier_updated"}


def _handle_subscription_deleted(data: dict) -> dict:
    """Process subscription cancellation."""
    return {"handled": True, "action": "subscription_canceled"}
