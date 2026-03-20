import sqlite3
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

_ROOT = Path(__file__).parent.parent

fake = Faker("en_US")

# =========================================================
# CONFIG — CONTROL YOUR DATA HERE
# =========================================================

NUM_ACCOUNTS = 5
USERS_PER_ACCOUNT = (1, 3)        # range (min, max)
INVOICES_PER_ACCOUNT = 4
NUM_TICKETS = 8

NUM_PROVIDERS = 4
NUM_APPOINTMENTS = 20

# =========================================================
# SUPPORT DB (EmerClinic SaaS)
# =========================================================

SUPPORT_DB = str(_ROOT / "support.db")

def init_support_db():
    conn = sqlite3.connect(SUPPORT_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS users;
    DROP TABLE IF EXISTS invoices;
    DROP TABLE IF EXISTS tickets;
    DROP TABLE IF EXISTS interactions;
    DROP TABLE IF EXISTS accounts;

    CREATE TABLE accounts (
        account_id     INTEGER PRIMARY KEY,
        clinic_name    TEXT,
        email          TEXT,
        plan           TEXT,
        billing_cycle  TEXT,
        price          REAL,
        status         TEXT,
        created_at     TEXT
    );

    CREATE TABLE users (
        user_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id  INTEGER,
        name        TEXT,
        email       TEXT,
        role        TEXT,
        last_login  TEXT
    );

    CREATE TABLE invoices (
        invoice_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id   INTEGER,
        amount       REAL,
        status       TEXT,
        issued_date  TEXT,
        due_date     TEXT,
        description  TEXT
    );

    CREATE TABLE tickets (
        ticket_id    TEXT PRIMARY KEY,
        account_id   INTEGER,
        summary      TEXT,
        priority     TEXT,
        category     TEXT,
        status       TEXT,
        created_at   TEXT
    );

    CREATE TABLE interactions (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id    TEXT,
        account_id   INTEGER,
        intent       TEXT,
        success      INTEGER,
        summary      TEXT,
        created_at   TEXT
    );
    """)

    # -----------------------------
    # ACCOUNTS
    # -----------------------------
    account_ids = []
    for i in range(1, NUM_ACCOUNTS + 1):
        plan = random.choice(["Basic", "Premium"])
        billing = random.choice(["monthly", "annual"])
        price = 99.0 if plan == "Basic" else 249.0  
        if billing == "annual":
            price *= 0.8

        cursor.execute("""
            INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i,
            fake.company(),
            fake.email(),
            plan,
            billing,
            round(price, 2),
            random.choice(["active", "active", "suspended", "trial"]),
            datetime.now().isoformat()
        ))

        account_ids.append(i)

    # -----------------------------
    # USERS
    # -----------------------------
    for acc_id in account_ids:
        num_users = random.randint(*USERS_PER_ACCOUNT)
        for _ in range(num_users):
            cursor.execute("""
                INSERT INTO users (account_id, name, email, role, last_login)
                VALUES (?, ?, ?, ?, ?)
            """, (
                acc_id,
                fake.name(),
                fake.email(),
                random.choice(["admin", "staff"]),
                datetime.now().isoformat()
            ))

    # -----------------------------
    # INVOICES
    # -----------------------------
    for acc_id in account_ids:
        for i in range(INVOICES_PER_ACCOUNT):
            status = random.choice(["paid", "paid", "pending", "overdue"])

            issued = datetime.now() - timedelta(days=30 * i)
            due = issued + timedelta(days=15)

            cursor.execute("""
                INSERT INTO invoices (account_id, amount, status, issued_date, due_date, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                acc_id,
                random.choice([99.0, 249.0]),
                status,
                issued.date().isoformat(),
                due.date().isoformat(),
                f"EmerClinic Subscription #{i+1}"
            ))

    # -----------------------------
    # TICKETS
    # -----------------------------
    for _ in range(NUM_TICKETS):
        cursor.execute("""
            INSERT INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            f"TKT-{uuid.uuid4().hex[:6].upper()}",
            random.choice(account_ids),
            fake.sentence(),
            random.choice(["low", "medium", "high"]),
            random.choice(["billing", "technical", "account", "feature_request"]),
            random.choice(["open", "open", "in_progress", "closed"]),
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()


# =========================================================
# CLINIC DEMO DB (LIGHTWEIGHT)
# =========================================================

CLINIC_DB = str(_ROOT / "clinic.db")

def init_clinic_db():
    conn = sqlite3.connect(CLINIC_DB)
    cursor = conn.cursor()

    cursor.executescript("""
    DROP TABLE IF EXISTS providers;
    DROP TABLE IF EXISTS appointments;

    CREATE TABLE providers (
        provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        specialty TEXT,
        available BOOLEAN
    );

    CREATE TABLE appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        patient_name TEXT,
        provider_id INTEGER,
        appointment_date TEXT,
        status TEXT,
        reason TEXT
    );
    """)

    # -----------------------------
    # PROVIDERS
    # -----------------------------
    provider_ids = []
    for _ in range(NUM_PROVIDERS):
        cursor.execute("""
            INSERT INTO providers (name, specialty, available)
            VALUES (?, ?, ?)
        """, (
            f"Dr. {fake.name()}",
            random.choice(["Dentist", "Orthodontist", "General Doctor"]),
            True
        ))
        provider_ids.append(cursor.lastrowid)

    # -----------------------------
    # APPOINTMENTS
    # -----------------------------
    for _ in range(NUM_APPOINTMENTS):
        cursor.execute("""
            INSERT INTO appointments (
                account_id, patient_name, provider_id,
                appointment_date, status, reason
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            random.randint(1, NUM_ACCOUNTS),
            fake.name(),
            random.choice(provider_ids),
            (datetime.now() + timedelta(days=random.randint(-10, 10))).strftime("%Y-%m-%d %H:%M"),
            random.choice(["scheduled", "completed", "cancelled"]),
            random.choice(["Cleaning", "Checkup", "Consultation"])
        ))

    conn.commit()
    conn.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    init_support_db()
    init_clinic_db()
    print("✅ EmerClinic databases created with configurable data!")