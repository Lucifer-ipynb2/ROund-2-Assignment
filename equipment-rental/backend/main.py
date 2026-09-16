from datetime import date, datetime
from typing import Optional
import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import supabase

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

LATE_FEE_PER_DAY = 20
DEFAULT_DEPOSIT = 1000
MAX_ACTIVE_ITEMS = 3

app = FastAPI(
    title="College AV Equipment Rental API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HELPERS
# ============================================================

def get_student(student_id: int):
    result = (
        supabase
        .table("students")
        .select("*")
        .eq("id", student_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def get_equipment(equipment_id: int):
    result = (
        supabase
        .table("equipment")
        .select("*")
        .eq("id", equipment_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def get_booking(booking_id: int):
    result = (
        supabase
        .table("bookings")
        .select("*")
        .eq("id", booking_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def get_rental(rental_id: int):
    result = (
        supabase
        .table("rentals")
        .select("*")
        .eq("id", rental_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def get_unit(unit_id: int):
    result = (
        supabase
        .table("equipment_units")
        .select("*")
        .eq("id", unit_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def active_item_count(student_id: int):
    """
    Counts active items currently associated
    with a student.

    confirmed = reserved
    issued = currently borrowed

    Cancelled and returned bookings do not count.
    """

    result = (
        supabase
        .table("bookings")
        .select("quantity")
        .eq("student_id", student_id)
        .in_("status", ["confirmed", "issued"])
        .execute()
    )

    return sum(
        int(row.get("quantity", 0))
        for row in result.data
    )


def overlapping_reserved(
    equipment_id: int,
    start: date,
    end: date,
    exclude_id: Optional[int] = None,
):
    """
    Calculate quantity already reserved/issued
    for an equipment item during a date range.

    Overlap condition:

        existing_start <= requested_end
        AND
        existing_end >= requested_start
    """

    query = (
        supabase
        .table("bookings")
        .select(
            "id,quantity,start_date,end_date,status"
        )
        .eq("equipment_id", equipment_id)
        .in_("status", ["confirmed", "issued"])
        .lte(
            "start_date",
            end.isoformat()
        )
        .gte(
            "end_date",
            start.isoformat()
        )
    )

    result = query.execute()

    total = 0

    for booking in result.data:

        if (
            exclude_id is not None
            and booking["id"] == exclude_id
        ):
            continue

        total += int(
            booking.get("quantity", 0)
        )

    return total


def equipment_rows():
    """
    Return equipment inventory summary.

    confirmed booking -> reserved
    issued rental     -> borrowed

    A confirmed booking does not change the
    physical equipment unit status.
    """

    equipment_result = (
        supabase
        .table("equipment")
        .select("*")
        .order("id")
        .execute()
    )

    units_result = (
        supabase
        .table("equipment_units")
        .select("*")
        .execute()
    )

    bookings_result = (
        supabase
        .table("bookings")
        .select(
            "id,equipment_id,quantity,"
            "start_date,end_date,status"
        )
        .in_("status", ["confirmed", "issued"])
        .execute()
    )

    units = units_result.data
    bookings = bookings_result.data

    today = date.today()

    rows = []

    for item in equipment_result.data:

        equipment_id = item["id"]

        item_units = [
            unit
            for unit in units
            if unit.get("equipment_id")
            == equipment_id
        ]

        total_units = int(
            item.get(
                "total_units",
                len(item_units)
            )
        )

        # ----------------------------------------------------
        # PHYSICAL BORROWED UNITS
        # ----------------------------------------------------

        borrowed_units = sum(
            1
            for unit in item_units
            if unit.get("status")
            == "borrowed"
        )

        # ----------------------------------------------------
        # CURRENT RESERVED UNITS
        # ----------------------------------------------------

        reserved_units = 0

        for booking in bookings:

            if (
                booking["equipment_id"]
                != equipment_id
            ):
                continue

            if booking["status"] != "confirmed":
                continue

            booking_start = date.fromisoformat(
                booking["start_date"]
            )

            booking_end = date.fromisoformat(
                booking["end_date"]
            )

            if (
                booking_start
                <= today
                <= booking_end
            ):
                reserved_units += int(
                    booking.get(
                        "quantity",
                        0
                    )
                )

        # ----------------------------------------------------
        # AVAILABLE UNITS
        # ----------------------------------------------------

        available_units = max(
            0,
            total_units
            - borrowed_units
            - reserved_units
        )

        rows.append({
            **item,
            "total_units": total_units,
            "available_units": available_units,
            "reserved_units": reserved_units,
            "borrowed_units": borrowed_units,
        })

    return rows


def booking_with_details(booking):

    student = get_student(
        booking["student_id"]
    )

    equipment = get_equipment(
        booking["equipment_id"]
    )

    return {
        **booking,

        "user_id": booking[
            "student_id"
        ],

        "user_name": (
            student["name"]
            if student
            else None
        ),

        "user_email": (
            student["email"]
            if student
            else None
        ),

        "equipment_name": (
            equipment["name"]
            if equipment
            else None
        ),
    }


def rental_with_details(rental):

    student = get_student(
        rental["student_id"]
    )

    unit = get_unit(
        rental["equipment_unit_id"]
    )

    equipment = None

    if unit:
        equipment = get_equipment(
            unit["equipment_id"]
        )

    return {
        **rental,

        "user_id": rental[
            "student_id"
        ],

        "user_name": (
            student["name"]
            if student
            else None
        ),

        "equipment_name": (
            equipment["name"]
            if equipment
            else None
        ),

        "unit_code": (
            unit["unit_code"]
            if unit
            else None
        ),

        "serial_number": (
            unit["serial_number"]
            if unit
            else None
        ),
    }


# ============================================================
# PYDANTIC MODELS
# ============================================================

class BookingIn(BaseModel):
    user_id: int = 1
    equipment_id: int
    quantity: int
    start_date: date
    end_date: date


class ReturnIn(BaseModel):
    damage_fee: float = 0


class TransferIn(BaseModel):
    new_user_id: int


class ChatIn(BaseModel):
    message: str
    user_id: int = 1


# ============================================================
# HEALTH / ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "message": (
            "College AV Equipment Rental API"
        ),
        "database": "Supabase PostgreSQL",
        "status": "running",
    }


@app.get("/api/health")
def health():

    try:

        (
            supabase
            .table("students")
            .select("id")
            .limit(1)
            .execute()
        )

        return {
            "status": "ok",
            "database": "supabase",
        }

    except Exception as e:

        return {
            "status": "error",
            "database": "supabase",
            "error": str(e),
        }


# ============================================================
# STUDENTS
# ============================================================

@app.get("/api/users")
def users():

    result = (
        supabase
        .table("students")
        .select("*")
        .order("id")
        .execute()
    )

    return [
        {
            **student,
            "user_id": student["id"],
        }
        for student in result.data
    ]


@app.get("/api/users/{user_id}")
def user(user_id: int):

    student = get_student(
        user_id
    )

    if not student:

        raise HTTPException(
            404,
            "Student not found",
        )

    return {
        **student,
        "user_id": student["id"],
    }


# ============================================================
# EQUIPMENT
# ============================================================

@app.get("/api/equipment")
def equipment():

    return equipment_rows()


@app.get(
    "/api/equipment/{equipment_id}/availability"
)
def availability(
    equipment_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
):

    if end_date < start_date:

        raise HTTPException(
            400,
            "End date cannot be before start date",
        )

    item = get_equipment(
        equipment_id
    )

    if not item:

        raise HTTPException(
            404,
            "Equipment not found",
        )

    reserved = overlapping_reserved(
        equipment_id,
        start_date,
        end_date,
    )

    total_units = int(
        item["total_units"]
    )

    available = max(
        0,
        total_units - reserved
    )

    return {
        "equipment_id": equipment_id,
        "equipment_name": item["name"],
        "total_units": total_units,
        "reserved_units": reserved,
        "available_units": available,
        "start_date": start_date,
        "end_date": end_date,
    }


# ============================================================
# BOOKINGS
# ============================================================

@app.get("/api/bookings")
def bookings(
    user_id: Optional[int] = None
):

    query = (
        supabase
        .table("bookings")
        .select("*")
    )

    if user_id is not None:

        query = query.eq(
            "student_id",
            user_id
        )

    result = (
        query
        .order(
            "start_date",
            desc=True
        )
        .execute()
    )

    return [
        booking_with_details(
            booking
        )
        for booking in result.data
    ]


@app.post("/api/bookings")
def create_booking(
    payload: BookingIn
):

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if payload.quantity < 1:

        raise HTTPException(
            400,
            "Quantity must be at least 1",
        )

    if payload.end_date < payload.start_date:

        raise HTTPException(
            400,
            "Invalid date range",
        )

    student = get_student(
        payload.user_id
    )

    if not student:

        raise HTTPException(
            404,
            "Student not found",
        )

    item = get_equipment(
        payload.equipment_id
    )

    if not item:

        raise HTTPException(
            404,
            "Equipment not found",
        )

    # --------------------------------------------------------
    # MAXIMUM ACTIVE ITEMS
    # --------------------------------------------------------

    current_items = active_item_count(
        payload.user_id
    )

    if (
        current_items
        + payload.quantity
        > MAX_ACTIVE_ITEMS
    ):

        raise HTTPException(
            400,
            f"Booking limit is "
            f"{MAX_ACTIVE_ITEMS} active items "
            f"per student",
        )

    # --------------------------------------------------------
    # DATE OVERLAP
    # --------------------------------------------------------

    reserved = overlapping_reserved(
        payload.equipment_id,
        payload.start_date,
        payload.end_date,
    )

    total_units = int(
        item["total_units"]
    )

    available = max(
        0,
        total_units - reserved
    )

    if payload.quantity > available:

        raise HTTPException(
            400,
            f"Only {available} unit(s) "
            f"available for those dates",
        )

    # --------------------------------------------------------
    # DEPOSIT
    # --------------------------------------------------------

    deposit_per_unit = float(
        item.get(
            "deposit_amount"
        )
        or DEFAULT_DEPOSIT
    )

    deposit = (
        deposit_per_unit
        * payload.quantity
    )

    # --------------------------------------------------------
    # CREATE BOOKING
    # --------------------------------------------------------

    result = (
        supabase
        .table("bookings")
        .insert({
            "student_id": payload.user_id,
            "equipment_id": payload.equipment_id,
            "quantity": payload.quantity,
            "start_date": (
                payload.start_date.isoformat()
            ),
            "end_date": (
                payload.end_date.isoformat()
            ),
            "status": "confirmed",
        })
        .execute()
    )

    if not result.data:

        raise HTTPException(
            500,
            "Booking could not be created",
        )

    booking = result.data[0]

    return {
        **booking_with_details(
            booking
        ),
        "deposit": deposit,
        "deposit_per_unit": (
            deposit_per_unit
        ),
    }


@app.delete(
    "/api/bookings/{booking_id}"
)
def cancel_booking(
    booking_id: int
):

    booking = get_booking(
        booking_id
    )

    if not booking:

        raise HTTPException(
            404,
            "Booking not found",
        )

    if booking["status"] != "confirmed":

        raise HTTPException(
            400,
            "Only confirmed bookings "
            "can be cancelled",
        )

    result = (
        supabase
        .table("bookings")
        .update({
            "status": "cancelled"
        })
        .eq(
            "id",
            booking_id
        )
        .execute()
    )

    return {
        "message": "Booking cancelled",

        "booking": (
            result.data[0]
            if result.data
            else None
        ),
    }


# ============================================================
# ISSUE / BORROW
# ============================================================

@app.post(
    "/api/bookings/{booking_id}/issue"
)
def issue_booking(
    booking_id: int
):

    booking = get_booking(
        booking_id
    )

    if not booking:

        raise HTTPException(
            404,
            "Booking not found",
        )

    if booking["status"] != "confirmed":

        raise HTTPException(
            400,
            "Booking is not issuable",
        )

    equipment_id = booking[
        "equipment_id"
    ]

    quantity = int(
        booking["quantity"]
    )

    # --------------------------------------------------------
    # CHECK PHYSICAL UNITS
    # --------------------------------------------------------

    units_result = (
        supabase
        .table("equipment_units")
        .select("*")
        .eq(
            "equipment_id",
            equipment_id
        )
        .eq(
            "status",
            "available"
        )
        .limit(quantity)
        .execute()
    )

    units = units_result.data

    if len(units) < quantity:

        raise HTTPException(
            400,
            f"Only {len(units)} "
            f"physical unit(s) are "
            f"currently available",
        )

    # --------------------------------------------------------
    # CHECK BOOKING DATE
    # --------------------------------------------------------

    booking_start = date.fromisoformat(
        booking["start_date"]
    )

    booking_end = date.fromisoformat(
        booking["end_date"]
    )

    today = date.today()

    if today < booking_start:

        raise HTTPException(
            400,
            "Equipment cannot be issued "
            "before the booking start date",
        )

    if today > booking_end:

        raise HTTPException(
            400,
            "Booking period has already ended",
        )

    equipment = get_equipment(
        equipment_id
    )

    if not equipment:

        raise HTTPException(
            404,
            "Equipment not found",
        )

    deposit_per_unit = float(
        equipment.get(
            "deposit_amount"
        )
        or DEFAULT_DEPOSIT
    )

    due_date = booking[
        "end_date"
    ]

    created_rentals = []

    # --------------------------------------------------------
    # CREATE RENTALS
    # --------------------------------------------------------

    try:

        for unit in units:

            rental_result = (
                supabase
                .table("rentals")
                .insert({
                    "booking_id": booking["id"],
                    "student_id": booking[
                        "student_id"
                    ],
                    "equipment_unit_id": unit[
                        "id"
                    ],
                    "issued_at": (
                        datetime.now()
                        .isoformat()
                    ),
                    "due_date": due_date,
                    "late_fee": 0,
                    "damage_fee": 0,
                    "status": "borrowed",
                })
                .execute()
            )

            if not rental_result.data:

                raise Exception(
                    "Rental creation failed"
                )

            rental = (
                rental_result.data[0]
            )

            # ------------------------------------------------
            # MARK UNIT BORROWED
            # ------------------------------------------------

            (
                supabase
                .table("equipment_units")
                .update({
                    "status": "borrowed"
                })
                .eq(
                    "id",
                    unit["id"]
                )
                .execute()
            )

            # ------------------------------------------------
            # CREATE DEPOSIT
            # ------------------------------------------------

            (
                supabase
                .table("deposits")
                .insert({
                    "student_id": booking[
                        "student_id"
                    ],
                    "rental_id": rental[
                        "id"
                    ],
                    "amount": deposit_per_unit,
                    "refunded_amount": 0,
                    "status": "held",
                })
                .execute()
            )

            created_rentals.append(
                rental_with_details(
                    rental
                )
            )

        # ----------------------------------------------------
        # MARK BOOKING ISSUED
        # ----------------------------------------------------

        (
            supabase
            .table("bookings")
            .update({
                "status": "issued"
            })
            .eq(
                "id",
                booking_id
            )
            .execute()
        )

    except Exception as e:

        raise HTTPException(
            500,
            f"Unable to issue booking: {e}",
        )

    return {
        "message": (
            "Equipment issued successfully"
        ),
        "booking_id": booking_id,
        "rentals": created_rentals,
    }


# ============================================================
# RENTALS
# ============================================================

@app.get("/api/rentals")
def rentals(
    user_id: Optional[int] = None
):

    query = (
        supabase
        .table("rentals")
        .select("*")
    )

    if user_id is not None:

        query = query.eq(
            "student_id",
            user_id
        )

    result = (
        query
        .order(
            "due_date",
            desc=True
        )
        .execute()
    )

    data = []

    today = date.today()

    for rental in result.data:

        due = date.fromisoformat(
            rental["due_date"]
        )

        returned = rental.get(
            "returned_at"
        )

        if returned:

            effective_date = date.fromisoformat(
                returned[:10]
            )

        else:

            effective_date = today

        days_late = max(
            0,
            (
                effective_date - due
            ).days
        )

        unit = get_unit(
            rental[
                "equipment_unit_id"
            ]
        )

        if not unit:
            continue

        equipment = get_equipment(
            unit["equipment_id"]
        )

        if not equipment:
            continue

        late_fee_per_day = float(
            equipment.get(
                "late_fee_per_day"
            )
            or LATE_FEE_PER_DAY
        )

        enriched = rental_with_details(
            rental
        )

        enriched["days_late"] = (
            days_late
        )

        enriched["calculated_late_fee"] = (
            days_late
            * late_fee_per_day
        )

        data.append(enriched)

    return data


# ============================================================
# TRANSFER ACTIVE LOAN
# ============================================================

@app.post(
    "/api/rentals/{rental_id}/transfer"
)
def transfer_rental(
    rental_id: int,
    payload: TransferIn,
):
    """
    Transfer an active loan from one borrower
    to another.

    Rules:

    1. Only active borrowed rentals can transfer.
    2. Original due date remains unchanged.
    3. Same physical equipment unit remains assigned.
    4. Equipment availability does not change.
    5. Deposit ownership moves to new borrower.
    6. New borrower must respect active item limit.
    """

    # --------------------------------------------------------
    # GET RENTAL
    # --------------------------------------------------------

    rental = get_rental(
        rental_id
    )

    if not rental:

        raise HTTPException(
            404,
            "Rental not found",
        )

    # --------------------------------------------------------
    # ACTIVE LOAN CHECK
    # --------------------------------------------------------

    if rental.get("returned_at"):

        raise HTTPException(
            400,
            "Returned equipment cannot be transferred",
        )

    if rental.get("status") != "borrowed":

        raise HTTPException(
            400,
            "Only active borrowed equipment "
            "can be transferred",
        )

    # --------------------------------------------------------
    # BORROWERS
    # --------------------------------------------------------

    old_user_id = rental[
        "student_id"
    ]

    new_user_id = payload.new_user_id

    if old_user_id == new_user_id:

        raise HTTPException(
            400,
            "Equipment is already assigned "
            "to this student",
        )

    # --------------------------------------------------------
    # NEW BORROWER EXISTS?
    # --------------------------------------------------------

    new_student = get_student(
        new_user_id
    )

    if not new_student:

        raise HTTPException(
            404,
            "New borrower not found",
        )

    # --------------------------------------------------------
    # NEW BORROWER ACTIVE ITEM LIMIT
    # --------------------------------------------------------

    new_user_active_items = (
        active_item_count(
            new_user_id
        )
    )

    if (
        new_user_active_items + 1
        > MAX_ACTIVE_ITEMS
    ):

        raise HTTPException(
            400,
            f"Transfer would exceed the "
            f"{MAX_ACTIVE_ITEMS} active item "
            f"limit for the new borrower",
        )

    # --------------------------------------------------------
    # PRESERVE ORIGINAL VALUES
    # --------------------------------------------------------

    original_due_date = rental[
        "due_date"
    ]

    equipment_unit_id = rental[
        "equipment_unit_id"
    ]

    original_status = rental[
        "status"
    ]

    # --------------------------------------------------------
    # UPDATE RENTAL OWNER ONLY
    # --------------------------------------------------------

    rental_result = (
        supabase
        .table("rentals")
        .update({
            "student_id": new_user_id,
        })
        .eq(
            "id",
            rental_id
        )
        .execute()
    )

    if not rental_result.data:

        raise HTTPException(
            500,
            "Rental transfer failed",
        )

    # --------------------------------------------------------
    # TRANSFER DEPOSIT OWNERSHIP
    # --------------------------------------------------------

    (
        supabase
        .table("deposits")
        .update({
            "student_id": new_user_id,
        })
        .eq(
            "rental_id",
            rental_id
        )
        .execute()
    )

    # --------------------------------------------------------
    # EQUIPMENT DETAILS
    # --------------------------------------------------------

    unit = get_unit(
        equipment_unit_id
    )

    equipment = None

    if unit:

        equipment = get_equipment(
            unit["equipment_id"]
        )

    # --------------------------------------------------------
    # RETURN TRANSFER RESULT
    # --------------------------------------------------------

    return {
        "message": (
            "Equipment transferred successfully"
        ),

        "rental_id": rental_id,

        "previous_borrower_id": (
            old_user_id
        ),

        "new_borrower_id": (
            new_user_id
        ),

        "new_borrower_name": (
            new_student["name"]
        ),

        "equipment_name": (
            equipment["name"]
            if equipment
            else None
        ),

        "unit_code": (
            unit["unit_code"]
            if unit
            else None
        ),

        "serial_number": (
            unit["serial_number"]
            if unit
            else None
        ),

        # IMPORTANT:
        # Original due date is preserved.
        "due_date": original_due_date,

        # IMPORTANT:
        # Original rental status is preserved.
        "status": original_status,

        # IMPORTANT:
        # Physical unit never changed.
        "equipment_unit_id": (
            equipment_unit_id
        ),

        # IMPORTANT:
        # Availability remains unchanged.
        "availability_changed": False,
    }


# ============================================================
# RETURN EQUIPMENT
# ============================================================

@app.post(
    "/api/rentals/{rental_id}/return"
)
def return_rental(
    rental_id: int,
    payload: ReturnIn,
):

    rental = get_rental(
        rental_id
    )

    if not rental:

        raise HTTPException(
            404,
            "Rental not found",
        )

    if rental.get("returned_at"):

        raise HTTPException(
            400,
            "Already returned",
        )

    if payload.damage_fee < 0:

        raise HTTPException(
            400,
            "Damage fee cannot be negative",
        )

    today = date.today()

    due = date.fromisoformat(
        rental["due_date"]
    )

    days_late = max(
        0,
        (
            today - due
        ).days
    )

    # --------------------------------------------------------
    # GET UNIT
    # --------------------------------------------------------

    unit = get_unit(
        rental["equipment_unit_id"]
    )

    if not unit:

        raise HTTPException(
            404,
            "Equipment unit not found",
        )

    equipment = get_equipment(
        unit["equipment_id"]
    )

    if not equipment:

        raise HTTPException(
            404,
            "Equipment not found",
        )

    # --------------------------------------------------------
    # CALCULATE FEES
    # --------------------------------------------------------

    late_fee_per_day = float(
        equipment.get(
            "late_fee_per_day"
        )
        or LATE_FEE_PER_DAY
    )

    deposit_amount = float(
        equipment.get(
            "deposit_amount"
        )
        or DEFAULT_DEPOSIT
    )

    late_fee = (
        days_late
        * late_fee_per_day
    )

    refund = max(
        0,
        deposit_amount
        - late_fee
        - payload.damage_fee
    )

    # --------------------------------------------------------
    # UPDATE RENTAL
    # --------------------------------------------------------

    (
        supabase
        .table("rentals")
        .update({
            "returned_at": (
                datetime.now()
                .isoformat()
            ),
            "late_fee": late_fee,
            "damage_fee": (
                payload.damage_fee
            ),
            "status": "returned",
        })
        .eq(
            "id",
            rental_id
        )
        .execute()
    )

    # --------------------------------------------------------
    # MAKE PHYSICAL UNIT AVAILABLE
    # --------------------------------------------------------

    (
        supabase
        .table("equipment_units")
        .update({
            "status": "available"
        })
        .eq(
            "id",
            rental["equipment_unit_id"]
        )
        .execute()
    )

    # --------------------------------------------------------
    # REFUND DEPOSIT
    # --------------------------------------------------------

    (
        supabase
        .table("deposits")
        .update({
            "refunded_amount": refund,
            "status": "refunded",
        })
        .eq(
            "rental_id",
            rental_id
        )
        .execute()
    )

    # --------------------------------------------------------
    # CHECK ALL RENTALS OF BOOKING
    # --------------------------------------------------------

    booking_id = rental[
        "booking_id"
    ]

    remaining = (
        supabase
        .table("rentals")
        .select("id")
        .eq(
            "booking_id",
            booking_id
        )
        .is_(
            "returned_at",
            "null"
        )
        .execute()
    )

    if not remaining.data:

        (
            supabase
            .table("bookings")
            .update({
                "status": "returned"
            })
            .eq(
                "id",
                booking_id
            )
            .execute()
        )

    return {
        "message": (
            "Equipment returned successfully"
        ),

        "rental_id": rental_id,

        "days_late": days_late,

        "late_fee": late_fee,

        "damage_fee": (
            payload.damage_fee
        ),

        "deposit": deposit_amount,

        "refund": refund,
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/api/dashboard")
def dashboard():

    equipment_data = equipment_rows()

    total_units = sum(
        int(item["total_units"])
        for item in equipment_data
    )

    available_units = sum(
        int(item["available_units"])
        for item in equipment_data
    )

    reserved_units = sum(
        int(
            item.get(
                "reserved_units",
                0
            )
        )
        for item in equipment_data
    )

    borrowed_units = sum(
        int(
            item.get(
                "borrowed_units",
                0
            )
        )
        for item in equipment_data
    )

    # --------------------------------------------------------
    # ACTIVE RENTALS
    # --------------------------------------------------------

    rentals_result = (
        supabase
        .table("rentals")
        .select(
            "id,due_date,returned_at,status"
        )
        .execute()
    )

    active_rentals = [
        rental
        for rental in rentals_result.data
        if not rental.get("returned_at")
    ]

    overdue_rentals = [
        rental
        for rental in active_rentals
        if date.fromisoformat(
            rental["due_date"]
        ) < date.today()
    ]

    return {
        "equipment_types": len(
            equipment_data
        ),

        "total_units": total_units,

        "available_units": available_units,

        "reserved_units": reserved_units,

        "borrowed_units": borrowed_units,

        "active_rentals": len(
            active_rentals
        ),

        "overdue_rentals": len(
            overdue_rentals
        ),
    }


# ============================================================
# REMINDERS
# ============================================================

@app.get("/api/reminders")
def reminders(
    user_id: int = 1
):

    result = (
        supabase
        .table("rentals")
        .select("*")
        .eq(
            "student_id",
            user_id
        )
        .is_(
            "returned_at",
            "null"
        )
        .execute()
    )

    today = date.today()

    output = []

    for rental in result.data:

        due = date.fromisoformat(
            rental["due_date"]
        )

        days = (
            due - today
        ).days

        rental_details = rental_with_details(
            rental
        )

        equipment_name = (
            rental_details[
                "equipment_name"
            ]
        )

        # ----------------------------------------------------
        # OVERDUE
        # ----------------------------------------------------

        if days < 0:

            late_days = -days

            message = (
                f"{equipment_name} is "
                f"overdue by "
                f"{late_days} day(s). "
                f"Late fee: ₹"
                f"{late_days * LATE_FEE_PER_DAY}."
            )

        # ----------------------------------------------------
        # DUE SOON
        # ----------------------------------------------------

        elif days <= 2:

            message = (
                f"{equipment_name} is due "
                f"in {days} day(s). "
                f"Please return it on time."
            )

        else:

            continue

        output.append({
            "rental_id": rental["id"],
            "due_date": rental["due_date"],
            "message": message,
            "status": "pending",
        })

    return output


# ============================================================
# AI FACTS
# ============================================================

def facts(user_id: int):

    equipment_data = equipment_rows()

    booking_result = (
        supabase
        .table("bookings")
        .select("*")
        .eq(
            "student_id",
            user_id
        )
        .order(
            "id",
            desc=True
        )
        .limit(10)
        .execute()
    )

    rental_result = (
        supabase
        .table("rentals")
        .select("*")
        .eq(
            "student_id",
            user_id
        )
        .is_(
            "returned_at",
            "null"
        )
        .execute()
    )

    bookings_data = [
        booking_with_details(
            booking
        )
        for booking in booking_result.data
    ]

    rentals_data = [
        rental_with_details(
            rental
        )
        for rental in rental_result.data
    ]

    return {
        "equipment": equipment_data,

        "my_bookings": bookings_data,

        "my_active_rentals": rentals_data,

        "rules": {
            "max_active_items": (
                MAX_ACTIVE_ITEMS
            ),

            "late_fee_per_day": (
                LATE_FEE_PER_DAY
            ),

            "deposit_per_unit": (
                DEFAULT_DEPOSIT
            ),
        },
    }


# ============================================================
# AI ASSISTANT
# ============================================================

@app.post("/api/ai/chat")
def ai_chat(
    payload: ChatIn
):

    api_key = os.getenv(
        "OPENROUTER_API_KEY"
    )

    model = os.getenv(
        "OPENROUTER_MODEL",
        "openrouter/free",
    )

    context = facts(
        payload.user_id
    )

    # --------------------------------------------------------
    # FALLBACK WITHOUT API KEY
    # --------------------------------------------------------

    if not api_key:

        equipment_lines = "\n".join(
            f"• {e['name']}: "
            f"{e['available_units']}/"
            f"{e['total_units']} "
            f"available now"
            for e in context[
                "equipment"
            ]
        )

        return {
            "reply": (
                "OpenRouter is not configured. "
                "Add OPENROUTER_API_KEY to "
                "backend/.env.\n\n"
                "Current system facts:\n"
                + equipment_lines
            )
        }

    # --------------------------------------------------------
    # AI PROMPT
    # --------------------------------------------------------

    prompt = f"""
You are the College AV Room AI assistant.

Use ONLY the supplied system data.

Never invent:
- equipment availability
- booking status
- rental status
- fees
- deposits
- dates
- student information

If the requested action requires changing
the database, tell the user to use the
appropriate application action.

Do not claim that a booking, return,
cancellation, transfer, or issue was completed
unless the backend explicitly confirms it.

System rules:
- Maximum active items: {MAX_ACTIVE_ITEMS}
- Late fee: ₹{LATE_FEE_PER_DAY} per day
- Default deposit: ₹{DEFAULT_DEPOSIT} per unit

SYSTEM DATA:
{context}

USER:
{payload.message}

Answer clearly and concisely.
"""

    # --------------------------------------------------------
    # OPENROUTER REQUEST
    # --------------------------------------------------------

    try:

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",

            headers={
                "Authorization": (
                    f"Bearer {api_key}"
                ),

                "Content-Type": (
                    "application/json"
                ),

                "HTTP-Referer": (
                    "http://localhost:5173"
                ),

                "X-Title": (
                    "College AV Rental"
                ),
            },

            json={
                "model": model,

                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a precise "
                            "college AV equipment "
                            "rental assistant."
                        ),
                    },

                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],

                "temperature": 0.2,
            },

            timeout=45,
        )

        response.raise_for_status()

        data = response.json()

        return {
            "reply": (
                data["choices"][0]
                ["message"]
                ["content"]
            )
        }

    except Exception as e:

        return {
            "reply": (
                "OpenRouter request failed. "
                "The rental system is still "
                "available.\n\n"
                f"Error: {str(e)}"
            )
        }