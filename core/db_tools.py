import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

_ROOT      = Path(__file__).parent.parent
SUPPORT_DB = str(_ROOT / "support.db")
CLINIC_DB  = str(_ROOT / "clinic.db")


# =========================================================
# HELPERS
# =========================================================

def _connect(db_name: str):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_to_list(rows) -> list[dict]:
    return [dict(row) for row in rows]


# =========================================================
# SUPPORT TOOLS  —  support.db
# =========================================================

# ── Account lookup ────────────────────────────────────────

def find_account_by_email(email: str) -> dict:
    """Find an account using the registered email."""
    with _connect(SUPPORT_DB) as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE email = ?",
            (email,),
        ).fetchone()

    if not row:
        return {"error": f"No account found for email '{email}'."}

    return dict(row)


def find_account_by_clinic_name(name: str) -> dict:
    """Find an account by clinic name (partial match)."""
    with _connect(SUPPORT_DB) as conn:
        row = conn.execute(
            "SELECT * FROM accounts WHERE clinic_name LIKE ?",
            (f"%{name}%",),
        ).fetchone()

    if not row:
        return {"error": f"No account found matching '{name}'."}

    return dict(row)


# ── Billing ───────────────────────────────────────────────

def get_customer_plan(account_id: int) -> dict:
    """Get the current subscription plan for an account."""
    with _connect(SUPPORT_DB) as conn:
        row = conn.execute(
            "SELECT plan, billing_cycle, price, status FROM accounts WHERE account_id = ?",
            (account_id,),
        ).fetchone()

    if not row:
        return {"error": f"Account {account_id} not found."}

    return dict(row)


def get_invoices(account_id: int) -> list[dict]:
    """Retrieve all invoices for an account."""
    with _connect(SUPPORT_DB) as conn:
        rows = conn.execute(
            "SELECT * FROM invoices WHERE account_id = ? ORDER BY issued_date DESC",
            (account_id,),
        ).fetchall()

    results = _rows_to_list(rows)

    if not results:
        return [{"error": f"No invoices found for account {account_id}."}]

    return results


def update_plan(account_id: int, new_plan: str, billing_cycle: str) -> dict:
    """
    Update the subscription plan for an account.
    new_plan      : 'Basic' or 'Premium'
    billing_cycle : 'monthly' or 'annual'
    """
    price_map = {
        ("Basic",   "monthly"): 99.0,
        ("Premium", "monthly"): 249.0,
        ("Basic",   "annual"):  950.0,
        ("Premium", "annual"):  2390.0,
    }

    price = price_map.get((new_plan, billing_cycle))
    if not price:
        return {"error": "Invalid plan or billing cycle. Use Basic/Premium and monthly/annual."}

    try:
        with _connect(SUPPORT_DB) as conn:
            conn.execute(
                "UPDATE accounts SET plan = ?, billing_cycle = ?, price = ? WHERE account_id = ?",
                (new_plan, billing_cycle, price, account_id),
            )
            conn.commit()

        return {
            "success": True,
            "message": f"Account {account_id} updated to {new_plan} ({billing_cycle}) at ${price}/mo.",
        }

    except Exception as e:
        return {"error": f"Failed to update plan: {e}"}


# ── Users ─────────────────────────────────────────────────

def get_users(account_id: int) -> list[dict]:
    """Get all users associated with an account."""
    with _connect(SUPPORT_DB) as conn:
        rows = conn.execute(
            "SELECT name, email, role FROM users WHERE account_id = ?",
            (account_id,),
        ).fetchall()

    results = _rows_to_list(rows)

    if not results:
        return [{"error": f"No users found for account {account_id}."}]

    return results


# ── Tickets / Escalation ──────────────────────────────────

def get_tickets_for_account(account_id: int) -> list[dict]:
    """Get all support tickets for an account, newest first."""
    with _connect(SUPPORT_DB) as conn:
        rows = conn.execute(
            "SELECT * FROM tickets WHERE account_id = ? ORDER BY created_at DESC",
            (account_id,),
        ).fetchall()

    results = _rows_to_list(rows)

    if not results:
        return [{"error": f"No tickets found for account {account_id}."}]

    return results


