export type RawBecFlags = Record<string, number> | string[] | null | undefined

export interface RawEmail {
  id: string
  sender?: string
  subject?: string
  body_text?: string
  body_html?: string
  is_spam?: boolean
  confidence?: number
  confidence_score?: number
  bec_flags?: RawBecFlags
  date?: string
  processed_at?: string
}

export interface Email {
  id: string
  sender: string
  subject: string
  body_text: string
  body_html: string
  date: string
  is_spam: boolean
  confidence: number
  bec_flags: Record<string, number>
}

export const BEC_LABELS: Record<string, string> = {
  persona_impersonation: 'Persona Building',
  victim_isolation: 'Victim Isolation',
  urgency_engagement: 'High Urgency',
  bank_manipulation: 'Fund Redirection',
  evasion_cleanup: 'Evasion Strategy',
  credential_phishing: 'Credential Phishing',
}

export const stripHtml = (value: string) => value.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()

export const getSenderDisplay = (sender: string) => {
  const raw = sender.trim()
  if (!raw) {
    return 'Unknown Sender'
  }

  const name = raw.split('<')[0]?.trim()
  return name || raw
}

export const normalizeBecFlags = (flags: RawBecFlags): Record<string, number> => {
  if (!flags) {
    return {}
  }

  if (Array.isArray(flags)) {
    return Object.fromEntries(flags.map((flag) => [flag, 1]))
  }

  return Object.fromEntries(
    Object.entries(flags).map(([flag, active]) => [flag, Number(active === 1)]),
  )
}

export const normalizeEmail = (raw: RawEmail): Email => ({
  id: raw.id,
  sender: raw.sender?.trim() || 'Unknown Sender',
  subject: raw.subject?.trim() || 'No subject',
  body_text: raw.body_text?.trim() || '',
  body_html: raw.body_html?.trim() || '',
  date: raw.date?.trim() || '',
  is_spam: Boolean(raw.is_spam),
  confidence: typeof raw.confidence === 'number'
    ? raw.confidence
    : typeof raw.confidence_score === 'number'
      ? raw.confidence_score
      : 0,
  bec_flags: normalizeBecFlags(raw.bec_flags),
})

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

export const getSafetyScore = (email: Email) => clamp((1 - email.confidence) * 100, 0, 100)

export const getThreatScore = (email: Email) => clamp(email.confidence * 100, 0, 100)

export const getActiveBecFlags = (email: Email) =>
  Object.entries(email.bec_flags)
    .filter(([, active]) => active === 1)
    .map(([flag]) => BEC_LABELS[flag] ?? flag.replaceAll('_', ' '))

export const getPreviewText = (email: Email) => {
  const preview = email.body_text || stripHtml(email.body_html)
  return preview || 'No preview available'
}
