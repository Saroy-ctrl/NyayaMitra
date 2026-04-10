/**
 * animations.spec.cjs
 * Playwright verification for shader, particles, and micro-animation additions.
 */
const { chromium } = require('@playwright/test');

const BASE = 'http://localhost:5173';

async function run() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto(BASE);
  await page.waitForTimeout(800);

  // CHECK 1: ShaderBackground canvas exists in DOM
  const canvasCount = await page.locator('canvas').count();
  console.log('CHECK 1 - canvas elements in DOM:', canvasCount, canvasCount >= 1 ? 'PASS' : 'FAIL');

  // CHECK 2: SpaceParticles — second canvas present (landing page)
  console.log('CHECK 2 - SpaceParticles canvas present:', canvasCount >= 2 ? 'PASS' : 'FAIL (count=' + canvasCount + ')');

  // CHECK 3: animate-float on hero headline
  const floatClass = await page.locator('h1.animate-float').count();
  console.log('CHECK 3 - animate-float on h1:', floatClass > 0 ? 'PASS' : 'FAIL');

  // CHECK 4: stat-reveal-1 on first stat card
  const statReveal1 = await page.locator('.stat-reveal-1').count();
  console.log('CHECK 4 - stat-reveal-1 class present:', statReveal1 > 0 ? 'PASS' : 'FAIL');

  // CHECK 5: Navigate to SELECT_DOC and check card-reveal classes
  await page.locator('button:has-text("Get Started")').first().click();
  await page.waitForTimeout(400);
  const cardReveal = await page.locator('.card-reveal').count();
  console.log('CHECK 5 - card-reveal classes on doc cards:', cardReveal > 0 ? 'PASS (count=' + cardReveal + ')' : 'FAIL');

  // CHECK 6: Full nav flow — click FIR -> textarea visible
  await page.locator('button:has-text("FIR")').first().click();
  await page.waitForTimeout(400);
  const textarea = await page.locator('textarea').isVisible();
  const step2 = await page.locator('text=Step 2 of 3').isVisible();
  console.log('CHECK 6a - INPUT_CASE textarea visible:', textarea ? 'PASS' : 'FAIL');
  console.log('CHECK 6b - Step 2 of 3 visible:', step2 ? 'PASS' : 'FAIL');

  // CHECK 7: Change type -> back to SELECT_DOC
  await page.locator('button:has-text("Change type")').click();
  await page.waitForTimeout(400);
  const step1Back = await page.locator('text=Step 1 of 3').isVisible();
  console.log('CHECK 7 - Change type returns to SELECT_DOC:', step1Back ? 'PASS' : 'FAIL');

  // CHECK 8: Header logo reset -> landing page
  await page.locator('button:has-text("NyayaMitra")').first().click();
  await page.waitForTimeout(400);
  const landingBack = await page.locator('h1.animate-float').count();
  console.log('CHECK 8 - Logo click returns to LANDING (h1.animate-float):', landingBack > 0 ? 'PASS' : 'FAIL');

  // CHECK 9: Background is not flat black — shader adds subtle texture
  // We check the fixed div with -z-10 class exists (ShaderBackground wrapper)
  const shaderDiv = await page.locator('div.fixed.-z-10.pointer-events-none').count();
  console.log('CHECK 9 - ShaderBackground wrapper div present:', shaderDiv > 0 ? 'PASS' : 'FAIL');

  // CHECK 10: Stat cards have backdrop-blur-sm
  const blurCards = await page.locator('.stat-reveal.backdrop-blur-sm').count();
  console.log('CHECK 10 - Stat cards have backdrop-blur-sm:', blurCards > 0 ? 'PASS' : 'FAIL');

  await browser.close();
}

run().catch(err => { console.error(err); process.exit(1); });
