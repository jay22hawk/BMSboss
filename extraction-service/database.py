"""
BMS Boss — Database Layer
SQLite-based persistence for multi-tenant account management.
Uses Python stdlib sqlite3 for zero-dependency operation.

Schema follows the PRD data model:
  Platform > Vendor > User > Client > Building > Project
"""

import sqlite3
import os
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "bmsboss.db"


def get_db() -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database schema. Safe to call multiple times (IF NOT EXISTS)."""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.close()


SCHEMA = """
-- ═══════════════════════════════════════════════════════════════
-- Vendor (Tenant) — the BMS company/installer
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS vendors (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT DEFAULT 'MA',
    zip TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    company_type TEXT DEFAULT 'incorporated',  -- incorporated, not_incorporated, exempt
    w9_tax_id TEXT,

    -- Stripe billing integration
    stripe_customer_id TEXT UNIQUE,
    subscription_tier TEXT DEFAULT 'trial',     -- trial, starter, professional, enterprise
    subscription_status TEXT DEFAULT 'trialing', -- trialing, active, past_due, canceled, unpaid
    stripe_subscription_id TEXT,
    trial_ends_at TEXT,
    billing_period_end TEXT,

    -- Tier limits (cached from Stripe product metadata)
    max_projects_per_month INTEGER DEFAULT 3,
    max_users INTEGER DEFAULT 1,

    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- User — individual users within a vendor account
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    vendor_id TEXT NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'admin',  -- admin, project_manager, viewer
    is_active INTEGER DEFAULT 1,
    last_login TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- Client — end customer / building owner
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    vendor_id TEXT NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    contact_name TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- Building / Site — a specific facility belonging to a client
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS buildings (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    client_id TEXT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT DEFAULT 'MA',
    zip TEXT,
    sqft REAL,
    building_type TEXT,  -- Education K-12, Office, Retail, etc.
    heating_fuel TEXT,   -- Natural Gas, Oil, Electric, Propane
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- Utility Account — electric/gas accounts linked to buildings
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS utility_accounts (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    building_id TEXT NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    account_number TEXT NOT NULL,
    utility_sponsor TEXT NOT NULL,  -- National Grid, Eversource, etc.
    account_type TEXT DEFAULT 'electric',  -- electric, gas
    service_address TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- Project — a BMS incentive application for a building
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    building_id TEXT NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
        -- draft, submitted_pre_approval, pre_approved, installed,
        -- submitted_final, approved, paid, archived
    project_type TEXT,  -- new_bms, replacement, addon, subscription
    bms_manufacturer TEXT,
    bms_product_type TEXT,
    total_project_cost REAL,
    estimated_incentive REAL,
    approved_incentive REAL,

    -- Calculator data (JSON blob for flexibility)
    calculator_data TEXT,  -- JSON: affected areas, sequences, etc.

    -- Generated files
    calculator_file_path TEXT,
    application_file_path TEXT,

    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- Document — files associated with projects
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
        -- utility_bill, calculator, application, proposal,
        -- sequence_of_operation, w9, screenshot, trend_data, other
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    uploaded_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- Bill Extraction — extracted data from utility bill PDFs
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS bill_extractions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    utility_account_id TEXT REFERENCES utility_accounts(id),
    raw_pdf_path TEXT,
    extracted_data TEXT,  -- JSON blob of ExtractedBillData
    utility_sponsor TEXT,
    extraction_warnings TEXT,  -- JSON array
    extracted_at TEXT DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════
-- Session tokens for auth
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vendor_id TEXT NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_users_vendor ON users(vendor_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_clients_vendor ON clients(vendor_id);
CREATE INDEX IF NOT EXISTS idx_buildings_client ON buildings(client_id);
CREATE INDEX IF NOT EXISTS idx_utility_accounts_building ON utility_accounts(building_id);
CREATE INDEX IF NOT EXISTS idx_projects_building ON projects(building_id);
CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_bill_extractions_project ON bill_extractions(project_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
"""


# ═══════════════════════════════════════════════════════════════
# Helper functions
# ═══════════════════════════════════════════════════════════════

def generate_id() -> str:
    return uuid.uuid4().hex


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a dict."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows) -> list:
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
    conn = get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    print(f"Tables: {', '.join(r['name'] for r in tables)}")
    conn.close()
