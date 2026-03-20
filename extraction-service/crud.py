"""
BMS Boss — CRUD Operations
Data access layer for clients, buildings, utility accounts, and projects.
All operations are scoped to a vendor_id for multi-tenant isolation.
"""

import json
from database import get_db, generate_id, now_iso, row_to_dict, rows_to_list


# ═══════════════════════════════════════════════════════════════
# Vendor Profile
# ═══════════════════════════════════════════════════════════════

def get_vendor(vendor_id: str) -> dict:
    conn = get_db()
    vendor = row_to_dict(conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone())
    conn.close()
    return vendor


def update_vendor(vendor_id: str, data: dict) -> dict:
    allowed = ['name', 'address', 'city', 'state', 'zip', 'phone', 'email',
               'website', 'company_type', 'w9_tax_id']
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not updates:
        return get_vendor(vendor_id)
    updates['updated_at'] = now_iso()
    set_clause = ', '.join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [vendor_id]
    conn = get_db()
    conn.execute(f"UPDATE vendors SET {set_clause} WHERE id = ?", values)
    conn.commit()
    result = row_to_dict(conn.execute("SELECT * FROM vendors WHERE id = ?", (vendor_id,)).fetchone())
    conn.close()
    return result


# ═══════════════════════════════════════════════════════════════
# Clients
# ═══════════════════════════════════════════════════════════════

def list_clients(vendor_id: str) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT c.*,
               (SELECT COUNT(*) FROM buildings WHERE client_id = c.id) as building_count,
               (SELECT COUNT(*) FROM projects p
                JOIN buildings b ON p.building_id = b.id
                WHERE b.client_id = c.id) as project_count
        FROM clients c WHERE c.vendor_id = ?
        ORDER BY c.name
    """, (vendor_id,)).fetchall()
    conn.close()
    return rows_to_list(rows)


def get_client(vendor_id: str, client_id: str) -> dict:
    conn = get_db()
    client = conn.execute(
        "SELECT * FROM clients WHERE id = ? AND vendor_id = ?", (client_id, vendor_id)
    ).fetchone()
    conn.close()
    return row_to_dict(client)


def create_client(vendor_id: str, data: dict) -> dict:
    client_id = generate_id()
    conn = get_db()
    conn.execute("""
        INSERT INTO clients (id, vendor_id, name, contact_name, contact_email, contact_phone, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (client_id, vendor_id, data.get('name'), data.get('contact_name'),
          data.get('contact_email'), data.get('contact_phone'), data.get('notes'),
          now_iso(), now_iso()))
    conn.commit()
    result = row_to_dict(conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone())
    conn.close()
    return result


def update_client(vendor_id: str, client_id: str, data: dict) -> dict:
    allowed = ['name', 'contact_name', 'contact_email', 'contact_phone', 'notes']
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return get_client(vendor_id, client_id)
    updates['updated_at'] = now_iso()
    set_clause = ', '.join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [client_id, vendor_id]
    conn = get_db()
    conn.execute(f"UPDATE clients SET {set_clause} WHERE id = ? AND vendor_id = ?", values)
    conn.commit()
    result = row_to_dict(conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone())
    conn.close()
    return result


def delete_client(vendor_id: str, client_id: str) -> bool:
    conn = get_db()
    conn.execute("DELETE FROM clients WHERE id = ? AND vendor_id = ?", (client_id, vendor_id))
    conn.commit()
    conn.close()
    return True


# ═══════════════════════════════════════════════════════════════
# Buildings
# ═══════════════════════════════════════════════════════════════

def list_buildings(vendor_id: str, client_id: str) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT b.*,
               (SELECT COUNT(*) FROM projects WHERE building_id = b.id) as project_count,
               (SELECT COUNT(*) FROM utility_accounts WHERE building_id = b.id) as utility_account_count
        FROM buildings b
        JOIN clients c ON b.client_id = c.id
        WHERE c.vendor_id = ? AND b.client_id = ?
        ORDER BY b.name
    """, (vendor_id, client_id)).fetchall()
    conn.close()
    return rows_to_list(rows)


def get_building(vendor_id: str, building_id: str) -> dict:
    conn = get_db()
    bldg = conn.execute("""
        SELECT b.* FROM buildings b
        JOIN clients c ON b.client_id = c.id
        WHERE b.id = ? AND c.vendor_id = ?
    """, (building_id, vendor_id)).fetchone()
    conn.close()
    return row_to_dict(bldg)


def create_building(vendor_id: str, client_id: str, data: dict) -> dict:
    # Verify client belongs to vendor
    client = get_client(vendor_id, client_id)
    if not client:
        return None
    building_id = generate_id()
    conn = get_db()
    conn.execute("""
        INSERT INTO buildings (id, client_id, name, address, city, state, zip, sqft,
                              building_type, heating_fuel, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (building_id, client_id, data.get('name'), data.get('address'), data.get('city'),
          data.get('state', 'MA'), data.get('zip'), data.get('sqft'),
          data.get('building_type'), data.get('heating_fuel'), data.get('notes'),
          now_iso(), now_iso()))
    conn.commit()
    result = row_to_dict(conn.execute("SELECT * FROM buildings WHERE id = ?", (building_id,)).fetchone())
    conn.close()
    return result


