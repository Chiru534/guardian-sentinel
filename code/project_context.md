# Project Context: Guardian Sentinel

## Executive Summary
This repository is a hybrid **research + application** project for phishing and Business Email Compromise (BEC) detection.

Today, the codebase is best understood as:

1. A **Python/TensorFlow detection backend** built around a saved Bi-LSTM model plus regex-based BEC heuristics.
2. A **FastAPI runtime** that serves predictions, Gmail inbox sync, feedback logging, and a built-in HTML dashboard.
3. A newer **TypeScript/React dashboard** in `guardian-ui/` that talks to the same backend.
4. Legacy/experimental assets for **Streamlit UI**, **retraining**, notebooks, and academic evaluation.

The project still reflects its academic origins, but the present working runtime is centered on:

- `api.py`
- `data_pipeline.py`
- `gmail_service.py`
- `index.html`
- `guardian-ui/`

## Current State

### What is working now
- The FastAPI app loads and serves the built-in dashboard from `GET /`.
- The `/predict` endpoint runs inference using the saved model and tokenizer.
- The Gmail integration module can authenticate, fetch unread messages, extract plaintext and HTML, and trash messages.
- Processed emails are persisted to `processed_emails.csv`.
- The built-in HTML frontend in `index.html` is updated to the current dark three-column dashboard layout.
- The React frontend in `guardian-ui/` currently passes:
  - `npm run lint`
  - `npm run build`

### What is not fully aligned yet
- The feedback logging and retraining pipeline are **not fully wired together**.
  - `api.py` appends raw rows to `user_feedback_log.csv`.
  - `future_scope/retrain.py` expects named columns such as `text` and `Label`.
- The Streamlit frontend in `future_scope/frontend.py` is still present, but it is no longer the primary UI path.
- `verify_project.py` is not fully reliable on the current Windows console setup because of encoding-sensitive output.
- `evaluate.py` mixes real model evaluation with **simulated** performance curve values for chart generation.

## Repository Layout

### Core backend
- `api.py`
  - FastAPI application
  - Serves `index.html`
  - Exposes inference, sync, delete, and feedback endpoints
- `data_pipeline.py`
  - text cleaning
  - stopword removal
  - optional stemming
  - BEC heuristic extraction
  - tokenizer wrapper
- `gmail_service.py`
  - Gmail OAuth flow
  - unread inbox fetch
  - MIME parsing
  - HTML-to-text cleanup
  - trash operation
- `models.py`
  - ANN, RNN, LSTM, Bi-LSTM definitions
- `model_base.py`
  - abstract model interface
- `main.py`
  - dataset loading
  - preprocessing
  - model training orchestration

### Saved artifacts and data
- `bilstm_model.h5`
- `ann_model.h5`
- `rnn_model.h5`
- `tokenizer.pickle`
- `processed_emails.csv`
- `spam_ham_dataset.csv`
- `BusinessEmail_train.csv`
- `BusinessEmail_test.csv`

### Frontends
- `index.html`
  - API-served HTML dashboard at `http://localhost:8000`
- `guardian-ui/`
  - React + TypeScript + Vite dashboard
  - separate frontend dev/build workflow
- `future_scope/frontend.py`
  - older Streamlit UI

### Evaluation and research
- `evaluate.py`
- `RESEARCH.md`
- `README.md`
- notebooks and extracted notebook code

### Future-scope / experimental
- `future_scope/retrain.py`
- `future_scope/index.html`
- `future_scope/frontend.py`

## Architecture

## 1. Detection Pipeline

### Input sources
The backend works with:
- direct text passed to `/predict`
- unread Gmail messages fetched by `/sync-inbox`
- cached previously processed messages from `processed_emails.csv`

### Preprocessing
`DataPreprocessor` in `data_pipeline.py` currently performs:
- lowercase normalization
- regex-based noise removal
- whitespace tokenization
- English stopword removal
- optional stemming

