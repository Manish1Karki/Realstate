import test from 'node:test'
import assert from 'node:assert/strict'
import { createPropertyChatHandler } from '../lib/property-chat/server.mjs'
import { ChatError } from '../lib/property-chat/nvidia.mjs'

const sample = {
  id: 7, property_type: 'house', transaction_type: 'sale', title: 'Synthetic test property',
  area_name: 'Test area', district: 'Test district', size: '3 Aana', total_price_npr: 25000000,
  road_access_note: '16 ft blacktop road', road_width_ft: 16, road_type: 'asphalt',
  contact_phone: '+9779800000000', contact_role: 'agent',
  contact_name: 'PRIVATE TEST NAME', address: 'PRIVATE TEST ADDRESS', description: 'PRIVATE TEST DESCRIPTION',
  source_url: 'https://example.com/test-only', amenities: [],
}
const env = {
  NODE_ENV: 'production', VERCEL: '1', BACKEND_API_URL: 'https://backend.example.com',
  BACKEND_PROXY_SECRET: 'SYNTHETIC-BACKEND-SECRET', NVIDIA_API_KEY: 'SYNTHETIC-NVIDIA-KEY', NVIDIA_MODEL: 'test/model',
}
function request(value, headers = {}) {
  return new Request('https://land.example.com/api/property-chat/chat', {
    method: 'POST', headers: { 'Content-Type': 'application/json', Origin: 'https://land.example.com', ...headers }, body: JSON.stringify(value),
  })
}
const question = { property_id: 7, question: 'Tell me about the road.', mode: 'nvidia' }

test('production chat loads only the chosen property and keeps secrets on the server', async () => {
  const calls = []
  const handle = createPropertyChatHandler({ env, fetchImpl: async (url, options) => {
    calls.push(String(url))
    assert.equal(options.headers['X-Land-Proxy-Token'], env.BACKEND_PROXY_SECRET)
    assert.equal(options.headers.Authorization, undefined)
    assert.equal(options.cache, 'no-store')
    assert.equal(options.redirect, 'error')
    assert.ok(options.signal instanceof AbortSignal)
    return Response.json(sample)
  }, answerWithNvidia: async (text, property, history, options) => {
    assert.equal(text, question.question)
    assert.equal(property.id, 7)
    assert.equal(options.key, env.NVIDIA_API_KEY)
    assert.equal(options.model, 'test/model')
    return 'The saved listing reports a 16 ft asphalt road.'
  } })
  const result = await handle(request(question))
  assert.equal(result.status, 200)
  assert.equal(result.headers.get('cache-control'), 'no-store')
  const text = await result.text()
  assert.match(text, /16 ft asphalt/)
  for (const value of [env.NVIDIA_API_KEY, env.BACKEND_PROXY_SECRET, sample.contact_phone, sample.contact_name, sample.address, sample.description, sample.source_url]) assert.ok(!text.includes(value))
  assert.deepEqual(calls, ['https://backend.example.com/api/properties/7'])
})

test('cross-site requests are rejected before reading data or calling AI', async () => {
  const handle = createPropertyChatHandler({ env, fetchImpl: async () => assert.fail('Unexpected backend request'), answerWithNvidia: async () => assert.fail('Unexpected AI request') })
  for (const headers of [{ Origin: 'https://attacker.example.com' }, { Origin: 'null' }, { 'Sec-Fetch-Site': 'cross-site' }]) assert.equal((await handle(request(question, headers))).status, 403)
})

test('malformed IDs and question bodies never reach the property backend', async () => {
  const handle = createPropertyChatHandler({ env, fetchImpl: async () => assert.fail('Unexpected backend request') })
  for (const property_id of ['../../auth/me', 0, -1, '1e2', '1/2', '12345678901']) assert.equal((await handle(request({ ...question, property_id }))).status, 400)
  for (const value of [null, [], { ...question, question: '' }, { ...question, question: 'a'.repeat(1001) }, { ...question, mode: 'invalid' }]) assert.equal((await handle(request(value))).status, 400)
  assert.equal((await handle(request(question, { 'Content-Type': 'text/plain' }))).status, 415)
  const malformed = new Request('https://land.example.com/api/property-chat/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{' })
  assert.equal((await handle(malformed)).status, 400)
})

test('oversized streamed or declared bodies are rejected', async () => {
  const handle = createPropertyChatHandler({ env, fetchImpl: async () => assert.fail('Unexpected backend request') })
  assert.equal((await handle(request({ ...question, extra: 'x'.repeat(12000) }))).status, 413)
  assert.equal((await handle(request(question, { 'Content-Length': '99999' }))).status, 413)
})

test('production requires HTTPS and backend authentication configuration', async () => {
  for (const config of [{ ...env, BACKEND_API_URL: 'http://backend.example.com' }, { ...env, BACKEND_PROXY_SECRET: '' }, { ...env, BACKEND_API_URL: 'https://user:password@backend.example.com' }]) {
    const handle = createPropertyChatHandler({ env: config, fetchImpl: async () => assert.fail('Unexpected backend request') })
    const result = await handle(request(question))
    assert.equal(result.status, 503)
    assert.doesNotMatch(await result.text(), /SYNTHETIC|password|backend\.example/)
  }
})

test('missing or failing backend returns a useful error without any local setup advice', async () => {
  for (const [fetchImpl, expected] of [
    [async () => new Response('', { status: 404 }), 404],
    [async () => new Response('internal backend secret', { status: 403 }), 503],
    [async () => { throw new Error('internal exception') }, 503],
    [async () => Response.json({ id: 8 }), 503],
  ]) {
    const result = await createPropertyChatHandler({ env, fetchImpl })(request(question))
    assert.equal(result.status, expected)
    assert.doesNotMatch(await result.text(), /localhost|8000|start the|internal|secret/i)
  }
})

test('published contacts and explicit rent calculations do not go to the AI provider', async () => {
  const handle = createPropertyChatHandler({ env, fetchImpl: async () => Response.json(sample), answerWithNvidia: async () => assert.fail('Contact or calculation sent to AI') })
  const contact = await handle(request({ ...question, question: 'What is the contact number?' }))
  assert.equal(contact.status, 200)
  const data = await contact.json()
  assert.equal(data.engine, 'listing')
  assert.match(data.answer, /listing agent/)
  assert.match(data.answer, /9800000000/)
  const calculation = await (await handle(request({ ...question, question: 'If monthly rent is NPR 50,000, what is the gross yield?' }))).json()
  assert.equal(calculation.engine, 'calculation')
  assert.match(calculation.answer, /2\.40%/)
})

test('provider errors keep useful statuses and hide local configuration and provider details', async () => {
  for (const status of [422, 429, 503, 504, 502]) {
    const handle = createPropertyChatHandler({ env, fetchImpl: async () => Response.json(sample), answerWithNvidia: async () => { throw new ChatError('SECRET demo settings local test', status) } })
    const result = await handle(request(question))
    assert.equal(result.status, status)
    assert.doesNotMatch(await result.text(), /SECRET|demo|settings|SYNTHETIC/)
  }
})

test('external listing URLs are removed from saved and provider answers', async () => {
  const handle = createPropertyChatHandler({ env, fetchImpl: async () => Response.json({ ...sample, road_access_note: 'Asphalt. https://example.com/test' }), answerWithNvidia: async () => 'Road details. Check [listing](https://example.com/property) or www.example.com.' })
  for (const mode of ['saved', 'nvidia']) {
    const result = await handle(request({ ...question, mode }))
    assert.equal(result.status, 200)
    assert.doesNotMatch((await result.json()).answer, /https?:\/\/|www\./)
  }
})
