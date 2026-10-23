# FoodShare Tracker

**A human-centred community food bank management system**

**Authors:** Ko Jing Rui 
**Course:** FIT1056 Software Engineering — Group 16  
**Tutor:** Dr Sanoop Mallissery  
**Version:** 2.1 · 23 October 2026

![FoodShare Tracker](assets/hero_banner.png)

FoodShare Tracker is a single-site Streamlit web application for community food banks. It brings donations, inventory, client profiles, food hampers, volunteer jobs, issue handling and CSV reporting into one browser-based system backed by a local JSON data file. It is designed for a small food bank that needs a clear, low-infrastructure workflow rather than a full enterprise platform.

---

## Table of contents

- [Overview](#overview)
- [Key features](#key-features)
- [Roles and permissions](#roles-and-permissions)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Getting started](#getting-started)
- [First run](#first-run)
- [Typical workflows](#typical-workflows)
- [Status model](#status-model)
- [Data, backups and logs](#data-backups-and-logs)
- [Reports](#reports)
- [Testing](#testing)
- [Security and privacy](#security-and-privacy)
- [Known limitations and out-of-scope items](#known-limitations-and-out-of-scope-items)
- [Troubleshooting](#troubleshooting)
- [Authors and acknowledgements](#authors-and-acknowledgements)

---

## Overview

Community food banks often manage donations, stock and client requests with paper forms and spreadsheets. Staff re-enter the same information, struggle to know what is in the warehouse, and cannot quickly answer questions such as:

- How much rice is left?
- Which hampers are waiting for a volunteer?
- Which donations were collected this week?
- Which client has an allergy that must be checked before packing?

FoodShare Tracker addresses these problems with:

- role-specific dashboards for five user types;
- a donation-to-stock workflow;
- a hamper workflow with packing, delivery and client confirmation;
- volunteer job claiming and route links;
- client messages and issue flagging;
- CSV reports for inventory, transactions, hampers, donations and volunteers;
- JSON persistence, backups and status/stock histories.

The application is intentionally small: one Streamlit process, one JSON data file and no separate database server. This keeps deployment simple for a single food bank site, but it also means there is no multi-site synchronisation or concurrent-writer support.

---

## Key features

### 1. Authentication and role management

- Register or sign in with **email or user ID** and password.
- Five roles: **Admin**, **Staff**, **Volunteer**, **Donor**, **Client**.
- Admin/Staff can create accounts; Admin can update or delete accounts.
- Passwords are hashed with bcrypt; a SHA-256 fallback is used when bcrypt is unavailable.
- Admin deletion requires the Admin password; self-deletion is blocked.
- Profile image, name, email and password updates.

### 2. Donation management

- Donors create donation offers with a description, items and a drop-off station.
- Staff/Admin can create donations on behalf of a donor.
- Donations move through `created`, `collected` and `stocked`.
- Staff/Admin can collect a donation and stock its items into inventory.
- A donor can cancel a `created` donation; Staff/Admin can delete a `flagged` donation.
- Every status change is recorded in a status history with a timestamp.

### 3. Inventory and stock

- Items store name, category, quantity, unit and minimum quantity.
- Add new items or restock existing items; an existing minimum quantity is preserved.
- Add or remove stock with a reason; every change is recorded as a stock transaction.
- Low-stock view shows items at or below `min_quantity`.
- Inventory and stock transactions can be exported to CSV.

### 4. Client profiles

- Client profile includes name, email, delivery address, free-text description and allergy list.
- Clients can update their own profile and password.
- Staff/Admin can update any client profile.
- Allergies are shown prominently during hamper packing.
- Structured household/dietary/religious fields are **not** implemented; the free-text description and allergy list are the only client-need fields.

### 5. Food hampers

- Create a hamper for a client, or leave it unassigned.
- Select items, add notes and assign a volunteer.
- Pack a hamper: checks every item and quantity, deducts stock, sets status `packed`.
- Unpack a hamper: returns items to inventory and sets status `created`.
- Deliver only a `packed` hamper; delivery sets `delivered` and completes the volunteer's job.
- A client can confirm receipt of a packed hamper.
- Staff/Admin can take over/reassign a job.
- Client can cancel a `created` request.
- Staff/Admin can delete `created` or `flagged` hampers; deleting a packed/flagged-packed hamper automatically unpacks its items.
- Status history is recorded for each transition.

### 6. Volunteer workflow

- Public volunteer application form.
- Applicants can check application status by email.
- Staff/Admin approve or delete applications; approval creates a Volunteer account.
- Volunteers claim/release unclaimed hamper and donation jobs.
- Active and completed job lists.
- Task detail shows pickup point, drop-off point, route flow and **Google Maps search links**.
- Volunteers can flag an issue on a task.
- A job cannot be claimed twice; a flagged job cannot be claimed until resolved.

### 7. Issue handling

- Volunteers and clients can flag an issue on a hamper or donation.
- The issue, reporter and previous status are recorded.
- Staff/Admin can open the detail page and use **Resolve Flagged Issue** with resolution notes; the previous status is restored.
- Staff/Admin can delete a flagged donation/hamper; a flagged packed hamper is auto-unpacked.
- There is **no consolidated Issues inbox**; resolution happens on the relevant detail page.

### 8. Client communication

- Clients can send, edit and delete messages to FoodBank.
- Message history is stored per client.
- There is **no staff message inbox**; staff do not have a page that aggregates client messages.

### 9. Public page

- Food bank address and description.
- Collection centres/stations.
- Impact metrics.
- Team/contact section.
- Verified volunteer directory.
- Volunteer application and application-status check.
- Login/register tabs for Donor and Client.

### 10. Reports

- Inventory CSV.
- Stock transaction CSV.
- Food hampers CSV.
- Donations CSV.
- Volunteers CSV.
- Batch ZIP containing all five reports.

### 11. Persistence and audit

- All changes are saved to `src/data/data.json`.
- `main.py` initialises logging and creates a timestamped backup before launch.
- Status histories and stock transaction records support later audit.
- `validate_data()` checks duplicate IDs/emails and missing references.

---

## Roles and permissions

| Role | Primary capabilities |
|---|---|
| **Admin** | Manage users (create, update, delete), stations, food bank profile; resolve/delete flagged records; export reports; manage inventory, donations and hampers. |
| **Staff** | Manage users/applications, donations, inventory, hampers, stations and reports; resolve/delete flagged records. |
| **Volunteer** | Apply for an account, claim/release jobs, view task detail and Maps links, deliver/collect, flag issues, view completed work. |
| **Donor** | Register/login, create donations with items and a station, view donation history/status, cancel a `created` donation. |
| **Client** | Register/login, maintain address/allergies/description, request a hamper, cancel a `created` request, confirm receipt, send messages, view history. |

Public visitors can view the landing page, stations, impact metrics, team/volunteer directory, and the volunteer application/status check.

---

## Technology stack

| Area | Technology |
|---|---|
| Language | Python 3.13 (recommended) |
| UI | Streamlit 1.50+ |
| Data | JSON (`src/data/data.json`) |
| Tables/analytics | pandas |
| Authentication | bcrypt (SHA-256 fallback) |
| Reporting | Python `csv` and `zipfile` |
| Testing | PyTest (`tests/test_food_bank.py`) |
| Logging | Python `logging` |
| Launcher | `main.py` (logging + backup + Streamlit), `launch.py` (UI router) |

There is **no database server**, no external API and no cloud dependency.

---

## Repository structure

```text
FoodShareTracker/
├── launch.py                  # Streamlit router / page setup
├── main.py                    # logging + backup + launch
├── run.bat                    # Windows convenience launcher
├── test.bat                   # Windows convenience test runner
├── src/
│   ├── app/
│   │   ├── FoodBank.py        # controller and JSON persistence
│   │   ├── user.py            # base User class
│   │   ├── admin.py           # AdminUser
│   │   ├── staff.py           # StaffUser
│   │   ├── volunteer.py       # VolunteerUser
│   │   ├── donor.py           # DonorUser
│   │   ├── client.py          # ClientUser
│   │   ├── donations.py       # Donation
│   │   ├── FoodHamper.py      # FoodHamper
│   │   ├── item.py            # Item
│   │   ├── inventory.py       # Inventory + stock records
│   │   └── utils.py           # validation, hashing, backup, logging
│   └── gui/
│       ├── main_page.py       # public page, login, registration
│       ├── new_system_page.py # first-admin setup
│       ├── admin_page.py      # admin dashboard
│       ├── staff_page.py      # staff dashboard
│       ├── donor_page.py      # donor dashboard
│       ├── volunteer_page.py  # volunteer dashboard
│       └── client_page.py     # client dashboard
├── tests/
│   └── test_food_bank.py      # PyTest suite (65 tests)
├── assets/
│   ├── default_avatar.png
│   └── hero_banner.png
├── src/data/                  # created at runtime; data.json is not committed
└── reports/                   # created at runtime for CSV/ZIP exports
```

---

## Getting started

### Prerequisites

- Python **3.13** recommended (Python 3.11+ should work with current Streamlit).
- `pip`.
- A modern browser.
- Optional but recommended: `bcrypt` for password hashing.
- Optional: Git for cloning.

### 1. Clone the repository

```bash
git clone https://github.com/KoJingRui1/FoodShareTracker.git
cd FoodShareTracker
```

### 2. Create and activate a virtual environment

Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

The repository **does not currently commit `requirements.txt`**. Install the packages manually:

```bash
python -m pip install --upgrade pip
python -m pip install streamlit pandas bcrypt pytest
```

If you want to create a local requirements file:

```bash
python -m pip freeze > requirements.txt
```

Do not commit a requirements file generated from a machine-specific environment unless the team has reviewed it.

### 4. Run the application

Recommended (initialises logging and backup):

```bash
python -m streamlit run main.py
```

Windows shortcut:

```bat
run.bat
```

`launch.py` alone starts the UI but skips the logger/backup setup. Use `main.py` for the intended startup path.

### 5. Open the app

Streamlit prints a local URL, normally:

```text
http://localhost:8501
```

Open it in a browser. If port 8501 is busy:

```bash
python -m streamlit run main.py --server.port 8502
```

---

## First run

`src/data/data.json` is **not committed**. On a fresh clone:

1. Start the app with `python -m streamlit run main.py`.
2. The first-run page asks for the first **Admin** account.
3. Create the Admin account.
4. Sign in with the Admin email (or user ID) and password.
5. Create Staff/Volunteer accounts as needed.
6. Donors and Clients can self-register from the public page.
7. Volunteer applicants apply publicly; Staff/Admin approve them.

If `src/data/data.json` already exists, the app opens the login/public page instead.

### Reset the demo data

Stop the app, then move or delete:

```text
src/data/data.json
src/data/backups/
```

and restart. The first-admin setup will appear again.

> Do not commit real client, donor or volunteer data to Git.

---

## Typical workflows

### A. Donation → inventory

1. Donor signs in and creates a donation with items and a station.
2. Staff collects the donation (`created → collected`).
3. Staff stocks the items (`collected → stocked`).
4. Inventory quantities increase; stock transactions are recorded.
5. Staff can export inventory/stock CSVs.

### B. Client request → hamper → delivery

1. Client registers/logs in and submits a hamper request with items and notes.
2. Staff reviews the client profile, allergy list and address.
3. Staff creates/assigns a hamper and selects items.
4. Staff packs the hamper; stock is checked and deducted.
5. Volunteer claims the job; task detail shows pickup/drop-off and Maps links.
6. Volunteer delivers the hamper.
7. Client confirms receipt.
8. Status history records each step.

### C. Volunteer application

1. Applicant submits the public volunteer form.
2. Applicant can check status by email.
3. Staff/Admin approve or delete the application.
4. Approval creates a Volunteer account.
5. Volunteer claims/releases jobs and updates completed work.

### D. Flagged issue

1. Volunteer/Client flags an issue on a hamper or donation.
2. Item status becomes `flagged`; previous status is stored.
3. Staff/Admin open the detail page.
4. Staff/Admin enter resolution notes and click **Mark Issue as Resolved**.
5. Previous status is restored.
6. Flagged records can be deleted; flagged packed hampers auto-unpack.

---

## Status model

### Donation

```text
created ──collect──> collected ──stock──> stocked
   │
   └── flagged (issue) ──resolve──> previous status
```

- Edit/delete a normal donation only while `created`.
- Donor can cancel their own `created` donation.
- Staff/Admin can delete a `flagged` donation.
- Stocking requires a valid donation and items; stock is added to inventory.

### Food hamper

```text
created / assigned ──pack──> packed ──deliver──> delivered
        ▲                       │
        └────── unpack ─────────┘
```

- Packing checks all items and quantities first, then deducts stock.
- Unpacking returns items to inventory.
- Delivery requires `packed`.
- Client confirmation requires `packed`.
- Deleting a packed/flagged-packed hamper auto-unpacks it.
- `flagged` records can be resolved or deleted.

---

## Data, backups and logs

| Path | Purpose |
|---|---|
| `src/data/data.json` | Main JSON data store |
| `src/data/backups/` | Timestamped backups created by `main.py` |
| `src/data/foodshare.log` | Application log |
| `reports/` | CSV and ZIP exports |

The JSON file contains users, donations, hampers, inventory, applications, stations, messages, status histories and stock records.

**Limitations:** the JSON store is single-file and does not support concurrent writers or multi-site synchronisation. For production use, move to a database with transactions and row-level locking.

---

## Reports

Staff/Admin can export:

- `inventory_report_*.csv`
- `stock_transactions_*.csv`
- `food_hampers_*.csv`
- `donations_*.csv`
- `volunteers_*.csv`
- a ZIP containing all five.

Empty datasets still produce header-only CSVs. Reports are raw exports; the app does not calculate trends or demand forecasts.

---

## Testing

Run the PyTest suite:

```bash
python -m pytest -v tests/test_food_bank.py
```

Windows shortcut:

```bat
test.bat
```

Expected result for the current code:

```text
65 passed
```

The tests cover authentication, donation and hamper lifecycles, packing/unpacking, delivery guards, issue flagging/resolution, client messaging, cascade deletion, JSON load/save and data validation.

There is **no committed AppTest/page-level suite**. Page behaviour should be checked manually in a browser for:

- first-admin setup;
- login for all five roles;
- donation create/collect/stock;
- hamper create/assign/pack/unpack/deliver/confirm;
- volunteer claim/release and Maps links;
- issue flag/resolve;
- client messages;
- CSV/ZIP download.

If PyTest reports temporary-directory permission errors, point `TMP`/`TEMP` to a writable directory or run the suite outside a restricted sandbox.

---

## Security and privacy

- Passwords use bcrypt with a per-password salt when bcrypt is installed; SHA-256 fallback is weaker and should not be used in production.
- Emails are unique.
- Role-based pages restrict client data to Staff/Admin and the assigned volunteer.
- Volunteers see the client's address, email and allergy list for their assigned task; this is necessary for delivery but should be explained in the privacy notice.
- The public page may show Staff/Volunteer names and profile images, but not client records.
- Admin account deletion requires the Admin password and blocks self-deletion.
- Do not commit `data.json`, backups, logs or real personal data.

---

## Known limitations and out-of-scope items

The following are **not implemented**:

- Expiry-date tracking and 7-day expiry alerts.
- Structured household composition, dietary, cultural or religious fields (only free-text description + allergy list).
- Structured substitution notes.
- Pickup notices by SMS/email and a staff message inbox (clients can send messages, but staff do not have an inbox).
- Email verification, password reset and multi-language support.
- Native iOS/Android app (the Streamlit UI works in a mobile browser).
- Analytics/trend reports.
- Large-text/accessibility modes and formal WCAG audit.
- Account deactivation (Admin deletion is a hard delete).
- Route optimization or an in-app navigation API (volunteer pages only open Google Maps search links).
- Concurrent writers, multi-site sync or database transactions.

Additional limitations:

- The UI is English-only.
- The JSON file is the single source of truth for one site.
- No `requirements.txt` or CI configuration is committed.
- No AppTest/page-level suite is committed; page checks are manual.
- The think-aloud usability evaluation is pending; usability evidence is currently a lightweight heuristic walkthrough, not empirical user data.

---

## Troubleshooting

### `streamlit: command not found`

Use the module form:

```bash
python -m streamlit run main.py
```

### `bcrypt` is missing

Install it:

```bash
python -m pip install bcrypt
```

Without bcrypt, the app uses a SHA-256 fallback. Existing bcrypt hashes require bcrypt to verify.

### Port already in use

```bash
python -m streamlit run main.py --server.port 8502
```

### First admin already exists

If `src/data/data.json` contains users, the first-admin setup is skipped. Move the data file aside if you intentionally want a fresh setup.

### Data looks corrupted

Stop the app and restore a file from `src/data/backups/`. Then run `validate_data()` or the test suite.

### PyTest temp-directory permission error

Set a writable temp directory before running:

```bat
set TMP=C:\temp
set TEMP=C:\temp
python -m pytest -v tests/test_food_bank.py
```

### JSON write failures

Check that `src/data/` is writable. The app writes a single JSON file and does not retry failed saves automatically.

---

## Authors and acknowledgements

**Authors**

- **Ko Jing Rui**
- **Baoxian Chen**

**Course:** FIT1056 Software Engineering — Group 16  
**Tutor:** Dr Sanoop Mallissery  
**Deliverable:** Deliverable 2 — FoodShare Tracker SRS and implementation

The project was developed as a university software engineering deliverable. It is not a production food-bank system; the limitations above are deliberate scope decisions for the MVP.

---

## Quick reference

```bash
# clone
git clone https://github.com/KoJingRui1/FoodShareTracker.git
cd FoodShareTracker

# environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# dependencies (no requirements.txt committed)
python -m pip install streamlit pandas bcrypt pytest

# run
python -m streamlit run main.py

# test
python -m pytest -v tests/test_food_bank.py
```
