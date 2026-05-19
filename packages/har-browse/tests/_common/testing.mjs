import { expect } from "@playwright/test";

/** Decode a `Network.responseReceived` event's body, base64 or utf8. */
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
 * @param {Array<{method: string, params: object}>} args.events
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
