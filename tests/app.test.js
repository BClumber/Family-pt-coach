// End-to-end checks for Family PT Coach (weekly schedule version).
// Run: FAMILY_CODE=4321 PORT=3999 node server.js &  then  node tests/app.test.js
const {chromium}=require('playwright');const fs=require('fs');const os=require('os');const path=require('path');
const BASE='http://localhost:3999';
const MON='2026-11-09T09:00:00';           // a Monday; tests move the phone's clock around this week
const at=(iso)=>new Date(iso).getTime();
const k=(iso)=>iso.slice(0,10);
let pass=0,fail=0;const ok=(c,m)=>{if(c){pass++;console.log('  ✓',m)}else{fail++;console.log('  ✗ FAIL:',m)}};
async function open(b,{when=MON,seed}={}){const ctx=await b.newContext({viewport:{width:390,height:844}});const pg=await ctx.newPage();
  await pg.clock.install({time:at(when)});await pg.route(/fonts\.g/,r=>r.abort());pg.errs=[];pg.on('pageerror',e=>pg.errs.push(e.message));
  await pg.goto(BASE+'/login');await pg.fill('input[name=code]','4321');await pg.click('button');await pg.waitForSelector('#main .card');
  if(seed){await pg.evaluate(seed.fn,seed.arg);await pg.reload();await pg.waitForSelector('#main .card')}
  return{ctx,pg}}
async function setDay(pg,when){await pg.clock.setSystemTime(at(when));await pg.reload();await pg.waitForSelector('#main .card')}
const T=(pg,s)=>pg.textContent(s);const go=(pg,v)=>pg.click(`[data-a=nav][data-id=${v}]`);
const stored=async pg=>{await pg.waitForTimeout(600);return pg.evaluate(()=>({st:JSON.parse(localStorage.getItem('ptc-state')),dd:JSON.parse(localStorage.getItem('ptc-days')||'{}')}))};
const names=async pg=>pg.locator('#main .check h3').allTextContents();
const card=(pg,n)=>pg.locator(`#main .check:has(h3:text-is("${n}"))`);
const tick=async(pg,n)=>{await card(pg,n).locator('[data-a=check]').click();await pg.waitForTimeout(450)};
const loadPlan=async(pg,key)=>{await go(pg,'program');await pg.click('[data-a=presets]');await pg.click(`[data-a=presetpick][data-id=${key}]`);await pg.click('[data-a=presetload]');await pg.waitForTimeout(450)};
// Old (before the weekly schedule) saved data, shaped like a phone that loaded both plans and ticked some exercises
const V2={fn:([days])=>{const ex=(id,name,extra)=>({id,name,sets:2,reps:10,holdSec:0,restSec:30,side:'both',progress:false,...extra});
  const st={v:2,activeId:'me',exampleBanner:false,profiles:[{id:'me',name:'Dovi',hue:0,startDate:'2026-10-26',increment:2,reminder:{time:'07:30'},restDays:[0],
    daily:{id:'daily',exercises:[ex('cc','Cat-cow',{demo:'cat-cow'}),ex('pp','Prone press-up',{demo:'prone-press-up'}),ex('pt','Pelvic tilt',{demo:'pelvic-tilt'}),ex('ng','Sciatic nerve glide',{demo:'nerve-glide'}),ex('hf','Hip flexor stretch',{holdSec:30}),ex('wk','Walk',{unit:'min'})]},
    dayTypes:[{id:'d1',name:'Legs & hips',exercises:[ex('sq','Wall squat',{progress:true})]},{id:'d2',name:'Spine & abs',exercises:[ex('gb','Glute bridge'),ex('db','Dead bug')]},{id:'d3',name:'Arms',exercises:[ex('py','Prone Y raise',{progress:true})]}]}]};
  localStorage.setItem('ptc-state',JSON.stringify(st));localStorage.setItem('ptc-days',JSON.stringify(days))},
 arg:[{'me_2026-11-03':{pid:'me',date:'2026-11-03',dayTypeId:'d1',checked:{sq:true,cc:true,pp:true},reps:{sq:12},pain:3,note:'old note'}}]};

