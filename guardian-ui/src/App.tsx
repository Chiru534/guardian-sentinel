import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { RefreshCw, Shield } from 'lucide-react'
import EmailDetail from './components/EmailDetail'
import {
  type Email,
  type RawEmail,
  getPreviewText,
  getSenderDisplay,
  normalizeEmail,
} from './types/email'

type InboxView = 'safe' | 'spam'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const App = () => {
  const [emails, setEmails] = useState<Email[]>([])
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null)
  const [currentView, setCurrentView] = useState<InboxView>('safe')
  const [isSyncing, setIsSyncing] = useState(false)
  const [statusMessage, setStatusMessage] = useState('Connecting to backend...')
  const [loadError, setLoadError] = useState<string | null>(null)
  const hasLoadedOnce = useRef(false)

  const syncInbox = useCallback(async () => {
    setIsSyncing(true)
    setLoadError(null)
    setStatusMessage('Synchronizing inbox...')

    try {
      const response = await fetch(`${API_BASE_URL}/sync-inbox`)
      if (!response.ok) {
        throw new Error(`Sync failed with status ${response.status}`)
      }

      const data = (await response.json()) as RawEmail[]
      const normalized = data.map(normalizeEmail)

      setEmails(normalized)
      setStatusMessage(normalized.length ? `Loaded ${normalized.length} emails.` : 'No emails available right now.')
      setSelectedEmailId((current) => {
        if (normalized.some((email) => email.id === current)) {
          return current
        }
        return normalized[0]?.id ?? null
      })
    } catch (error) {
      console.error('Failed to sync inbox:', error)

      if (!hasLoadedOnce.current) {
        setEmails(MOCK_EMAILS)
        setSelectedEmailId(MOCK_EMAILS[0]?.id ?? null)
      }

      setLoadError('Backend unavailable. Showing demo data.')
      setStatusMessage('Unable to reach backend inbox sync.')
    } finally {
      hasLoadedOnce.current = true
      setIsSyncing(false)
    }
  }, [])

  useEffect(() => {
    void syncInbox()
  }, [syncInbox])

  const safeEmails = useMemo(() => emails.filter((email) => !email.is_spam), [emails])
  const spamEmails = useMemo(() => emails.filter((email) => email.is_spam), [emails])

  const visibleEmails = useMemo(
    () => (currentView === 'safe' ? safeEmails : spamEmails),
    [currentView, safeEmails, spamEmails],
  )

  const selectedEmail = useMemo(
    () => emails.find((email) => email.id === selectedEmailId) ?? visibleEmails[0] ?? null,
    [emails, selectedEmailId, visibleEmails],
  )

  useEffect(() => {
    if (selectedEmail && selectedEmail.id !== selectedEmailId) {
      setSelectedEmailId(selectedEmail.id)
    }
  }, [selectedEmail, selectedEmailId])

  const handleFeedback = async (correctLabel: number) => {
    if (!selectedEmail) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_text: selectedEmail.body_text || selectedEmail.subject,
          correct_label: correctLabel,
        }),
      })

      if (!response.ok) {
        throw new Error(`Feedback failed with status ${response.status}`)
      }

      setStatusMessage(`Feedback recorded for "${selectedEmail.subject}".`)
    } catch (error) {
      console.error('Failed to send feedback:', error)
      setStatusMessage('Unable to record feedback right now.')
    }
  }

  const handleDeleteThreat = async () => {
    if (!selectedEmail) {
      return
    }

    const confirmed = window.confirm(`Delete "${selectedEmail.subject}" from Gmail?`)
    if (!confirmed) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/delete-email/${encodeURIComponent(selectedEmail.id)}`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`Delete failed with status ${response.status}`)
      }

      const remaining = emails.filter((email) => email.id !== selectedEmail.id)
      setEmails(remaining)
      setSelectedEmailId(remaining[0]?.id ?? null)
      setStatusMessage(`Deleted "${selectedEmail.subject}".`)
    } catch (error) {
      console.error('Failed to delete threat:', error)
      setStatusMessage('Threat delete failed. Check backend Gmail permissions.')
    }
  }

  return (
    <div className="guardian-app">
      <div className="guardian-shell">
        <aside className="sidebar-panel">
          <div className="brand-block">
            <div className="brand-row">
              <div className="brand-badge">
                <Shield size={16} />
              </div>
              <h1>Guardian Sentinel</h1>
            </div>
            <p>AI Email Security Center</p>
          </div>

          <button type="button" className="sync-button" onClick={() => void syncInbox()} disabled={isSyncing}>
            <RefreshCw size={16} className={isSyncing ? 'spin-icon' : ''} />
            <span>{isSyncing ? 'Syncing Inbox...' : 'Sync Live Inbox'}</span>
          </button>

          <div className="sidebar-divider" />

          <div className="stats-stack">
            <StatCard value={emails.length} label="Total Emails" tone="cyan" />
            <StatCard value={safeEmails.length} label="Safe Emails" tone="green" />
            <StatCard value={spamEmails.length} label="Threats Detected" tone="red" />
          </div>

          <div className="sidebar-footer">
            <p>{loadError ?? statusMessage}</p>
            <span>Backend: {API_BASE_URL}</span>
          </div>
        </aside>

        <section className="list-panel">
          <div className="tab-header">
            <button
              type="button"
              className={`tab-button ${currentView === 'safe' ? 'active' : ''}`}
              onClick={() => setCurrentView('safe')}
            >
              Safe Inbox
            </button>
            <button
              type="button"
              className={`tab-button ${currentView === 'spam' ? 'active' : ''}`}
              onClick={() => setCurrentView('spam')}
            >
              Spam
            </button>
          </div>

          <div className="message-list">
            {visibleEmails.length ? (
              visibleEmails.map((email) => (
                <button
                  key={email.id}
                  type="button"
                  className={`message-card ${selectedEmail?.id === email.id ? 'active' : ''}`}
                  onClick={() => setSelectedEmailId(email.id)}
                >
                  <div className="message-card-top">
                    <div className="message-icons">
                      <span className="message-check" />
                      <span className="message-star">★</span>
                    </div>
                    <div className="message-main">
                      <div className="message-sender">{getSenderDisplay(email.sender)}</div>
                      <div className="message-subject">{email.subject}</div>
                      <div className="message-preview">{getPreviewText(email)}</div>
                    </div>
                    <div className={`message-badge ${email.is_spam ? 'threat' : 'safe'}`}>
                      {email.is_spam ? 'Threat' : 'Safe'}
                    </div>
                  </div>
                </button>
              ))
            ) : (
              <div className="empty-list-state">No emails available in this view.</div>
            )}
          </div>
        </section>

        <section className="detail-panel">
          <EmailDetail
            email={selectedEmail}
            onMarkSafe={() => void handleFeedback(0)}
            onDeleteThreat={() => void handleDeleteThreat()}
          />
        </section>
      </div>
    </div>
  )
}

interface StatCardProps {
  value: number
  label: string
  tone: 'cyan' | 'green' | 'red'
}

const StatCard = ({ value, label, tone }: StatCardProps) => (
  <div className="stat-card">
    <div className={`stat-value ${tone}`}>{value}</div>
    <div className="stat-label">{label}</div>
  </div>
)

const MOCK_EMAILS: Email[] = [
  {
    id: 'demo-safe-1',
    sender: 'Salesforce Webinars <events@salesforce.com>',
    subject: 'Build Intelligent Enterprises: How MuleSoft Powers Agentic Transformation',
    body_text: 'The on-demand recording is now available.',
    body_html: `
      <div>
        <p>The on-demand recording is now available.</p>
        <p><a href="https://www.salesforce.com/">Watch the replay</a></p>
      </div>
    `,
    date: 'Demo',
    is_spam: false,
    confidence: 0.012,
    bec_flags: {},
  },
  {
    id: 'demo-safe-2',
    sender: 'Cerebras Systems <news@cerebras.ai>',
    subject: 'What Can You Build with Cerebras?',
    body_text: 'Join our Discord and explore the quickstart guides.',
    body_html: `
      <div style="font-family: Arial, sans-serif; line-height: 1.6;">
        <p>Hi there,</p>
        <p>Here are a few ways to get started with Cerebras:</p>
        <ul>
          <li><a href="https://discord.gg/cerebras">Join our Discord</a></li>
          <li><a href="https://github.com/Cerebras">Github Issues</a></li>
          <li><a href="https://www.cerebras.ai/">Explore the docs</a></li>
        </ul>
        <div class="gmail_quote">Sent via Cerebras community update.</div>
      </div>
    `,
    date: 'Demo',
    is_spam: false,
    confidence: 0.085,
    bec_flags: {},
  },
  {
    id: 'demo-threat-1',
    sender: 'CEO Office <payments@secure-wire-now.com>',
    subject: 'URGENT: Process confidential transfer immediately',
    body_text: 'Keep this confidential and process the wire transfer today.',
    body_html: '',
    date: 'Demo',
    is_spam: true,
    confidence: 0.982,
    bec_flags: {
      urgency_engagement: 1,
      bank_manipulation: 1,
      victim_isolation: 1,
    },
  },
]

export default App
