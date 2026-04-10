const { test, expect, chromium } = require('@playwright/test');

const BASE = 'http://localhost:5174';

test('full navigation flow', async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Test 1: Landing page
  await page.goto(BASE);
  await page.waitForTimeout(500);
  
  const heroHindi = await page.locator('text=\u0928\u094d\u092f\u093e\u092f\u092e\u093f\u0924\u094d\u0930').first().isVisible();
  const heroEN = await page.locator('text=NyayaMitra').first().isVisible();
  const getStarted = await page.locator('button:has-text("Get Started")').first().isVisible();
  const stat50m = await page.locator('text=50M+').first().isVisible();
  
  console.log('LANDING - hero Hindi visible:', heroHindi);
  console.log('LANDING - hero EN visible:', heroEN);
  console.log('LANDING - Get Started visible:', getStarted);
  console.log('LANDING - 50M+ stat visible:', stat50m);
  
  // Test 2: Click Get Started -> SELECT_DOC
  await page.locator('button:has-text("Get Started")').first().click();
  await page.waitForTimeout(400);
  
  const step1 = await page.locator('text=Step 1 of 3').isVisible();
  console.log('SELECT_DOC - Step 1 of 3 visible:', step1);
  
  // Test 3: Click Back -> LANDING
  await page.locator('button:has-text("Back")').click();
  await page.waitForTimeout(400);
  
  const heroAgain = await page.locator('text=NyayaMitra').first().isVisible();
  console.log('BACK to LANDING - hero visible:', heroAgain);
  
  // Test 4: Get Started -> FIR -> INPUT_CASE
  await page.locator('button:has-text("Get Started")').first().click();
  await page.waitForTimeout(400);
  await page.locator('button:has-text("FIR")').first().click();
  await page.waitForTimeout(400);
  
  const step2 = await page.locator('text=Step 2 of 3').isVisible();
  const textarea = await page.locator('textarea').isVisible();
  console.log('INPUT_CASE - Step 2 of 3 visible:', step2);
  console.log('INPUT_CASE - textarea visible:', textarea);
  
  // Test 5: Try example fills textarea
  await page.locator('button:has-text("Try example")').click();
  await page.waitForTimeout(300);
  const textVal = await page.locator('textarea').inputValue();
  console.log('TRY EXAMPLE - textarea filled (len):', textVal.length);
  
  // Test 6: Change type -> SELECT_DOC
  await page.locator('button:has-text("Change type")').click();
  await page.waitForTimeout(400);
  const step1Again = await page.locator('text=Step 1 of 3').isVisible();
  console.log('BACK to SELECT_DOC - Step 1 visible:', step1Again);
  
  // Test 7: Landing Try Demo
  await page.goto(BASE);
  await page.waitForTimeout(500);
  await page.locator('button:has-text("Try Demo")').first().click();
  await page.waitForTimeout(400);
  const step2Demo = await page.locator('text=Step 2 of 3').isVisible();
  const demoText = await page.locator('textarea').inputValue();
  console.log('TRY DEMO - Step 2 visible:', step2Demo);
  console.log('TRY DEMO - pre-filled text length:', demoText.length);
  
  // Test 8: Click NyayaMitra logo -> LANDING
  await page.locator('button:has-text("NyayaMitra")').first().click();
  await page.waitForTimeout(400);
  const landingBack = await page.locator('text=NyayaMitra').first().isVisible();
  console.log('LOGO CLICK - landing visible:', landingBack);
  
  await browser.close();
});