def create_support_ticket(
    account_id: int,
    summary: str,
    priority: str = "medium",
    category: str = "general",
) -> dict:
    """
    Create a support ticket for an account.
    priority : 'low', 'medium', 'high'
    category : 'billing', 'technical', 'account', 'feature_request', 'general'
    """
    try:
        ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"

        with _connect(SUPPORT_DB) as conn:
            conn.execute(
                """
                INSERT INTO tickets (ticket_id, account_id, summary, priority, category, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'open', ?)
                """,
                (ticket_id, account_id, summary, priority, category, datetime.now().isoformat()),
            )
            conn.commit()

        return {
            "ticket_id": ticket_id,
            "message": f"Support ticket created. ID: {ticket_id}",
        }

    except Exception as e:
        return {"error": f"Failed to create ticket: {e}"}


def update_ticket_status(ticket_id: str, status: str) -> dict:
    """
    Update the status of a support ticket.
    status : 'open', 'in_progress', 'closed'
    """
    valid = {"open", "in_progress", "closed"}
    if status not in valid:
        return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(valid)}."}

    try:
        with _connect(SUPPORT_DB) as conn:
            cursor = conn.execute(
                "UPDATE tickets SET status = ? WHERE ticket_id = ?",
                (status, ticket_id),
            )
            conn.commit()

        if cursor.rowcount > 0:
            return {"success": True, "message": f"Ticket {ticket_id} updated to '{status}'."}

        return {"error": f"Ticket {ticket_id} not found."}

    except Exception as e:
        return {"error": f"Failed to update ticket: {e}"}


# ── Account status ────────────────────────────────────────

def reactivate_account(account_id: int) -> dict:
    """Reactivate a suspended or trial account back to active."""
    try:
        with _connect(SUPPORT_DB) as conn:
            cursor = conn.execute(
                "UPDATE accounts SET status = 'active' WHERE account_id = ?",
                (account_id,),
            )
            conn.commit()

        if cursor.rowcount > 0:
            return {"success": True, "message": f"Account {account_id} reactivated."}

        return {"error": f"Account {account_id} not found."}

    except Exception as e:
        return {"error": f"Failed to reactivate account: {e}"}


# ── Feedback loop ─────────────────────────────────────────

