'use client'

import { useEffect, useState } from 'react'
import WhatsAppIcon from './whatsapp-icon'

export default function WhatsAppButton({ href, className = 'site-whatsapp', label = 'Chat with Land Discover on WhatsApp' }: { href: string; className?: string; label?: string }) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    let shown = false
    function update() {
      const scrollRange = Math.max(0, document.documentElement.scrollHeight - window.innerHeight)
      const next = window.scrollY > Math.min(220, scrollRange / 3)
      if (shown !== next) { shown = next; setVisible(next) }
    }
    update()
    window.addEventListener('scroll', update, { passive: true })
    window.addEventListener('resize', update, { passive: true })
    return () => {
      window.removeEventListener('scroll', update)
      window.removeEventListener('resize', update)
    }
  }, [])

  return <a className={className + ' whatsapp-scroll-link'} data-visible={visible} href={href} target="_blank" rel="noopener noreferrer" aria-label={label} aria-hidden={!visible} inert={!visible} tabIndex={visible ? 0 : -1} title="Chat on WhatsApp"><WhatsAppIcon /></a>
}
