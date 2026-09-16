import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const api = async (path, opt = {}) => {
  const r = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(opt.headers || {})
    },
    ...opt
  });

  const text = await r.text();

  let d;

  try {
    d = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(text || 'Request failed');
  }

  if (!r.ok) {
    throw new Error(d.detail || d.message || 'Request failed');
  }

  return d;
};


function App() {
  // =========================
  // USER / APP STATE
  // =========================

  const [user, setUser] = useState(1);
  const [users, setUsers] = useState([]);

  const [tab, setTab] = useState('dashboard');

  const [dash, setDash] = useState({});
  const [eq, setEq] = useState([]);
  const [book, setBook] = useState([]);
  const [rent, setRent] = useState([]);
  const [rem, setRem] = useState([]);

  const [err, setErr] = useState('');
  const [loading, setLoading] = useState(false);


  // =========================
  // LOAD DATA
  // =========================

  const load = async () => {
    try {
      setLoading(true);
      setErr('');

      // Load real users from backend
      const usersData = await api('/api/users');

      // Load dashboard
      const dashboardData = await api('/api/dashboard');

      // Load equipment
      const equipmentData = await api('/api/equipment');

      // Load current user's bookings
      const bookingsData = await api(
        '/api/bookings?user_id=' + user
      );

      // Load current user's rentals
      const rentalsData = await api(
        '/api/rentals?user_id=' + user
      );

      // Load current user's reminders
      const remindersData = await api(
        '/api/reminders?user_id=' + user
      );


      setUsers(usersData);
      setDash(dashboardData);
      setEq(equipmentData);
      setBook(bookingsData);
      setRent(rentalsData);
      setRem(remindersData);


      // Make sure selected user exists
      if (
        usersData.length > 0 &&
        !usersData.some((u) => u.id === user)
      ) {
        setUser(usersData[0].id);
      }

    } catch (e) {
      console.error('Load error:', e);
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };


  // =========================
  // LOAD WHEN USER CHANGES
  // =========================

  useEffect(() => {
    load();
  }, [user]);


  // =========================
  // CURRENT USER
  // =========================

  const currentUser = users.find(
    (u) => u.id === user
  );


  return (
    <div className="app">

      {/* =========================
          SIDEBAR
      ========================= */}

      <aside>

        <h1>
          AV<span>Rent</span>
        </h1>

        <p className="muted">
          College AV Room
        </p>


        {/* NAVIGATION */}

        {[
          'dashboard',
          'equipment',
          'bookings',
          'rentals',
          'ai'
        ].map((x) => (

          <button
            type="button"
            className={
              tab === x
                ? 'nav active'
                : 'nav'
            }
            onClick={() => setTab(x)}
            key={x}
          >
            {x === 'ai'
              ? '✦ AI Assistant'
              : x[0].toUpperCase() + x.slice(1)}
          </button>

        ))}


        {/* =========================
            REAL USER SELECTOR
        ========================= */}

        <div className="userbox">

          <small>
            Signed in as
          </small>

          <b>
            {currentUser?.name || 'Loading user...'}
          </b>

          <select
            value={user}
            onChange={(e) =>
              setUser(Number(e.target.value))
            }
            disabled={users.length === 0}
          >

            {users.length === 0 ? (
              <option>
                Loading users...
              </option>
            ) : (

              users.map((u) => (

                <option
                  value={u.id}
                  key={u.id}
                >
                  {u.name} · {u.student_login_id}
                </option>

              ))

            )}

          </select>

        </div>

      </aside>


      {/* =========================
          MAIN
      ========================= */}

      <main>

        <header>

          <div>

            <div className="eyebrow">
              EQUIPMENT MANAGEMENT
            </div>

            <h2>
              {tab === 'ai'
                ? 'AI Assistant'
                : tab[0].toUpperCase() + tab.slice(1)}
            </h2>

          </div>


          <button
            type="button"
            className="refresh"
            onClick={load}
            disabled={loading}
          >
            {loading
              ? 'Loading...'
              : '↻ Refresh'}
          </button>

        </header>


        {/* ERROR */}

        {err && (
          <div className="error">
            {err}
          </div>
        )}


        {/* REMINDER */}

        {rem.length > 0 && (
          <div className="notice">
            🔔 {rem[0].message}
          </div>
        )}


        {/* DASHBOARD */}

        {tab === 'dashboard' && (
          <Dashboard
            d={dash}
            eq={eq}
            setTab={setTab}
          />
        )}


        {/* EQUIPMENT */}

        {tab === 'equipment' && (
          <Equipment
            eq={eq}
          />
        )}


        {/* BOOKINGS */}

        {tab === 'bookings' && (
          <Bookings
            data={book}
            eq={eq}
            user={user}
            load={load}
          />
        )}


        {/* RENTALS */}

        {tab === 'rentals' && (
          <Rentals
            data={rent}
            load={load}
          />
        )}


        {/* AI */}

        {tab === 'ai' && (
          <AI
            user={user}
          />
        )}

      </main>

    </div>
  );
}


/* =====================================================
   DASHBOARD
===================================================== */

function Dashboard({
  d,
  eq,
  setTab
}) {

  return (
    <>

      {/* =========================
          DASHBOARD CARDS
      ========================= */}

      <div className="cards">

        {[
          [
            'Equipment Types',
            d.equipment_types,
            '◈'
          ],

          [
            'Total Units',
            d.total_units,
            '▦'
          ],

          [
            'Available',
            d.available_units,
            '✓'
          ],

          [
            'Borrowed',
            d.borrowed_units,
            '↗'
          ],

          [
            'Overdue',
            d.overdue_rentals,
            '!'
          ]

        ].map((c) => (

          <div
            className="card"
            key={c[0]}
          >

            <span>
              {c[2]}
            </span>

            <small>
              {c[0]}
            </small>

            <strong>
              {c[1] ?? 0}
            </strong>

          </div>

        ))}

      </div>


      {/* =========================
          DASHBOARD GRID
      ========================= */}

      <div className="grid">

        {/* EQUIPMENT STATUS */}

        <section className="panel">

          <div className="panelhead">

            <h3>
              Equipment status
            </h3>

            <button
              type="button"
              onClick={() =>
                setTab('bookings')
              }
            >
              New booking →
            </button>

          </div>


          {eq.map((e) => (

            <div
              className="equiprow"
              key={e.id}
            >

              <div className="icon">

                {e.category === 'Camera'
                  ? '📷'
                  : e.category === 'Audio'
                  ? '🎙️'
                  : e.category === 'Display'
                  ? '📽️'
                  : '🦿'}

              </div>


              <div className="grow">

                <b>
                  {e.name}
                </b>

                <small>
                  {e.category} · {e.description}
                </small>

              </div>


              <div>

                <b>
                  {e.available_units}/{e.total_units}
                </b>

                <small>
                  available now
                </small>

              </div>

            </div>

          ))}

        </section>


        {/* RULES */}

        <section className="panel">

          <h3>
            Rules
          </h3>

          <ul className="rules">

            <li>
              Maximum 3 active items per student
            </li>

            <li>
              Late fee: ₹20 per day
            </li>

            <li>
              Refundable deposit: ₹1,000 per unit
            </li>

            <li>
              Overlapping reservations are blocked
            </li>

            <li>
              AI assistant answers from live backend data
            </li>

          </ul>

        </section>

      </div>

    </>
  );
}


/* =====================================================
   EQUIPMENT
===================================================== */

function Equipment({
  eq
}) {

  return (

    <section className="panel">

      <h3>
        Inventory
      </h3>


      <table>

        <thead>

          <tr>

            <th>
              Equipment
            </th>

            <th>
              Category
            </th>

            <th>
              Total
            </th>

            <th>
              Available now
            </th>

          </tr>

        </thead>


        <tbody>

          {eq.map((e) => (

            <tr key={e.id}>

              <td>

                <b>
                  {e.name}
                </b>

                <br />

                <small>
                  {e.description}
                </small>

              </td>


              <td>
                {e.category}
              </td>


              <td>
                {e.total_units}
              </td>


              <td>

                <span className="pill">
                  {e.available_units}
                </span>

              </td>

            </tr>

          ))}

        </tbody>

      </table>

    </section>

  );
}


/* =====================================================
   BOOKINGS
===================================================== */

function Bookings({
  data,
  eq,
  user,
  load
}) {

  const today = new Date();

  const tomorrow = new Date(
    Date.now() + 86400000
  );


  const formatDate = (date) => {
    return date
      .toISOString()
      .slice(0, 10);
  };


  const [s, setS] = useState({

    equipment_id:
      eq[0]?.id || 1,

    quantity: 1,

    start_date:
      formatDate(today),

    end_date:
      formatDate(tomorrow)

  });


  const [submitting, setSubmitting] =
    useState(false);


  // Set first equipment when equipment loads

  useEffect(() => {

    if (
      eq.length > 0 &&
      !s.equipment_id
    ) {

      setS((prev) => ({
        ...prev,
        equipment_id: eq[0].id
      }));

    }

  }, [eq]);


  // =========================
  // CREATE BOOKING
  // =========================

  const submit = async (e) => {

    e.preventDefault();

    console.log(
      'Confirm booking clicked'
    );


    if (!s.equipment_id) {

      alert(
        'Please select equipment.'
      );

      return;
    }


    if (
      !s.quantity ||
      Number(s.quantity) < 1
    ) {

      alert(
        'Quantity must be at least 1.'
      );

      return;
    }


    if (
      !s.start_date ||
      !s.end_date
    ) {

      alert(
        'Please select start and return dates.'
      );

      return;
    }


    if (
      s.end_date < s.start_date
    ) {

      alert(
        'Return date cannot be before start date.'
      );

      return;
    }


    try {

      setSubmitting(true);


      const payload = {

        user_id:
          Number(user),

        equipment_id:
          Number(s.equipment_id),

        quantity:
          Number(s.quantity),

        start_date:
          s.start_date,

        end_date:
          s.end_date

      };


      console.log(
        'Booking payload:',
        payload
      );


      const result = await api(
        '/api/bookings',
        {
          method: 'POST',

          body:
            JSON.stringify(payload)
        }
      );


      console.log(
        'Booking response:',
        result
      );


      alert(
        'Booking created successfully!'
      );


      await load();

    } catch (x) {

      console.error(
        'Booking error:',
        x
      );

      alert(
        x.message
      );

    } finally {

      setSubmitting(false);

    }

  };


  // =========================
  // CANCEL BOOKING
  // =========================

  const cancelBooking = async (
    id
  ) => {

    try {

      await api(
        '/api/bookings/' + id,
        {
          method: 'DELETE'
        }
      );


      alert(
        'Booking cancelled.'
      );


      await load();

    } catch (e) {

      console.error(e);

      alert(
        e.message
      );

    }

  };


  return (

    <div className="grid">

      {/* CREATE BOOKING */}

      <section className="panel">

        <h3>
          Create booking
        </h3>


        <form
          onSubmit={submit}
        >

          {/* EQUIPMENT */}

          <label>

            Equipment

            <select
              value={s.equipment_id}
              onChange={(e) =>
                setS({
                  ...s,
                  equipment_id:
                    e.target.value
                })
              }
            >

              {eq.map((x) => (

                <option
                  value={x.id}
                  key={x.id}
                >
                  {x.name}
                </option>

              ))}

            </select>

          </label>


          {/* QUANTITY */}

          <label>

            Quantity

            <input
              type="number"
              min="1"
              max="8"
              value={s.quantity}
              onChange={(e) =>
                setS({
                  ...s,
                  quantity:
                    e.target.value
                })
              }
            />

          </label>


          {/* DATES */}

          <div className="twocol">

            <label>

              Start

              <input
                type="date"
                value={s.start_date}
                onChange={(e) =>
                  setS({
                    ...s,
                    start_date:
                      e.target.value
                  })
                }
              />

            </label>


            <label>

              Return

              <input
                type="date"
                value={s.end_date}
                onChange={(e) =>
                  setS({
                    ...s,
                    end_date:
                      e.target.value
                  })
                }
              />

            </label>

          </div>


          {/* SUBMIT */}

          <button
            type="submit"
            className="primary"
            disabled={submitting}
          >

            {submitting
              ? 'Creating booking...'
              : 'Confirm booking'}

          </button>

        </form>

      </section>


      {/* MY BOOKINGS */}

      <section className="panel">

        <h3>
          My bookings
        </h3>


        {data.length === 0 ? (

          <p className="muted">
            No bookings yet.
          </p>

        ) : (

          data.map((b) => (

            <div
              className="booking"
              key={b.id}
            >

              <div>

                <b>
                  {b.equipment_name}
                </b>

                <small>

                  {b.start_date}
                  {' → '}
                  {b.end_date}
                  {' · '}
                  {b.quantity}
                  {' unit(s)'}

                </small>

              </div>


              <span className="status">
                {b.status}
              </span>


              {b.status === 'confirmed' && (

                <button
                  type="button"
                  onClick={() =>
                    cancelBooking(b.id)
                  }
                >
                  Cancel
                </button>

              )}

            </div>

          ))

        )}

      </section>

    </div>

  );
}


/* =====================================================
   RENTALS
===================================================== */

function Rentals({
  data,
  load
}) {


  // =========================
  // RETURN RENTAL
  // =========================

  const returnRental = async (
    id
  ) => {

    try {

      const d = await api(
        '/api/rentals/' +
        id +
        '/return',
        {
          method: 'POST',

          body:
            JSON.stringify({
              damage_fee: 0
            })
        }
      );


      alert(
        `Returned. Late fee ₹${d.late_fee}. Refund ₹${d.refund}.`
      );


      await load();

    } catch (e) {

      console.error(e);

      alert(
        e.message
      );

    }

  };


  return (

    <section className="panel">

      <h3>
        My rentals
      </h3>


      {data.length === 0 ? (

        <p className="muted">
          No issued rentals. Admin can issue
          a confirmed booking from the API/demo flow.
        </p>

      ) : (

        data.map((r) => (

          <div
            className="booking"
            key={r.id}
          >

            <div>

              <b>
                {r.equipment_name}
              </b>

              <small>

                Due {r.due_date}
                {' · '}
                {r.quantity}
                {' unit(s)'}

              </small>

            </div>


            {r.returned_at ? (

              <span className="status">
                Returned
              </span>

            ) : (

              <>

                <span className="status">
                  Active
                </span>


                <button
                  type="button"
                  onClick={() =>
                    returnRental(r.id)
                  }
                >
                  Return
                </button>

              </>

            )}

          </div>

        ))

      )}

    </section>

  );
}


/* =====================================================
   AI ASSISTANT
===================================================== */

function AI({
  user
}) {

  const [msg, setMsg] =
    useState('');


  const [out, setOut] =
    useState(
      'Ask: Is a DSLR available? Do I have overdue equipment?'
    );


  const [sending, setSending] =
    useState(false);


  // =========================
  // SEND MESSAGE
  // =========================

  const send = async (e) => {

    e.preventDefault();


    if (!msg.trim()) {
      return;
    }


    try {

      setSending(true);

      setOut(
        'Thinking…'
      );


      const response =
        await api(
          '/api/ai/chat',
          {
            method: 'POST',

            body:
              JSON.stringify({
                message: msg,
                user_id: user
              })
          }
        );


      setOut(
        response.reply
      );

      setMsg('');

    } catch (e) {

      console.error(e);

      setOut(
        e.message
      );

    } finally {

      setSending(false);

    }

  };


  return (

    <section className="ai panel">

      <div className="orb">
        ✦
      </div>


      <h3>
        College AV Assistant
      </h3>


      <p className="muted">

        Ask about availability,
        your bookings, rentals,
        rules, deposits or late fees.

      </p>


      <div className="chat">

        {out}

      </div>


      <form
        onSubmit={send}
      >

        <input
          value={msg}
          onChange={(e) =>
            setMsg(e.target.value)
          }
          placeholder="e.g. Is a projector free this weekend?"
        />


        <button
          type="submit"
          className="primary"
          disabled={sending}
        >

          {sending
            ? 'Sending...'
            : 'Send'}

        </button>

      </form>


      <small className="muted">

        The AI uses live backend facts
        and must not invent availability.

      </small>

    </section>

  );
}


/* =====================================================
   REACT ROOT
===================================================== */

createRoot(
  document.getElementById('root')
).render(
  <App />
);