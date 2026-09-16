# AVRent — Solution Reasoning

## 1. Introduction

AVRent was designed as a small but extensible equipment-rental system for a college Audio-Visual (AV) room.

The main challenge is not simply storing equipment records. The system needs to manage **limited physical inventory over time**, where multiple students may request the same type of equipment for overlapping periods.

The solution therefore focuses on four core concerns:

1. **Inventory correctness**
2. **Reservation and availability correctness**
3. **Rental lifecycle management**
4. **Clear separation between frontend, business logic, and persistence**

The architecture was intentionally kept simple enough to implement and demonstrate within the assessment time while still leaving a clear path toward a production system.

---

# 2. Understanding the Problem

The original paper-based workflow creates several problems.

A simple equipment register might contain:

```text
Student        Equipment       Date
-----------------------------------------
Student A      Projector       Monday
Student B      Projector       Monday
```

This does not provide enough information to determine:

* How many projectors physically exist
* Which specific unit is currently borrowed
* Whether the equipment is already reserved
* When it should be returned
* Whether the borrower has exceeded their borrowing limit
* Whether a deposit has been collected
* Whether a late fee is applicable

Therefore, the system needs to model both the **equipment type** and the **individual physical units**.

---

# 3. Core Design Principle

The central design principle is:

> The frontend should display information and collect user input, while the backend should enforce business rules and the database should remain the source of truth.

The resulting architecture is:

```text
React
  ↓
FastAPI
  ↓
Supabase / PostgreSQL
```

For AI functionality:

```text
React
  ↓
FastAPI
  ↓
Application Data
  ↓
OpenRouter
```

This prevents business rules from being duplicated in the frontend.

For example, the frontend may prevent a user from entering an invalid quantity, but the backend must still validate the quantity because frontend validation cannot be trusted as an enforcement mechanism.

---

# 4. Why React for the Frontend?

React was selected because the application is primarily an interactive dashboard.

The interface contains several pieces of dynamic state:

* Current user
* Current navigation tab
* Equipment inventory
* Bookings
* Rentals
* Reminders
* AI conversation state
* Loading/error states

React's component model makes it straightforward to divide the interface into logical sections:

```text
App
├── Dashboard
├── Equipment
├── Bookings
├── Rentals
└── AI Assistant
```

This also makes individual sections easier to extend later.

---

# 5. Why FastAPI for the Backend?

FastAPI was selected for the backend because it provides:

* Request validation through Pydantic
* Automatic API documentation
* Simple REST endpoint development
* Good Python ecosystem compatibility
* Easy integration with AI APIs
* A lightweight architecture suitable for the project

More importantly, FastAPI provides a natural location for implementing the application's business rules.

For example:

```text
POST /api/bookings
```

does more than insert a row.

The backend first checks:

```text
Student exists?
       ↓
Equipment exists?
       ↓
Valid dates?
       ↓
Valid quantity?
       ↓
Borrowing limit?
       ↓
Equipment available?
       ↓
Create booking
```

This makes the backend the enforcement layer.

---

# 6. Why Supabase/PostgreSQL?

The data has clear relationships.

For example:

```text
Student
   ↓
Booking
   ↓
Rental
   ↓
Equipment Unit
```

and:

```text
Rental
   ↓
Deposit
```

A relational database is therefore appropriate.

Supabase provides a hosted PostgreSQL database while also simplifying development and deployment.

The relational model allows the application to use IDs and foreign-key relationships rather than duplicating information across records.

---

# 7. Equipment Type vs Physical Unit

One of the most important modeling decisions was separating:

```text
equipment
```

from:

```text
equipment_units
```

For example:

```text
Equipment:
DSLR Camera
Total units: 5
```

is different from the physical assets:

```text
DSLR-001
DSLR-002
DSLR-003
DSLR-004
DSLR-005
```

This distinction is important because the problem states that popular equipment can have multiple units.

Without this separation, it would be difficult to answer questions such as:

* Which physical camera was issued?
* Which camera is damaged?
* Which unit is available?
* Which serial number is currently with a student?

The `equipment` table therefore represents the product/equipment category, while `equipment_units` represents the physical inventory.

---

# 8. Why Bookings and Rentals Are Separate

A booking and a rental represent two different stages of the process.

A booking means:

> A student has reserved equipment for a particular period.

A rental means:

> The equipment has actually been issued to the student.

Therefore:

