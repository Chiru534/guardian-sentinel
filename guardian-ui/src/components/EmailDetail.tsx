import { AlertTriangle, ShieldAlert, ShieldCheck } from 'lucide-react'
import SafeHTMLContent from './SafeHTMLContent'
import {
  type Email,
  getActiveBecFlags,
  getSafetyScore,
  getSenderDisplay,
  getThreatScore,
  stripHtml,
} from '../types/email'

interface EmailDetailProps {
  email: Email | null
  onMarkSafe: () => void
  onDeleteThreat: () => void
}

const EmailDetail = ({ email, onMarkSafe, onDeleteThreat }: EmailDetailProps) => {
  if (!email) {
    return (
      <div className="detail-empty-state">
        <div className="detail-empty-icon">✉️</div>
        <h2>Select an Email</h2>
        <p>Choose a message from the inbox to review the analysis, sender, and email body.</p>
      </div>
    )
  }

  const activeFlags = getActiveBecFlags(email)
  const hasHtmlBody = email.body_html.trim().length > 0
  const fallbackText = email.body_text || stripHtml(email.body_html) || 'No message body available.'

  return (
    <>
      <div className={`analysis-banner ${email.is_spam ? 'threat' : 'safe'}`}>
        <div className="analysis-title">
          {email.is_spam ? (
            <>
              <AlertTriangle size={18} />
              <span>Threat Analysis: {getThreatScore(email).toFixed(1)}% Risk</span>
            </>
          ) : (
            <>
              <ShieldCheck size={18} />
              <span>Safety Analysis: {getSafetyScore(email).toFixed(1)}% Secure</span>
            </>
          )}
        </div>
        <p>
          {email.is_spam
            ? 'This email triggered the threat engine and should be reviewed before taking any action.'
            : 'This email passed all security scans and appears to be legitimate business communication.'}
        </p>
      </div>

      <div className="detail-scroll">
        <div className="detail-meta-label">Message ID</div>
        <div className="detail-meta-value">{email.id}</div>

        <h2 className="detail-subject">{email.subject}</h2>

        <div className="detail-meta-label">From</div>
        <div className="detail-meta-value detail-from">{getSenderDisplay(email.sender)}</div>

        <div className="detail-divider" />

        <div className="detail-meta-label">Message Content</div>
        <div className="email-html-shell">
          {hasHtmlBody ? (
            <SafeHTMLContent html={email.body_html} />
          ) : (
            <pre className="email-plain-content">{fallbackText}</pre>
          )}
        </div>

        {activeFlags.length > 0 && (
          <>
            <div className="detail-divider" />
            <div className="detail-meta-label">Triggered Flags</div>
            <div className="flag-row">
              {activeFlags.map((flag) => (
                <span key={`${email.id}-${flag}`} className="flag-chip">
                  <ShieldAlert size={12} />
                  {flag}
                </span>
              ))}
            </div>
          </>
        )}
      </div>

      <div className="detail-actions">
        {email.is_spam ? (
          <button type="button" className="action-button danger" onClick={onDeleteThreat}>
            Delete Threat
          </button>
        ) : (
          <button type="button" className="action-button primary" onClick={onMarkSafe}>
            Mark Safe
          </button>
        )}
      </div>
    </>
  )
}

export default EmailDetail