def update_building(vendor_id: str, building_id: str, data: dict) -> dict:
    allowed = ['name', 'address', 'city', 'state', 'zip', 'sqft', 'building_type', 'heating_fuel', 'notes']
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return get_building(vendor_id, building_id)
    updates['updated_at'] = now_iso()
    set_clause = ', '.join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [building_id]
    conn = get_db()
    conn.execute(f"UPDATE buildings SET {set_clause} WHERE id = ?", values)
    conn.commit()
    result = row_to_dict(conn.execute("SELECT * FROM buildings WHERE id = ?", (building_id,)).fetchone())
    conn.close()
    return result


# ═══════════════════════════════════════════════════════════════
# Utility Accounts
# ═══════════════════════════════════════════════════════════════

def list_utility_accounts(vendor_id: str, building_id: str) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT ua.* FROM utility_accounts ua
        JOIN buildings b ON ua.building_id = b.id
        JOIN clients c ON b.client_id = c.id
        WHERE c.vendor_id = ? AND ua.building_id = ?
        ORDER BY ua.account_type, ua.utility_sponsor
    """, (vendor_id, building_id)).fetchall()
    conn.close()
    return rows_to_list(rows)


def create_utility_account(vendor_id: str, building_id: str, data: dict) -> dict:
    bldg = get_building(vendor_id, building_id)
    if not bldg:
        return None
    acct_id = generate_id()
    conn = get_db()
    conn.execute("""
        INSERT INTO utility_accounts (id, building_id, account_number, utility_sponsor,
                                     account_type, service_address, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (acct_id, building_id, data.get('account_number'), data.get('utility_sponsor'),
          data.get('account_type', 'electric'), data.get('service_address'),
          data.get('notes'), now_iso()))
    conn.commit()
    result = row_to_dict(conn.execute("SELECT * FROM utility_accounts WHERE id = ?", (acct_id,)).fetchone())
    conn.close()
    return result


# ═══════════════════════════════════════════════════════════════
# Projects
# ═══════════════════════════════════════════════════════════════

PROJECT_STATUSES = [
    'draft', 'submitted_pre_approval', 'pre_approved', 'installed',
    'submitted_final', 'approved', 'paid', 'archived'
]


def list_projects(vendor_id: str, building_id: str = None, status: str = None) -> list:
    conn = get_db()
    query = """
        SELECT p.*, b.name as building_name, b.address as building_address,
               c.name as client_name, c.id as client_id
        FROM projects p
        JOIN buildings b ON p.building_id = b.id
        JOIN clients c ON b.client_id = c.id
        WHERE c.vendor_id = ?
    """
    params = [vendor_id]
    if building_id:
        query += " AND p.building_id = ?"
        params.append(building_id)
    if status:
        query += " AND p.status = ?"
        params.append(status)
    query += " ORDER BY p.updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows_to_list(rows)


def get_project(vendor_id: str, project_id: str) -> dict:
    conn = get_db()
    project = conn.execute("""
        SELECT p.*, b.name as building_name, b.address as building_address,
               b.sqft as building_sqft, b.building_type, b.heating_fuel,
               c.name as client_name, c.id as client_id
        FROM projects p
        JOIN buildings b ON p.building_id = b.id
        JOIN clients c ON b.client_id = c.id
        WHERE p.id = ? AND c.vendor_id = ?
    """, (project_id, vendor_id)).fetchone()
    conn.close()
    return row_to_dict(project)


