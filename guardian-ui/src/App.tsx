import { useCallback, useEffect, useMemo, useState } from 'react'
import { RefreshCw, Shield } from 'lucide-react'
import { Toaster, toast } from 'react-hot-toast'
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
} from 'recharts'
import EmailDetail from './components/EmailDetail'
import {
  type Email,
  type RawEmail,
  getPreviewText,
  getSenderDisplay,
  normalizeEmail,
} from './types/email'

type InboxView = 'safe' | 'spam'
type SyncScope = 'read' | 'unread' | 'inbox' | 'sent' | 'archived' | 'trash_spam' | 'all'

interface GmailProfile {
  emailAddress: string
  messagesTotal: number
  threadsTotal: number
  historyId?: string
}

interface SyncResponse {
  emails: RawEmail[]
  scope: SyncScope
  project_count: number
  fetched_count: number
  removed_count: number
  analyzed_count: number
  reused_count: number
  profile: GmailProfile | null
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const EMAIL_CACHE_KEY = 'guardian_emails_cache'
const SELECTED_EMAIL_KEY = 'guardian_selected_email_id'
const INBOX_VIEW_KEY = 'guardian_inbox_view'
const SYNC_SCOPE_KEY = 'guardian_sync_scope'
const LOADED_SYNC_SCOPE_KEY = 'guardian_loaded_sync_scope'
const SAFE_CHART_COLOR = '#00f2ff'
const THREAT_CHART_COLOR = '#ff004c'
const SYNC_TIMEOUT_MS = 120000

const SYNC_SCOPE_OPTIONS: Array<{ value: SyncScope; label: string; description: string }> = [
  { value: 'read', label: 'Already Read', description: 'Only mails that are already marked as read.' },
  { value: 'unread', label: 'Unread Only', description: 'Only mails that are still unread.' },
  { value: 'inbox', label: 'Inbox Mails', description: 'All inbox mails, read and unread.' },
  { value: 'sent', label: 'Sent Mails', description: 'Messages from the Sent mailbox.' },
  { value: 'archived', label: 'Archived Mails', description: 'Messages no longer in Inbox, Sent, Spam, or Trash.' },
  { value: 'trash_spam', label: 'Trash / Spam', description: 'Messages currently in Trash or Spam.' },
  { value: 'all', label: 'All Gmail History', description: 'Everything accessible in the connected Gmail account.' },
]

const getScopeLabel = (scope: SyncScope) =>
  SYNC_SCOPE_OPTIONS.find((option) => option.value === scope)?.label ?? scope

const isSyncScope = (value: string): value is SyncScope =>
  value === 'read' ||
  value === 'unread' ||
  value === 'inbox' ||
  value === 'sent' ||
  value === 'archived' ||
  value === 'trash_spam' ||
  value === 'all'

const normalizeLegacySyncResponse = (payload: RawEmail[] | SyncResponse, fallbackScope: SyncScope): SyncResponse =>
  Array.isArray(payload)
    ? {
        emails: payload,
        scope: fallbackScope,
        project_count: payload.length,
        fetched_count: payload.length,
        removed_count: 0,
        analyzed_count: 0,
        reused_count: payload.length,
        profile: null,
      }
    : payload

const getErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string }
    if (payload?.detail) {
      return payload.detail
    }
  } catch {
    // Fall back to generic HTTP status below.
  }

  return `Request failed with status ${response.status}`
}

const fetchWithTimeout = async (url: string, init: RequestInit, timeoutMs: number) => {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    return await fetch(url, { ...init, signal: controller.signal })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error(`Sync timed out after ${Math.round(timeoutMs / 1000)} seconds. Try a smaller Gmail scope.`)
    }
    throw error
  } finally {
    window.clearTimeout(timeoutId)
  }
}

const SkeletonRow = () => (
  <div className="animate-pulse rounded-xl border border-cyan-500/20 bg-slate-900/70 p-4">
    <div className="flex items-start gap-3">
      <div className="h-10 w-10 rounded-lg bg-slate-700/70" />
      <div className="min-w-0 flex-1 space-y-3">
        <div className="h-3 w-28 rounded bg-slate-700/70" />
        <div className="h-4 w-3/4 rounded bg-slate-600/80" />
        <div className="h-3 w-full rounded bg-slate-700/60" />
      </div>
      <div className="h-8 w-20 rounded-full bg-slate-700/70" />
    </div>
  </div>
)

