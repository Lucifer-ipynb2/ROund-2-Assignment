# Reasoning & Design Decisions

## Interpretation
The paper register problem implies five core needs: a source of truth for equipment, date-aware availability, controlled reservations, accountable borrowing/return, and reminders that reduce overdue equipment.

## Assumptions
- A student can have at most **3 active items** at a time.
- Late fee is **₹20 per day**.
- Deposit is **₹1,000 per reserved unit** and is refundable after late/damage deductions.
- Booking dates are inclusive.
- A booking reserves a quantity of units for its date range; overlapping confirmed/issued bookings consume that quantity.
- A rental's due date is the booking end date.
- Reminders are generated in-app when an item is due within two days or is overdue.
- The MVP uses a demo student/admin selector instead of spending assessment time on full authentication.

## Architecture
React provides the user interface. FastAPI is the business-rule layer and SQLite is the source of truth. The AI assistant calls the backend, receives current equipment/booking/rental facts, and sends those facts to OpenRouter for natural-language answers.

The AI is deliberately **not** allowed to decide availability or invent booking state. Availability, limits, fees, and return/refund calculations are deterministic backend rules.

## Important business rules
1. **No double booking:** availability is calculated as total units minus overlapping confirmed/issued quantities.
2. **Booking limit:** the sum of active reserved quantities cannot exceed 3 for a student.
3. **Late fee:** `late_days × ₹20`.
4. **Refund:** `deposit − late_fee − damage_fee`, never below zero.
5. **Return state:** a booking becomes returned only after all rentals created from that booking have been returned.

## Trade-offs for a 2.5-hour assessment
- SQLite instead of PostgreSQL: zero external database setup and enough for an MVP.
- Demo roles instead of full JWT auth: keeps the main domain problem demonstrable.
- In-app reminders instead of email/SMS: avoids third-party notification setup.
- OpenRouter context-based assistant instead of complex function-calling: easier to build and test within the time limit while preserving the key safety property that backend data remains authoritative.

## Future improvements
- Real authentication and role-based access control.
- Physical unit IDs/QR codes so staff can track exact serial numbers.
- Automated scheduled email reminders.
- Payment/deposit ledger with transaction IDs.
- Audit logs.
- Tests for every overlap/limit/fee edge case.
- AI tool calling for controlled actions such as creating/cancelling bookings after explicit confirmation.
