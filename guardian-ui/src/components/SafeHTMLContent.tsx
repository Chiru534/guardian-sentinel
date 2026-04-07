import { useMemo } from 'react'
import DOMPurify from 'dompurify'

const TRUSTED_IFRAME_HOSTS = new Set([
  'youtube.com',
  'www.youtube.com',
  'm.youtube.com',
  'youtu.be',
  'www.youtu.be',
  'player.vimeo.com',
  'vimeo.com',
  'www.vimeo.com',
  'drive.google.com',
  'docs.google.com',
])

const ALLOWED_TAGS = [
  'p', 'br', 'b', 'i', 'u', 'strong', 'em', 'a', 'div', 'span',
  'table', 'tr', 'td', 'th', 'tbody', 'thead', 'tfoot',
  'ul', 'ol', 'li',
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'img', 'figure', 'blockquote', 'pre', 'code', 'font', 'style', 'iframe',
]

const ALLOWED_ATTR = [
  'href', 'src', 'alt', 'title', 'style', 'class', 'width', 'height',
  'align', 'valign', 'border', 'cellpadding', 'cellspacing', 'bgcolor',
  'color', 'target',
]

const SAFE_LINK_PROTOCOLS = new Set(['http:', 'https:', 'mailto:'])
const SAFE_MEDIA_PROTOCOLS = new Set(['http:', 'https:', 'cid:'])

const hasUnsafeScriptScheme = (value: string) => value.trim().toLowerCase().startsWith('javascript:')

const parseUrl = (value: string) => {
  try {
    return new URL(value, window.location.origin)
  } catch {
    return null
  }
}

const isSafeHref = (href: string) => {
  if (!href || hasUnsafeScriptScheme(href)) {
    return false
  }

  const parsed = parseUrl(href)
  return parsed !== null && SAFE_LINK_PROTOCOLS.has(parsed.protocol)
}

const isSafeMediaSrc = (src: string) => {
  if (!src || hasUnsafeScriptScheme(src)) {
    return false
  }

  if (src.trim().toLowerCase().startsWith('cid:')) {
    return true
  }

  const parsed = parseUrl(src)
  return parsed !== null && SAFE_MEDIA_PROTOCOLS.has(parsed.protocol)
}

const isTrustedIframe = (src: string) => {
  if (!isSafeMediaSrc(src)) {
    return false
  }

  const parsed = parseUrl(src)
  return parsed !== null && TRUSTED_IFRAME_HOSTS.has(parsed.hostname.toLowerCase())
}

interface SafeHTMLContentProps {
  html: string
  className?: string
}

const SafeHTMLContent = ({ html, className }: SafeHTMLContentProps) => {
  const sanitizedHtml = useMemo(() => {
    // Email HTML needs a broader allowlist than app-authored content because
    // marketing emails rely on tables, inline styles, font tags, and wrappers.
    const sanitized = DOMPurify.sanitize(html, {
      ALLOWED_TAGS,
      ALLOWED_ATTR,
      KEEP_CONTENT: true,
      FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input', 'button', 'textarea', 'select'],
      FORBID_ATTR: ['srcset'],
    })

    const doc = new DOMParser().parseFromString(`<div>${sanitized}</div>`, 'text/html')
    const container = doc.body.firstElementChild

    if (!container) {
      return ''
    }

    container.querySelectorAll('*').forEach((element) => {
      Array.from(element.attributes).forEach((attribute) => {
        if (attribute.name.toLowerCase().startsWith('on')) {
          element.removeAttribute(attribute.name)
        }
      })
    })

    container.querySelectorAll('a').forEach((link) => {
      const href = link.getAttribute('href') ?? ''
      if (!isSafeHref(href)) {
        link.removeAttribute('href')
      } else {
        link.setAttribute('target', '_blank')
        link.setAttribute('rel', 'noopener noreferrer')
      }
    })

    container.querySelectorAll('img').forEach((image) => {
      const src = image.getAttribute('src') ?? ''
      if (!isSafeMediaSrc(src)) {
        image.removeAttribute('src')
      }
      image.setAttribute('loading', 'lazy')
      image.setAttribute('referrerpolicy', 'no-referrer')
      image.classList.add('email-html-image')
    })

    // Iframes are only kept for trusted video hosts so we preserve embeds
    // without allowing arbitrary third-party content execution surfaces.
    container.querySelectorAll('iframe').forEach((iframe) => {
      const src = iframe.getAttribute('src') ?? ''
      if (!isTrustedIframe(src)) {
        iframe.remove()
        return
      }

      iframe.setAttribute('loading', 'lazy')
      iframe.setAttribute('referrerpolicy', 'no-referrer')
      iframe.classList.add('email-html-iframe')
      if (!iframe.getAttribute('title')) {
        iframe.setAttribute('title', 'Embedded email content')
      }
    })

    return container.innerHTML
  }, [html])

  return (
    <div
      className={className ? `email-html-content ${className}` : 'email-html-content'}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  )
}

export default SafeHTMLContent
