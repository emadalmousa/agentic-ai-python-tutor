const puppeteer = require('/home/emad-almousa/.npm/_npx/7d92d9a2d2ccc630/node_modules/puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 900, deviceScaleFactor: 2 });

  const filePath = path.resolve(__dirname, 'phase3.html');
  await page.goto('file://' + filePath, { waitUntil: 'networkidle0' });

  const slideCount = await page.evaluate(() => document.querySelectorAll('.slide').length);
  console.log(`Found ${slideCount} slides`);

  const screenshots = [];
  for (let i = 0; i < slideCount; i++) {
    await page.evaluate((idx) => {
      const allSlides = document.querySelectorAll('.slide');
      allSlides.forEach(s => s.classList.remove('active'));
      allSlides[idx].classList.add('active');
      // set font size like the JS does
      document.documentElement.style.fontSize = idx === 0 ? '130%' : '149.5%';
    }, i);
    await new Promise(r => setTimeout(r, 400));
    const imgBuffer = await page.screenshot({ type: 'png' });
    screenshots.push(imgBuffer);
    console.log(`  Captured slide ${i + 1}/${slideCount}`);
  }

  await browser.close();

  // Build PDF with one image per page using raw PDF generation
  // Use Chrome's built-in PDF from a data-URI multi-page approach via a helper page
  const browser2 = await puppeteer.launch({
    executablePath: '/usr/bin/google-chrome',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page2 = await browser2.newPage();

  const imgsHtml = screenshots.map((buf, i) => {
    const b64 = buf.toString('base64');
    return `<div class="page"><img src="data:image/png;base64,${b64}" /></div>`;
  }).join('\n');

  const html = `<!DOCTYPE html>
<html>
<head>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #000; }
  .page {
    width: 297mm;
    height: 167.0625mm;
    page-break-after: always;
    overflow: hidden;
  }
  .page img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  @page { size: 297mm 167.0625mm; margin: 0; }
</style>
</head>
<body>${imgsHtml}</body>
</html>`;

  await page2.setContent(html, { waitUntil: 'networkidle0' });
  await page2.pdf({
    path: path.resolve(__dirname, 'phase3.pdf'),
    width: '297mm',
    height: '167.0625mm',
    printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 }
  });

  await browser2.close();
  console.log('PDF saved: phase3.pdf');
})().catch(e => { console.error(e); process.exit(1); });
