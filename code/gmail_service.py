import os.path
import base64
import socket
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
SYNC_SCOPE_VALUES = (
    'read',
    'unread',
    'inbox',
    'sent',
    'archived',
    'trash_spam',
    'all',
)


def authenticate_gmail(allow_interactive=True):
    """
    [Phase 1 Authentication] 
    Handles OAuth2 flow, token storage, and automatic refreshing.
    Requires 'credentials.json' from Google Cloud Console.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    token_was_updated = False

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("[LOG] Refreshing expired Gmail API token...")
                creds.refresh(Request())
                token_was_updated = True
            except Exception as refresh_error:
                print(f"[WARNING] Token refresh failed: {refresh_error}")
                creds = None
                # Auto-delete the stale token so the next restart triggers a clean OAuth flow
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                    print(
                        f"[CLEANUP] Removed stale {TOKEN_FILE}. Restart the server to re-authenticate.")

        if not creds or not creds.valid:
            if not allow_interactive:
                raise RuntimeError(
                    "Gmail authorization requires an interactive login. "
                    "Run the backend once in an interactive terminal to complete OAuth."
                )

            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"CRITICAL: '{CREDENTIALS_FILE}' not found. Download it from Google Cloud Console.")

            print("[LOG] Starting new OAuth2 Authentication Flow...")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            try:
                creds = flow.run_local_server(port=0)
            except OSError as local_server_error:
                if getattr(local_server_error, "winerror", None) == 10013 or isinstance(local_server_error, socket.error):
                    print(
                        "[WARNING] Local OAuth callback server failed. Falling back to manual console auth.")
                    if not hasattr(flow, "run_console"):
                        raise RuntimeError(
                            "Local OAuth callback server could not start and console authentication is unavailable in this library version."
                        ) from local_server_error
                    creds = flow.run_console(
                        authorization_prompt_message=(
                            "Open this URL in your browser, authorize Gmail access, then paste the verification code here:\n{url}\n"
                        ),
                        authorization_code_message="Enter the authorization code: ",
                    )
                else:
                    raise
            token_was_updated = True

    if creds and (token_was_updated or not os.path.exists(TOKEN_FILE)):
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            print(f"[SUCCESS] Token saved to {TOKEN_FILE}")

    return build('gmail', 'v1', credentials=creds)


def get_gmail_profile(service):
    """Return the connected Gmail profile metadata."""
    try:
        return service.users().getProfile(userId='me').execute()
    except HttpError as error:
        print(f"[ERROR] Unable to fetch Gmail profile: {error}")
        return None


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


def _get_scope_requests(scope):
    if scope == 'read':
        return [{"query": "-label:UNREAD"}]
    if scope == 'unread':
        return [{"label_ids": ["UNREAD"]}]
    if scope == 'inbox':
        return [{"label_ids": ["INBOX"]}]
    if scope == 'sent':
        return [{"label_ids": ["SENT"]}]
    if scope == 'archived':
        return [{"query": "-label:INBOX -label:SENT -label:SPAM -label:TRASH -label:DRAFT"}]
    if scope == 'trash_spam':
        return [{"label_ids": ["TRASH"]}, {"label_ids": ["SPAM"]}]
    if scope == 'all':
        return [{}]
    raise ValueError(f"Unsupported sync scope: {scope}")


def _list_message_refs(service, label_ids=None, query=None, limit=None):
    refs = []
    seen_ids = set()
    page_token = None

    while True:
        request_args = {
            "userId": "me",
            "maxResults": 500,
        }
        if label_ids:
            request_args["labelIds"] = label_ids
        if query:
            request_args["q"] = query
        if page_token:
            request_args["pageToken"] = page_token

        results = service.users().messages().list(**request_args).execute()
        for message in results.get('messages', []):
            message_id = message.get('id')
            if not message_id or message_id in seen_ids:
                continue

            seen_ids.add(message_id)
            refs.append({"id": message_id})
            if limit is not None and len(refs) >= limit:
                return refs

        page_token = results.get('nextPageToken')
        if not page_token:
            break

    return refs


def fetch_emails(service, scope='unread', limit=None):
    """
    Fetch Gmail messages for the selected mailbox scope.
    """
    try:
        message_refs = []
        seen_ids = set()

        for request in _get_scope_requests(scope):
            refs = _list_message_refs(
                service,
                label_ids=request.get("label_ids"),
                query=request.get("query"),
                limit=None if limit is None else max(
                    limit - len(message_refs), 0),
            )
            for ref in refs:
                if ref['id'] in seen_ids:
                    continue

                seen_ids.add(ref['id'])
                message_refs.append(ref)
                if limit is not None and len(message_refs) >= limit:
                    break

            if limit is not None and len(message_refs) >= limit:
                break

        if not message_refs:
            print(f"[LOG] No Gmail messages found for scope '{scope}'.")
            return []

        print(
            f"[LOG] Fetching content for {len(message_refs)} messages from scope '{scope}'...")
        email_data = []

        for msg in message_refs:
            full_msg = service.users().messages().get(
                userId='me', id=msg['id']).execute()
            payload = full_msg.get('payload', {})
            headers = payload.get('headers', [])
            date_sent = next(
                (h['value'] for h in headers if h['name'].lower() == 'date'), "")
            subject = next(
                (h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
            sender = next(
                (h['value'] for h in headers if h['name'].lower() == 'from'), "Unknown Sender")

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


def fetch_unread_emails(service, max_results=20):
    """
    [Targeted Fetching] 
    Interface with Gmail API to retrieve unread inbox messages.
    """
    return fetch_emails(service, scope='unread', limit=max_results)


def trash_email(service, user_id='me', msg_id=None):
    """Moves email to Trash."""
    try:
        if not msg_id:
            return None
        return service.users().messages().trash(userId=user_id, id=msg_id).execute()
    except Exception as error:
        print(f"Trash error: {error}")
        return None


if __name__ == '__main__':
    try:
        svc = authenticate_gmail()
        emails = fetch_unread_emails(svc, max_results=3)
        for e in emails:
            print(
                f"Subject: {e['subject']} | HTML Length: {len(e['body_html'])}")
    except Exception as ex:
        print(f"Error: {ex}")
