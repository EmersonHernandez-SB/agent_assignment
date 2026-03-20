# EmerClinic Support Agent

A multi-agent AI customer support system for **EmerClinic** — a practice management SaaS platform used by dental and medical clinics. Built with LangGraph, OpenAI GPT-4o-mini, ChromaDB, FastAPI, and Streamlit.

---

## Table of Contents

- [Overview](#overview)
- [Multi-Agent Graph](#multi-agent-graph)
  - [Graph Structure](#graph-structure)
  - [Shared State](#shared-state)
  - [Router & Intent Classification](#router--intent-classification)
  - [Tool Loops](#tool-loops)
  - [Memory & Multi-Turn Conversations](#memory--multi-turn-conversations)
- [Agents & Tools](#agents--tools)
  - [FAQ Agent](#faq-agent--rag)
  - [Scheduling Agent](#scheduling-agent)
  - [Operations Agent](#operations-agent)
  - [Billing Agent](#billing-agent)
  - [Escalation Node](#escalation-node)
- [Data Layer](#data-layer)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Testing the Agent](#testing-the-agent)
- [Email Notifications](#email-notifications)

---

## Overview

The EmerClinic Support Agent is a **multi-agent LangGraph system** that routes incoming support requests to the appropriate specialist agent. Each agent operates independently with its own system prompt, a scoped set of tools, and a dedicated tool-call loop. A single shared state object carries all context — conversation history, current intent, identified patient and account, and escalation flags — across every node in the graph.

The system is exposed through:
- A **REST API** (`api.py`) built with FastAPI
- A **chat UI** (`ui.py`) built with Streamlit
- A **single launcher** (`start.py`) that starts both services with one command

---

## Multi-Agent Graph

### Graph Structure

The graph is built with **LangGraph `StateGraph`** and compiled with a **`MemorySaver` checkpointer** for persistent multi-turn memory. Every incoming message enters at the `router` node, gets classified, and is dispatched to the appropriate agent. Each agent runs its own tool loop until the LLM produces a response with no further tool calls, at which point execution returns to `END` (or escalation, if flagged).

```
                         ┌─────────────────────┐
          START ────────►│      router_node      │
                         └──────────┬──────────┘
                                    │  conditional edge (route_from_router)
               ┌────────────────────┼────────────────────────┐
               │            │       │        │               │
               ▼            ▼       ▼        ▼               ▼
           [general]     [faq]  [operations][scheduling]  [billing]
             END          │         │           │              │
                          ▼         │           │              │
                         END    ┌───┴───┐   ┌───┴───┐   ┌────┴────┐
                                │ tools │   │ tools │   │  tools  │
                                └───┬───┘   └───┬───┘   └────┬────┘
                                    │           │             │
                                    └─────┬─────┘─────────────┘
                                          │  (needs_escalation=True OR
                                          │   user requests human)
                                          ▼
                                   [escalation_node]
                                          │
                                     ┌────┴────┐
                                     │  tools  │
                                     └────┬────┘
                                          ▼
                                         END
```

**Edge types used:**
- `add_edge(START, "router")` — every message starts at the router
- `add_conditional_edges("router", route_from_router, {...})` — dispatches to the right agent based on classified intent
- `add_conditional_edges(agent, should_continue, {...})` — each agent either loops back through its tool node, escalates, or ends
- `add_edge(tool_node, agent)` — tool results feed back into the same agent LLM
- `"general" → END` — router writes the reply directly without going to a downstream agent

---

### Shared State

All nodes read from and write to a single `State` object (LangGraph `TypedDict`). This is what allows context — like which patient was identified or which agent handled the last turn — to persist across every step of a multi-turn conversation.

| Field              | Type          | Description                                                        |
|--------------------|---------------|--------------------------------------------------------------------|
| `messages`         | `list[AnyMessage]` | Full conversation history. Uses `add_messages` reducer — messages are appended, never overwritten. |
| `intent`           | `str`         | The intent last classified by the router (`faq`, `scheduling`, etc.) |
| `patient_id`       | `int \| None` | Set once a patient is identified in the clinic system              |
| `account_id`       | `int \| None` | Set once an EmerClinic account is identified                       |
| `thread_id`        | `str`         | Stable session ID passed to LangGraph's checkpointer for memory    |
| `current_agent`    | `str`         | Name of the node that last processed the message                   |
| `needs_escalation` | `bool`        | Any agent can flip this to `True` to trigger the escalation node   |
| `resolved`         | `bool`        | Set to `True` by the escalation node when the handoff is complete  |

The `messages` field uses LangGraph's `add_messages` annotation, meaning new messages from each node are **appended** to the list rather than replacing it. This gives every agent access to the full conversation history on every invocation.

---

### Router & Intent Classification

The router is the entry point for every message. It uses `ChatOpenAI.with_structured_output(Intent)` — a Pydantic model — to force the LLM to return a valid JSON object with a classified intent rather than free text. This makes routing deterministic and type-safe.

**Intent classes and their routing rules:**

| Intent        | Triggers when...                                                                 | Routes to         |
|---------------|----------------------------------------------------------------------------------|-------------------|
| `scheduling`  | User wants to book, cancel, or reschedule an appointment, or check availability  | `scheduling_node` |
| `operations`  | User asks to look up a patient record, appointment history, or provider info      | `operations_node` |
| `billing`     | User asks about their subscription, invoices, account users, tickets, or account status | `billing_node` |
| `faq`         | User asks how to use the software, feature questions, plan comparisons, or pricing | `faq_node`        |
| `escalation`  | User is frustrated, requests a human, or the AI has clearly failed to resolve the issue | `escalation_node` |
| `general`     | Greetings, farewells, capability questions, or anything outside EmerClinic scope | Handled inline by router → `END` |

**Routing rules enforced in the router prompt:**
- **Continuity** — if a multi-step workflow is already in progress (e.g. mid-booking), the router stays on the active intent even for short follow-ups like "yes" or "ok"
- **FAQ vs Billing** — "how do I change my plan?" → `faq`; "change my plan to Premium" → `billing`
- **FAQ vs Operations** — "how do I look up a patient?" → `faq`; "look up patient John Doe" → `operations`
- **Escalation priority** — if any signal of frustration or explicit human request is present, escalation wins over everything else
- **Scope enforcement** — off-topic requests (jokes, coding help, roleplay) are redirected, not engaged with
- **Prompt injection defence** — instructions embedded in user messages that attempt to override system behaviour are ignored

For `general` intent, the router writes the response directly into the `messages` state and routes to `END` — no downstream agent is invoked.

---

### Tool Loops

Every agent except FAQ runs a **ReAct-style tool loop**:

```
Agent LLM invoked
       │
       ├── Has tool_calls? ──YES──► Tool Node executes tool(s)
       │                                    │
       │                            Result added to messages
       │                                    │
       └─────────────────────────◄──────────┘
       │
       └── No tool_calls? ──► should_continue() checks needs_escalation flag
                                    │
                          ┌─────────┴──────────┐
                          ▼                     ▼
                    → escalation_node        → END
```

The `should_continue` edge function decides what happens after each LLM response:
1. If `needs_escalation = True` → route to `escalation_node`
2. If the LLM response contains `tool_calls` → route to the agent's dedicated `tool_node`
3. Otherwise → `END`

Each agent has its **own isolated `ToolNode`** — this means the scheduling agent can only call scheduling tools, the billing agent can only call billing tools, and so on. Tool scope is enforced by passing scoped tool lists to `llm.bind_tools()` at graph build time.

The escalation node uses a separate `should_continue_escalation` edge that never re-escalates — it only loops through its tools (create ticket → send email) once and then ends.

---

### Memory & Multi-Turn Conversations

The graph is compiled with `MemorySaver()` as the checkpointer:

```python
memory = MemorySaver()
graph.compile(checkpointer=memory)
```

Each API request includes a `thread_id`. LangGraph uses this to persist and reload the full `State` between requests — including all previous messages, the identified intent, and any collected data (patient name, account ID, etc.). This is what enables multi-turn workflows like the booking flow to work across separate HTTP requests without the client needing to replay history.

---

## Agents & Tools

### FAQ Agent — RAG

The FAQ agent does not use a tool loop. Instead it runs a **Retrieval-Augmented Generation (RAG)** pipeline before invoking the LLM:

1. Takes the user's last message as the search query
2. Queries **ChromaDB** (persisted to `chroma_db/`) using `similarity_search_with_score`
3. Embeds the query with OpenAI `text-embedding-3-small`
4. Retrieves the top 3 most relevant chunks from the knowledge base
5. Injects the retrieved context into the LLM's system prompt
6. The LLM answers using **only** the provided context — it is explicitly instructed not to use outside knowledge

If no relevant chunks are found (or the score is too low), the agent adds a message saying it doesn't have the information and sets `needs_escalation = True`.

**Knowledge base:** 11 markdown documents in `core/rag_docs/`, chunked at 600 tokens with 100-token overlap:

| Document | Covers |
|----------|--------|
| `plans_overview.md` | Plan tiers, feature comparison, pricing |
| `billing_faq.md` | Payment failures, refunds, billing cycles |
| `how_to_export_csv.md` | Exporting patient data |
| `how_to_add_provider.md` | Adding providers to the system |
| `how_to_add_patient.md` | Patient registration workflow |
| `user_roles_and_permissions.md` | Admin, provider, and staff roles |
| `hipaa_and_data_security.md` | Compliance, data handling, security |
| `troubleshooting.md` | Common errors and fixes |
| `system_requirements.md` | Browser/OS requirements |
| `integrations.md` | Third-party integrations |
| `calendar_sync.md` | Google Calendar and iCal setup |

---

### Scheduling Agent

Handles the full appointment lifecycle with a strict **10-step booking workflow**:

```
1. Collect patient name
2. Collect reason for visit
3. Collect preferred date (validates it is not in the past)
4. Call get_available_providers → present list
5. User selects provider (name resolved to ID via get_available_providers)
6. Call get_available_slots(provider_id, date) → present available times
7. User selects a time slot
8. Show confirmation summary to user
9. User confirms explicitly ("yes" / "confirm" / "go ahead")
10. Call add_appointment → call send_email_tool with booking details
```

Key behaviours enforced by the system prompt:
- **Context continuity** — scans full message history before each response; never re-asks for information already collected
- **Confirmation gate** — `add_appointment`, `cancel_appointment`, and `reschedule_appointment` can only be called after an explicit user confirmation following a full summary
- **Date validation** — rejects any date in the past; today's date is injected into the prompt at runtime
- **Provider ID resolution** — always calls `get_available_providers` to resolve a name to an ID; never hardcodes IDs
- **Booked slot handling** — if the user picks a taken time, shows only the available ones from the already-retrieved slot data (no redundant tool call)

**Tools available to the Scheduling Agent:**

| Tool | Purpose |
|------|---------|
| `get_available_providers` | List all providers and their specialties |
| `get_available_slots` | Get open time slots for a provider on a date |
| `get_patient_appointments` | Look up a patient's full appointment history |
| `get_appointments` | Get all appointments for an account |
| `add_appointment` | Book a new appointment |
| `cancel_appointment` | Cancel an appointment by ID |
| `reschedule_appointment` | Move an appointment to a new date/time |
| `send_email_tool` | Send booking confirmation email |

---

### Operations Agent

Provides read-only access to clinic data for staff lookup tasks.

Key behaviours:
- Always calls the tool **first** with whatever information the user provided — does not ask for clarification before attempting a lookup
- Distinguishes between patient lookups (`get_patient_appointments`) and provider lookups (`get_appointments_by_provider`) — never searches a provider name as a patient
- If multiple records match, only then asks for disambiguating info (DOB, partial ID)
- Never shows raw error dicts to the user — translates them into plain language

**Tools available to the Operations Agent:**

| Tool | Purpose |
|------|---------|
| `get_patient_appointments` | Look up all appointments for a patient by name (partial match) |
| `get_appointments_by_provider` | Get all appointments for a specific provider |
| `get_available_providers` | List all providers, used to resolve provider names to IDs |

---

### Billing Agent

Handles all EmerClinic subscription management tasks. Always starts by identifying the account (via email or clinic name) before taking any action.

**Workflow enforced by the system prompt:**
1. **Identify** — `find_account_by_email` or `find_account_by_clinic_name`
2. **Understand** — call the relevant tool based on the request type (plan, invoices, users, tickets)
3. **Act** — plan changes and reactivations require explicit user confirmation first
4. **Confirm** — send email after any successful plan change or ticket creation

Key behaviours:
- Reports prices **exactly as stored** in the database — no substitution of list prices
- Never calls `update_plan` or `reactivate_account` without the user explicitly requesting it
- If the same issue cannot be resolved after 2 tool attempts, escalates automatically

**EmerClinic subscription plans (reference):**

| Plan | Monthly | Annual | Features |
|------|---------|--------|----------|
| Basic | $99/mo | $950/yr | 1 provider, up to 500 patients, standard reports, email support |
| Premium | $249/mo | $2,390/yr | Unlimited providers & patients, insurance verification, advanced analytics, calendar sync, API access, priority support |

**Tools available to the Billing Agent:**

| Tool | Purpose |
|------|---------|
| `find_account_by_email` | Look up an account by registered email |
| `find_account_by_clinic_name` | Look up an account by clinic name (partial match) |
| `get_customer_plan` | Get current plan, billing cycle, and price |
| `get_invoices` | Retrieve full billing history |
| `update_plan` | Change plan and/or billing cycle |
| `get_users` | List all users and roles on an account |
| `get_tickets_for_account` | List all support tickets for an account |
| `create_support_ticket` | Open a new support ticket |
| `update_ticket_status` | Update ticket status (open / in_progress / closed) |
| `reactivate_account` | Reactivate a suspended or trial account |
| `send_email_tool` | Send plan change or ticket confirmation email |

---

### Escalation Node

Triggered automatically when `needs_escalation = True` in state, or when the router classifies intent as `escalation`.

Executes a fixed 3-step workflow — always in this order:
1. **Create ticket** — calls `create_support_ticket` with a synthesised summary of the unresolved issue, priority `"high"`, category `"escalation"`
2. **Notify team** — calls `send_email_tool` to alert the support team with ticket ID, account ID, issue summary, and user tone
3. **Farewell message** — writes a warm, human-sounding closing message to the user that includes the ticket ID and a 4-business-hour response commitment

The escalation node uses its own separate tool loop (`should_continue_escalation`) that never re-escalates. If `create_support_ticket` fails, it still sends the email and still writes the farewell — using "N/A" as the ticket ID.

**Tools available to the Escalation Node:**

| Tool | Purpose |
|------|---------|
| `create_support_ticket` | Opens a high-priority escalation ticket |
| `send_email_tool` | Notifies the support team |

---

## Data Layer

The system uses two SQLite databases, both included in the repository with pre-seeded demo data.

**`support.db`** — EmerClinic SaaS layer (used by Billing and Escalation agents):

| Table | Contents |
|-------|----------|
| `accounts` | Clinic subscriptions — plan, billing cycle, contracted price, status |
| `invoices` | Billing history per account |
| `users` | Team members and roles (admin, provider, staff) per account |
| `tickets` | Support ticket history with priority, category, and status |
| `interactions` | Agent interaction log for analytics |

**`clinic.db`** — Demo clinic data (used by Scheduling and Operations agents):

| Table | Contents |
|-------|----------|
| `providers` | Doctors, their specialties, and availability flag |
| `appointments` | Patient appointments with date, provider, reason, and status |

**Pre-seeded accounts for testing:**

| Email | Clinic | Plan | Billing | Status |
|-------|--------|------|---------|--------|
| `grossamy@example.com` | Martinez Group | Premium | annual | active |
| `russellamy@example.org` | Richards-Fischer | Premium | monthly | trial |
| `danny78@example.com` | Berry LLC | Premium | annual | suspended |

**Pre-seeded providers for testing:**

| ID | Name | Specialty |
|----|------|-----------|
| 1 | Dr. Linda Henderson | General Doctor |
| 2 | Dr. Scott Garcia | Dentist |
| 3 | Dr. Ms. Andrea Chan | Orthodontist |
| 4 | Dr. Greg Diaz | Orthodontist |

---

## Project Structure

```
agent-builder-assignment/
│
├── core/
│   ├── agent.py          # LangGraph graph: all nodes, prompts, edges, tool loops
│   ├── db_tools.py       # All SQLite tool functions (support.db + clinic.db)
│   ├── db_creation.py    # Database schema and seed data
│   ├── faq_rag.py        # ChromaDB vector store setup and RAG retrieval
│   └── rag_docs/         # 11 markdown documents for the FAQ knowledge base
│
├── notebooks/
│   └── inspect_data.ipynb  # Browse both databases interactively
│
├── api.py              # FastAPI REST API (POST /chat, GET /health)
├── ui.py               # Streamlit chat interface
├── start.py            # Single-command launcher (API + UI)
│
├── support.db          # Pre-seeded SaaS accounts database
├── clinic.db           # Pre-seeded clinic demo database
├── chroma_db/          # Persisted ChromaDB vector store
│
├── .env                # Environment variables (create manually — see below)
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Prerequisites

- **Python 3.10+**
- An **OpenAI API key** with access to `gpt-4o-mini` and `text-embedding-3-small`
- (Optional) A **Gmail account** with an App Password for email notifications

---

## Installation

**1. Clone the repository**

```bash
git clone <repo-url>
cd agent-builder-assignment
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create your `.env` file** (see [Environment Variables](#environment-variables) below)

**5. Run the project**

```bash
python start.py
```

That's it. Both databases and the vector store are already included in the repository.

---

## Environment Variables

Create a `.env` file in the project root:

```env
# ── Required ────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-...

# ── Optional: Email notifications ───────────────────────────────────
# If not set, the agent skips email steps gracefully and tells the user.
# No functionality is blocked by missing email credentials.

GMAIL_USER=your-address@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
SUPPORT_EMAIL=support@yourteam.com
```

> **How to get a Gmail App Password:** Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), create a password for "Mail". Two-Factor Authentication must be enabled on the account. Copy the 16-character password — this goes in `GMAIL_APP_PASSWORD`, not your regular login password.

---

## Running the Project

### Single command

```bash
python start.py
```

```
🚀  Starting EmerClinic Support Agent
    API  →  http://127.0.0.1:8000
    UI   →  http://localhost:8501

    Press Ctrl+C to stop both services.
```

Open **http://localhost:8501** in your browser to use the Streamlit chat interface.
Press **Ctrl+C** to shut down both services cleanly.

### Running services separately

```bash
# API only (with hot reload)
uvicorn api:app --host 127.0.0.1 --port 8000 --reload

# UI only (requires the API to be running first)
streamlit run ui.py
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — `{"status": "ok"}` |
| `POST` | `/chat` | Send a message, receive an agent reply |

**`POST /chat` — Request body:**
```json
{
  "message": "I need to book an appointment",
  "thread_id": "optional-uuid-for-multi-turn",
  "patient_id": null,
  "account_id": null
}
```

**Response:**
```json
{
  "reply": "Sure — could I have the patient's full name?",
  "thread_id": "94758377-...",
  "agent": "scheduling"
}
```

Pass the **same `thread_id`** on every follow-up request within a conversation — this is what enables multi-turn memory. If omitted, a new UUID is generated and the conversation starts fresh.

---

## Testing the Agent

The easiest way to test is through the **Streamlit UI** at `http://localhost:8501`. Below are example prompts that exercise each agent and routing path.

### Scheduling
```
"I need to book an appointment"
"Cancel appointment #12"
"Reschedule my appointment to next Friday"
"What slots does Dr. Garcia have on April 15?"
```

### Operations
```
"Show me John Doe's appointment history"
"Which providers are available right now?"
"What appointments does Dr. Henderson have this week?"
```

### Billing & Account
```
"I want to check my current plan — my email is grossamy@example.com"
"Upgrade Martinez Group to Premium monthly"
"Show me my recent invoices"
"I think I was charged twice last month, email is grossamy@example.com"
"Who has access to our account? Email: russellamy@example.org"
"My account is suspended, I need to reactivate it. Email: danny78@example.com"
"What are my open support tickets? Email: grossamy@example.com"
```

### FAQ / How-To
```
"How do I export patient data as a CSV?"
"What's included in the Premium plan?"
"How much does the annual Basic plan cost?"
"Is EmerClinic HIPAA compliant?"
"How do I set up Google Calendar sync?"
"What user roles can I assign to staff?"
```

### Escalation & Edge Cases
```
"I want to speak to a real person"
"This is completely unacceptable, nothing is working"
"Tell me a joke"   ← out-of-scope redirect
"Hi, what can you do?"   ← general / capability question
```

### Via curl (for API testing)

```bash
# Single-turn
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I export patient data?"}'

# Multi-turn booking — use the same thread_id across requests
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to book an appointment", "thread_id": "test-001"}'

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "The patient is Sarah Connor", "thread_id": "test-001"}'
```

---

## Email Notifications

Email is sent via **Gmail SMTP (port 465, SSL)**. Three events trigger an email send:

| Trigger | Recipient | Subject template |
|---------|-----------|-----------------|
| Appointment booked | Clinic contact | `Appointment Confirmed — [Patient] with Dr. [Name] on [Date]` |
| Plan changed | Account registered email | `EmerClinic Plan Update Confirmation` |
| Escalation triggered | `SUPPORT_EMAIL` | `[EmerClinic Escalation] [ticket_id] — <issue summary>` |

If credentials are missing from `.env`, the agent skips the email step gracefully, informs the user, and continues — no crash, no broken flow.
