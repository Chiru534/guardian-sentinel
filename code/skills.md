# 🛡️ Guardian Sentinel: Agentic Guardrails & Skills

This document defines the strict architectural boundaries, technology constraints, and operational patterns for the Guardian Sentinel project. All AI agents MUST read and adhere to these rules during every coding session to prevent hallucination and maintain system integrity.

---

### 1. 🧰 Approved Tech Stack & Versions
The project utilizes a specific, hardened stack. **Do not introduce outside libraries.**

| Component | Technology | Primary Libraries |
| :--- | :--- | :--- |
| **Deep Learning** | TensorFlow 2.x | `tensorflow`, `keras`, `numpy` |
| **NLP Engine** | NLTK / Regex | `nltk`, `re`, `pickle` |
| **Data Fetcher** | Google Gmail API | `google-api-python-client`, `google-auth-oauthlib` |
| **Backend API** | FastAPI | `fastapi`, `uvicorn`, `pydantic` |
| **Frontend UI** | Streamlit | `streamlit`, `requests` |
| **Testing** | Playwright | `pytest`, `pytest-playwright` |
| **Sanitization** | BeautifulSoup4 | `beautifulsoup4` |

---

### 2. 🚫 Absolute Anti-Patterns (Zero Tolerance)
The following actions are strictly prohibited and considered hallucinations or architectural violations:

> [!CAUTION]
> **No IMAP/POP3**: Do NOT use `imaplib` or `poplib`. The system is built exclusively on the **Google Gmail API**.
> **No CSS Files**: Do NOT invent or suggest external `.css` files. Streamlit handles UI styling natively or via `st.markdown` injections.
> **No External Databases**: Do NOT suggest PostgreSQL, MongoDB, or SQL. All data is managed in-memory, CSV logs, or serialized artifacts (`.h5`, `.pickle`).
> **No Hard Sleeps**: In Playwright E2E tests, **Never** use `time.sleep()`. Rely on Playwright's auto-waiting locators and `expect(...).to_be_visible()`.
> **No Model Imports in UI**: The Frontend (`frontend.py`) MUST NOT import `tensorflow`, `keras`, or `models.py`. It communicates **only** via HTTP REST calls to the FastAPI backend.

---

### 3. 🏗️ Architectural Rules & State Management
To maintain the "Master-Detail" webmail flow:

1.  **Strict State Isolation**: Use `st.session_state` to store `emails`, `selected_email`, and `current_view`. Never store large objects in global script variables to avoid state loss on rerun.
2.  **API-First Communication**: The frontend must use `requests.get` or `requests.post` to interact with `http://localhost:8000`. 
3.  **Authentication Control**: `gmail_service.py` is the single source of truth for OAuth2 tokens. The logic for `credentials.json` and `token.json` must be kept isolated from the UI layer.
4.  **Heuristic Priority**: Always run the `DataPreprocessor.engineer_bec_features` before neural inference to ensure hybrid explainability.

---

### 4. 🛰️ Backend API Contract (`/sync-inbox`)
When modifying the UI or Backend, ensure the data exchange strictly follows this schema:

**Endpoint**: `GET /sync-inbox`  
**Response JSON Structure**:
```json
[
  {
    "id": "string (Gmail Message ID)",
    "sender": "string (Display Name <email@val.com>)",
    "subject": "string",
    "body_text": "string (Cleaned Plaintext)",
    "is_spam": "boolean (ML Prediction Result)",
    "confidence": "float (0.0 to 1.0)",
    "bec_flags": "list or dict (Heuristic triggers)"
  }
]
```

**Endpoint**: `POST /delete-email/{id}`  
**Response JSON**: `{"status": "deleted", "id": "string"}`

---

### 5. 🧪 Testing Ethics
All UI tests in `tests/test_frontend.py` MUST:
1.  Use `page.route()` or a dedicated **Mock FastAPI Server** (on port 8000) for E2E validation.
2.  Verify the "Quarantine" logic by asserting the presence of `🚨 BEC ATTACK DETECTED`.
3.  Confirm the "Kill Switch" by verifying that the targeted email button is removed from the DOM after `click()`.

> [!IMPORTANT]
> Failure to adhere to this `skills.md` specification will result in architectural debt and broken production flows.