(async()=>{
 const b=await chromium.launch();
 console.log('Server');
 {const r=await fetch(BASE+'/',{redirect:'manual'});ok(r.status===303,'locked without passcode');
  const r2=await fetch(BASE+'/login',{method:'POST',body:'code=0000',headers:{'content-type':'application/x-www-form-urlencoded'}});ok(r2.status===401,'wrong passcode refused');}

 console.log('Fresh phone, weekly schedule');
 {const{ctx,pg}=await open(b);
  ok((await T(pg,'.hero h2')).includes('Legs & hips'),'Monday is a legs day');
  ok((await names(pg)).includes('Glute bridge'),'legs exercises on Monday');
  await tick(pg,'Glute bridge');await pg.reload();await pg.waitForSelector('.check');ok(await card(pg,'Glute bridge').locator('.cb[aria-pressed=true]').count()===1,'check-off survives reload');
  await setDay(pg,'2026-11-11T09:00:00');ok(await pg.locator('#main .check:not(.carry)').count()===0,'Wednesday is a rest day (only carried-over exercises)');
  await go(pg,'program');const tabs=(await pg.locator('[data-a=ptab]').allTextContents()).join('|');ok(/Mon.*Legs/.test(tabs)&&/Wed.*Rest/.test(tabs)&&/Sat.*Rest/.test(tabs),'program shows Mon–Sun schedule');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Old saved data moves over');
 {const{ctx,pg}=await open(b,{seed:V2});const s=await stored(pg);const p=s.st.profiles[0];
  ok(s.st.v===3,'converted to the weekly schedule');
  const lib=p.lib.map(e=>e.name);ok(!lib.some(n=>/press-up|Pelvic|nerve/i.test(n)),'press-up, pelvic tilt and nerve glide removed');
  ok(['Cat-cow','Hip flexor stretch','Walk','Wall squat','Glute bridge','Dead bug','Prone Y raise'].every(n=>lib.includes(n)),'all other exercises kept');
  ok(p.lib.find(e=>e.name==='Glute bridge').progress===true&&p.lib.find(e=>e.name==='Hip flexor stretch').progress===false,'strength goes up weekly, stretches stay');
  const day=n=>(p.week[n]||[]).map(id=>p.lib.find(e=>e.id===id).name);
  ok(day(1).includes('Wall squat')&&day(1).includes('Dead bug')&&day(2).includes('Prone Y raise')&&!day(3).length,'legs+core Mon, upper Tue, rest Wed');
  ok(await pg.evaluate(()=>!!localStorage.getItem('ptc-state-before-v3')),'old program kept as a safety copy');
  await go(pg,'week');ok((await T(pg,'.hist')).includes('Wall squat')&&(await T(pg,'.hist')).includes('old note'),'old history still shown');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Very first version data');
 {const{ctx,pg}=await open(b,{seed:{fn:()=>{localStorage.setItem('ptc-state',JSON.stringify({v:1,activeId:'a',profiles:[{id:'a',name:'Mom',hue:0,exercises:[{id:'x',name:'Clamshell',sets:2,reps:12,holdSec:0,restSec:30,side:'each'}]}]}));localStorage.removeItem('ptc-days')}}});
  ok((await T(pg,'#chips')).includes('Mom')&&(await names(pg)).includes('Clamshell'),'person and exercise kept, on a legs day');ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Reps go up 2 every week');
 {const{ctx,pg}=await open(b);await loadPlan(pg,'lumbar');await go(pg,'today');
  const dose=n=>card(pg,n).locator('.dose').textContent();
  ok((await dose('Glute bridge'))==='2 × 10 · 3 s hold','week 1: 10 reps');
  await setDay(pg,'2026-11-16T09:00:00');ok((await dose('Glute bridge'))==='2 × 12 · 3 s hold','week 2: 12 reps');
  await setDay(pg,'2026-11-23T09:00:00');ok((await dose('Glute bridge'))==='2 × 14 · 3 s hold','week 3: 14 reps');
  ok((await dose('Figure-4 stretch')).startsWith('2 × 1 '),'stretch stays the same');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Sore? Move it');
 {const{ctx,pg}=await open(b);await loadPlan(pg,'lumbar');await go(pg,'today');
  await card(pg,'Dead bug').locator('[data-a=sore]').click();
  const rec=await pg.locator('[data-a=moveto]:has(.pill.done)').getAttribute('data-id');ok(rec==='2026-11-11','recommends Wednesday (Tue follows a core day)');
  ok((await pg.locator('[data-a=moveto][data-id="2026-11-10"]').textContent()).includes('day before'),'warns about the day after a core day');
  await pg.click('[data-a=moveto][data-id="2026-11-11"]');ok(!(await names(pg)).includes('Dead bug'),'gone from today');
  await setDay(pg,'2026-11-11T09:00:00');ok((await names(pg)).includes('Dead bug')&&(await T(pg,'.pill.moved')).includes('Mon'),'shows up Wednesday marked moved');
  await tick(pg,'Dead bug');await setDay(pg,'2026-11-12T09:00:00');ok(!(await pg.locator('.check.carry').count()),'done: nothing carried');
  // skip
  await card(pg,'Bird dog').locator('[data-a=sore]').click();await pg.click('[data-a=moveskip]');ok(!(await names(pg)).includes('Bird dog'),'skip it this week');
  await setDay(pg,'2026-11-13T09:00:00');ok(!(await names(pg)).includes('Bird dog'),'skipped one is not carried over');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Take today off');
 {const{ctx,pg}=await open(b);const before=(await names(pg)).length;
  await pg.click('[data-a=offday]');ok((await T(pg,'.hero h2'))==='Day off'&&(await T(pg,'.hero')).includes('Wed'),'Monday off, moved to Wednesday (a rest day)');
  await setDay(pg,'2026-11-11T09:00:00');ok((await names(pg)).length===before,'Wednesday has Monday’s workout');
  await setDay(pg,'2026-11-09T12:00:00');await pg.click('[data-a=offundo]');ok((await names(pg)).length===before,'undo brings it back');
  await setDay(pg,'2026-11-11T12:00:00');ok((await T(pg,'.hero h2'))==='Rest day','Wednesday back to rest');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Missed exercises carry over, after the muscle has rested');
 {const{ctx,pg}=await open(b);await loadPlan(pg,'lumbar');await go(pg,'today');
  await tick(pg,'Glute bridge');  // did part of Monday: legs worked, core skipped
  await setDay(pg,'2026-11-10T09:00:00');const carried=await pg.locator('.check.carry h3').allTextContents();
  ok(carried.includes('Dead bug')&&carried.includes('Figure-4 stretch'),'core and stretches carry to Tuesday');
  ok((await T(pg,'.check.carry .pill.missed'))==='Missed yesterday','marked Missed yesterday');
  await pg.click('.check.carry:has(h3:text-is("Dead bug")) [data-a=check]');await pg.waitForTimeout(400);
  await setDay(pg,'2026-11-11T09:00:00');const c2=await pg.locator('.check.carry h3').allTextContents();ok(!c2.includes('Dead bug')&&c2.includes('Figure-4 stretch'),'done one gone, others keep carrying');
  ok(!c2.includes('Bird dog'),'core waits a day after core was done');
  ok((await T(pg,'.check.carry .pill.missed')).startsWith('Missed Mon'),'label shows when it was missed');
  await setDay(pg,'2026-11-12T09:00:00');ok((await names(pg)).includes('Bird dog'),'Bird dog back on its own day (Thursday)');
  ok(pg.errs.length===0,'no errors');await ctx.close()}
 {const{ctx,pg}=await open(b);await tick(pg,'Clamshell');  // legs only, legs missed too
  await setDay(pg,'2026-11-10T09:00:00');ok(!(await pg.locator('.check.carry h3').allTextContents()).includes('Heel slide'),'missed legs exercise waits a day after a legs day');
  await setDay(pg,'2026-11-11T09:00:00');ok((await pg.locator('.check.carry h3').allTextContents()).includes('Heel slide'),'shows up after the rest day');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Edit a past day');
 {const{ctx,pg}=await open(b,{when:'2026-11-10T09:00:00'});await go(pg,'week');await pg.click('.wk button >> nth=0');
  await pg.click('[data-a=edopen]');await pg.click('[data-a=edall]');await pg.click('.edl button:has-text("Clamshell")');await pg.click('[data-a=edpain][data-id="2"]');await pg.fill('#ed-note','Did these');await pg.click('[data-a=eddone]');await pg.waitForTimeout(500);
  await pg.reload();await pg.waitForSelector('.card');await go(pg,'week');ok((await T(pg,'.hist')).includes('Clamshell')&&(await T(pg,'.hist')).includes('Did these'),'edited day saved in history');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Changing the schedule');
 {const{ctx,pg}=await open(b);await go(pg,'program');
  await pg.click('label:has(#td4)');await pg.waitForTimeout(300);let s=await stored(pg);let p=s.st.profiles[0];
  ok(!(p.week[4]||[]).length&&(p.week[5]||[]).length,'turning off Thursday rebuilds the week');
  await pg.click('label:has(#td4)');await pg.click('[data-a=ptab][data-id="2"]');await pg.click('[data-a=dayadd]');await pg.click('[data-a=pick]:has-text("Clamshell")');
  ok((await T(pg,'#main')).includes('back to back'),'warns when legs land on back-to-back days');
  await pg.click('[data-a=ptab][data-id=all]');await pg.click('[data-a=exadd]');await pg.fill('#f-name','Bicep curl');await pg.click('[data-a=exsave]');
  s=await stored(pg);p=s.st.profiles[0];const bc=p.lib.find(e=>e.name==='Bicep curl');ok(bc&&bc.group==='upper'&&(p.week[2]||[]).includes(bc.id),'new exercise guessed as upper and placed on upper days');
  await pg.click('[data-a=rebuild]');s=await stored(pg);ok(s.st.profiles[0].auto===true&&!(s.st.profiles[0].week[2]||[]).includes(s.st.profiles[0].lib.find(e=>e.name==='Clamshell').id),'rebuild puts things back');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Timer and exercise editing');
 {const{ctx,pg}=await open(b);await pg.click('[data-a=timer] >> nth=0');await pg.waitForSelector('#sdyn');await pg.click('[data-a=sall]');
  ok(await pg.locator('.check.on').count()===1,'timer Mark done ticks it');
  await go(pg,'program');await pg.click('[data-a=ptab][data-id=all]');await pg.click('.ex:has-text("Heel slide") [data-a=exedit]');await pg.click('[data-a=exdel]');await pg.click('[data-a=exdel]');
  const s=await stored(pg);ok(!s.st.profiles[0].lib.some(e=>e.name==='Heel slide')&&!Object.values(s.st.profiles[0].week).flat().some(id=>!s.st.profiles[0].lib.find(e=>e.id===id)),'deleted everywhere');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Second person');
 {const{ctx,pg}=await open(b);await pg.click('[data-a=addprof]');await pg.fill('#p-name','Mom');await pg.click('[data-a=psave]');
  ok((await T(pg,'.hero h2'))==='Rest day','new person starts empty');
  await pg.click('[data-a=prof] >> nth=0');await tick(pg,'Glute bridge');await pg.click('[data-a=prof] >> nth=1');await pg.click('[data-a=prof] >> nth=0');
  ok(await pg.locator('.check.on').count()===1,'people keep separate check-offs');ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Two copies open at once');
 {const{ctx,pg}=await open(b);const pg2=await ctx.newPage();await pg2.clock.install({time:at(MON)});await pg2.route(/fonts\.g/,r=>r.abort());await pg2.goto(BASE+'/');await pg2.waitForSelector('.check');
  await tick(pg,'Glute bridge');await pg2.locator('#main .check:has(h3:text-is("Clamshell")) [data-a=check]').click();await pg2.waitForTimeout(500);
  const s=await stored(pg);const td=Object.values(s.dd).find(x=>x.date==='2026-11-09');ok(td&&Object.values(td.checked).filter(Boolean).length===2,'ticks from both copies kept');await ctx.close()}

 console.log('Backup and restore');
 {const{ctx,pg}=await open(b);await tick(pg,'Glute bridge');const s=await stored(pg);const f=path.join(os.tmpdir(),'ptc-backup.json');fs.writeFileSync(f,JSON.stringify({app:'family-pt-coach',state:s.st,days:s.dd}));
  await pg.evaluate(()=>localStorage.clear());await pg.reload();await pg.waitForSelector('.check');ok(await pg.locator('.check.on').count()===0,'wiped');
  await go(pg,'program');await pg.click('[data-a=editprof]');await pg.setInputFiles('#f-restore',f);await pg.waitForTimeout(500);await go(pg,'today');
  ok(await pg.locator('.check.on').count()===1,'restore brings check-offs back');ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Video upload');
 {const{ctx,pg}=await open(b);await go(pg,'program');await pg.click('[data-a=ptab][data-id=all]');await pg.click('[data-a=exedit] >> nth=0');
  await pg.setInputFiles('#f-vid',path.join(__dirname,'..','public','demos','clamshell.mp4'));await pg.waitForSelector('[data-a=vremove]');await pg.click('[data-a=exsave]');await pg.waitForTimeout(500);
  await pg.reload();await pg.waitForTimeout(800);await go(pg,'program');ok((await T(pg,'#main')).includes('▶ Video'),'uploaded video survives reload');ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Offline');
 {const{ctx,pg}=await open(b);await pg.waitForTimeout(1500);await pg.reload();await pg.waitForTimeout(800);await ctx.setOffline(true);await pg.reload();
  ok(await pg.locator('.check').count()>0,'opens with no signal');await ctx.close()}

 await b.close();console.log(`\n${pass} passed, ${fail} failed`);process.exit(fail?1:0);
})().catch(e=>{console.error(e);process.exit(2)});
