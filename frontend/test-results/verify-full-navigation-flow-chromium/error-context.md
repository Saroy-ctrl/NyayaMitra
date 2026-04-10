# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: verify.spec.cjs >> full navigation flow
- Location: tests\verify.spec.cjs:5:1

# Error details

```
Error: locator.click: Error: strict mode violation: locator('button:has-text("Back")') resolved to 2 elements:
    1) <button class="flex items-center gap-1 text-sm text-zinc-500 hover:text-zinc-300 transition-colors duration-200">← Back</button> aka getByRole('button', { name: '← Back' })
    2) <button class="flex flex-col gap-3 rounded-xl border p-5 text-left transition-all duration-200 cursor-pointer border-zinc-800 bg-zinc-900 hover:border-amber-500 hover:bg-zinc-800 hover:scale-[1.02] hover:shadow-lg hover:shadow-amber-500/10">…</button> aka getByRole('button', { name: '⚖️ Legal Notice कानूनी नोटिस' })

Call log:
  - waiting for locator('button:has-text("Back")')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - button "⚖ NyayaMitra AI Legal Document Assistant • न्यायमित्र" [ref=e6] [cursor=pointer]:
        - generic [ref=e7]:
          - generic [ref=e8]: ⚖
          - generic [ref=e9]:
            - text: NyayaMitra
            - paragraph [ref=e10]: AI Legal Document Assistant • न्यायमित्र
      - generic [ref=e11]: Powered by Llama 3.3 • भारत
  - main [ref=e12]:
    - generic [ref=e14]:
      - generic [ref=e15]:
        - generic [ref=e16]:
          - paragraph [ref=e17]: Step 1 of 3
          - button "← Back" [ref=e18] [cursor=pointer]
        - heading "What document do you need?" [level=2] [ref=e19]
        - paragraph [ref=e20]: आपको किस प्रकार का दस्तावेज़ चाहिए? नीचे से चुनें।
      - generic [ref=e21]:
        - button "📋 FIR प्रथम सूचना रिपोर्ट Report a crime to the police पुलिस में शिकायत दर्ज करें BNS 2023 + BNSS 2023" [ref=e22] [cursor=pointer]:
          - generic [ref=e23]: 📋
          - generic [ref=e24]:
            - paragraph [ref=e25]: FIR
            - paragraph [ref=e26]: प्रथम सूचना रिपोर्ट
          - paragraph [ref=e27]: Report a crime to the police
          - paragraph [ref=e28]: पुलिस में शिकायत दर्ज करें
          - generic [ref=e29]: BNS 2023 + BNSS 2023
        - button "⚖️ Legal Notice कानूनी नोटिस Formal demand letter with legal backing कानूनी मांग पत्र BNS 2023" [ref=e30] [cursor=pointer]:
          - generic [ref=e31]: ⚖️
          - generic [ref=e32]:
            - paragraph [ref=e33]: Legal Notice
            - paragraph [ref=e34]: कानूनी नोटिस
          - paragraph [ref=e35]: Formal demand letter with legal backing
          - paragraph [ref=e36]: कानूनी मांग पत्र
          - generic [ref=e37]: BNS 2023
        - button "🛒 Consumer Complaint उपभोक्ता शिकायत File with Consumer Commission उपभोक्ता आयोग में शिकायत Consumer Protection Act 2019" [ref=e38] [cursor=pointer]:
          - generic [ref=e39]: 🛒
          - generic [ref=e40]:
            - paragraph [ref=e41]: Consumer Complaint
            - paragraph [ref=e42]: उपभोक्ता शिकायत
          - paragraph [ref=e43]: File with Consumer Commission
          - paragraph [ref=e44]: उपभोक्ता आयोग में शिकायत
          - generic [ref=e45]: Consumer Protection Act 2019
        - button "💰 Cheque Bounce Notice चेक बाउंस नोटिस Demand payment for dishonoured cheque बाउंस हुए चेक की वसूली NI Act §138" [ref=e46] [cursor=pointer]:
          - generic [ref=e47]: 💰
          - generic [ref=e48]:
            - paragraph [ref=e49]: Cheque Bounce Notice
            - paragraph [ref=e50]: चेक बाउंस नोटिस
          - paragraph [ref=e51]: Demand payment for dishonoured cheque
          - paragraph [ref=e52]: बाउंस हुए चेक की वसूली
          - generic [ref=e53]: NI Act §138
        - button "🏠 Tenant Eviction Notice बेदखली नोटिस Notice to vacate the premises किरायेदार को खाली करने की नोटिस Transfer of Property Act + Delhi RCA" [ref=e54] [cursor=pointer]:
          - generic [ref=e55]: 🏠
          - generic [ref=e56]:
            - paragraph [ref=e57]: Tenant Eviction Notice
            - paragraph [ref=e58]: बेदखली नोटिस
          - paragraph [ref=e59]: Notice to vacate the premises
          - paragraph [ref=e60]: किरायेदार को खाली करने की नोटिस
          - generic [ref=e61]: Transfer of Property Act + Delhi RCA
      - generic [ref=e62]:
        - paragraph [ref=e63]: Want to see how it works? Try a pre-filled example.
        - button "⚡ Try Demo" [ref=e64] [cursor=pointer]:
          - generic [ref=e65]: ⚡
          - text: Try Demo
  - contentinfo [ref=e66]:
    - paragraph [ref=e67]: NyayaMitra • Not a substitute for professional legal advice • कानूनी सलाह के लिए वकील से मिलें
```

