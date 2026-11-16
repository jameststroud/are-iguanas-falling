// Re-takes the two site screenshots in assets/press/ (YES night and NO night).
// Dev tool only, the site does not use it. From the repo folder:
//   python3 -m http.server 8765     (in one terminal)
//   npm install playwright && npx playwright install chromium   (first time only)
//   node scripts/press_screenshots.js
// The YES shot uses a made-up cold forecast so it can be taken on a warm night.
const { chromium } = require("playwright");
const fs = require("fs");
const BASE = process.env.BASE || "http://localhost:8765/";
const real = JSON.parse(fs.readFileSync("status.json", "utf8"));
const COLD = [41, 43, 46, 47, 45, 52, 39, 37]; // illustrative only, not a real forecast
const WARM = [66, 67, 65, 63, 62, 72, 60, 58];
(async () => {
  const browser = await chromium.launch();
  for (const state of ["yes", "no"]) {
    const s = JSON.parse(JSON.stringify(real));
    s.cities.forEach((c, i) => { c.min = (state === "yes" ? COLD : WARM)[i]; });
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 1180 }, deviceScaleFactor: 2, colorScheme: "light" });
    await ctx.addInitScript(() => { try { localStorage.setItem("iguana-lang", "en"); } catch (e) {} });
    const page = await ctx.newPage();
    await page.route("**/status.json*", r => r.fulfill({ contentType: "application/json", body: JSON.stringify(s) }));
    await page.route("**/falls.json*", r => r.fulfill({ contentType: "application/json", body: '{"count":0,"points":[]}' }));
    await page.route(/gc\.zgo\.at|goatcounter\.com/, r => r.abort());
    await page.goto(BASE + "index.html", { waitUntil: "networkidle" });
    await page.waitForTimeout(3500); // let the iguana finish falling
    await page.screenshot({ path: `assets/press/screenshot-${state}.png` });
    console.log(`wrote assets/press/screenshot-${state}.png`);
    await ctx.close();
  }
  await browser.close();
})();
