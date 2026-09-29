// Usage: node check_browser.cjs /absolute/report-dir [path-to-playwright-module] [chrome-executable]
const fs=require('fs'),path=require('path');
const {pathToFileURL}=require('url');
(async()=>{
 const root=path.resolve(process.argv[2]||'.');
 let playwright;try{playwright=require(process.argv[3]||'playwright')}catch(e){throw new Error('Playwright unavailable; supply installed module path. No browser validation completed.')}
 const browser=await playwright.chromium.launch({headless:true,...(process.argv[4]?{executablePath:process.argv[4]}:{})});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));await page.route(/^https?:/,r=>r.abort());
  await page.goto(pathToFileURL(path.join(root,'index.html')).href);
  await page.evaluate(async()=>{await Promise.all([...document.querySelectorAll('img[src]')].map(im=>{im.loading='eager';return im.decode().catch(()=>{})}))});
  const result=await page.evaluate(()=>({offline:true,brokenImages:[...document.querySelectorAll('img[src]')].filter(i=>!i.naturalWidth).length,desktopOverflow:document.documentElement.scrollWidth>innerWidth}));
  await page.screenshot({path:path.join(root,'qa-desktop.png')});
  result.media=[];
  for(const media of await page.locator('video,audio').all()){
   const value=await media.evaluate(async m=>{m.muted=true;try{await m.play();await new Promise(r=>setTimeout(r,1000));const value={file:m.getAttribute('src'),playing:m.currentTime>0,duration:m.duration};m.pause();return value}catch(e){return {file:m.getAttribute('src'),playing:false,error:e.name}}});result.media.push(value);
  }
  result.zoom='not_present';
  if(await page.locator('.zoom').count()){
   await page.locator('.zoom').first().click();
   result.zoom=await page.locator('#lightbox').evaluate(async d=>{await d.querySelector('img').decode();return d.open&&d.querySelector('img').naturalWidth>0});
   await page.keyboard.press('Escape');result.escClose=await page.locator('#lightbox').evaluate(d=>!d.open);
  }
  await page.setViewportSize({width:390,height:844});await page.goto(pathToFileURL(path.join(root,'index.html')).href);
  result.mobileOverflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  await page.screenshot({path:path.join(root,'qa-mobile.png')});result.errors=errors;
  result.pass=!result.brokenImages&&!result.desktopOverflow&&!result.mobileOverflow&&!errors.length&&result.media.every(m=>m.playing)&&(result.zoom==='not_present'||(result.zoom&&result.escClose));
  fs.writeFileSync(path.join(root,'browser-checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));if(!result.pass)process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e.message);process.exitCode=1});
