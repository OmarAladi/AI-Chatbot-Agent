"""
Booking tools (SQLite).

This is a direct port of the notebook's DB/tool logic, with only filesystem path
adaptations to work as a real project.
"""
from __future__ import annotations

import sqlite3
from langchain.tools import tool

from cob_demo_agent.utils.env import get_env
from cob_demo_agent.utils.paths import DATA_DIR
from cob_demo_agent.sre.log_manager.logger import get_logger

logger = get_logger("cob_demo_agent.booking_tools")

# Keep the original variable name; allow override via env.
DB_PATH = get_env("COB_DB_PATH", str(DATA_DIR / "appointments.db"))

# ----------------------------
# Core DB functions (callable)
# ----------------------------
def _get_conn():
    """Create a SQLite connection (simple helper)."""
    return sqlite3.connect(DB_PATH)


def core_list_available_slots(service: str, date: str) -> list[str]:
    """Return available times (HH:MM) for a given service and date."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT time FROM appointments
        WHERE service=? AND date=? AND status='free'
        ORDER BY time ASC;
        """,
        (service, date),
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def core_check_slot_availability(service: str, date: str, time: str) -> str:
    """
    Check if the slot exists and is free.
    Returns: "available", "booked", or "not_found"
    """
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT status FROM appointments
        WHERE service=? AND date=? AND time=?;
        """,
        (service, date, time),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return "not_found"
    return "available" if row[0] == "free" else "booked"


def core_book_slot(service: str, date: str, time: str, customer_name: str, phone: str) -> str:
    """Book slot using an atomic update. Returns a human-readable result."""
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE appointments
        SET status='booked',
            customer_name=?,
            phone=?,
            created_at=datetime('now')
        WHERE service=? AND date=? AND time=? AND status='free';
        """,
        (customer_name, phone, service, date, time),
    )

    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 1:
        return "success"
    # distinguish between booked and not_found
    status = core_check_slot_availability(service, date, time)
    if status == "booked":
        return "booked"
    return "not_found"


# ----------------------------
# Tools (LangChain @tool)
# ----------------------------
@tool
def list_available_slots(service: str, date: str) -> str:
    """
    List available times for a given service and date.
    date format: "YYYY-MM-DD"
    Returns a newline-separated list of times.
    """
    times = core_list_available_slots(service, date)
    if not times:
        return "No available times found for that service/date."
    return "Available times:\n" + "\n".join(times)


@tool
def check_slot_availability(service: str, date: str, time: str) -> str:
    """
    Check if a specific slot is available.
    date format: "YYYY-MM-DD"
    time format: "HH:MM"
    Returns: "available", "booked", or "not_found"
    """
    return core_check_slot_availability(service, date, time)


@tool
def book_slot(service: str, date: str, time: str, customer_name: str, phone: str) -> str:
    """
    Book a slot if it is currently free (atomic update).
    date format: "YYYY-MM-DD"
    time format: "HH:MM"
    Returns a confirmation message or an error reason.
    """
    result = core_book_slot(service, date, time, customer_name, phone)

    if result == "success":
        return (
            f"Booking confirmed.\n"
            f"Service: {service}\n"
            f"Date: {date}\n"
            f"Time: {time}\n"
            f"Customer: {customer_name}\n"
            f"Phone: {phone}\n"
            f"Duration: 30 minutes"
        )

    if result == "booked":
        return "Sorry, that slot is already booked. Please choose another available time."
    if result == "not_found":
        return "Sorry, that slot does not exist in the schedule. Please ask for available times."

    return "Sorry, I could not complete the booking. Please try another slot."