### Heuristic layer
The heuristic engine adds binary flags for:
- `persona_impersonation`
- `victim_isolation`
- `urgency_engagement`
- `bank_manipulation`
- `evasion_cleanup`
- `credential_phishing`

These are simple regex checks, used mainly for explainability and UI display.

### Neural layer
The deployed classifier uses:
- saved Keras model: `bilstm_model.h5`
- saved tokenizer: `tokenizer.pickle`
- max sequence length: `50`

The backend currently classifies with a threshold of:
- `score > 0.5` => spam/threat

## 2. FastAPI Runtime

The current API surface in `api.py` is:

### `GET /`
Serves the built-in dashboard HTML:
- returns `index.html`

This is not a JSON health endpoint anymore.

### `POST /predict`
Accepts:
```json
{
  "email_text": "string"
}
```

Returns:
```json
{
  "is_spam": true,
  "confidence_score": 0.96,
  "bec_flags": {
    "persona_impersonation": 1,
    "victim_isolation": 1,
    "urgency_engagement": 1,
    "bank_manipulation": 1,
    "evasion_cleanup": 0,
    "credential_phishing": 0
  }
}
```

### `GET /sync-inbox`
Current behavior:
- authenticates with Gmail if available
- fetches unread inbox messages
- skips emails already cached in `processed_emails.csv`
- runs preprocessing and model inference
- stores:
  - `body_text`
  - `body_html`
  - spam flag
  - confidence
  - BEC flags
  - date
  - processed timestamp

If Gmail is unavailable or sync fails, it falls back to returning the in-memory/cached email list.

### `POST /delete-email/{email_id}`
Current behavior:
- trashes the Gmail message using the Gmail API
- removes it from `processed_emails`
- rewrites `processed_emails.csv`

### `POST /feedback`
Accepts:
```json
{
  "email_text": "string",
  "correct_label": 0
}
```

Current behavior:
- appends raw CSV rows to `user_feedback_log.csv`

Important note:
- this file format does **not** currently match what `future_scope/retrain.py` expects.

## 3. Gmail Integration

`gmail_service.py` handles:
- OAuth2 authentication with `credentials.json` and `token.json`
- token refresh
- unread inbox fetch from Gmail
- recursive MIME traversal
- extraction of:
  - sender
  - subject
  - plain text body
  - HTML body
  - sent date
- trashing a selected message

### Gmail scopes
The code currently uses:
- `https://www.googleapis.com/auth/gmail.modify`

That gives read/modify permissions for inbox sync and trash operations.

## 4. Frontends

### A. Built-in HTML frontend
File:
- `index.html`

Served by:
- `http://localhost:8000/`

Current UI structure:
- left sidebar with sync button and counters
- middle inbox list with `Safe Inbox` and `Spam` tabs
- right detail panel with:
  - banner analysis
  - message id
  - sender
  - subject
  - body
  - action button

This is now the closest UI to the API runtime because it is shipped directly by `api.py`.

### B. React frontend
Folder:
- `guardian-ui/`

Stack:
- React
- TypeScript
- Vite
- DOMPurify
- lucide-react

Current state:
- code updated to use explicit React structure and plain CSS classes
- backend integration points preserved
- build and lint are passing

Backend URL used by default:
- `http://localhost:8000`

Override support:
- `VITE_API_BASE_URL`

### C. Streamlit frontend
File:
- `future_scope/frontend.py`

Status:
- still present
- not the primary runtime path
- useful mainly as a legacy prototype

## 5. Training and Evaluation

### Training orchestration
`main.py` loads and merges:
- `spam_ham_dataset.csv`
- `BusinessEmail_train.csv`
- `BusinessEmail_test.csv`

The `SpamDetectionSystem` class:
- preprocesses all text
- splits into train/test
- fits tokenizer
- pads sequences
- trains selected model architecture

### Model options
Implemented in `models.py`:
- ANN
- RNN
- LSTM
- BiLSTM

