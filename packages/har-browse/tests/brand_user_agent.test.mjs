/**
 * `brandUserAgent` must produce a *grammatical* User-Agent, so the
 * oracle here is RFC 9110's ABNF rather than a string match:
 *
 *   User-Agent = product *( RWS ( product / comment ) )
 *   product    = token [ "/" token ]
 *   comment    = "(" *( ctext / quoted-pair / comment ) ")"
 *
 * The distinction is load-bearing because the two branches brand in
 * two different positions. `;` and `:` are not token characters, so
 * the `; `-separated comment spelling is ungrammatical as a trailing
 * product -- which is exactly the bug the fallback branch shipped
 * before this test existed. Real Chromium always has a system-info
 * comment, so the e2e spec can never reach that branch.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { brandUserAgent } from "../src/host_puppeteer.mjs";

const CHROMIUM =
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " +
  "Chrome/147.0.0.0 Safari/537.36";

const TCHAR = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;
// ctext plus the parens that make up balanced nesting (checked below);
// a literal backslash would start a quoted-pair, which we never emit.
const COMMENT_CHAR = /^[\t \x21-\x27\x2A-\x5B\x5D-\x7E()]*$/;

/**
 * Split a User-Agent into its grammar elements, throwing on anything
 * the ABNF rejects.
 *
 * @param {string} ua
 * @returns {Array<{kind: "product" | "comment", text: string}>}
 */
function parseUserAgent(ua) {
  /** @type {Array<{kind: "product" | "comment", text: string}>} */
  const elements = [];
  let i = 0;
  while (i < ua.length) {
    if (ua[i] === " ") {
      // RWS: exactly one run of space between elements, none leading.
      if (!elements.length) throw new Error("leading whitespace");
      while (ua[i] === " ") i++;
      if (i >= ua.length) throw new Error("trailing whitespace");
      continue;
    }
    if (ua[i] === "(") {
      const start = i;
      let depth = 0;
      for (; i < ua.length; i++) {
        if (ua[i] === "(") depth++;
        else if (ua[i] === ")" && --depth === 0) {
          i++;
          break;
        }
      }
      if (depth !== 0) throw new Error(`unterminated comment: ${ua.slice(start)}`);
      const text = ua.slice(start + 1, i - 1);
      if (!COMMENT_CHAR.test(text)) throw new Error(`non-ctext in comment: ${text}`);
      elements.push({ kind: "comment", text });
      continue;
    }
    const start = i;
    while (i < ua.length && ua[i] !== " " && ua[i] !== "(") i++;
    const text = ua.slice(start, i);
    const [name, version, ...rest] = text.split("/");
    if (rest.length) throw new Error(`product has two versions: ${text}`);
    for (const tok of version === undefined ? [name] : [name, version]) {
      if (!TCHAR.test(tok)) throw new Error(`not a token: ${JSON.stringify(tok)}`);
    }
    elements.push({ kind: "product", text });
  }
  if (!elements.length || elements[0].kind !== "product") {
    throw new Error("User-Agent must start with a product");
  }
  return elements;
}

test("the oracle rejects the ungrammatical spellings it exists to catch", () => {
  assert.throws(() => parseUserAgent(`${CHROMIUM} har-browse/1.0.0; +https://x.y`));
  assert.throws(() => parseUserAgent("Mozilla/5.0 (unterminated"));
  assert.throws(() => parseUserAgent("(comment-first)"));
  assert.doesNotThrow(() => parseUserAgent(CHROMIUM));
});

test("branding a Chromium UA extends the system-information comment", () => {
  const branded = brandUserAgent(CHROMIUM);
  const elements = parseUserAgent(branded);

  assert.equal(elements[1].kind, "comment");
  assert.match(elements[1].text, /^X11; Linux x86_64; har-browse\/\d[\d.]*; \+https?:\/\//);
  // The gate Google enforces is on shape: nothing may trail the
  // browser's product list (sbin/ua-gate-probe.mjs).
  assert.deepEqual(
    elements.filter((_, n) => n !== 1),
    parseUserAgent(CHROMIUM).filter((_, n) => n !== 1),
    "only the system-information comment changed",
  );
});

test("a UA with no comment gets a trailing product and contact comment", () => {
  const branded = brandUserAgent("Weird/1.0");
  const elements = parseUserAgent(branded);

  assert.equal(elements[0].text, "Weird/1.0");
  assert.match(elements[1].text, /^har-browse\/\d[\d.]*$/);
  assert.equal(elements[2].kind, "comment");
  assert.match(elements[2].text, /^\+https?:\/\//);
});
