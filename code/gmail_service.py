import os.path
import base64
import re
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CONFIGURATION & SCOPES ---
# If modifying these scopes, delete the file token.json.
# .modify allows reading, marking as read, and modifying labels (quarantine).
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def authenticate_gmail():
    """
    [Phase 1 Authentication] 
    Handles OAuth2 flow, token storage, and automatic refreshing.
    Requires 'credentials.json' from Google Cloud Console.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[LOG] Refreshing expired Gmail API token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(f"CRITICAL: '{CREDENTIALS_FILE}' not found. Download it from Google Cloud Console.")
            
            print("[LOG] Starting new OAuth2 Authentication Flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print(f"[SUCCESS] Token saved to {TOKEN_FILE}")

    return build('gmail', 'v1', credentials=creds)

def clean_html_for_ai(html_content):
    """
    [Sanitization for AI] 
    Extracts plaintext for Bi-LSTM inference.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def decode_part_body(service, message_id, part_body):
    """
    Gmail can return either inline `data` or an `attachmentId` for large MIME parts.
    This helper normalizes both cases into a decoded string.
    """
    data = part_body.get('data')
    if data:
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

    attachment_id = part_body.get('attachmentId')
    if service and message_id and attachment_id:
        attachment = service.users().messages().attachments().get(
            userId='me',
            messageId=message_id,
            id=attachment_id
        ).execute()
        attachment_data = attachment.get('data')
        if attachment_data:
            return base64.urlsafe_b64decode(attachment_data).decode('utf-8', errors='replace')

    return ""

def extract_body_dual(service, message_id, payload):
    """
    [Dual Extraction] 
    Returns a dictionary containing:
    - 'text': Pure text for the neural network.
    - 'html': Original HTML structure for the premium UI.
    """
    result = {"text": "", "html": ""}
    
    # helper for recursive traversal
    def traverse(p):
        mime_type = p.get('mimeType')
        part_body = p.get('body', {})
        decoded_content = decode_part_body(service, message_id, part_body)
        
        if mime_type == 'text/plain' and decoded_content:
            result["text"] += decoded_content
        elif mime_type == 'text/html' and decoded_content:
            decoded_html = decoded_content
            result["html"] += decoded_html
            # If we don't have text yet, clean this HTML for the text version
            if not result["text"]:
                result["text"] = clean_html_for_ai(decoded_html)
        
        if 'parts' in p:
            for part in p['parts']:
                traverse(part)

    traverse(payload)
    return result

def fetch_unread_emails(service, max_results=20):
    """
    [Targeted Fetching] 
    Interface with Gmail API to retrieve unread inbox messages.
    """
    try:
        results = service.users().messages().list(
            userId='me', 
            labelIds=['INBOX', 'UNREAD'], 
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        email_data = []

        if not messages:
            print("[LOG] No new unread emails found.")
            return []

        print(f"[LOG] Fetching content for {len(messages)} messages...")

        for msg in messages:
            full_msg = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = full_msg.get('payload')
            headers = payload.get('headers')
            date_sent = next((h['value'] for h in headers if h['name'].lower() == 'date'), "")

            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Unknown Sender")

            # Extract both formats
            dual_body = extract_body_dual(service, msg['id'], payload)

            email_data.append({
                "id": msg['id'],
                "sender": sender,
                "subject": subject,
                "body_text": dual_body["text"],
                "body_html": dual_body["html"],
                "date": date_sent
            })

        return email_data

    except HttpError as error:
        print(f"[ERROR] An API error occurred: {error}")
        return []

def trash_email(service, user_id='me', msg_id=None):
    """Moves email to Trash."""
    try:
        if not msg_id: return None
        return service.users().messages().trash(userId=user_id, id=msg_id).execute()
    except Exception as error:
        print(f"Trash error: {error}")
        return None

if __name__ == '__main__':
    try:
        svc = authenticate_gmail()
        emails = fetch_unread_emails(svc, max_results=3)
        for e in emails:
            print(f"Subject: {e['subject']} | HTML Length: {len(e['body_html'])}")
    except Exception as ex:
        print(f"Error: {ex}")