def create_project(vendor_id: str, building_id: str, data: dict) -> dict:
    bldg = get_building(vendor_id, building_id)
    if not bldg:
        return None
    project_id = generate_id()
    conn = get_db()
    conn.execute("""
        INSERT INTO projects (id, building_id, name, status, project_type,
                             bms_manufacturer, bms_product_type, total_project_cost,
                             calculator_data, notes, created_at, updated_at)
        VALUES (?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_id, building_id, data.get('name'), data.get('project_type'),
          data.get('bms_manufacturer'), data.get('bms_product_type'),
          data.get('total_project_cost'),
          json.dumps(data.get('calculator_data')) if data.get('calculator_data') else None,
          data.get('notes'), now_iso(), now_iso()))
    conn.commit()
    result = row_to_dict(conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone())
    conn.close()
    return result


def update_project(vendor_id: str, project_id: str, data: dict) -> dict:
    allowed = ['name', 'status', 'project_type', 'bms_manufacturer', 'bms_product_type',
               'total_project_cost', 'estimated_incentive', 'approved_incentive',
               'calculator_data', 'calculator_file_path', 'application_file_path', 'notes']
    updates = {}
    for k, v in data.items():
        if k in allowed:
            if k == 'calculator_data' and isinstance(v, dict):
                updates[k] = json.dumps(v)
            else:
                updates[k] = v
    if not updates:
        return get_project(vendor_id, project_id)
    updates['updated_at'] = now_iso()
    set_clause = ', '.join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [project_id]
    conn = get_db()
    conn.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", values)
    conn.commit()
    result = get_project(vendor_id, project_id)
    conn.close()
    return result


def duplicate_project(vendor_id: str, project_id: str, new_name: str = None,
                      new_building_id: str = None) -> dict:
    """Clone a project for easy duplication."""
    source = get_project(vendor_id, project_id)
    if not source:
        return None
    data = {
        'name': new_name or f"{source['name']} (Copy)",
        'project_type': source['project_type'],
        'bms_manufacturer': source['bms_manufacturer'],
        'bms_product_type': source['bms_product_type'],
        'total_project_cost': source['total_project_cost'],
        'calculator_data': json.loads(source['calculator_data']) if source.get('calculator_data') else None,
        'notes': f"Duplicated from: {source['name']}",
    }
    target_building = new_building_id or source['building_id']
    return create_project(vendor_id, target_building, data)


# ═══════════════════════════════════════════════════════════════
# Dashboard / Summary
# ═══════════════════════════════════════════════════════════════

def get_vendor_dashboard(vendor_id: str) -> dict:
    """Get summary stats for the vendor dashboard."""
    conn = get_db()

    client_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM clients WHERE vendor_id = ?", (vendor_id,)
    ).fetchone()['cnt']

    building_count = conn.execute("""
        SELECT COUNT(*) as cnt FROM buildings b
        JOIN clients c ON b.client_id = c.id WHERE c.vendor_id = ?
    """, (vendor_id,)).fetchone()['cnt']

    projects = conn.execute("""
        SELECT p.status, COUNT(*) as cnt,
               COALESCE(SUM(p.estimated_incentive), 0) as total_incentive
        FROM projects p
        JOIN buildings b ON p.building_id = b.id
        JOIN clients c ON b.client_id = c.id
        WHERE c.vendor_id = ?
        GROUP BY p.status
    """, (vendor_id,)).fetchall()

    total_projects = sum(r['cnt'] for r in projects)
    active_projects = sum(r['cnt'] for r in projects if r['status'] not in ('archived', 'paid'))
    total_incentive_pipeline = sum(r['total_incentive'] for r in projects if r['status'] not in ('archived',))
    approved_incentives = sum(r['total_incentive'] for r in projects if r['status'] in ('approved', 'paid'))

    recent_projects = conn.execute("""
        SELECT p.id, p.name, p.status, p.estimated_incentive, p.updated_at,
               b.name as building_name, c.name as client_name
        FROM projects p
        JOIN buildings b ON p.building_id = b.id
        JOIN clients c ON b.client_id = c.id
        WHERE c.vendor_id = ?
        ORDER BY p.updated_at DESC LIMIT 5
    """, (vendor_id,)).fetchall()

    conn.close()

    return {
        "client_count": client_count,
        "building_count": building_count,
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_incentive_pipeline": total_incentive_pipeline,
        "approved_incentives": approved_incentives,
        "projects_by_status": {r['status']: r['cnt'] for r in projects},
        "recent_projects": rows_to_list(recent_projects),
    }
