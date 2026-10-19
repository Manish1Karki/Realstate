// Server-side entry point. Only the Next.js route imports this module.
import { propertyView } from './context.mjs'
import { savedAnswer, rentScenario } from './answers.mjs'
import { nvidiaAnswer, ChatError } from './nvidia.mjs'

const DEFAULT_MODEL = 'nvidia/nemotron-3.5-lightning-30b-a3b'
const MAX_BODY_BYTES = 12000

function response(status, body) {
  return Response.json(body, { status, headers: {
    'Cache-Control': 'no-store',
    'X-Content-Type-Options': 'nosniff',
    'X-Robots-Tag': 'noindex, nofollow',
    'Referrer-Policy': 'no-referrer',
  } })
}

function checkOrigin(request) {
  const origin = request.headers.get('origin')
  if (request.headers.get('sec-fetch-site') === 'cross-site' || (origin && origin !== new URL(request.url).origin)) {
    throw new ChatError('Please ask your question from this property page.', 403)
  }
}

async function jsonBody(request) {
  if (!/^application\/json(?:\s*;|$)/i.test(request.headers.get('content-type') || '')) throw new ChatError('Send a JSON question.', 415)
  if (Number(request.headers.get('content-length')) > MAX_BODY_BYTES) throw new ChatError('This message is too long. Please send a shorter property question.', 413)
  let raw = ''
  if (request.body) {
    const reader = request.body.getReader()
    const decoder = new TextDecoder()
    let bytes = 0
    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        bytes += value.byteLength
        if (bytes > MAX_BODY_BYTES) {
          await reader.cancel()
          throw new ChatError('This message is too long. Please send a shorter property question.', 413)
        }
        raw += decoder.decode(value, { stream: true })
      }
      raw += decoder.decode()
    } finally { reader.releaseLock() }
  }
  try {
    const value = JSON.parse(raw)
    if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error()
    return value
  } catch { throw new ChatError('The message could not be read. Please try again.', 400) }
}

function inputValues(input) {
  if (!/^\d{1,10}$/.test(String(input.property_id)) || Number(input.property_id) < 1) throw new ChatError('Please choose a valid property.', 400)
  const question = typeof input.question === 'string' ? input.question.trim() : ''
  if (!question || question.length > 1000) throw new ChatError('Please ask a question between 1 and 1,000 characters.', 400)
  const mode = input.mode ?? 'nvidia'
  if (!['saved', 'nvidia'].includes(mode)) throw new ChatError('Choose a valid answer mode.', 400)
  return { id: Number(input.property_id), question, mode, history: input.history }
}

async function loadProperty(id, env, fetchImpl) {
  let url
  try {
    const base = new URL(env.LAND_API_URL || env.BACKEND_API_URL || 'http://127.0.0.1:8000')
    const production = env.NODE_ENV === 'production' || Boolean(env.VERCEL)
    if (base.username || base.password || (production && (base.protocol !== 'https:' || !env.BACKEND_PROXY_SECRET)) || !['https:', 'http:'].includes(base.protocol)) throw new Error()
    url = new URL('/api/properties/' + id, base.origin)
  } catch { throw new ChatError('The property service is not connected yet. Please try again later.', 503) }

  let upstream
  try {
    upstream = await fetchImpl(url, { headers: {
      Accept: 'application/json',
      ...(env.BACKEND_PROXY_SECRET ? { 'X-Land-Proxy-Token': env.BACKEND_PROXY_SECRET } : {}),
    }, cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(25000) })
  } catch { throw new ChatError('The property details are taking too long to load. Please try again shortly.', 503) }
  if (upstream.status === 404) throw new ChatError('This property is no longer available in the saved public listings.', 404)
  if (!upstream.ok) throw new ChatError('The property details could not be loaded. Please try again shortly.', 503)
  try {
    const property = await upstream.json()
    if (!property || Number(property.id) !== id || Array.isArray(property)) throw new Error()
    return property
  } catch { throw new ChatError('The property details could not be read. Please try again shortly.', 503) }
}

function providerError(error) {
  if (!(error instanceof ChatError)) return new ChatError('The AI assistant could not answer right now. Please try again.', 502)
  if (error.status === 422) return new ChatError('Please leave out phone numbers, emails and private personal details. Only add your property question.', 422)
  if (error.status === 429) return new ChatError('The AI service is busy. Please wait a moment and try again.', 429)
  if (error.status === 504) return new ChatError('The AI service took too long to answer. Please try again.', 504)
  if (error.status === 503) return new ChatError('The AI assistant is not connected yet. Please try again later.', 503)
  return new ChatError('The AI assistant could not finish its answer. Please try again later.', 502)
}

// Dependencies can be replaced by synthetic fixtures in tests. No live AI calls are needed.
export function createPropertyChatHandler({ env = process.env, fetchImpl = fetch, answerWithNvidia = nvidiaAnswer } = {}) {
  return async function handle(request) {
    try {
      checkOrigin(request)
      const { id, question, mode, history } = inputValues(await jsonBody(request))
      const property = await loadProperty(id, env, fetchImpl)
      const calculation = rentScenario(question, propertyView(property).facts)
      const contactQuestion = /\b(contact|phone|number|owner|advertiser|agent)\b/i.test(question)
      let answer
      if (mode === 'saved' || contactQuestion || calculation) answer = calculation || savedAnswer(question, property)
      else {
        try { answer = await answerWithNvidia(question, property, history, { key: env.NVIDIA_API_KEY, model: env.NVIDIA_MODEL || DEFAULT_MODEL }) }
        catch (error) { throw providerError(error) }
      }
      // Listing text is untrusted too. Never return links to outside property websites.
      answer = answer.replace(/\[([^\]]+)\]\(https?:\/\/[^)]+\)/gi, '$1').replace(/(?:https?:\/\/|www\.)[^\s<>\])]+/gi, '').trim()
      if (!answer) throw new ChatError('The AI assistant did not return an answer. Please try again.', 502)
      return response(200, { answer, property_id: id, engine: calculation ? 'calculation' : mode === 'saved' ? 'saved' : contactQuestion ? 'listing' : 'nvidia' })
    } catch (error) {
      return response(error instanceof ChatError ? error.status : 500, { error: error instanceof ChatError ? error.message : 'The assistant could not complete that request. Please try again.' })
    }
  }
}
