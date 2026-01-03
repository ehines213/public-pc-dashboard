# Public PC Fleet Dashboard

A lightweight internal monitoring dashboard for managing and visualizing the health of public-access computers (e.g., library PCs).  
This project simulates device check-ins, evaluates system health, and presents real-time status through a web dashboard.

---

## Overview

The **Public PC Fleet Dashboard** is designed to help IT staff quickly identify issues across a fleet of shared computers.  
It tracks disk usage, antivirus status, authentication failures, reboot requirements, and network health indicators.

The system includes:
- A FastAPI backend
- A SQLite database
- A browser-based dashboard UI
- A simulator to generate realistic device check-ins

---

## Key Features

- **Real-time device status monitoring**
  - GREEN / YELLOW / RED health classification
- **Trend indicators**
  - Disk usage change
  - Authentication failure trends
- **Sortable & filterable dashboard**
  - Filter by severity
  - Search by device ID
- **Per-device detail view**
  - Historical check-ins
  - Metrics over time
- **API key protection**
  - Simple header-based authentication
- **Auto-refreshing dashboard**
  - Updates every 5 seconds

---

## Technology Stack

- **Backend:** Python, FastAPI
- **Database:** SQLite
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Other:** REST API, localStorage, JSON

---

## Project Structure

public-pc-dashboard/
├── app/
│ ├── main.py # FastAPI app & routes
│ ├── db.py # Database access layer
│ ├── models.py # Pydantic models
│ └── health_rules.py # Status classification logic
├── static/
│ ├── dashboard.html # Main dashboard UI
│ └── device.html # Device detail page
├── simulate_checkins.py # Device check-in simulator
├── schema.sql # Database schema
├── dashboard.db # SQLite database
├── requirements.txt
└── README.md


---

## How It Works

1. **Simulated devices** send periodic check-ins to the API
2. Each check-in is stored in SQLite
3. Health rules evaluate system state
4. The dashboard fetches aggregated device data
5. Status, trends, and metrics are rendered in the browser

---

## Running the Project Locally

### 1. Set up virtual environment

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

### 2. Start the API server

uvicorn app.main:app --reload

### 3. Run the simulator in separate terminal

python simulate_checkins.py

### 4. Open the Dashboard


### API Authentication

The dashboard uses a simple API key mechanism:

API key is defined in app/main.py

Stored in browser localStorage

Sent via x-api-key request header

This is intended for internal/demo use and can be replaced with environment variables or OAuth in production.

### Use Case

This project reflects real-world scenarios encountered in:

Public libraries
Schools
Computer labs
Shared workstation environments

It demonstrates system monitoring, backend/frontend integration, and practical IT tooling.


### Future Enhancements

User authentication & roles
Export reports
Alerts and notifications
Deployment via Docker
Charts for historical trends

 
