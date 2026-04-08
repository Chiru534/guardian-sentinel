# Project Context: Guardian Sentinel

## Executive Summary
Guardian Sentinel is a final-year project focused on detecting phishing emails and Business Email Compromise (BEC) attacks through a hybrid AI pipeline. The project combines:

- a Python/TensorFlow detection backend
- a Gmail ingestion layer
- heuristic BEC signal extraction
- a FastAPI runtime for inference and inbox operations
- a React dashboard for visualization and review

At its current stage, the project is best understood as a complete academic system with both research and application layers. It is strong enough to be presented as a full final-year project because it covers:

- problem definition
- dataset handling and preprocessing
- model training and evaluation
- runtime inference
- frontend integration
- Gmail-based real-world workflow
- explainable threat analysis

It should be positioned as an academic prototype with practical implementation, rather than as a fully production-hardened commercial product.

## Project Identity

### Project title
Guardian Sentinel: Hybrid Deep Learning Framework for Phishing and Business Email Compromise Detection

### Project domain
- Cybersecurity
- Natural Language Processing
- Deep Learning
- Intelligent Email Threat Detection

### Project type
Final-year academic project with full-stack implementation and machine learning integration.

## Core Problem
Traditional spam filters often fail to detect sophisticated phishing and BEC emails because many of these messages look like legitimate business communication. Attackers frequently use:

- urgency
- impersonation of executives or partners
- confidential language
- payment redirection requests
- credential theft language

The project solves this by combining sequence-based text classification with rule-based explainability.

## What the Project Does
Guardian Sentinel can:

- classify email text as safe or suspicious
- assign a confidence score
- detect BEC-related behavioral signals
- synchronize emails from Gmail
- cache processed results for faster reloads
- display messages in a security dashboard
- let the user inspect threat details
- allow suspicious emails to be deleted from Gmail
- record user feedback for future model improvement

## High-Level Architecture

### 1. Input Layer
Input can come from:

- direct API prediction requests
- Gmail inbox synchronization
- cached processed email records

### 2. Preprocessing Layer
The preprocessing pipeline in `data_pipeline.py` performs:

- lowercase normalization
- regex-based cleanup
- tokenization
- stopword removal
- optional stemming

### 3. Heuristic Explainability Layer
The heuristic layer extracts BEC-oriented flags such as:

- `persona_impersonation`
- `victim_isolation`
- `urgency_engagement`
- `bank_manipulation`
- `evasion_cleanup`
- `credential_phishing`

These help explain why an email may be suspicious.

### 4. Neural Detection Layer
The deployed inference runtime uses:

- `bilstm_model.h5`
- `tokenizer.pickle`
- max sequence length of `50`

The model predicts a confidence score, and the current threshold is:

- `score > 0.5` => threat / spam

### 5. Backend Runtime Layer
The FastAPI application in `api.py` handles:

- model loading
- email prediction
- Gmail profile lookup
- inbox sync
- threat deletion
- feedback logging
- cache reset

### 6. Frontend Layer
The main interactive UI is the React application in `guardian-ui/`. It provides:

- Safe Inbox view
- Spam view
- detail panel for selected email
- Gmail profile panel
- project counters
- sync scope controls
- analytics overview
- threat export support

## Repository Layout

### Core backend
- `api.py` - live FastAPI runtime
- `data_pipeline.py` - text preprocessing and BEC heuristics
- `gmail_service.py` - Gmail OAuth, fetch, parsing, and delete support
- `models.py` - ANN, RNN, LSTM, Bi-LSTM model definitions
- `model_base.py` - common model interface
- `main.py` - training workflow

### Frontend
- `guardian-ui/src/App.tsx` - main React dashboard logic
- `guardian-ui/src/components/EmailDetail.tsx` - detail panel
- `guardian-ui/src/components/SafeHTMLContent.tsx` - sanitized HTML renderer
- `guardian-ui/src/types/email.ts` - email normalization and helpers

### Evaluation and research
- `evaluate.py`
- `RESEARCH.md`
- `README.md`
- model artifacts and notebook-derived files

### Legacy or secondary UI assets
- `index.html` - backend-served HTML dashboard
- `future_scope/frontend.py` - Streamlit prototype

## Main Features Present in the Project

### Detection features
- phishing/spam prediction
- BEC indicator extraction
- confidence scoring
- threat/safe classification

### Backend features
- REST API with FastAPI
- processed email caching through CSV
- Gmail-based live sync
- Gmail profile retrieval
- delete-to-trash action for threats
- feedback logging

### Frontend features
- modern email security dashboard
- split Safe / Spam inbox experience
- selected email analysis panel
- profile and sync status display
- project-level counters
- cache-aware reload behavior
- threat export support
- overview analytics tab

### Research and evaluation features
- multiple model architectures for comparison
- training pipeline
- tokenizer generation
- confusion matrix generation
- performance curve generation

## Runtime Flow

### Backend startup
On startup, the backend:

1. creates the text preprocessor
2. loads the saved Bi-LSTM model
3. loads the tokenizer
4. loads cached processed emails from CSV

### Predict flow
When `/predict` is called:

1. email text is cleaned
2. heuristic BEC flags are extracted
3. text is tokenized and padded
4. the model predicts a score
5. the API returns verdict, confidence, and flags

### Gmail sync flow
When `/sync-inbox` is called:

1. Gmail OAuth credentials are loaded
2. the selected mailbox scope is fetched
3. text and HTML bodies are extracted where available
4. the model runs on the message body
5. processed email objects are cached and returned

## Presentation Positioning
For college presentation purposes, the project should be described as:

"An AI-based email threat detection system that combines deep learning, explainable heuristics, Gmail integration, and a dashboard interface for phishing and Business Email Compromise analysis."

This is appropriate as a full final-year project because it includes:

- end-to-end implementation
- research backing
- model logic
- API integration
- UI layer
- real-world data flow

It should not be presented as a fully enterprise-ready deployed security product. A better and more accurate description is:

- full academic project
- practical prototype
- deployable research system

## Current Strengths

### Academic strength
- clear cybersecurity problem statement
- machine learning and NLP relevance
- explainability through heuristics
- multiple implemented architectures
- evaluation outputs included

### Technical strength
- real backend/frontend separation
- Gmail integration
- persistent cached state
- actionable UI
- deployable inference path

### Presentation strength
- visually strong dashboard
- clear safe vs threat workflow
- easy to explain architecture
- good report and PPT potential

## Current Limitations
The project is strong for academic presentation, but a few limitations should be acknowledged honestly:

- the backend root path does not fully serve the built React static assets
- startup failures in the backend are logged but not always surfaced as hard failures
- some cached emails may preserve stale analysis until refreshed
- the feedback logging path is not yet aligned with retraining logic
- evaluation assets and runtime assets still coexist in the same repository
- there are multiple UI surfaces, which increases maintenance drift

These do not make the project weak as a college submission, but they do matter if the project is described as production-grade software.

## Recommended Demo Path
For the most reliable college presentation:

1. run the FastAPI backend on port `8000`
2. run the React frontend through Vite, usually on `5173`
3. use the React dashboard as the main presentation UI
4. show one safe email and one threat email
5. explain the confidence score and BEC flags
6. show confusion matrix and performance curves as evaluation evidence

## Best One-Line Summary
Guardian Sentinel is a hybrid deep learning based phishing and BEC email detection system with Gmail integration, explainable threat analysis, and a full-stack dashboard suitable for final-year academic presentation.

