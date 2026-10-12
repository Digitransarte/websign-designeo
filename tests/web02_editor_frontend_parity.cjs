/** WEB-02 visual parity gate. Read-only Chrome/Playwright.
 * Baseline (unauthenticated): WEB02_URL=https://wp-lab.designeo.pt node tests/web02_editor_frontend_parity.cjs
 * With authorized editor storageState: WEB02_EDITOR_URL=... WEB02_STORAGE_STATE=... node ...
 * Without editor credentials this checks frontend contracts ONLY and reports editor parity NOT TESTED.
 */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const CASES = [
  { id: 'hero-title', frontend: '.dl-hero h1', editor: '.editor-styles-wrapper .dl-hero h1', minFont: 40 },
  { id: 'services-title', frontend: '#servicos h2', editor: '.editor-styles-wrapper #servicos h2', minFont: 24 },
  { id: 'cta-title', frontend: '#sobre h2', editor: '.editor-styles-wrapper #sobre h2', minFont: 24 },
  { id: 'hero-button', frontend: '.dl-hero .wp-block-button__link', editor: '.editor-styles-wrapper .dl-hero .wp-block-button__link', minContrast: 4.5 },
  { id: 'cta-button', frontend: '#sobre .wp-block-button__link', editor: '.editor-styles-wrapper #sobre .wp-block-button__link' }
];

function luminance(color) {
  const rgb = [...color.matchAll(/[\d.]+/g)].slice(0,3).map(x => +x[0]);
  if (rgb.length !== 3) throw new Error('Unsupported computed color: ' + color);
  return rgb.map(x => {
    const v=x/255;
    return v <= .04045 ? v/12.92 : ((v+.055)/1.055)**2.4;
  }).reduce((sum,x,i) => sum+x*[.2126,.7152,.0722][i],0);
}
function contrast(a,b) {
  const x=luminance(a), y=luminance(b);
  return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);
}
async function measure(page, selector) {
  return page.locator(selector).first().evaluate(el => {
    const s=getComputedStyle(el), r=el.getBoundingClientRect();
    return { text:el.textContent.trim(), fontSize:parseFloat(s.fontSize),
      color:s.color, background:s.backgroundColor, font:s.fontFamily,
      width:r.width, height:r.height, visibility:s.visibility };
  });
}

(async () => {
 const browser=await chromium.launch({headless:true,...(process.env.WEB02_CHROME?{executablePath:process.env.WEB02_CHROME}:{})});
 try {
   const context=await browser.newContext(process.env.WEB02_STORAGE_STATE?
     {storageState:process.env.WEB02_STORAGE_STATE}:{});
   const frontend=await context.newPage();
   await frontend.goto(process.env.WEB02_URL||'https://wp-lab.designeo.pt/',{waitUntil:'networkidle'});
   const editorURL=process.env.WEB02_EDITOR_URL;
   const editor=editorURL?await context.newPage():null;
   if(editor) await editor.goto(editorURL,{waitUntil:'networkidle'});
   const report={frontend:'PASS',editorParity:editor?'PENDING':'NOT_TESTED',cases:[]};
   for(const item of CASES){
     const actual=await measure(frontend,item.frontend);
     if(item.minFont) assert.ok(actual.fontSize>=item.minFont,
       item.id+': frontend type scale regressed: '+actual.fontSize+'px');
     if(item.minContrast && actual.background!=='rgba(0, 0, 0, 0)')
       assert.ok(contrast(actual.color,actual.background)>=item.minContrast,
         item.id+': text/button contrast regressed');
     let other=null;
     if(editor){
       const locator=editor.locator(item.editor).first();
       assert.ok(await locator.count(),item.id+': missing editor component');
       other=await measure(editor,item.editor);
       assert.equal(other.text,actual.text,item.id+': content parity');
       assert.ok(Math.abs(other.fontSize-actual.fontSize)<=1,
         item.id+': font size parity '+other.fontSize+' vs '+actual.fontSize);
     }
     report.cases.push({id:item.id,frontend:actual,editor:other});
   }
   if(editor) report.editorParity='PASS';
   console.log(JSON.stringify(report));
 } finally {await browser.close();}
})().catch(e=>{console.error('WEB02_PARITY_FAIL:',e.message);process.exitCode=1});
