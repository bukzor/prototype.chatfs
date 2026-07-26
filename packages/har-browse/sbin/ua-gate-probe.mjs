#!/usr/bin/env node
// @ts-check
// Which User-Agent strings does a provider refuse?
//
//   sbin/ua-gate-probe.mjs trash/live-verify/run8.jsonl [--match GenerateContent]
//
// Verified 2026-07-26 that aistudio answers PERMISSION_DENIED to
// GenerateContent when our tool-identifying UA suffix is present, and
// answers normally without it -- across models, with attestation
// passing and client hints intact. That leaves a policy question
// (`design.kb/030-requirements.kb/unblocked-sessions.md` calls honest
// self-identification policy, not leakage) which is only answerable by
// knowing *what* the gate objects to. Hence this: many UA spellings,
// one session, no human clicking send each time.
//
// Method: lift a real request out of a capture and replay it from the
// page's own context, once per UA variant, changing nothing else. The
// first variant is a control with an untouched UA -- if the control
// fails, the captured credentials have aged out and every other result
// this run is meaningless, so the script says so and stops.
//
// Costs a real generation per variant. Keep the variant list short.
import { createReadStream } from "node:fs";
import { createInterface } from "node:readline";
import { parseArgs } from "node:util";
import puppeteer from "puppeteer-core";
import { chromium } from "playwright-core";
import { cachePath } from "../src/cache.mjs";

const { values, positionals } = parseArgs({
  options: {
    match: { type: "string", default: "GenerateContent" },
    profile: { type: "string", default: "default_profile" },
    origin: { type: "string", default: "https://aistudio.google.com/" },
  },
  allowPositionals: true,
});

const TOOL = "har-browse/1.0.0";
const HOME = "https://github.com/bukzor/prototype.chatfs";

// Each variant is a way of being honest about what we are. The
// question is which of them a provider treats as disqualifying.
const VARIANTS = [
  { name: "control: untouched UA", ua: (base) => base },
  { name: "suffix + contact URL (shipped)", ua: (base) => `${base} ${TOOL} (+${HOME})` },
  { name: "suffix, no URL", ua: (base) => `${base} ${TOOL}` },
  { name: "suffix, no version", ua: (base) => `${base} har-browse` },
  // Is any trailing product refused, or only a name that reads like a
  // tool? Distinguishes "unknown token in the product list" from a
  // keyword match on ours.
  { name: "suffix, neutral name", ua: (base) => `${base} Foo/1.0` },
  {
    name: "inside the platform comment",
    ua: (base) => base.replace("(X11; Linux x86_64)", `(X11; Linux x86_64; ${TOOL})`),
  },
  {
    name: "platform comment, with contact URL",
    ua: (base) =>
      base.replace("(X11; Linux x86_64)", `(X11; Linux x86_64; ${TOOL}; +${HOME})`),
  },
];

/** Lift the last matching request (url, headers, body) out of a capture. */
async function templateFrom(path, match) {
  /** @type {Map<string, any>} */
  const requests = new Map();
  let found = null;
  for await (const line of createInterface({
    input: createReadStream(path),
    crlfDelay: Infinity,
  })) {
    if (!line.trim()) continue;
    let event;
    try {
      event = JSON.parse(line);
    } catch {
      continue;
    }
    if (event.method === "Network.requestWillBeSent") {
      requests.set(event.params.requestId, event.params.request);
    } else if (event.method === "Network.responseReceived") {
      const url = event.params.response?.url ?? "";
      const request = requests.get(event.params.requestId);
      // Skip the CORS preflight, which carries no body.
      if (url.includes(match) && request?.postData) found = request;
    }
  }
  return found;
}

const capture = positionals[0];
if (!capture) {
  console.error("usage: ua-gate-probe.mjs <capture.jsonl> [--match SUBSTRING]");
  process.exit(2);
}
const template = await templateFrom(capture, values.match);
if (!template) {
  console.error(`no request with a body matching ${values.match} in ${capture}`);
  process.exit(1);
}

// The browser owns these: sending captured copies would either be
// ignored or would contradict the UA we are testing.
const BROWSER_OWNED = /^(sec-ch-ua|user-agent|host|origin|referer|content-length|cookie)/i;
const headers = Object.fromEntries(
  Object.entries(template.headers).filter(([k]) => !BROWSER_OWNED.test(k)),
);

console.log(`replaying ${template.url.slice(0, 90)}`);
console.log(`  ${Object.keys(headers).length} headers, ${template.postData.length} byte body\n`);

const browser = await puppeteer.launch({
  executablePath: process.env.HAR_BROWSE_BROWSER ?? chromium.executablePath(),
  userDataDir: cachePath("profile", values.profile),
  headless: false,
  defaultViewport: null,
  networkEnabled: false,
  ignoreDefaultArgs: ["--enable-automation"],
  args: ["--disable-blink-features=AutomationControlled", "--hide-crash-restore-bubble"],
});
try {
  const page = (await browser.pages())[0] ?? (await browser.newPage());
  await page.goto(values.origin, { waitUntil: "domcontentloaded" });
  const cdp = await page.createCDPSession();
  const baseUA = await browser.userAgent();

  for (const variant of VARIANTS) {
    const ua = variant.ua(baseUA);
    await cdp.send("Network.setUserAgentOverride", { userAgent: ua });
    const result = await page.evaluate(
      async (url, body, hdrs, extra) => {
        const h = { ...hdrs };
        if (extra) h[extra[0]] = extra[1];
        try {
          const res = await fetch(url, {
            method: "POST",
            headers: h,
            body,
            credentials: "include",
          });
          return { status: res.status, text: (await res.text()).slice(0, 120) };
        } catch (e) {
          return { status: 0, text: `fetch failed: ${e.message}` };
        }
      },
      template.url,
      template.postData,
      headers,
      variant.header ?? null,
    );

    const verdict = result.status === 200 ? "OK     " : "REFUSED";
    console.log(`${verdict} ${String(result.status).padEnd(4)} ${variant.name}`);
    console.log(`             ua: ...${ua.slice(-72)}`);
    if (result.status !== 200) console.log(`             ${result.text.replace(/\n/g, " ")}`);

    if (variant === VARIANTS[0] && result.status !== 200) {
      console.log(
        "\nControl failed: the captured credentials have expired, or the\n" +
          "request is not replayable. Take a fresh capture and rerun --\n" +
          "no conclusion can be drawn from the variants below it.",
      );
      break;
    }
  }
} finally {
  await browser.close();
}
