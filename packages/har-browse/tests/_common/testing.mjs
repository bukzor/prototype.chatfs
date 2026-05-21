import { expect } from "@playwright/test";

/**
 * @typedef {{ method: string; params?: any }} CDPMessage
 * @typedef {{ events: AsyncIterable<CDPMessage> }} CaptureSessionLike
 */

/**
 * Drain a capture session's events iterator to completion. Equivalent to
 * `for await (const m of session.events) acc.push(m)`.
 *
 * @param {CaptureSessionLike} session
 * @returns {Promise<CDPMessage[]>}
 */
export async function drainMessages(session) {
  /** @type {CDPMessage[]} */
  const messages = [];
  for await (const msg of session.events) messages.push(msg);
  return messages;
}

/**
 * First Network.responseReceived event whose URL contains `urlSubstring`.
 * Returns undefined if no match.
 *
 * @param {CDPMessage[]} messages
 * @param {string} urlSubstring
 */
export function findRR(messages, urlSubstring) {
  return messages.find(
    (m) =>
      m.method === "Network.responseReceived" &&
      (m.params?.response?.url ?? "").includes(urlSubstring),
  );
}

/**
 * Decode a `Network.responseReceived` event's body, base64 or utf8.
 * @param {CDPMessage} rr
 */
export function decodeRRBody(rr) {
  const r = rr.params?.response;
  if (!r || r.body == null) return null;
  return r.encoding === "base64"
    ? Buffer.from(r.body, "base64").toString("utf8")
    : r.body;
}

/**
 * Walk `messages` and return one entry per `Network.responseReceived`
 * whose URL contains `pathname` and whose body is present and JSON-parseable.
 * Entries are `{ idx, url, body }`. Bodyless RRs are skipped.
 *
 * @param {CDPMessage[]} messages
 * @param {string} [pathname]
 */
export function parsedPayloadRRs(messages, pathname = "/payload") {
  const out = [];
  for (let idx = 0; idx < messages.length; idx++) {
    const m = messages[idx];
    if (m.method !== "Network.responseReceived") continue;
    const r = m.params?.response;
    if (!r || !(r.url ?? "").includes(pathname)) continue;
    const text = decodeRRBody(m);
    if (text == null) continue;
    out.push({ idx, url: r.url, body: JSON.parse(text) });
  }
  return out;
}

/**
 * Assert the set of `n` values parsed from captured `Network.responseReceived`
 * bodies for `pathname` equals exactly {1..served}, where served is the
 * count of matching requests in `requestLog`.
 *
 * Surfaces gaps *within* the captured set (missing n's, duplicates,
 * unparseable bodies) — a strictly stronger check than counting
 * captured-vs-served, which only sees fully-missed entries.
 *
 * @param {object} args
 * @param {CDPMessage[]} args.events
 * @param {Array<{pathname: string}>} args.requestLog
 * @param {string} [args.pathname="/payload"]
 */
export function assertNoGaps({ events, requestLog, pathname = "/payload" }) {
  const served = requestLog.filter((r) => r.pathname === pathname).length;
  const ns = parsedPayloadRRs(events, pathname).map((rr) => {
    expect(typeof rr.body.n, `n is number in body for ${pathname}`).toBe(
      "number",
    );
    return rr.body.n;
  });
  ns.sort((a, b) => a - b);
  const expected = Array.from({ length: served }, (_, i) => i + 1);
  expect(ns).toEqual(expected);
}

/**
 * Three consistency checks bundled for capture-stress tests:
 *   1. Captured n's are unique (no duplicate emissions).
 *   2. Every n is in [1, served] (no synthetic post-BARRIER injection).
 *   3. body.id round-trips to the URL's `id` param (no body corruption).
 *
 * @param {object} args
 * @param {CDPMessage[]} args.messages
 * @param {{ requestLog: Array<{pathname: string}> }} args.server
 * @param {string} [args.pathname]
 */
export function assertCapturedConsistent({ messages, server, pathname = "/payload" }) {
  const rrs = parsedPayloadRRs(messages, pathname);
  const ns = rrs.map((rr) => rr.body.n);
  expect(new Set(ns).size, "captured n values unique").toBe(ns.length);
  const served = server.requestLog.filter((r) => r.pathname === pathname).length;
  for (const n of ns) {
    expect(
      Number.isInteger(n) && n >= 1 && n <= served,
      `captured n=${n} in [1, ${served}]`,
    ).toBe(true);
  }
  for (const { url, body } of rrs) {
    const urlId = new URL(url).searchParams.get("id");
    expect(body.id, `body.id round-trips for n=${body.n}`).toBe(urlId);
  }
}