```text
Booking
   ↓
Issue
   ↓
Rental
   ↓
Return
```

Keeping them separate provides a cleaner lifecycle.

It also prevents a reservation from being treated as physical possession before the equipment has actually been issued.

---

# 9. Availability Reasoning

Availability is a time-dependent concept.

Suppose the AV room owns:

```text
5 DSLR cameras
```

and one is already reserved for a particular date range.

Then the number available for that period is reduced.

The basic idea is:

```text
Available
=
Total Units
− Reserved Units
− Borrowed Units
```

The backend examines reservations that overlap the requested period.

This is preferable to simply storing a static `available = true/false` value because multiple units of the same equipment type can exist.

---

# 10. Overlapping Reservation Logic

The system needs to prevent two students from reserving more equipment than physically exists.

For example:

```text
Total projectors = 3
```

If:

```text
Student A → 2 projectors
Student B → 1 projector
```

are already reserved for the same period, another request for:

```text
1 projector
```

must be rejected.

The backend therefore considers overlapping bookings rather than looking only at today's inventory.

Conceptually:

```text
Requested Quantity
+
Existing Overlapping Quantity
<=
Total Units
```

If the condition is false, the booking is rejected.

This is one of the most important business rules because the original problem specifically mentions multiple clubs arriving for the same equipment.

---

# 11. Date Validation

A booking must have:

```text
start_date
end_date
```

The backend should reject invalid date ranges.

For example:

```text
Start: 2026-09-20
End:   2026-09-18
```

is invalid.

The frontend also performs basic validation for better user experience, but the backend remains responsible for enforcing the rule.

---

# 12. Maximum Active Items

The system limits a student to:

```text
3 active items
```

This addresses the requirement that one person should not be able to book out a large portion of the AV room.

The important point is that this is a **backend rule**, not merely a frontend restriction.

Even if a user manually sends an API request, the backend should still reject a request that violates the limit.

---

# 13. Deposit Design

A deposit is modeled separately from the rental.

This allows the system to distinguish between:

```text
Rental
```

and:

```text
Financial obligation associated with the rental
```

The `deposits` table stores:

* Student
* Rental
* Deposit amount
* Refunded amount
* Deposit status

This is more flexible than simply storing a deposit value directly inside the rental.

---

# 14. Late Fee Reasoning

Late fees are calculated when the equipment is returned.

The general calculation is:

```text
Late Days
=
Return Date − Due Date
```

Then:

```text
Late Fee
=
Late Days × Daily Late Fee
```

For the default application configuration:

```text
Daily late fee = ₹20
```

If the equipment is returned on or before the due date:

```text
Late Days = 0
Late Fee = ₹0
```

This calculation belongs in the backend because it is a business rule and should not depend on the client's implementation.

---

# 15. Refund Calculation

The system treats the deposit as refundable subject to applicable charges.

The conceptual calculation is:

```text
Refund
=
Deposit
−
Late Fee
−
Damage Fee
```

The refund is constrained so that it cannot become negative.

For example:

```text
Deposit     = ₹1,000
Late Fee    = ₹100
Damage Fee  = ₹200

Refund      = ₹700
```

This calculation is performed during the return process.

---

# 16. Rental Return Lifecycle

Returning equipment is not simply changing a status.

A return can affect several pieces of information:

```text
Rental status
Return timestamp
Late fee
Damage fee
Deposit refund
Equipment unit status
```

The intended lifecycle is:

```text
Active Rental
      ↓
Return Request
      ↓
Calculate Late Days
      ↓
Calculate Late Fee
      ↓
Apply Damage Fee
      ↓
Calculate Refund
      ↓
Mark Rental Returned
```

This provides a clear audit trail of the rental lifecycle.

---

# 17. Active Loan Transfer

The additional requirement introduced an important modeling problem:

> How can an active rental move from one borrower to another without creating a new rental?

The solution is to modify the ownership/reference of the existing rental rather than creating a second rental.

Before:

```text
Rental #15
Student: Divyang
Unit: DSLR-002
Due: 2026-09-20
Status: Active
```

After transfer:

```text
Rental #15
Student: Rahul
Unit: DSLR-002
Due: 2026-09-20
Status: Active
```

The following properties remain unchanged:

```text
Rental ID
Equipment Unit
Original Due Date
Rental Status
```

Only the borrower changes.

---

# 18. Why Transfer Does Not Affect Availability

