from fastapi import FastAPI
app = FastAPI()

@app.get("/sync-inbox")
def sync():
    return [
        {
            "id": "msg_safe_001",
            "sender": "boss@business.com",
            "subject": "Quarterly Update Meeting",
            "body_text": "Team, please find the quarterly results attached. Let's meet at 10 AM.",
            "is_spam": False,
            "confidence": 0.02,
            "bec_flags": {}
        },
        {
            "id": "msg_threat_666",
            "sender": "ceo-office@company.co",
            "subject": "URGENT: Confidential Wire Transfer Required",
            "body_text": "I am in a meeting. Transfer $50,000 to the attached bank account.",
            "is_spam": True,
            "confidence": 0.985,
            "bec_flags": ["Urgency Engagement", "Bank Manipulation"]
        }
    ]

@app.post("/delete-email/{email_id}")
def delete(email_id: str):
    return {"status": "deleted", "id": email_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
