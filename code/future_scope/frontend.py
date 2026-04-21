import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION (Phase 3: The Guardian Interface) ---
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Guardian Sentinel | AI Unified Inbox",
    page_icon="🛡️",
    layout="wide"
)

# --- CUSTOM CSS: Modern Enterprise Security UI ---
st.markdown("""
<style>
    .main {
        background: #f8f9fa;
    }
    .email-card {
        padding: 1rem;
        background: white;
        border-radius: 8px;
        border-left: 5px solid #6c5ce7;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .email-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .quarantine-card {
        border-left: 5px solid #d63031;
    }
    .sidebar-brand {
        font-size: 1.5rem;
        font-weight: bold;
        color: #6c5ce7;
        padding-bottom: 2rem;
    }
    .bec-flag {
        background: #ffeaa7;
        color: #d63031;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 5px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE SESSION STATE ---
if 'emails' not in st.session_state:
    st.session_state.emails = []
if 'current_view' not in st.session_state:
    st.session_state.current_view = "Safe Inbox"
if 'selected_email' not in st.session_state:
    st.session_state.selected_email = None

def sync_inbox():
    """Fetches live Gmail streams through our Bi-LSTM + BEC Backend API."""
    with st.spinner("Synchronizing with Gmail API & running AI Scanning..."):
        try:
            response = requests.post(
                f"{API_BASE_URL}/sync-inbox",
                json={"scope": "unread"},
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                # Handle both legacy (list) and new (dict with 'emails' key) response formats
                if isinstance(data, list):
                    st.session_state.emails = data
                else:
                    st.session_state.emails = data.get("emails", [])
                st.session_state.selected_email = None
                st.success(f"Successfully synced {len(st.session_state.emails)} messages.")
            else:
                st.error(f"Backend Retrieval Error: {response.text}")
        except Exception as e:
            st.error(f"Network Connection Failed: {e}")

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<div class='sidebar-brand'>🛡️ Guardian Sentinel</div>", unsafe_allow_html=True)
    
    if st.button("🔄 Sync Live Inbox", use_container_width=True):
        sync_inbox()
    
    st.divider()
    
    st.session_state.current_view = st.radio(
        "Navigation",
        ["Safe Inbox", "Spam"],
        label_visibility="collapsed"
    )
    
    st.divider()
    if st.session_state.emails:
        safe_count = len([e for e in st.session_state.emails if not e['is_spam']])
        threat_count = len([e for e in st.session_state.emails if e['is_spam']])
        st.metric("Total Emails Sync'd", len(st.session_state.emails))
        st.metric("Safe Emails", safe_count)
        st.metric("Threats Detected", threat_count, delta_color="inverse")

# --- MASTER-DETAIL LAYOUT ---
col_master, col_detail = st.columns([1, 2])

# A. Master List View (Left Column)
with col_master:
    # Filter the emails based on the AI verdict and current view from sidebar
    if st.session_state.current_view == "Safe Inbox":
        display_list = [e for e in st.session_state.emails if not e.get('is_spam')]
        header_text = "📥 Non-Spam Messages"
    else:
        display_list = [e for e in st.session_state.emails if e.get('is_spam')]
        header_text = "🛡️ Spam Threats"
    
    # Display the filtered list
    st.subheader(header_text)
    
    if not display_list:
        st.info("No emails to display in this view. Use 'Sync' to fetch updates.")
    else:
        for idx, mail in enumerate(display_list):
            if st.button(f"✉️ {mail['subject'][:50]}...", key=f"email_{mail['id']}_{idx}", use_container_width=True):
                st.session_state.selected_email = mail
                st.rerun()

# B. Detail Reading Pane (Right Column)
with col_detail:
    if st.session_state.selected_email:
        mail = st.session_state.selected_email
        
        # 1. Threat Warning Header (EXPLAINABLE AI)
        if mail['is_spam']:
            st.error("🚨 **BEC ATTACK DETECTED**")
            st.markdown(f"""
            This email has been moved to Quarantine. The **Bi-LSTM Neural Engine** identified malicious intent 
            pattern with **{mail['confidence']:.1%} confidence**.
            """)
            
            # Display Triggered Heuristics
            if mail.get('bec_flags'):
                st.markdown("#### Triggered AI Security Flags:")
                # Handle دونوں ڈکشنری اور لسٹ فارمیٹ
                flags = mail['bec_flags']
                if isinstance(flags, dict):
                    for flag, active in flags.items():
                        if active:
                            st.markdown(f"<span class='bec-flag'>🚩 {flag.replace('_', ' ').title()}</span>", unsafe_allow_html=True)
                elif isinstance(flags, list):
                    for flag in flags:
                        st.markdown(f"<span class='bec-flag'>🚩 {flag.replace('_', ' ').title()}</span>", unsafe_allow_html=True)
            st.divider()

        # 2. Standard Header Metadata
        st.caption(f"Message ID: {mail['id']}")
        st.title(mail['subject'])
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**From:** {mail['sender']}")
        with c2:
            st.write(f"Scanned: {mail['confidence']:.0%}")
        
        st.divider()
        
        # 3. Body Text (The "Email Body")
        st.markdown("##### Message Content")
        st.text(mail['body_text'])
        
        st.divider()
        
        # 4. Action Bar
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            if st.button("✅ Mark as Safe", use_container_width=True):
                st.toast("Success: Email marked as legitimate.")
        with btn_col2:
            if mail['is_spam']:
                # Phase 4 Automation Loop
                if st.button("🗑️ Confirm Threat & Delete from Gmail", type="primary", use_container_width=True):
                    try:
                        res = requests.post(f"{API_BASE_URL}/delete-email/{mail['id']}")
                        if res.status_code == 200:
                            st.session_state.emails = [e for e in st.session_state.emails if e['id'] != mail['id']]
                            st.session_state.selected_email = None
                            st.success("Neutralized: Threat moved to Gmail Trash.")
                            st.rerun()
                        else:
                            st.error("Action Failed Check API.")
                    except Exception as e:
                        st.error(f"Network error: {e}")
            else:
                if st.button("🗑️ Archive", use_container_width=True):
                    st.toast("Email archived locally.")
    else:
        # Default Empty State for Reading Pane
        st.write("")
        st.write("")
        st.write("")
        st.image("https://img.icons8.com/clouds/200/security-checked.png")
        st.markdown("<h3 style='text-align: center; color: #636e72;'>Guardian Sentinel: Select an email to scan</h3>", unsafe_allow_html=True)

st.caption("Advanced AI Webmail Prototype | Phase 3 Interface Rollout | Secure MLOps System")
