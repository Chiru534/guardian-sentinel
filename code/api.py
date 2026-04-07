from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tensorflow as tf
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
import numpy as np
import os
import csv
import shutil
import subprocess
from data_pipeline import DataPreprocessor
import json
from datetime import datetime

# Email persistence
PROCESSED_EMAILS_CSV = "processed_emails.csv"

def load_processed_emails():
    """Load previously processed emails from CSV with HTML support."""
    if not os.path.exists(PROCESSED_EMAILS_CSV):
        return []
    
    emails = []
    try:
        with open(PROCESSED_EMAILS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                emails.append({
                    "id": row["id"],
                    "sender": row["sender"],
                    "subject": row["subject"],
                    "body_text": row["body_text"],
                    "body_html": row.get("body_html", ""),
                    "is_spam": row["is_spam"].lower() == "true",
                    "confidence": float(row["confidence"]),
                    "bec_flags": json.loads(row["bec_flags"]) if row.get("bec_flags") else {},
                    "date": row.get("date", ""),
                    "processed_at": row.get("processed_at", "")
                })
    except Exception as e:
        print(f"[WARNING] Load error: {e}")
        return []
    return emails

def save_processed_emails(emails):
    """Save processed emails including HTML content."""
    try:
        with open(PROCESSED_EMAILS_CSV, 'w', newline='', encoding='utf-8') as f:
            if emails:
                fieldnames = ["id", "sender", "subject", "body_text", "body_html", "is_spam", "confidence", "bec_flags", "date", "processed_at"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for email in emails:
                    writer.writerow({
                        "id": email["id"],
                        "sender": email["sender"],
                        "subject": email["subject"],
                        "body_text": email["body_text"],
                        "body_html": email.get("body_html", ""),
                        "is_spam": str(email["is_spam"]).lower(),
                        "confidence": str(email["confidence"]),
                        "bec_flags": json.dumps(email["bec_flags"]),
                        "date": email.get("date", ""),
                        "processed_at": email.get("processed_at", datetime.now().isoformat())
                    })
    except Exception as e:
        print(f"[WARNING] Save error: {e}")

# Global state
processed_emails = []

try:
    import gmail_service
    GMAIL_AVAILABLE = True
except ImportError as e:
    GMAIL_AVAILABLE = False

MODEL_PATH = "bilstm_model.h5"
TOKENIZER_PATH = "tokenizer.pickle"
MAX_LENGTH = 50

app = FastAPI(title="Guardian Sentinel Engine", version="1.2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

model = None
tokenizer = None
preprocessor = None

class PredictionRequest(BaseModel):
    email_text: str

class PredictionResponse(BaseModel):
    is_spam: bool
    confidence_score: float
    bec_flags: dict

class FeedbackRequest(BaseModel):
    email_text: str
    correct_label: int

@app.on_event("startup")
def load_artifacts():
    global model, tokenizer, preprocessor, processed_emails
    try:
        preprocessor = DataPreprocessor(stem=False)
        model = tf.keras.models.load_model(MODEL_PATH)
        with open(TOKENIZER_PATH, 'rb') as handle:
            tokenizer = pickle.load(handle)
        processed_emails = load_processed_emails()
        print(f"[READY] Engine online. Loaded {len(processed_emails)} emails.")
    except Exception as e:
        print(f"[CRITICAL] Startup failure: {e}")

@app.on_event("shutdown")
def cleanup():
    if processed_emails:
        save_processed_emails(processed_emails)

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.post("/predict", response_model=PredictionResponse)
async def predict_email(request: PredictionRequest):
    if model is None: raise HTTPException(status_code=503, detail="Offline")
    try:
        bec_flags = preprocessor.engineer_bec_features(request.email_text)
        cleaned_text = preprocessor.preprocess(request.email_text)
        seq = tokenizer.texts_to_sequences([cleaned_text])
        padded = pad_sequences(seq, maxlen=MAX_LENGTH, padding='post')
        score = float(model.predict(padded, verbose=0)[0][0])
        return {"is_spam": score > 0.5, "confidence_score": score, "bec_flags": bec_flags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sync-inbox")
async def sync_live_inbox():
    global processed_emails
    if not GMAIL_AVAILABLE: return processed_emails
    try:
        gmail_svc = gmail_service.authenticate_gmail()
        processed_by_id = {email['id']: email for email in processed_emails}
        emails = gmail_service.fetch_unread_emails(gmail_svc, max_results=20)
        
        new_processed = []
        for email in emails:
            existing = processed_by_id.get(email['id'])
            should_refresh_existing = bool(existing) and (
                not existing.get('body_html') or
                not existing.get('body_text')
            )
            if existing and not should_refresh_existing:
                continue
            
            # Predict using plaintext
            bec_flags = preprocessor.engineer_bec_features(email['body_text'])
            cleaned = preprocessor.preprocess(email['body_text'])
            seq = tokenizer.texts_to_sequences([cleaned])
            padded = pad_sequences(seq, maxlen=MAX_LENGTH, padding='post')
            score = float(model.predict(padded, verbose=0)[0][0])
            
            # Save DUAL format (text for model/search, HTML for premium display)
            processed_email = {
                "id": email['id'],
                "sender": email['sender'],
                "subject": email['subject'],
                "body_text": email['body_text'],
                "body_html": email.get('body_html', ""),
                "is_spam": score > 0.5,
                "confidence": score,
                "bec_flags": bec_flags,
                "date": email.get('date', ''),
                "processed_at": datetime.now().isoformat()
            }

            if existing:
                processed_emails = [e for e in processed_emails if e['id'] != email['id']]
            else:
                new_processed.append(processed_email)

            processed_emails.append(processed_email)
            processed_by_id[email['id']] = processed_email

        if new_processed or any(not e.get('body_html') for e in processed_emails):
            save_processed_emails(processed_emails)
        return processed_emails
    except Exception as e:
        print(f"[SYNC ERROR] {e}")
        return processed_emails

@app.post("/delete-email/{email_id}")
async def delete_threat_email(email_id: str):
    global processed_emails
    if not GMAIL_AVAILABLE: raise HTTPException(status_code=503, detail="Offline")
    try:
        service = gmail_service.authenticate_gmail()
        if gmail_service.trash_email(service, msg_id=email_id):
            processed_emails = [e for e in processed_emails if e['id'] != email_id]
            save_processed_emails(processed_emails)
            return {"status": "deleted"}
        raise HTTPException(status_code=500, detail="Failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def log_feedback(request: FeedbackRequest):
    try:
        with open("user_feedback_log.csv", mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([request.email_text.replace('\n', ' '), request.correct_label])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