A transfer is not a new reservation.

The equipment is already allocated to an active rental.

Therefore:

```text
Before Transfer
DSLR-002 → Divyang

After Transfer
DSLR-002 → Rahul
```

The physical unit never becomes available in between.

Consequently, the availability count must not increase or decrease as a result of the transfer.

This preserves the meaning of availability:

> Availability represents whether a physical unit is free, not which student is responsible for it.

---

# 19. Transfer Validation

A transfer should only be allowed when:

1. The rental exists.
2. The rental is active.
3. The target student exists.
4. The target student is eligible to receive the item.
5. The original due date remains unchanged.

The backend performs these checks before updating the rental.

The transfer therefore behaves like:

```text
Validate
   ↓
Update borrower
   ↓
Preserve equipment allocation
   ↓
Preserve due date
```

rather than:

```text
Return old rental
   ↓
Create new booking
   ↓
Issue new rental
```

The second approach would incorrectly change the equipment lifecycle and availability.

---

# 20. Reminder Design

The reminder system is based on rental state and due dates.

A reminder can represent events such as:

```text
Upcoming return
Overdue return
```

The reminder is associated with:

```text
student_id
rental_id
```

This makes it possible to determine exactly which student and rental a reminder belongs to.

A production version could connect this system to email, SMS, or push notifications.

---

# 21. AI Assistant Reasoning

The AI assistant is intentionally placed behind the backend.

The frontend does not directly call OpenRouter.

Instead:

```text
React
  ↓
FastAPI
  ↓
Gather relevant application information
  ↓
OpenRouter
```

This provides two advantages.

### Security

The OpenRouter API key remains on the backend.

### Grounding

The backend can provide current application facts to the model.

For example, when the user asks:

```text
Is a DSLR available?
```

the AI should not rely on general knowledge.

It should use current inventory information supplied by the application.

This reduces the chance of the model inventing availability.

---

# 22. Why the AI Is Not the Source of Truth

The AI model is treated as an interface for understanding and communicating information.

It is **not** the authority for:

* Inventory
* Booking status
* Rental status
* Due dates
* Deposits
* Fees

Those values belong to the backend/database.

Therefore:

```text
Database
   ↓
Backend
   ↓
AI Context
   ↓
Natural-language response
```

rather than:

```text
AI
   ↓
Guess application state
```

This distinction is important for a rental system where incorrect availability information can cause real operational problems.

---

# 23. Frontend User Management

The frontend obtains users from:

```text
GET /api/users
```

rather than hardcoding student names.

This means the UI can display database-backed users such as:

```text
STU001 → Divyang Jain
STU002 → Rahul Sharma
STU003 → Priya Singh
```

The selected user ID is then passed to:

```text
/api/bookings
/api/rentals
/api/reminders
/api/ai/chat
```

This keeps the frontend connected to actual backend state.

For a production deployment, this manual user selector would be replaced by authentication.

---

# 24. Error Handling Strategy

The application uses multiple layers of validation.

### Frontend

Provides immediate user feedback:

```text
Quantity must be at least 1
Return date cannot be before start date
```

### Backend

Performs authoritative validation:

```text
Student exists?
Equipment exists?
Availability?
Borrowing limit?
Rental status?
Transfer target?
```

### Database

Provides persistent storage and relational consistency.

The goal is to avoid relying on only one layer for correctness.

---

# 25. Security Reasoning

Sensitive credentials are kept on the backend.

The frontend should never contain:

```text
SUPABASE_SECRET_KEY
OPENROUTER_API_KEY
```

The architecture is therefore:

```text
Browser
   ↓
Public API
   ↓
Server-side credentials
   ↓
Database / AI provider
```

The `.gitignore` also prevents environment files from being committed to the repository.

For production, authentication, authorization, database RLS policies, HTTPS, rate limiting, and secret management would be added.

---

# 26. Why Not Put Business Logic in React?

Putting booking rules entirely in React would be insecure and difficult to maintain.

For example:

```javascript
if (quantity <= 3) {
   createBooking();
}
```

would only protect users interacting through that specific UI.

A malicious or modified client could bypass it.

Instead:

```text
React
   ↓
POST /api/bookings
   ↓
FastAPI validates rules
   ↓
Supabase
```

The backend therefore remains authoritative.

---

# 27. Separation of Responsibilities

The system follows clear responsibilities.

## React

Responsible for:

