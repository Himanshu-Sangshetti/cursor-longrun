// Opens a URL at desktop and mobile width, prints evidence lines, exits 0 pass / 1 fail.
// Called by live.sh with NODE_PATH pointing at the node_modules that holds playwright.
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const require = createRequire(join(process.env.NODE_PATH || ".", "x.js"));
const { chromium } = require("playwright");
const [url, ...expect] = process.argv.slice(2);
const out = join(process.env.TMPDIR || tmpdir(), "longrun-live");
mkdirSync(out, { recursive: true });
const stamp = new Date().toISOString().replace(/[:.]/g, "-");
const fails = [];

const browser = await chromium.launch();
for (const [label, width] of [["desktop", 1280], ["mobile", 390]]) {
  const page = await browser.newPage({ viewport: { width, height: 900 } });
  const errors = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  const res = await page.goto(url, { waitUntil: "networkidle", timeout: 45000 }).catch((e) => ({ status: () => 0, e }));
  const status = res.status();
  const text = await page.evaluate(() => document.body?.innerText || "");
  const words = text.split(/\s+/).filter(Boolean).length;
  const brokenImgs = await page.evaluate(() => [...document.images].filter((i) => i.complete && i.naturalWidth === 0).length);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  const shot = join(out, `${stamp}-${label}.png`);
  await page.screenshot({ path: shot, fullPage: true });
  console.log(`${label}: status ${status}, words ${words}, broken images ${brokenImgs}, console errors ${errors.length}, horizontal overflow ${overflow}px`);
  console.log(`${label}: screenshot ${shot}`);
  if (status < 200 || status >= 400) fails.push(`${label} status ${status}`);
  if (brokenImgs) fails.push(`${label} ${brokenImgs} broken images`);
  if (overflow > 1) fails.push(`${label} overflows by ${overflow}px`);
  for (const t of expect) {
    const ok = text.includes(t);
    console.log(`${label}: expected "${t}" ${ok ? "found" : "MISSING"}`);
    if (!ok) fails.push(`${label} missing "${t}"`);
  }
  await page.close();
}
await browser.close();
if (fails.length) { console.log(`FAIL live: ${fails.join("; ")}`); process.exit(1); }
console.log("PASS live");
