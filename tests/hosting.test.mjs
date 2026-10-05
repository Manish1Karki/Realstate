import test from 'node:test';
import assert from 'node:assert/strict';
import { Writable } from 'node:stream';
import { readFileSync, existsSync } from 'node:fs';
import { createProxy } from '../api/proxy.js';

const env = { BACKEND_API_URL: 'https://backend.example.org', BACKEND_PROXY_SECRET: 'test-shared-secret', VERCEL: '1' };
function response() {
  const chunks = [];
  const headers = {};
  const res = new Writable({ write(chunk, encoding, callback) { chunks.push(chunk.toString()); callback(); } });
  res.setHeader = (key, value) => { headers[key.toLowerCase()] = value; };
  res.headers = headers;
  res.text = () => chunks.join('');
  return res;
}
function request(overrides = {}) {
  return { method: 'GET', query: { path: 'properties' }, url: '/api/properties?district=Kathmandu', headers: { host: 'prototype.vercel.app' }, ...overrides };
}

test('API proxy forwards query filters and uses only the configured backend', async () => {
  let called;
  const proxy = createProxy({ env, fetchImpl: async (url, options) => {
    called = { url: String(url), options };
    return new Response(JSON.stringify({ items: [] }), { headers: { 'Content-Type': 'application/json' } });
  } });
  const res = response(); await proxy(request(), res);
  assert.equal(called.url, 'https://backend.example.org/api/properties?district=Kathmandu');
  assert.equal(called.options.headers['X-Land-Proxy-Token'], env.BACKEND_PROXY_SECRET);
  assert.equal(res.statusCode, 200);
  assert.equal(res.headers['cache-control'], 'no-store');
  assert.deepEqual(JSON.parse(res.text()), { items: [] });
});

test('authentication forwards credentials and Set-Cookie without exposing proxy secrets', async () => {
  const proxy = createProxy({ env, fetchImpl: async (url, options) => {
    assert.equal(options.headers.cookie, 'land_discover_session=old-session');
    assert.equal(options.headers.origin, 'https://prototype.vercel.app');
    assert.equal(options.headers['X-Land-Frontend-Origin'], 'https://prototype.vercel.app');
    assert.equal(JSON.parse(options.body).email, 'person@example.org');
    return new Response(JSON.stringify({ user: { id: 1 } }), { headers: { 'Set-Cookie': 'land_discover_session=new-session; HttpOnly; Secure; SameSite=Lax; Path=/' } });
  } });
  const res = response();
  await proxy(request({ method: 'POST', query: { path: 'auth/login' }, url: '/api/auth/login', headers: { host: 'prototype.vercel.app', origin: 'https://prototype.vercel.app', cookie: 'land_discover_session=old-session', 'content-type': 'application/json' }, body: { email: 'person@example.org', password: 'test-password' } }), res);
  assert.match(res.headers['set-cookie'][0], /HttpOnly/);
  assert.ok(!res.text().includes(env.BACKEND_PROXY_SECRET));
});

test('missing backend configuration returns a clear service error', async () => {
  const res = response(); await createProxy({ env: {} })(request(), res);
  assert.equal(res.statusCode, 503);
});

test('cross-origin mutation and path traversal do not contact the backend', async () => {
  const proxy = createProxy({ env, fetchImpl: () => { throw new Error('Must not be called'); } });
  const first = response(); await proxy(request({ method: 'POST', headers: { host: 'prototype.vercel.app', origin: 'https://evil.example.org' } }), first);
  assert.equal(first.statusCode, 403);
  const second = response(); await proxy(request({ query: { path: '../../private' } }), second);
  assert.equal(second.statusCode, 400);
});

test('upstream failure does not expose backend details or secrets', async () => {
  const res = response(); await createProxy({ env, fetchImpl: async () => { throw new Error(env.BACKEND_PROXY_SECRET); } })(request(), res);
  assert.equal(res.statusCode, 502);
  assert.ok(!res.text().includes(env.BACKEND_PROXY_SECRET));
});

test('compiled prototype includes landing, aggregator, login and excludes VisualTour', () => {
  const landing = readFileSync(new URL('../dist/index.html', import.meta.url), 'utf8');
  const aggregator = readFileSync(new URL('../dist/aggregator/index.html', import.meta.url), 'utf8');
  assert.match(landing, /\/assets\//);
  assert.match(aggregator, /\/aggregator\/assets\//);
  assert.ok(!existsSync(new URL('../dist/VisualTour', import.meta.url)));
  const config = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf8'));
  for (const path of ['/login', '/properties', '/aggregator']) assert.ok(config.rewrites.some(route => route.source === path));
  assert.ok(!config.rewrites.some(route => /tour/i.test(route.source)));
});