* UI
* Forms
* Navigation
* Loading states
* Error display
* Sending API requests

## FastAPI

Responsible for:

* Validation
* Business rules
* Availability
* Booking logic
* Rental lifecycle
* Transfer logic
* Return calculations
* AI orchestration

## Supabase

Responsible for:

* Persistent data
* Relational storage
* Equipment records
* Student records
* Booking records
* Rental records
* Deposit records
* Reminder records

## OpenRouter

Responsible for:

* Natural-language AI responses

---

# 28. Trade-offs

Because this was implemented as an assessment project, several deliberate trade-offs were made.

## Simplicity vs Production Complexity

The implementation keeps the number of services small:

```text
React + FastAPI + Supabase
```

instead of introducing unnecessary infrastructure.

A production system could add:

* Redis
* Background workers
* Message queues
* Dedicated authentication
* Notification services
* Observability infrastructure

but these are not necessary to demonstrate the core rental workflow.

---

## Manual User Selection vs Authentication

The current prototype allows selecting a seeded student from the interface.

This keeps the assessment workflow simple.

A production implementation should replace this with authenticated user sessions.

---

## REST API vs Direct Database Access

The application uses a backend REST API instead of allowing the frontend to directly manipulate database records.

This adds a small layer of complexity but provides much stronger control over business rules and credentials.

---

# 29. Scalability Considerations

The current design can be extended without replacing the core data model.

Potential extensions include:

```text
Authentication
     ↓
Role-based authorization
     ↓
Admin workflows
     ↓
Automated notifications
     ↓
Audit logging
     ↓
Analytics
```

The equipment-unit model also allows the inventory to scale beyond the initial demonstration dataset.

---

# 30. Testing Strategy

The most important tests should focus on business rules rather than only UI rendering.

### Inventory

```text
Correct total units
Correct available units
```

### Booking

```text
Valid booking succeeds
Invalid date fails
Unavailable quantity fails
Overlapping reservation fails
```

### Borrowing Limit

```text
Fourth active item is rejected
```

### Return

```text
On-time return → zero late fee
Late return → correct late fee
Damage → correct refund
```

### Transfer

```text
Active rental can transfer
Inactive rental cannot transfer
Target student must exist
Due date remains unchanged
Equipment unit remains unchanged
Availability remains unchanged
```

### AI

```text
AI receives live backend facts
API errors are surfaced
Missing API configuration is handled
```

---

# 31. Important Invariants

Several invariants should always remain true.

### Inventory

```text
Available Units
+
Borrowed/Allocated Units
+
Other Reserved Units
```

must remain consistent with the physical inventory.

### Rental

An active rental should have:

```text
student_id
equipment_unit_id
due_date
status = active
```

### Returned Rental

A returned rental should have:

```text
returned_at != null
status = returned
```

### Transfer

A transfer should not change:

```text
equipment_unit_id
due_date
```

### Booking

A confirmed booking must not exceed available inventory for its period.

---

# 32. Final Architecture

The final design can be summarized as:

```text
                         ┌──────────────────┐
                         │      Student     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  React Frontend  │
                         └────────┬─────────┘
                                  │
                              HTTP/JSON
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  FastAPI Backend │
                         │                  │
                         │ Validation       │
                         │ Availability     │
                         │ Bookings         │
                         │ Rentals          │
                         │ Transfers        │
                         │ Returns          │
                         │ Reminders        │
                         │ AI orchestration │
                         └───────┬──────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   │                           │
                   ▼                           ▼
          ┌─────────────────┐         ┌─────────────────┐
          │ Supabase        │         │ OpenRouter      │
          │ PostgreSQL      │         │ AI API          │
          └─────────────────┘         └─────────────────┘
```

---

# 33. Conclusion

The solution was designed around the actual operational problem rather than treating the assignment as a simple CRUD application.

The most important design choices were:

1. Separate equipment types from physical units.
2. Separate reservations from actual rentals.
3. Calculate availability using real backend data.
4. Enforce borrowing and reservation rules on the backend.
5. Track deposits independently from rentals.
6. Calculate late fees during return processing.
7. Treat loan transfer as a borrower change on the existing active rental.
8. Preserve the original equipment allocation and due date during transfer.
9. Keep AI behind the backend and ground it in application data.
10. Keep secrets outside the frontend and repository.

This structure provides a compact assessment-ready implementation while maintaining a clear path toward a more production-ready college equipment management platform.