def log_interaction(
    thread_id: str,
    account_id: int,
    intent: str,
    success: bool,
    summary: str,
) -> dict:
    """Log a completed agent interaction for analytics and feedback."""
    try:
        with _connect(SUPPORT_DB) as conn:
            conn.execute(
                """
                INSERT INTO interactions (thread_id, account_id, intent, success, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (thread_id, account_id, intent, int(success), summary, datetime.now().isoformat()),
            )
            conn.commit()

        return {"success": True, "message": "Interaction logged."}

    except Exception as e:
        return {"error": f"Failed to log interaction: {e}"}


# =========================================================
# CLINIC DEMO TOOLS  —  clinic.db
# =========================================================

# ── Providers ─────────────────────────────────────────────

def get_available_providers() -> list[dict]:
    """Return all available providers."""
    with _connect(CLINIC_DB) as conn:
        rows = conn.execute(
            "SELECT * FROM providers WHERE available = 1"
        ).fetchall()

    results = _rows_to_list(rows)

    if not results:
        return [{"error": "No providers currently available."}]

    return results


# ── Appointments ──────────────────────────────────────────

def get_appointments(account_id: int) -> list[dict]:
    """Get all appointments for an account, ordered by date."""
    with _connect(CLINIC_DB) as conn:
        rows = conn.execute(
            """
            SELECT a.*, p.name AS provider_name, p.specialty
            FROM appointments a
            JOIN providers p ON a.provider_id = p.provider_id
            WHERE a.account_id = ?
            ORDER BY a.appointment_date
            """,
            (account_id,),
        ).fetchall()

    results = _rows_to_list(rows)

    if not results:
        return [{"error": f"No appointments found for account {account_id}."}]

    return results


def get_appointments_by_provider(provider_id: int) -> list[dict]:
    """
    Get all appointments assigned to a specific provider by their provider ID.
    Use this when the user asks about a provider's schedule, not a patient's.
    """
    with _connect(CLINIC_DB) as conn:
        rows = conn.execute(
            """
            SELECT a.*, p.name AS provider_name, p.specialty
            FROM appointments a
            JOIN providers p ON a.provider_id = p.provider_id
            WHERE a.provider_id = ?
            ORDER BY a.appointment_date
            """,
            (provider_id,),
        ).fetchall()

    results = _rows_to_list(rows)

    if not results:
        return [{"error": f"No appointments found for provider ID {provider_id}."}]

    return results


def get_patient_appointments(patient_name: str) -> list[dict]:
    """
    Look up all appointments for a patient by name (partial match).
    Useful for the demo agent to pull a patient's full history.
    """
    with _connect(CLINIC_DB) as conn:
        rows = conn.execute(
            """
            SELECT a.*, p.name AS provider_name, p.specialty
            FROM appointments a
            JOIN providers p ON a.provider_id = p.provider_id
            WHERE a.patient_name LIKE ?
            ORDER BY a.appointment_date DESC
            """,
            (f"%{patient_name}%",),
        ).fetchall()

    results = _rows_to_list(rows)

    if not results:
        return [{"error": f"No appointments found for patient '{patient_name}'."}]

    return results


def add_appointment(
    account_id: int,
    patient_name: str,
    provider_id: int,
    appointment_date: str,
    reason: str,
) -> dict:
    """
    Book a new appointment.
    appointment_date format: 'YYYY-MM-DD HH:MM'
    """
    try:
        with _connect(CLINIC_DB) as conn:
            cursor = conn.execute(
                """
                INSERT INTO appointments (account_id, patient_name, provider_id, appointment_date, status, reason)
                VALUES (?, ?, ?, ?, 'scheduled', ?)
                """,
                (account_id, patient_name, provider_id, appointment_date, reason),
            )
            conn.commit()

        return {
            "appointment_id": cursor.lastrowid,
            "message": f"Appointment booked for {patient_name} on {appointment_date}.",
        }

    except Exception as e:
        return {"error": f"Failed to book appointment: {e}"}


def cancel_appointment(appointment_id: int) -> dict:
    """Cancel an appointment by ID."""
    try:
        with _connect(CLINIC_DB) as conn:
            cursor = conn.execute(
                "UPDATE appointments SET status = 'cancelled' WHERE appointment_id = ?",
                (appointment_id,),
            )
            conn.commit()

        if cursor.rowcount > 0:
            return {"success": True, "message": f"Appointment {appointment_id} cancelled."}

        return {"error": f"Appointment {appointment_id} not found."}

    except Exception as e:
        return {"error": f"Failed to cancel appointment: {e}"}


def reschedule_appointment(appointment_id: int, new_datetime: str) -> dict:
    """
    Reschedule an appointment to a new date/time.
    new_datetime format: 'YYYY-MM-DD HH:MM'
    """
    try:
        with _connect(CLINIC_DB) as conn:
            cursor = conn.execute(
                "UPDATE appointments SET appointment_date = ?, status = 'scheduled' WHERE appointment_id = ?",
                (new_datetime, appointment_id),
            )
            conn.commit()

        if cursor.rowcount > 0:
            return {"success": True, "message": f"Appointment {appointment_id} rescheduled to {new_datetime}."}

        return {"error": f"Appointment {appointment_id} not found."}

    except Exception as e:
        return {"error": f"Failed to reschedule: {e}"}


# ── Availability ──────────────────────────────────────────

def get_available_slots(provider_id: int, date: str) -> dict:
    """
    Get open time slots for a provider on a given date.
    date format: 'YYYY-MM-DD'
    """
    with _connect(CLINIC_DB) as conn:
        rows = conn.execute(
            """
            SELECT appointment_date FROM appointments
            WHERE provider_id = ?
            AND DATE(appointment_date) = DATE(?)
            AND status != 'cancelled'
            """,
            (provider_id, date),
        ).fetchall()

    booked_times = {row["appointment_date"][11:16] for row in rows}

    all_slots = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
    available  = [t for t in all_slots if t not in booked_times]

    return {
        "date":            date,
        "provider_id":     provider_id,
        "available_slots": available,
        "booked_slots":    list(booked_times),
        "message":         f"{len(available)} slot(s) available on {date}.",
    }
