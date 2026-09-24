# SamoGo

> **Community automation should feel simple, even when the system behind it is not.**

**SamoGo** is a commercial product currently in development for simplifying user-generated content management in VK communities.

The platform is being designed around a simple experience: connect a community and manage routine content workflows from one place — without requiring users to understand automation systems or technical integrations.

Planned product areas include:

- collecting user-generated content;
- creating and publishing posts;
- publication scheduling;
- conversational automation through a community bot.

**Настроил. И само пошло.**

## Product principle

Automation tools can become complicated very quickly. SamoGo takes the opposite approach: technical complexity belongs inside the platform, not in the user's workflow.

The goal is to make everyday community management approachable for non-technical users while keeping the underlying backend structured enough to support automation and integrations as the product grows.

## Development status

🚧 **Active development / early MVP**

The complete product is developed in a private repository.

This repository is intentionally a **portfolio showcase**, not the full SamoGo source tree. It publishes a small, real backend subsystem so the implementation style can be reviewed without exposing unreleased workflows, detailed VK integration, commercial logic or the internal roadmap.

## Selected backend sample: authentication lifecycle

The public code sample is a self-contained authentication subsystem taken from the developing product. It is deliberately infrastructure-oriented rather than a disclosure of SamoGo's product-defining workflows.

```text
Login request
     │
     ▼
One-time code
     │  hashed at rest
     ▼
Verification ──► attempt / expiry checks
     │
     ▼
User + session
     │  session token hashed at rest
     ▼
Authentication / logout
```

The sample demonstrates:

- one-time login codes with a 10-minute lifetime;
- invalidation of previous active codes;
- a five-attempt verification limit;
- hashed OTP storage;
- hashed session-token storage;
- session expiration and revocation;
- normalized user identity;
- SQLite constraints and foreign keys;
- tests for security-sensitive lifecycle behavior.

### Code layout

```text
app/
├── auth/
│   ├── service.py       # authentication rules and lifecycle
│   └── repository.py    # persistence boundary
└── db/
    └── database.py      # SQLite schema and transactions

tests/
├── test_auth_service.py
└── test_auth_database.py
```

## What this repository demonstrates

This showcase is intended to make several engineering qualities directly inspectable:

- Python backend development;
- separation of application logic from persistence;
- explicit authentication lifecycle and state handling;
- expiry, one-time-use and attempt-limit rules;
- relational constraints and transactional persistence;
- automated tests around important invariants;
- product development from concept toward a working MVP.

## Technology

**Public sample:** Python 3.12 · SQLite · unittest  
**Private product:** FastAPI · Uvicorn · Jinja2 · JavaScript · HTML/CSS · VK integration

## What remains private

SamoGo is an independently developed commercial product. The public repository therefore intentionally excludes:

- the complete application source;
- detailed VK connection and integration flows;
- unreleased user-generated-content workflows;
- product-specific automation behavior;
- production configuration and credentials;
- production infrastructure;
- commercial logic and the internal roadmap.

The boundary is intentional: this repository shows **how the backend is engineered** without publishing the implementation that defines the product's competitive behavior.

## Source availability

This repository is published for portfolio and code-review purposes.

**No open-source license is granted.** The complete SamoGo product and unreleased product design remain private.