# Test source

```ts
  1  | const { test, expect, chromium } = require('@playwright/test');
  2  | 
  3  | const BASE = 'http://localhost:5174';
  4  | 
  5  | test('full navigation flow', async () => {
  6  |   const browser = await chromium.launch({ headless: true });
  7  |   const page = await browser.newPage();
  8  |   
  9  |   // Test 1: Landing page
  10 |   await page.goto(BASE);
  11 |   await page.waitForTimeout(500);
  12 |   
  13 |   const heroHindi = await page.locator('text=\u0928\u094d\u092f\u093e\u092f\u092e\u093f\u0924\u094d\u0930').first().isVisible();
  14 |   const heroEN = await page.locator('text=NyayaMitra').first().isVisible();
  15 |   const getStarted = await page.locator('button:has-text("Get Started")').first().isVisible();
  16 |   const stat50m = await page.locator('text=50M+').first().isVisible();
  17 |   
  18 |   console.log('LANDING - hero Hindi visible:', heroHindi);
  19 |   console.log('LANDING - hero EN visible:', heroEN);
  20 |   console.log('LANDING - Get Started visible:', getStarted);
  21 |   console.log('LANDING - 50M+ stat visible:', stat50m);
  22 |   
  23 |   // Test 2: Click Get Started -> SELECT_DOC
  24 |   await page.locator('button:has-text("Get Started")').first().click();
  25 |   await page.waitForTimeout(400);
  26 |   
  27 |   const step1 = await page.locator('text=Step 1 of 3').isVisible();
  28 |   console.log('SELECT_DOC - Step 1 of 3 visible:', step1);
  29 |   
  30 |   // Test 3: Click Back -> LANDING
> 31 |   await page.locator('button:has-text("Back")').click();
     |                                                 ^ Error: locator.click: Error: strict mode violation: locator('button:has-text("Back")') resolved to 2 elements:
  32 |   await page.waitForTimeout(400);
  33 |   
  34 |   const heroAgain = await page.locator('text=NyayaMitra').first().isVisible();
  35 |   console.log('BACK to LANDING - hero visible:', heroAgain);
  36 |   
  37 |   // Test 4: Get Started -> FIR -> INPUT_CASE
  38 |   await page.locator('button:has-text("Get Started")').first().click();
  39 |   await page.waitForTimeout(400);
  40 |   await page.locator('button:has-text("FIR")').first().click();
  41 |   await page.waitForTimeout(400);
  42 |   
  43 |   const step2 = await page.locator('text=Step 2 of 3').isVisible();
  44 |   const textarea = await page.locator('textarea').isVisible();
  45 |   console.log('INPUT_CASE - Step 2 of 3 visible:', step2);
  46 |   console.log('INPUT_CASE - textarea visible:', textarea);
  47 |   
  48 |   // Test 5: Try example fills textarea
  49 |   await page.locator('button:has-text("Try example")').click();
  50 |   await page.waitForTimeout(300);
  51 |   const textVal = await page.locator('textarea').inputValue();
  52 |   console.log('TRY EXAMPLE - textarea filled (len):', textVal.length);
  53 |   
  54 |   // Test 6: Change type -> SELECT_DOC
  55 |   await page.locator('button:has-text("Change type")').click();
  56 |   await page.waitForTimeout(400);
  57 |   const step1Again = await page.locator('text=Step 1 of 3').isVisible();
  58 |   console.log('BACK to SELECT_DOC - Step 1 visible:', step1Again);
  59 |   
  60 |   // Test 7: Landing Try Demo
  61 |   await page.goto(BASE);
  62 |   await page.waitForTimeout(500);
  63 |   await page.locator('button:has-text("Try Demo")').first().click();
  64 |   await page.waitForTimeout(400);
  65 |   const step2Demo = await page.locator('text=Step 2 of 3').isVisible();
  66 |   const demoText = await page.locator('textarea').inputValue();
  67 |   console.log('TRY DEMO - Step 2 visible:', step2Demo);
  68 |   console.log('TRY DEMO - pre-filled text length:', demoText.length);
  69 |   
  70 |   // Test 8: Click NyayaMitra logo -> LANDING
  71 |   await page.locator('button:has-text("NyayaMitra")').first().click();
  72 |   await page.waitForTimeout(400);
  73 |   const landingBack = await page.locator('text=NyayaMitra').first().isVisible();
  74 |   console.log('LOGO CLICK - landing visible:', landingBack);
  75 |   
  76 |   await browser.close();
  77 | });
  78 | 
```