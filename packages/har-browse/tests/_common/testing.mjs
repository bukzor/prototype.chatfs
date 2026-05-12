import { expect } from "@playwright/test";

function decodeRRBody(rr) {
  const r = rr.params?.response;
  if (!r || r.body == null) return null;
  return r.encoding === "base64"
    ? Buffer.from(r.body, "base64").toString("utf8")
    : r.body;
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
  const ns = [];
  for (const e of events) {
    if (e.method !== "Network.responseReceived") continue;
    if (!(e.params?.response?.url ?? "").includes(pathname)) continue;
    const body = decodeRRBody(e);
    expect(body, `body present for ${pathname}`).toBeTruthy();
    const parsed = JSON.parse(body);
    expect(typeof parsed.n, `n is number in body for ${pathname}`).toBe(
      "number",
    );
    ns.push(parsed.n);
  }
  ns.sort((a, b) => a - b);
  const expected = Array.from({ length: served }, (_, i) => i + 1);
  expect(ns).toEqual(expected);
}
