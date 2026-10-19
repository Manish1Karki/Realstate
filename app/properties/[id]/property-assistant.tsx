'use client'

import { FormEvent, useState } from 'react'

type Message = { role: 'assistant' | 'user'; text: string }

const suggestions = [
  'Give me a simple summary of this property.',
  'How is the road access?',
  'What is nearby?',
  'Why is this property priced this way?',
]

function ChatIcon() {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 4h16v12H9l-5 4V4Z" /><path d="M8 8h8M8 12h5" /></svg>
}

export default function PropertyAssistant({ propertyId, title }: { propertyId: number; title: string }) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [status, setStatus] = useState('Ask a question about this property.')
  const [busy, setBusy] = useState(false)

  async function ask(value: string) {
    const text = value.trim()
    if (!text || busy) return
    setQuestion('')
    setMessages(previous => [...previous, { role: 'user', text }])
    setBusy(true)
    setStatus('Looking at the saved property details…')
    try {
      const response = await fetch('/api/property-chat/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ property_id: propertyId, question: text, mode: 'nvidia' }),
      })
      const result = await response.json() as { answer?: string; error?: string }
      if (!response.ok || !result.answer) throw new Error(result.error || 'The assistant could not answer right now.')
      setMessages(previous => [...previous, { role: 'assistant', text: result.answer! }])
      setStatus('You can ask another question.')
    } catch (error) {
      const message = error instanceof Error ? error.message : 'The assistant could not answer right now.'
      setMessages(previous => [...previous, { role: 'assistant', text: message }])
      setStatus('The assistant is unavailable. Please try again shortly.')
    } finally {
      setBusy(false)
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void ask(question)
  }

  return <section className="property-ai-assistant" aria-labelledby="property-ai-heading">
    <div className="property-ai-intro">
      <span className="property-ai-icon"><ChatIcon /></span>
      <div><p className="eyebrow">PROPERTY HELP</p><h2 id="property-ai-heading">Ask Land Discover AI</h2><p>Ask simple questions about {title}, its road, nearby places, or the listed price.</p><small>Uses saved listing facts with NVIDIA AI. Do not add private personal details.</small></div>
    </div>
    <div className="property-ai-chat">
      {messages.length > 0 && <div className="property-ai-messages" role="log" aria-live="polite" aria-relevant="additions">{messages.map((message, index) => <article className={'property-ai-message ' + message.role} key={index}><span>{message.role === 'user' ? 'You' : 'Land Discover AI'}</span><p>{message.text}</p></article>)}</div>}
      {messages.length === 0 && <div className="property-ai-suggestions" aria-label="Suggested questions">{suggestions.map(item => <button type="button" key={item} onClick={() => void ask(item)} disabled={busy}>{item}</button>)}</div>}
      <form className="property-ai-form" onSubmit={submit}>
        <label htmlFor={'property-ai-question-' + propertyId}>Your question</label>
        <div><input id={'property-ai-question-' + propertyId} value={question} onChange={event => setQuestion(event.target.value)} placeholder="For example: What hospitals are nearby?" maxLength={500} disabled={busy} required /><button type="submit" disabled={busy || !question.trim()}>{busy ? 'Thinking…' : 'Ask AI'}</button></div>
        <p role="status">{status}</p>
      </form>
    </div>
  </section>
}
