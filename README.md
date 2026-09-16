# AVRent — College AV Equipment Rental System

> A full-stack equipment rental and lending management system for a college Audio-Visual (AV) room, built with **React, FastAPI, Supabase, and OpenRouter**.

AVRent replaces a paper-based AV equipment register with a centralized system for managing equipment inventory, reservations, active rentals, returns, deposits, late fees, reminders, and borrower transfers.

The system is designed around real-world rental constraints such as limited physical units, overlapping reservations, per-student borrowing limits, refundable deposits, overdue charges, and live availability.

---

## Table of Contents

* [Overview](#overview)
* [Problem Statement](#problem-statement)
* [Solution](#solution)
* [Key Features](#key-features)
* [System Architecture](#system-architecture)
* [Technology Stack](#technology-stack)
* [Application Workflow](#application-workflow)
* [Database Design](#database-design)
* [Business Rules](#business-rules)
* [Equipment Availability](#equipment-availability)
* [Booking Workflow](#booking-workflow)
* [Rental and Return Workflow](#rental-and-return-workflow)
* [Loan Transfer](#loan-transfer)
* [Reminder System](#reminder-system)
* [AI Assistant](#ai-assistant)
* [REST API](#rest-api)
* [Project Structure](#project-structure)
* [Environment Configuration](#environment-configuration)
* [Local Development](#local-development)
* [Running the Backend](#running-the-backend)
* [Running the Frontend](#running-the-frontend)
* [Testing the API](#testing-the-api)
* [Security Considerations](#security-considerations)
* [Design Decisions](#design-decisions)
* [Error Handling](#error-handling)
* [Future Improvements](#future-improvements)
* [Assessment Requirements](#assessment-requirements)
* [Author](#author)

---

# Overview

AVRent is a college AV-room management application for lending equipment such as:

* DSLR cameras
* Projectors
* Wireless microphones
* Tripods

The application manages the complete lifecycle of an equipment request:

```text
Student
   │
   ▼
Check Equipment
   │
   ▼
Create Reservation
   │
   ▼
Confirmed Booking
   │
   ▼
Equipment Issued
   │
   ▼
Active Rental
   │
   ├──────────────► Transfer to another borrower
   │
   ▼
Return Equipment
   │
   ▼
Late Fee Calculation
   │
   ▼
Deposit Refund
```

The backend is responsible for enforcing business rules and maintaining data consistency, while the React frontend provides the user interface.

---

# Problem Statement

The college AV room currently relies on a paper register to manage equipment.

This creates several operational problems:

1. Staff cannot reliably determine whether an item is available.
2. Multiple clubs may request the same limited equipment.
3. Popular equipment has multiple physical units that must be tracked individually.
4. Students may keep equipment beyond the expected return date.
5. There is no consistent mechanism for calculating late fees.
6. Refundable deposits need to be tracked.
7. A student should not be able to reserve an excessive amount of equipment.
8. Borrowers need reminders about upcoming or overdue returns.
9. An active loan may need to be transferred from one student to another without changing the equipment allocation or original due date.
10. Students need a convenient way to ask availability and rental-related questions.

AVRent addresses these problems through a centralized digital workflow.

---

# Solution

AVRent provides:

* Centralized equipment inventory
* Individual physical-unit tracking
* Reservation management
* Date-overlap validation
* Per-student borrowing limits
* Equipment issuance
* Active rental tracking
* Return processing
* Late-fee calculation
* Refundable deposit tracking
* Overdue reminders
* Active-loan transfer
* AI-powered natural-language assistance
* Live data from the backend and database

The application follows a simple principle:

> **The frontend displays and requests data; the backend owns business rules; the database stores the source of truth.**

---

# Key Features

## 1. Equipment Inventory

The system maintains equipment types and their physical units.

Example:

| Equipment           | Total Units |
| ------------------- | ----------: |
| DSLR Camera         |           5 |
| Projector           |           3 |
| Wireless Microphone |           6 |
| Tripod              |           8 |

Each physical unit can have its own:

* Unit code
* Serial number
* Condition
* Status

This allows the system to distinguish between multiple copies of the same equipment.

---

## 2. Live Availability

The dashboard displays current inventory information such as:

* Total equipment types
* Total physical units
* Available units
* Borrowed units
* Overdue rentals

Availability is calculated from backend data rather than hardcoded frontend values.

---

## 3. Reservations

Students can create bookings by selecting:

* Equipment
* Quantity
* Start date
* End date

The backend validates availability before creating a booking.

---

## 4. Overlapping Reservation Protection

The system prevents conflicting reservations when the requested quantity exceeds the number of units available for the requested date range.

This protects the AV room from double-booking the same physical resources.

---

## 5. Borrowing Limit

A student cannot have more than:

```text
3 active items
```

at the same time.

This prevents a single borrower from reserving or holding an unreasonable amount of AV equipment.

---

## 6. Deposits

Equipment can require a refundable deposit.

Example:

```text
DSLR Camera → ₹1,000
Projector → ₹1,500
Wireless Microphone → ₹500
Tripod → ₹300
```

The deposit is tracked separately from the rental record.

---

## 7. Late Fees

The system calculates late fees based on the number of days after the due date.

Example:

```text
Late fee = Late days × Daily late-fee rate
```

The default application rule is:

```text
₹20 per late day
```

The backend performs the calculation during return processing.

---

## 8. Return Processing

When equipment is returned, the system records:

* Return timestamp
* Late fee
* Damage fee
* Refund amount
* Rental status

The refundable amount can therefore be represented as:

```text
Refund = Deposit − Late Fee − Damage Fee
```

with the refund amount prevented from becoming negative.

---

## 9. Loan Transfer

An active rental can be transferred from one student to another.

The transfer operation:

* Changes the borrower
* Preserves the original due date
* Preserves the equipment unit
* Preserves the active rental
* Does not create a new equipment allocation
* Does not change equipment availability
* Updates the associated deposit ownership

This models a real transfer of responsibility rather than treating the transfer as a new rental.

---

## 10. Reminders

The backend can generate reminders for active rentals.

Reminder scenarios can include:

* Upcoming due date
* Overdue equipment
* Return-related notifications

---

## 11. AI Assistant

AVRent includes an AI assistant that can answer natural-language questions about the AV room.

Example questions:

```text
Is a DSLR available?

Do I have any overdue equipment?

What is the late fee?

How much deposit is required?

Is a projector free this weekend?

What are the booking rules?
```

The frontend sends the question to the FastAPI backend.

The backend gathers relevant application data and sends the request to the configured OpenRouter model.

The AI is instructed to rely on backend facts rather than inventing availability.

---

# System Architecture

```text
┌─────────────────────────────┐
│        React Frontend       │
│          Vite + CSS         │
└──────────────┬──────────────┘
               │ HTTP / JSON
               ▼
┌─────────────────────────────┐
│       FastAPI Backend       │
│                             │
│  • Validation               │
│  • Business Rules           │
│  • Availability             │
│  • Bookings                 │
│  • Rentals                  │
│  • Transfers                │
│  • Returns                  │
│  • Reminders                │
│  • AI orchestration         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│           Supabase          │
│      PostgreSQL Database    │
│                             │
│  • Students                 │
│  • Equipment                │
│  • Physical Units           │
│  • Bookings                 │
│  • Rentals                  │
│  • Deposits                 │
│  • Reminders                │
└─────────────────────────────┘

               │
               │ AI request
               ▼
┌─────────────────────────────┐
│         OpenRouter          │
│        AI Model API         │
└─────────────────────────────┘
```

### Architectural Principle

The React application never directly accesses the Supabase database using privileged credentials.

Instead:

```text
React → FastAPI → Supabase
```

This keeps database credentials and business rules on the server side.

---

# Technology Stack

## Frontend

* React
* Vite
* JavaScript
* CSS
* Fetch API

## Backend

* Python
* FastAPI
* Pydantic
* Uvicorn
* python-dotenv
* Supabase Python client

## Database

* Supabase
* PostgreSQL

## AI

* OpenRouter API
* Configurable OpenRouter model
* Default model configuration: `openrouter/free`

## Development

* GitHub Codespaces
* Git
* GitHub

---

# Application Workflow

## Student Booking Flow

```text
1. Student selects equipment
        ↓
2. Student selects quantity
        ↓
3. Student selects start and return dates
        ↓
4. Frontend sends booking request
        ↓
5. FastAPI validates student
        ↓
6. FastAPI checks borrowing limit
        ↓
7. FastAPI checks overlapping reservations
        ↓
8. Booking is created
        ↓
9. Equipment availability is updated
```

---

# Database Design

The application uses separate tables for logical equipment types and physical equipment units.

## Students

Stores borrower information.

```text
students
├── id
├── student_login_id
├── name
├── email
├── role
└── created_at
```

Example:

```text
STU001 | Divyang Jain | divyang@college.edu | student
```

---

## Equipment

Stores equipment types.

```text
equipment
├── id
├── name
├── category
├── description
├── total_units
├── deposit_amount
├── late_fee_per_day
├── status
└── created_at
```

---

## Equipment Units

Represents individual physical equipment.

```text
equipment_units
├── id
├── equipment_id
├── unit_code
├── serial_number
├── condition
├── status
└── created_at
```

For example:

```text
DSLR Camera
├── DSLR-001
├── DSLR-002
├── DSLR-003
├── DSLR-004
└── DSLR-005
```

---

## Bookings

Stores reservations.

```text
bookings
├── id
├── student_id
├── equipment_id
├── quantity
├── start_date
├── end_date
├── status
└── created_at
```

A booking represents a reservation request for a quantity of an equipment type.

---

## Rentals

Stores actual issued equipment.

```text
rentals
├── id
├── booking_id
├── student_id
├── equipment_unit_id
├── issued_at
├── due_date
├── returned_at
├── late_fee
├── damage_fee
└── status
```

This is where the application tracks the actual physical item being borrowed.

---

## Deposits

Tracks refundable deposits.

```text
deposits
├── id
├── student_id
├── rental_id
├── amount
├── refunded_amount
├── status
└── created_at
```

---

## Reminders

Stores return-related reminders.

```text
reminders
├── id
├── student_id
├── rental_id
├── message
├── reminder_type
├── status
└── sent_at
```

---

# Business Rules

The core business rules are enforced in the backend.

## Maximum Active Items

```text
Maximum active items per student = 3
```

---

## Late Fee

Default:

```text
₹20 per day
```

---

## Deposit

The deposit amount depends on the equipment type.

---

## Overlapping Reservations

A reservation cannot exceed the available quantity during the requested period.

Conceptually:

```text
available units
=
total units
− overlapping reserved units
− active borrowed units
```

The backend uses reservation dates to determine conflicts.

---

## Return Calculation

The return calculation follows:

```text
late_fee = late_days × late_fee_per_day

refund =
    max(
        0,
        deposit − late_fee − damage_fee
    )
```

---

## Loan Transfer Rule

For an active rental transfer:

```text
Old borrower
      ↓
New borrower

Equipment unit ─────────── unchanged
Due date ───────────────── unchanged
Rental status ──────────── unchanged
Availability ───────────── unchanged
Deposit ────────────────── borrower updated
```

The transfer does not release or re-book the physical unit.

---

# Equipment Availability

Availability is intentionally calculated from backend state.

For example, if there are:

```text
5 DSLR cameras
```

and one unit is reserved for the requested period:

```text
5 total
− 1 reserved
= 4 available
```

This allows the UI to display:

```text
4 / 5 available now
```

The frontend does not maintain its own independent inventory count.

---

# Booking Workflow

A booking request contains:

```json
{
  "user_id": 1,
  "equipment_id": 1,
  "quantity": 1,
  "start_date": "2026-09-16",
  "end_date": "2026-09-17"
}
```

The backend validates:

1. Student exists
2. Equipment exists
3. Quantity is valid
4. Date range is valid
5. Student borrowing limit is respected
6. Requested quantity is available
7. Reservation does not conflict with existing bookings

If validation succeeds, a confirmed booking is created.

---

# Rental and Return Workflow

A confirmed booking can be issued as a rental.

When issued:

```text
Booking
   ↓
Equipment unit assigned
   ↓
Rental created
   ↓
Due date stored
   ↓
Deposit associated
```

When returned:

```text
Active Rental
   ↓
Return request
   ↓
Late days calculated
   ↓
Late fee calculated
   ↓
Damage fee applied
   ↓
Refund calculated
   ↓
Rental marked returned
```

---

# Loan Transfer

The system supports transferring an active rental to another borrower.

Example:

```text
Before:

Divyang Jain
   ↓
DSLR-001
Due: 2026-09-20


Transfer


After:

Rahul Sharma
   ↓
DSLR-001
Due: 2026-09-20
```

Notice that:

```text
DSLR-001 → unchanged
Due date → unchanged
Rental → same rental
Availability → unchanged
```

Only the responsible borrower changes.

The backend also validates the target borrower before performing the transfer.

---

# Reminder System

The reminder endpoint provides rental-related notifications.

Typical reminders can include:

### Upcoming Return

```text
Your DSLR Camera is due soon.
```

### Overdue

```text
Your Projector is overdue.
Please return it as soon as possible.
```

The reminder system is backed by the rental and due-date information stored in the database.

---

# AI Assistant

The AI assistant is exposed through:

```text
POST /api/ai/chat
```

Request:

```json
{
  "message": "Is a DSLR available?",
  "user_id": 1
}
```

The backend can use:

* Current equipment
* Current availability
* Student bookings
* Active rentals
* Rental rules
* Late-fee information

to construct the context supplied to the AI model.

The intended architecture is:

```text
User question
      ↓
React
      ↓
FastAPI
      ↓
Live application data
      ↓
OpenRouter
      ↓
AI response
      ↓
React
```

The frontend never exposes the OpenRouter API key.

---

# REST API

## Health

### `GET /`

Returns basic API information.

### `GET /api/health`

Checks backend health.

---

## Users

### `GET /api/users`

Returns all students.

### `GET /api/users/{user_id}`

Returns a specific student.

---

## Equipment

### `GET /api/equipment`

Returns equipment inventory and current availability.

### `GET /api/equipment/{equipment_id}/availability`

Returns availability information for a specific equipment type.

---

## Bookings

### `GET /api/bookings`

Returns bookings.

Optional:

```text
?user_id=<id>
```

### `POST /api/bookings`

Creates a new booking.

Example:

```json
{
  "user_id": 1,
  "equipment_id": 1,
  "quantity": 1,
  "start_date": "2026-09-16",
  "end_date": "2026-09-17"
}
```

### `DELETE /api/bookings/{booking_id}`

Cancels a booking.

---

## Issue Equipment

### `POST /api/bookings/{booking_id}/issue`

Issues equipment for a confirmed booking and creates the associated rental records.

---

## Rentals

### `GET /api/rentals`

Returns rentals.

Optional:

```text
?user_id=<id>
```

---

## Transfer Rental

### `POST /api/rentals/{rental_id}/transfer`

Transfers an active rental to another student.

Example request:

```json
{
  "new_user_id": 2
}
```

The original due date and equipment unit remain unchanged.

---

## Return Rental

### `POST /api/rentals/{rental_id}/return`

Returns a rental.

Example:

```json
{
  "damage_fee": 0
}
```

The response contains the calculated late fee and refund.

---

## Dashboard

### `GET /api/dashboard`

Returns dashboard statistics including:

* Equipment types
* Total units
* Available units
* Borrowed units
* Overdue rentals

---

## Reminders

### `GET /api/reminders`

Returns reminders.

Optional:

```text
?user_id=<id>
```

---

## AI

### `POST /api/ai/chat`

Sends a natural-language question to the AI assistant.

---

# Project Structure

```text
equipment-rental/
│
├── .devcontainer/
│   └── devcontainer.json
│
├── backend/
│   ├── database.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── style.css
│   │
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── README.md
├── REASONING.md
├── AI_LOGS.md
└── .gitignore
```

---

# Environment Configuration

Create:

```text
backend/.env
```

with:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_secret_key

OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=openrouter/free
```

### Security

Do **not** commit `.env` to GitHub.

The project `.gitignore` excludes:

```text
backend/.env
```

API keys should only exist in the backend environment.

---

# Local Development

## Requirements

Recommended:

* Python 3.10+
* Node.js 18+
* npm
* Git
* Supabase project
* OpenRouter API key for AI functionality

---

# Backend Setup

Move into the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Linux/Fedora:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```text
backend/.env
```

Then start FastAPI:

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

---

# Frontend Setup

Open another terminal.

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start Vite:

```bash
npm run dev -- --host 0.0.0.0
```

The frontend will be available on the Vite development port shown in the terminal.

---

# Running with GitHub Codespaces

The application can be developed directly inside GitHub Codespaces.

Typical workflow:

```text
GitHub Repository
       ↓
GitHub Codespace
       ↓
Backend Terminal
       │
       └── FastAPI :8000
       
Frontend Terminal
       │
       └── Vite development server
```

Codespaces provides port forwarding so the development servers can be opened through the Codespaces forwarded-port interface.

---

# Testing the API

Check backend health:

```bash
curl http://localhost:8000/api/health
```

Get users:

```bash
curl http://localhost:8000/api/users
```

Get equipment:

```bash
curl http://localhost:8000/api/equipment
```

Get dashboard:

```bash
curl http://localhost:8000/api/dashboard
```

Get bookings for a student:

```bash
curl "http://localhost:8000/api/bookings?user_id=1"
```

Get rentals:

```bash
curl "http://localhost:8000/api/rentals?user_id=1"
```

These endpoints can also be tested interactively through FastAPI's Swagger UI:

```text
/docs
```

---

# Security Considerations

## Secrets

Supabase and OpenRouter credentials are backend-only.

They should never be:

* Hardcoded in React
* Committed to Git
* Included in frontend JavaScript
* Exposed in API responses

---

## Database Access

The application follows:

```text
Frontend
   ↓
FastAPI
   ↓
Supabase
```

rather than:

```text
Frontend
   ↓
Supabase using secret key
```

This keeps privileged database credentials outside the browser.

---

## Input Validation

FastAPI/Pydantic validates incoming request structures.

Additional business validation checks:

* Student existence
* Equipment existence
* Quantity
* Dates
* Availability
* Borrowing limits
* Rental status
* Transfer target
* Return state

---

# Design Decisions

## Why FastAPI?

FastAPI provides:

* Strong request validation
* Automatic OpenAPI documentation
* Simple REST API development
* Good Python integration
* Straightforward async-compatible architecture

It also fits naturally with the Python-based AI/data-processing ecosystem.

---

## Why Supabase?

Supabase provides a managed PostgreSQL database with:

* Relational data modeling
* SQL
* Hosted database infrastructure
* API access
* Easy development workflow

The relational structure is appropriate because bookings, rentals, students, deposits, and physical equipment units have clear relationships.

---

## Why Separate Equipment and Equipment Units?

An equipment type represents a category of inventory:

```text
DSLR Camera
```

while a unit represents a physical item:

```text
DSLR-001
DSLR-002
DSLR-003
```

This separation allows the system to support multiple copies of popular equipment while still tracking individual physical assets.

---

## Why Keep Booking and Rental Separate?

A booking represents an intended reservation.

A rental represents equipment that has actually been issued.

Therefore:

```text
Booking ≠ Rental
```

This distinction makes the lifecycle easier to manage:

```text
Booking
   ↓
Issue
   ↓
Rental
   ↓
Return
```

---

## Why Transfer the Existing Rental?

The new transfer requirement is modeled as a change of responsibility rather than a new booking.

Therefore the transfer changes:

```text
rental.student_id
```

while preserving:

```text
rental.equipment_unit_id
rental.due_date
rental.status
```

This ensures the physical equipment remains allocated to the same active rental.

---

# Error Handling

The backend returns meaningful HTTP errors for invalid operations.

Examples include:

```text
Student not found
Equipment not found
Booking not found
Rental not found
Invalid date range
Requested quantity unavailable
Maximum active item limit exceeded
Rental is already returned
Rental is not active
Invalid transfer target
```

The React frontend displays API errors to the user instead of silently failing.

---

# Current Seed Data

The development database contains sample student accounts such as:

| Login ID | Name         | Role    |
| -------- | ------------ | ------- |
| STU001   | Divyang Jain | student |
| STU002   | Rahul Sharma | student |
| STU003   | Priya Singh  | student |

Example equipment:

| Equipment           | Category           | Units |
| ------------------- | ------------------ | ----: |
| DSLR Camera         | Camera             |     5 |
| Projector           | Display            |     3 |
| Wireless Microphone | Audio              |     6 |
| Tripod              | Camera Accessories |     8 |

These values are development/demo data and can be replaced with real college inventory.

---

# Future Improvements

Potential production improvements include:

## Authentication

Integrate college SSO or Supabase Auth so students do not select their identity manually.

```text
College Login
     ↓
Authenticated Session
     ↓
Student Account
```

---

## Admin Dashboard

Add dedicated admin functionality for:

* Issuing equipment
* Managing inventory
* Adding/removing physical units
* Approving bookings
* Recording damage
* Managing deposits
* Viewing all borrowers
* Managing reminders

---

## Automated Notifications

Integrate email or messaging services for:

* Booking confirmation
* Upcoming due date
* Overdue notifications
* Transfer confirmation
* Deposit refund notification

---

## Scheduled Reminder Jobs

A background scheduler could periodically detect:

```text
Due tomorrow
Due today
Overdue
```

and automatically create/send notifications.

---

## Better Availability Engine

A production-grade availability engine could use explicit unit allocation and database transactions to guarantee consistency under simultaneous booking requests.

---

## Audit Logging

Track important actions:

```text
Booking created
Booking cancelled
Equipment issued
Rental transferred
Equipment returned
Damage recorded
Deposit refunded
```

This would improve accountability and troubleshooting.

---

## Automated Tests

Add:

* Unit tests
* API tests
* Database integration tests
* Frontend tests
* End-to-end tests

Critical scenarios should include:

```text
Overbooking
Maximum borrowing limit
Late return
Early return
Transfer
Return after transfer
Unavailable equipment
Invalid dates
```

---

# Assessment Requirements

This project was designed around the supplied AV-room equipment-rental requirements.

### Requirement: Track Equipment

Implemented through:

```text
equipment
equipment_units
```

### Requirement: Multiple Units

Implemented using individual `equipment_units`.

### Requirement: Check Availability

Implemented through the equipment and availability endpoints.

### Requirement: Prevent Double Booking

Implemented through date-overlap and quantity validation.

### Requirement: Sensible Return Date

Bookings require a start and return date.

### Requirement: Late Fee

Late fees are calculated during rental return processing.

### Requirement: Refundable Deposit

Deposits are stored separately and refunds are calculated during return.

### Requirement: Maximum Borrowing Limit

The backend enforces a maximum of three active items per student.

### Requirement: Reminders

Reminder records and reminder API are included.

### Requirement: Active Loan Transfer

Active rentals can be transferred between borrowers while preserving:

* Original due date
* Physical equipment unit
* Active rental
* Equipment availability

### Requirement: AI Assistance

The system includes an AI assistant backed by OpenRouter and grounded in live application information.

---

# Engineering Summary

AVRent intentionally separates responsibilities:

```text
┌───────────────────────┐
│       Frontend        │
│       React/Vite      │
│                       │
│ Presentation + UX     │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│       Backend         │
│        FastAPI        │
│                       │
│ Business Logic        │
│ Validation            │
│ Rental Lifecycle      │
│ Availability          │
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│       Database        │
│       Supabase        │
│      PostgreSQL       │
│                       │
│ Persistent State      │
└───────────────────────┘
```

This separation makes the application easier to maintain, test, secure, and extend.

---

# Author

**Divyang Jain**

B.Tech Computer Science & Engineering

GitHub: `Lucifer-ipynb2`

---

## Project Status

**Status: Functional assessment prototype**

The core equipment rental workflow is implemented, including inventory, bookings, availability, rentals, returns, deposits, late fees, reminders, AI assistance, and active-loan transfer.