### Important current behavior
There are two training modes implied by the code:

1. Reusable API:
   - `train_model(..., epochs=30, batch_size=32)` defaults to longer training
2. Script entrypoint in `main.py`:
   - currently trains ANN, RNN, and BiLSTM with `epochs=1`
   - saves quick artifacts

So the script block in `main.py` is currently closer to a quick artifact-generation path than a full research retraining run.

### Evaluation
`evaluate.py` currently does two different things:

1. Real evaluation of saved models on `BusinessEmail_test.csv`
2. Synthetic generation of performance curves using hardcoded values

That means:
- confusion matrix and classification report are tied to the real saved model
- `performance_curves.png` is currently illustrative, not pulled from actual training logs

## 6. Present Startup Commands

### Backend
From `code/`:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Built-in HTML dashboard
Open after backend start:
```text
http://localhost:8000
```

### React frontend
From `guardian-ui/`:
```bash
npm run dev
```

Typical local URL:
```text
http://localhost:5173
```
or another Vite port if 5173 is already occupied.

### React production build
From `guardian-ui/`:
```bash
npm run build
npm run preview
```

### Streamlit frontend
From `code/`:
```bash
streamlit run future_scope/frontend.py
```

## 7. Key Files and Their Roles

### Core application
- `api.py` — live backend runtime
- `data_pipeline.py` — preprocessing + heuristics
- `gmail_service.py` — Gmail integration
- `models.py` — network architectures
- `model_base.py` — abstract model contract
- `main.py` — training controller

### UI
- `index.html` — API-served dashboard
- `guardian-ui/src/App.tsx` — React dashboard logic
- `guardian-ui/src/index.css` — React dashboard styling
- `future_scope/frontend.py` — Streamlit UI

### Operations / utility
- `verify_project.py` — project integrity script
- `processed_emails.csv` — cached synced inbox data
- `user_feedback_log.csv` — feedback rows

## 8. Known Limitations

### Feedback and retraining mismatch
Current mismatch:
- `api.py` writes CSV rows without the schema expected by `future_scope/retrain.py`
- `future_scope/retrain.py` expects `text` and `Label` columns

Result:
- retraining is not reliable without schema cleanup

### Startup resilience hides failures
`api.py` catches startup failures while loading:
- model
- tokenizer
- preprocessor

Result:
- the app may still start and serve HTML even if inference artifacts failed to load

### Evaluation is partly illustrative
`evaluate.py` uses hardcoded accuracy/loss points for plot generation.

Result:
- the curves are not guaranteed to reflect the current saved model training history

### Multiple frontends are present
There are three UI surfaces:
- built-in HTML
- React/Vite
- Streamlit

Result:
- documentation and expectations can drift if changes are made in only one frontend

### Verification script is not fully hardened
`verify_project.py` is still useful as a helper, but it is not yet a trustworthy cross-environment health check.

## 9. Recommended Mental Model

If you are onboarding to this repo now, the cleanest way to think about it is:

- **Backend truth** lives in `api.py`, `data_pipeline.py`, `gmail_service.py`, and the saved model/tokenizer artifacts.
- **Primary built-in UI** lives in `index.html` at `localhost:8000`.
- **Primary separate frontend app** lives in `guardian-ui/`.
- **Academic/research assets** still exist and explain why the repo contains multiple models, notebooks, and research claims.
- **Future-scope code** exists, but not all of it is currently production-aligned.

## 10. Next High-Value Improvements

If this project is being actively continued, the highest-value next steps are:

1. Align `/feedback` output with `future_scope/retrain.py` input schema.
2. Decide which frontend is primary:
   - built-in HTML
   - React/Vite
   - Streamlit
3. Add a real JSON health endpoint such as `/health`.
4. Replace simulated evaluation plots with plots from actual training history.
5. Harden startup and sync error reporting so failures are visible to the UI.
