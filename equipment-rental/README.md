# AVRent — College AV Equipment Rental System

A practical MVP for the college AV room: inventory, date-based availability, bookings, borrowing/return, late fees, refundable deposits, booking limits, reminders, and an OpenRouter-powered AI assistant.

## Tech stack
- React + Vite
- FastAPI + SQLite
- OpenRouter API (optional; the app still runs without it)

## Run in GitHub Codespaces
Open the repository in a Codespace, then use two terminals.

### Terminal 1 — backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env if you want the live AI assistant.
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2 — frontend
```bash
cd frontend
npm install
npm run dev
```
Open port **5173** in the Codespaces Ports tab.

## Demo flow
1. Dashboard → inspect inventory.
2. Bookings → create a booking for a date range.
3. Confirm that overlapping quantity is rejected.
4. Issue a booking using `POST /api/bookings/{id}/issue` if demonstrating the admin flow.
5. Rentals → return an issued rental and see late-fee/refund calculation.
6. AI Assistant → ask about live equipment and your bookings.

## API highlights
- `GET /api/equipment`
- `GET /api/equipment/{id}/availability?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- `GET/POST /api/bookings`
- `DELETE /api/bookings/{id}`
- `POST /api/bookings/{id}/issue`
- `GET /api/rentals`
- `POST /api/rentals/{id}/return`
- `GET /api/dashboard`
- `GET /api/reminders`
- `POST /api/ai/chat`

## OpenRouter
Create `backend/.env` from `.env.example` and set `OPENROUTER_API_KEY`. Do **not** commit the real key. `.gitignore` excludes `.env` and the SQLite database.

## Debugging
- Backend health: `http://localhost:8000/api/health`
- FastAPI docs: `http://localhost:8000/docs`
- If port 5173 is already in use, run `npm run dev -- --port 5174` and open the new port.
- If the database needs a clean reset, stop the backend and delete `backend/equipment_rental.db`; it will be recreated with seed data.
