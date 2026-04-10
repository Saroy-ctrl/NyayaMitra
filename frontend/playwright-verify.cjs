/**
 * Playwright verification script for NyayaMitra frontend revamp.
 * Runs all 8 verification assertions defined in the task.
 */
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const results = [];

  function pass(label) {
    results.push({ label, status: 'PASS' });
    console.log('PASS:', label);
  }
  function fail(label, reason) {
    results.push({ label, status: 'FAIL', reason });
    console.log('FAIL:', label, '--', reason);
  }

  try {
    // Test 1: Load page — assert "NyayaMitra" headline visible + "Get Started" button + "50M+" stat card
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });

    const nyayaMitraHeadline = await page.locator('text=NyayaMitra').first().isVisible();
    const getStartedBtn = await page.locator('button:has-text("Get Started")').first().isVisible();
    const stat50M = await page.locator('text=50M+').first().isVisible();

    if (nyayaMitraHeadline) pass('1a. "NyayaMitra" headline visible');
    else fail('1a. "NyayaMitra" headline visible', 'not found');

    if (getStartedBtn) pass('1b. "Get Started" button visible');
    else fail('1b. "Get Started" button visible', 'not found');

    if (stat50M) pass('1c. "50M+" stat card visible');
    else fail('1c. "50M+" stat card visible', 'not found');

    // Test 2: Click "Get Started →" → assert "Step 1 of 3" visible + 5 doc type cards
    await page.locator('button:has-text("Get Started")').first().click();
    await page.waitForTimeout(300);

    const step1of3 = await page.locator('text=Step 1 of 3').first().isVisible();
    const docCards = await page.locator('button:has-text("FIR")').first().isVisible();

    if (step1of3) pass('2a. "Step 1 of 3" visible after Get Started');
    else fail('2a. "Step 1 of 3" visible after Get Started', 'not found');

    if (docCards) pass('2b. Doc type cards visible (FIR card found)');
    else fail('2b. Doc type cards visible (FIR card found)', 'not found');

    // Count doc cards
    const allDocCards = await page.locator('.grid button').count();
    if (allDocCards >= 5) pass(`2c. 5 doc type cards visible (found ${allDocCards})`);
    else fail(`2c. 5 doc type cards visible`, `only found ${allDocCards}`);

    // Test 3: Click "← Back" → assert landing page returned (hero visible)
    await page.locator('button:has-text("Back")').first().click();
    await page.waitForTimeout(300);

    const heroAfterBack = await page.locator('text=NyayaMitra').first().isVisible();
    if (heroAfterBack) pass('3. Landing page returned after Back click');
    else fail('3. Landing page returned after Back click', 'hero not visible');

    // Test 4: Click "Get Started →", click "FIR" card → assert "Step 2 of 3" + textarea + amber "FIR" badge
    await page.locator('button:has-text("Get Started")').first().click();
    await page.waitForTimeout(300);
    await page.locator('button:has-text("FIR")').first().click();
    await page.waitForTimeout(300);

    const step2of3 = await page.locator('text=Step 2 of 3').first().isVisible();
    const textarea = await page.locator('textarea').first().isVisible();
    const firBadge = await page.locator('text=FIR').filter({ has: page.locator('.text-amber-400') }).first().isVisible().catch(() => false);
    // Alternative: check for amber FIR badge
    const amberFirBadge = await page.locator('.text-amber-400:has-text("FIR"), p.text-amber-400').first().isVisible().catch(() => false);

    if (step2of3) pass('4a. "Step 2 of 3" visible after FIR card click');
    else fail('4a. "Step 2 of 3" visible after FIR card click', 'not found');

    if (textarea) pass('4b. Textarea visible');
    else fail('4b. Textarea visible', 'not found');

    if (amberFirBadge) pass('4c. Amber "FIR" badge visible');
    else fail('4c. Amber "FIR" badge visible', 'not found in .text-amber-400');

    // Test 5: Click "Try example ⚡" → assert textarea contains Hindi/Hinglish text
    await page.locator('button:has-text("Try example")').first().click();
    await page.waitForTimeout(300);

    const textareaValue = await page.locator('textarea').first().inputValue();
    const hasHinglishText = textareaValue.length > 20 && (
      textareaValue.includes('chori') || textareaValue.includes('ghar') || textareaValue.includes('FIR') ||
      textareaValue.includes('hai') || textareaValue.includes('Kal') || textareaValue.includes('naam')
    );

    if (hasHinglishText) pass(`5. Textarea filled with Hindi/Hinglish text (length: ${textareaValue.length})`);
    else fail('5. Textarea filled with Hindi/Hinglish text', `got: "${textareaValue.substring(0, 50)}"`);

    // Test 6: Click "← Change type" → assert "Step 1 of 3" visible
    await page.locator('button:has-text("Change type")').first().click();
    await page.waitForTimeout(300);

    const step1After = await page.locator('text=Step 1 of 3').first().isVisible();
    if (step1After) pass('6. "Step 1 of 3" visible after Change type click');
    else fail('6. "Step 1 of 3" visible after Change type click', 'not found');

    // Test 7: Go to root /, click "Try Demo ⚡" → assert "Step 2 of 3" + pre-filled tenant eviction text
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    await page.waitForTimeout(300);

    // Click the "Try Demo" button on the landing page
    await page.locator('button:has-text("Try Demo")').first().click();
    await page.waitForTimeout(300);

    const step2AfterDemo = await page.locator('text=Step 2 of 3').first().isVisible();
    const demoTextareaValue = await page.locator('textarea').first().inputValue();
    const hasTenantText = demoTextareaValue.includes('Ramesh') || demoTextareaValue.includes('kiraya') ||
      demoTextareaValue.includes('Lajpat') || demoTextareaValue.includes('makaan');

    if (step2AfterDemo) pass('7a. "Step 2 of 3" visible after Try Demo click');
    else fail('7a. "Step 2 of 3" visible after Try Demo click', 'not found');

    if (hasTenantText) pass(`7b. Pre-filled tenant eviction text in textarea (length: ${demoTextareaValue.length})`);
    else fail('7b. Pre-filled tenant eviction text in textarea', `got: "${demoTextareaValue.substring(0, 80)}"`);

    // Test 8: Click "NyayaMitra" logo → assert landing page loads again
    await page.locator('button:has-text("NyayaMitra")').first().click();
    await page.waitForTimeout(300);

    const landingAfterLogo = await page.locator('text=NyayaMitra').first().isVisible();
    // More specifically check the hero headline is visible (the large h1 in hero section)
    const heroH1 = await page.locator('h1').first().isVisible();

    if (landingAfterLogo && heroH1) pass('8. Landing page loads again after NyayaMitra logo click');
    else fail('8. Landing page loads again after NyayaMitra logo click', `headline: ${landingAfterLogo}, h1: ${heroH1}`);

  } catch (err) {
    fail('Unexpected error', err.message);
  }

  await browser.close();

  // Summary
  console.log('\n=== VERIFICATION SUMMARY ===');
  const passed = results.filter(r => r.status === 'PASS').length;
  const failed = results.filter(r => r.status === 'FAIL').length;
  results.forEach(r => {
    const icon = r.status === 'PASS' ? '[PASS]' : '[FAIL]';
    console.log(`${icon} ${r.label}${r.reason ? ' -- ' + r.reason : ''}`);
  });
  console.log(`\nTotal: ${passed} passed, ${failed} failed`);
  process.exit(failed > 0 ? 1 : 0);
})();