const EmptyInboxState = () => (
  <div className="flex min-h-[320px] flex-col items-center justify-center rounded-xl border border-cyan-500/20 bg-slate-950/30 px-6 text-center">
    <div className="mb-4 rounded-full border border-cyan-500/30 bg-cyan-500/10 p-4 text-cyan-300">
      <Shield size={28} />
    </div>
    <h3 className="text-xl font-semibold text-white">Perimeter Secure: No threats detected.</h3>
    <p className="mt-2 max-w-md text-sm text-slate-400">
      Your monitored inbox is currently clear. New messages will appear here as soon as they are synced.
    </p>
  </div>
)

const App = () => {
  const [emails, setEmails] = useState<Email[]>([])
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null)
  const [currentView, setCurrentView] = useState<InboxView>('safe')
  const [selectedSyncScope, setSelectedSyncScope] = useState<SyncScope>('unread')
  const [isSyncing, setIsSyncing] = useState(false)
  const [statusMessage, setStatusMessage] = useState('Connecting to backend...')
  const [loadError, setLoadError] = useState<string | null>(null)
  const [gmailProfile, setGmailProfile] = useState<GmailProfile | null>(null)
  const [lastSyncSummary, setLastSyncSummary] = useState<Omit<SyncResponse, 'emails' | 'profile'> | null>(null)
  const [activeTab, setActiveTab] = useState<'inbox' | 'overview'>('inbox')
  const [loadedSyncScope, setLoadedSyncScope] = useState<SyncScope>('unread')

  const persistRawEmails = useCallback((data: RawEmail[]) => {
    localStorage.setItem(EMAIL_CACHE_KEY, JSON.stringify(data))
  }, [])

  const applyEmails = useCallback(
    (data: RawEmail[], preferredEmailId?: string | null) => {
      const normalized = data.map(normalizeEmail)
      setEmails(normalized)
      setSelectedEmailId((current) => {
        const candidate = preferredEmailId ?? current
        if (candidate && normalized.some((email) => email.id === candidate)) {
          return candidate
        }
        return normalized[0]?.id ?? null
      })
    },
    [],
  )

  const fetchLocalInbox = useCallback(
    async (background = false) => {
      if (!background) {
        setIsSyncing(true)
        setStatusMessage('Reading security archives...')
      }

      setLoadError(null)

      try {
        const response = await fetch(`${API_BASE_URL}/emails`)
        if (!response.ok) {
          throw new Error(`Local fetch failed: ${response.status}`)
        }

        const data = (await response.json()) as RawEmail[]
        persistRawEmails(data)
        applyEmails(data)
        setStatusMessage(data.length ? 'Ready.' : 'Archives empty. Please Sync Live Inbox.')
      } catch (error) {
        console.error('Failed to fetch local inbox:', error)
        setLoadError('Backend offline. Showing cached/mock data.')
      } finally {
        if (!background) {
          setIsSyncing(false)
        }
      }
    },
    [applyEmails, persistRawEmails],
  )

  const fetchGmailProfile = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/gmail-profile`)
      if (!response.ok) {
        throw new Error(await getErrorMessage(response))
      }

      const payload = (await response.json()) as { profile?: GmailProfile | null }
      setGmailProfile(payload.profile ?? null)
    } catch (error) {
      console.error('Failed to fetch Gmail profile:', error)
      setGmailProfile(null)
    }
  }, [])

  const syncInbox = useCallback(async () => {
    setIsSyncing(true)
    setLoadError(null)
    setStatusMessage(`Synchronizing ${getScopeLabel(selectedSyncScope)} from Gmail...`)

    try {
      let response = await fetchWithTimeout(
        `${API_BASE_URL}/sync-inbox`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            scope: selectedSyncScope,
          }),
        },
        SYNC_TIMEOUT_MS,
      )

      if (response.status === 404 || response.status === 405) {
        response = await fetchWithTimeout(`${API_BASE_URL}/sync-inbox`, {}, SYNC_TIMEOUT_MS)
      }

      if (!response.ok) {
        throw new Error(await getErrorMessage(response))
      }

      const payload = (await response.json()) as RawEmail[] | SyncResponse
      const data = normalizeLegacySyncResponse(payload, selectedSyncScope)
      persistRawEmails(data.emails)
      applyEmails(data.emails)
      setGmailProfile(data.profile)
      setLoadedSyncScope(data.scope)
      setLastSyncSummary({
        scope: data.scope,
        project_count: data.project_count,
        fetched_count: data.fetched_count,
        removed_count: data.removed_count,
        analyzed_count: data.analyzed_count,
        reused_count: data.reused_count,
      })
      setStatusMessage(
        `Synced ${data.fetched_count} mails from ${getScopeLabel(data.scope)}. Queue: ${data.project_count}. Removed: ${data.removed_count}.`,
      )
    } catch (error) {
      console.error('Failed to sync inbox:', error)
      setGmailProfile(null)
      setLoadError(error instanceof Error ? error.message : 'Unable to reach backend inbox sync.')
    } finally {
      setIsSyncing(false)
    }
  }, [applyEmails, persistRawEmails, selectedSyncScope])

  useEffect(() => {
    const cached = localStorage.getItem(EMAIL_CACHE_KEY)
    const cachedSelectedEmailId = localStorage.getItem(SELECTED_EMAIL_KEY)
    const cachedInboxView = localStorage.getItem(INBOX_VIEW_KEY)
    const cachedSyncScope = localStorage.getItem(SYNC_SCOPE_KEY)

    if (cachedInboxView === 'safe' || cachedInboxView === 'spam') {
      setCurrentView(cachedInboxView)
    }

    if (cachedSyncScope && isSyncScope(cachedSyncScope)) {
      setSelectedSyncScope(cachedSyncScope)
    }

    const cachedLoadedScope = localStorage.getItem(LOADED_SYNC_SCOPE_KEY)
    if (cachedLoadedScope && isSyncScope(cachedLoadedScope)) {
      setLoadedSyncScope(cachedLoadedScope)
    }

    if (cached) {
      try {
        const data = JSON.parse(cached) as RawEmail[]
        applyEmails(data, cachedSelectedEmailId)
        setStatusMessage('Loaded from local cache.')
        void fetchGmailProfile()
      } catch (error) {
        console.error('Cache corruption:', error)
      }
    }

    void fetchLocalInbox(Boolean(cached))
  }, [applyEmails, fetchGmailProfile, fetchLocalInbox])

  useEffect(() => {
    if (selectedEmailId) {
      localStorage.setItem(SELECTED_EMAIL_KEY, selectedEmailId)
      return
    }

    localStorage.removeItem(SELECTED_EMAIL_KEY)
  }, [selectedEmailId])

  useEffect(() => {
    localStorage.setItem(INBOX_VIEW_KEY, currentView)
  }, [currentView])

  useEffect(() => {
    localStorage.setItem(SYNC_SCOPE_KEY, selectedSyncScope)
  }, [selectedSyncScope])

  useEffect(() => {
    localStorage.setItem(LOADED_SYNC_SCOPE_KEY, loadedSyncScope)
  }, [loadedSyncScope])

  const safeEmails = useMemo(() => emails.filter((email) => !email.is_spam), [emails])
  const spamEmails = useMemo(() => emails.filter((email) => email.is_spam), [emails])

  const visibleEmails = useMemo(
    () => (currentView === 'safe' ? safeEmails : spamEmails),
    [currentView, safeEmails, spamEmails],
  )

  const overviewPieData = useMemo(
    () => [
      { name: 'Safe', value: safeEmails.length },
      { name: 'Threat', value: spamEmails.length },
    ],
    [safeEmails.length, spamEmails.length],
  )

  const topSendersData = useMemo(() => {
    const counts = new Map<string, number>()

    for (const email of emails) {
      const sender = getSenderDisplay(email.sender)
      counts.set(sender, (counts.get(sender) ?? 0) + 1)
    }

    return Array.from(counts.entries())
      .map(([sender, count]) => ({ sender, count }))
      .sort((left, right) => right.count - left.count)
      .slice(0, 4)
  }, [emails])

  const hasThreats = spamEmails.length > 0

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

  const handleResetProjectCache = async () => {
    const confirmed = window.confirm('Clear all cached project emails from the dashboard and backend cache?')
    if (!confirmed) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/cache/reset`, {
        method: 'POST',
      })

      if (!response.ok) {
        if (response.status === 404 || response.status === 405) {
          setEmails([])
          setSelectedEmailId(null)
          setGmailProfile(null)
          setLastSyncSummary(null)
          setLoadedSyncScope(selectedSyncScope)
          localStorage.removeItem(EMAIL_CACHE_KEY)
          localStorage.removeItem(SELECTED_EMAIL_KEY)
          setStatusMessage('Local cache cleared. Restart the backend to enable server cache reset.')
          toast.success('Local cache cleared', {
            style: { background: '#0f172a', color: '#fff' },
          })
          return
        }

        throw new Error(await getErrorMessage(response))
      }

      setEmails([])
      setSelectedEmailId(null)
      setGmailProfile(null)
      setLastSyncSummary(null)
      setLoadedSyncScope(selectedSyncScope)
      localStorage.removeItem(EMAIL_CACHE_KEY)
      localStorage.removeItem(SELECTED_EMAIL_KEY)
      setStatusMessage('Project cache cleared. Run a Gmail sync to repopulate messages.')
      toast.success('Project cache cleared', {
        style: { background: '#0f172a', color: '#fff' },
      })
    } catch (error) {
      console.error('Failed to reset project cache:', error)
      setLoadError(error instanceof Error ? error.message : 'Failed to reset project cache.')
    }
  }

  const exportThreatReport = () => {
    const threatEmails = emails.filter((email) => email.is_spam)

    if (!threatEmails.length) {
      toast('No threats available to export', { icon: '🛡️' })
      return
    }

    const escapeCsvValue = (value: string | number) => `"${String(value).replaceAll('"', '""')}"`
    const rows = [
      ['id', 'sender', 'subject', 'confidence', 'date'],
      ...threatEmails.map((email) => [email.id, email.sender, email.subject, email.confidence, email.date]),
    ]
    const csv = rows.map((row) => row.map(escapeCsvValue).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'guardian-threat-report.csv'
    document.body.append(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
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
      persistRawEmails(
        remaining.map((email) => ({
          id: email.id,
          sender: email.sender,
          subject: email.subject,
          body_text: email.body_text,
          body_html: email.body_html,
          date: email.date,
          is_spam: email.is_spam,
          confidence: email.confidence,
          bec_flags: email.bec_flags,
        })),
      )
      setStatusMessage(`Deleted "${selectedEmail.subject}".`)
      toast.success('Threat Successfully Neutralized', {
        style: { background: THREAT_CHART_COLOR, color: '#fff' },
      })
    } catch (error) {
      console.error('Failed to delete threat:', error)
      setStatusMessage('Threat delete failed. Check backend Gmail permissions.')
    }
  }

  const activeScopeDescription =
    SYNC_SCOPE_OPTIONS.find((option) => option.value === selectedSyncScope)?.description ?? ''
  const loadedScopeDescription =
    SYNC_SCOPE_OPTIONS.find((option) => option.value === loadedSyncScope)?.description ?? ''

  return (
    <div className="guardian-app">
      <Toaster position="bottom-right" />
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

          <div className="profile-card">
            <div className="profile-label">Connected Profile</div>
            {gmailProfile ? (
              <>
                <div className="profile-address">{gmailProfile.emailAddress}</div>
                <div className="profile-stats">
                  <span>{gmailProfile.messagesTotal.toLocaleString()} messages</span>
                  <span>{gmailProfile.threadsTotal.toLocaleString()} threads</span>
                </div>
              </>
            ) : (
              <div className="profile-empty">Profile will appear after a successful verified Gmail sync.</div>
            )}
          </div>

          <div className="sync-controls">
            <label className="sync-field">
              <span>Sync Scope</span>
              <select
                value={selectedSyncScope}
                onChange={(event) => setSelectedSyncScope(event.target.value as SyncScope)}
                disabled={isSyncing}
              >
                {SYNC_SCOPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <p className="sync-hint">{activeScopeDescription}</p>
            <button type="button" className="sync-button" onClick={() => void syncInbox()} disabled={isSyncing}>
              <RefreshCw size={16} className={isSyncing ? 'spin-icon' : ''} />
              <span>{isSyncing ? 'Syncing Gmail...' : `Sync ${getScopeLabel(selectedSyncScope)}`}</span>
            </button>
            <button type="button" className="secondary-action-button" onClick={() => void handleResetProjectCache()}>
              Clear Project Cache
            </button>
          </div>

          <div className="sidebar-divider" />

          <div className="stats-stack">
            <StatCard value={emails.length} label="Project Queue" tone="cyan" />
            <StatCard value={safeEmails.length} label="Safe Emails" tone="green" />
            <StatCard value={spamEmails.length} label="Threats Detected" tone="red" />
          </div>

          <div className="scope-summary">
            <div className="scope-summary-row">
              <span>Current Scope</span>
              <strong>{getScopeLabel(loadedSyncScope)}</strong>
            </div>
            <div className="scope-summary-row">
              <span>Mails To Process</span>
              <strong>{emails.length}</strong>
            </div>
            <div className="scope-summary-row">
              <span>Loaded Dataset</span>
              <strong>{loadedScopeDescription}</strong>
            </div>
            {selectedSyncScope !== loadedSyncScope ? (
              <div className="scope-summary-row">
                <span>Pending Sync Scope</span>
                <strong>{getScopeLabel(selectedSyncScope)}</strong>
              </div>
            ) : null}
            {lastSyncSummary ? (
              <>
                <div className="scope-summary-row">
                  <span>Fetched Last Sync</span>
                  <strong>{lastSyncSummary.fetched_count}</strong>
                </div>
                <div className="scope-summary-row">
                  <span>Removed Missing</span>
                  <strong>{lastSyncSummary.removed_count}</strong>
                </div>
              </>
            ) : null}
          </div>

          <div className="sidebar-footer">
            <p>{loadError ?? statusMessage}</p>
            <span>Backend: {API_BASE_URL}</span>
          </div>
        </aside>

        <div className="main-content-shell">
          <div className="panel-toggle">
            <button
              type="button"
              className={`panel-toggle-button ${activeTab === 'inbox' ? 'active' : ''}`}
              onClick={() => setActiveTab('inbox')}
            >
              Inbox
            </button>
            <button
              type="button"
              className={`panel-toggle-button ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
          </div>

          {activeTab === 'inbox' ? (
            <div className="main-content-grid">
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
                  {isSyncing ? (
                    Array.from({ length: 5 }, (_, index) => <SkeletonRow key={index} />)
                  ) : emails.length === 0 ? (
                    <EmptyInboxState />
                  ) : visibleEmails.length ? (
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
                            <span className="message-star">*</span>
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
          ) : (
            <section className="overview-panel">
              <div className="overview-header">
                <div>
                  <p className="overview-eyebrow">Mailbox Overview</p>
                  <h2 className="overview-heading">Threat telemetry from your current project queue</h2>
                </div>
                <button type="button" onClick={exportThreatReport} className="overview-export-button">
                  Export Threat CSV
                </button>
              </div>

              {emails.length === 0 ? (
                <div className="overview-empty-state">
                  <div className="overview-empty-icon">
                    <Shield size={28} />
                  </div>
                  <h3>No mailbox activity available yet.</h3>
                  <p>Run a sync to populate analytics for sender volume and threat distribution.</p>
                </div>
              ) : (
                <div className="overview-grid">
                  <div className="overview-card">
                    <div className="overview-card-head">
                      <h3>Safe vs Threat Ratio</h3>
                      <p>
                        {hasThreats ? 'Threats are present in the current queue.' : 'All synced emails are currently marked safe.'}
                      </p>
                    </div>
                    <div className="overview-chart-shell">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={overviewPieData}
                            dataKey="value"
                            nameKey="name"
                            innerRadius={60}
                            outerRadius={80}
                            stroke="none"
                            paddingAngle={4}
                            label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                          >
                            {overviewPieData.map((entry) => (
                              <Cell
                                key={entry.name}
                                fill={entry.name === 'Safe' ? SAFE_CHART_COLOR : THREAT_CHART_COLOR}
                                stroke="none"
                              />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{
                              background: '#0f172a',
                              border: '1px solid rgba(0, 242, 255, 0.18)',
                              borderRadius: '12px',
                              color: '#fff',
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="overview-card">
                    <div className="overview-card-head">
                      <h3>Top Senders</h3>
                      <p>The four most active senders in the current project queue.</p>
                    </div>
                    <div className="overview-chart-shell">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={topSendersData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                          <XAxis dataKey="sender" stroke="#94a3b8" tickLine={false} axisLine={false} interval={0} angle={-12} textAnchor="end" height={60} />
                          <YAxis stroke="#94a3b8" tickLine={false} axisLine={false} allowDecimals={false} />
                          <Tooltip
                            contentStyle={{
                              background: '#0f172a',
                              border: '1px solid rgba(0, 242, 255, 0.18)',
                              borderRadius: '12px',
                              color: '#fff',
                            }}
                          />
                          <Bar dataKey="count" fill={SAFE_CHART_COLOR} radius={[8, 8, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
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

export default App
