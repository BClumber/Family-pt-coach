// End-to-end checks for Family PT Coach. Run: FAMILY_CODE=4321 PORT=3999 node server.js & node tests/app.test.js
const {chromium}=require('playwright');const fs=require('fs');const os=require('os');const path=require('path');
const BASE='http://localhost:3999';
const key=n=>{const d=new Date();d.setDate(d.getDate()-n);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')};
let pass=0,fail=0;const ok=(c,m)=>{if(c){pass++;console.log('  ✓',m)}else{fail++;console.log('  ✗ FAIL:',m)}};
async function fresh(b,{seed}={}){const ctx=await b.newContext({viewport:{width:390,height:844}});const pg=await ctx.newPage();
  await pg.route(/fonts\.g/,r=>r.abort());pg.errs=[];pg.on('pageerror',e=>pg.errs.push(e.message));
  await pg.goto(BASE+'/login');await pg.fill('input[name=code]','4321');await pg.click('button');await pg.waitForSelector('#main');
  if(seed){await pg.evaluate(seed);await pg.reload();await pg.waitForSelector('#main .card')}
  return{ctx,pg}}
const T=(pg,s)=>pg.textContent(s);const go=(pg,v)=>pg.click(`[data-a=nav][data-id=${v}]`);
const stored=pg=>pg.evaluate(()=>({st:JSON.parse(localStorage.getItem('ptc-state')),dd:JSON.parse(localStorage.getItem('ptc-days')||'{}')}));
const loadPlan=async(pg,k)=>{await go(pg,'program');await pg.click('[data-a=presets]');await pg.click(`[data-a=presetpick][data-id=${k}]`);await pg.click('[data-a=presetload]');await pg.waitForTimeout(500)};
(async()=>{
 const b=await chromium.launch();
 console.log('Server');
 {const r=await fetch(BASE+'/',{redirect:'manual'});ok(r.status===303,'locked without passcode');
  const r2=await fetch(BASE+'/login',{method:'POST',body:'code=0000',headers:{'content-type':'application/x-www-form-urlencoded'}});ok(r2.status===401,'wrong passcode refused');}

 console.log('Fresh phone');
 {const{ctx,pg}=await fresh(b);
  ok((await T(pg,'.hero h2')).includes('Day 1'),'starts on Day 1');
  await pg.click('.check [data-a=check] >> nth=0');await pg.waitForTimeout(500);await pg.reload();await pg.waitForSelector('.check');
  ok(await pg.locator('.check.on').count()===1,'check-off survives reload');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Old saved data (first version, single exercise list)');
 {const{ctx,pg}=await fresh(b,{seed:()=>{localStorage.setItem('ptc-state',JSON.stringify({v:1,activeId:'a',profiles:[{id:'a',name:'Dovi',hue:0,reminder:{days:[1],time:'07:00'},exercises:[{id:'x',name:'Clamshell',sets:2,reps:12,holdSec:0,restSec:30,side:'each'}]}]}));localStorage.removeItem('ptc-days')}});
  ok((await T(pg,'#chips')).includes('Dovi'),'person kept');ok((await pg.locator('.check h3').allTextContents()).includes('Clamshell'),'exercise kept');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Old saved data (before every-day list)');
 {const{ctx,pg}=await fresh(b,{seed:()=>{const s=JSON.parse(localStorage.getItem('ptc-state'));for(const p of s.profiles)delete p.daily;delete s.t;localStorage.setItem('ptc-state',JSON.stringify(s))}});
  ok(await pg.locator('.check').count()>0,'loads and shows exercises');ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Plans, rotation, every-day ticks');
 {const{ctx,pg}=await fresh(b);await loadPlan(pg,'lumbar');await loadPlan(pg,'yti');
  const s=await stored(pg);const p=s.st.profiles[0];
  ok(p.daily.exercises.length===9&&p.dayTypes[1].exercises.length===4&&p.dayTypes[2].exercises.length===3,'both plans loaded into the right days');
  await go(pg,'today');await pg.click('.check [data-a=check] >> nth=0'); // every-day tick creates today's record
  // now fill in yesterday as Day 1
  await pg.evaluate(()=>{const s=JSON.parse(localStorage.getItem('ptc-state'));s.profiles[0].dayTypes[0].exercises.push({id:'sq',name:'Wall squat',sets:2,reps:10,holdSec:0,restSec:30,side:'both',progress:true});s.t=Date.now()+5000;localStorage.setItem('ptc-state',JSON.stringify(s))});
  await pg.reload();await pg.waitForSelector('.hero');
  await go(pg,'week');await pg.click('.wk button >> nth='+((new Date().getDay()+6)%7-1>=0?(new Date().getDay()+6)%7-1:0));
  const isMon=new Date().getDay()===1;
  if(!isMon){await pg.click('[data-a=edopen]');await pg.click('[data-a=edset] >> nth=0');await pg.click('.edl button:has-text("Wall squat")');await pg.click('[data-a=eddone]');await pg.waitForTimeout(500);
    await go(pg,'today');ok((await T(pg,'.hero h2')).includes('Day 2'),'filling in yesterday moves today to Day 2 even after an every-day tick');
    await pg.click('.check:has-text("Glute bridge") [data-a=check]');await pg.waitForTimeout(500);
    const s2=await stored(pg);const td=Object.values(s2.dd).find(x=>x.date===key(0));
    ok(td&&td.dayTypeId===s2.st.profiles[0].dayTypes[1].id,'today saved as Day 2');
    ok(td&&Object.values(td.checked).filter(Boolean).length===2,'every-day tick kept');}
  // switch workout: every-day tick must stay
  await pg.click('[data-a=setday] >> nth=2');await pg.waitForTimeout(400);
  ok(await pg.locator('.check.on').count()===1,'switching workout keeps every-day ticks, clears the other day\'s');
  ok((await T(pg,'.hero h2')).includes('Day 3'),'switched to Day 3');
  await pg.click('.check:has-text("Prone Y raise") [data-a=check]');await pg.reload();await pg.waitForSelector('.hero');
  ok((await T(pg,'.hero h2')).includes('Day 3'),'picked workout survives reload');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Rest days');
 {const{ctx,pg}=await fresh(b);await loadPlan(pg,'lumbar');await go(pg,'today');
  const before=await T(pg,'.hero h2');await pg.click('[data-a=reston]');
  ok((await T(pg,'.hero h2'))==='Rest day','make today a rest day');
  await go(pg,'week');const g=(await pg.locator('.wk').first().locator('button').allTextContents()).join('|');
  ok(g.includes(before.split(' · ')[0].replace('Day ','D')+'next'),'today\'s workout moves to tomorrow');
  await go(pg,'today');await pg.click('[data-a=restoff]');ok((await T(pg,'.hero h2'))===before,'undo rest day');
  await go(pg,'program');await pg.click('[data-a=editprof]');await pg.click('#p-r'+new Date().getDay());await pg.click('[data-a=psave]');await go(pg,'today');
  ok((await T(pg,'.hero h2'))==='Rest day','weekly rest day applies');
  ok((await T(pg,'[data-a=restoff]'))==='Work out anyway','can work out anyway');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Timer, exercise editing, minutes');
 {const{ctx,pg}=await fresh(b);
  await pg.click('[data-a=timer] >> nth=0');await pg.waitForSelector('#sdyn');await pg.click('[data-a=sall]');
  ok(await pg.locator('.check.on').count()===1,'timer "Mark done" ticks the exercise');
  await go(pg,'program');await pg.click('[data-a=exadd]');await pg.fill('#f-name','Bike');await pg.selectOption('#f-unit','min');await pg.fill('#f-reps','15');await pg.click('[data-a=exsave]');
  ok((await pg.locator('.ex .dose').allTextContents()).some(t=>t.startsWith('15 min')),'minutes exercise added');
  await pg.click('.ex:has-text("Bike") [data-a=exedit]');await pg.click('[data-a=exdel]');await pg.click('[data-a=exdel]');
  ok(!(await pg.locator('.ex h3').allTextContents()).includes('Bike'),'exercise deleted');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Second person');
 {const{ctx,pg}=await fresh(b);await pg.click('[data-a=addprof]');await pg.fill('#p-name','Mom');await pg.click('[data-a=psave]');
  ok((await T(pg,'#chips')).includes('Mom'),'person added');
  await go(pg,'program');await pg.click('[data-a=exadd]');await pg.fill('#f-name','Shoulder roll');await pg.click('[data-a=exsave]');
  await go(pg,'today');await pg.click('.check [data-a=check] >> nth=0');
  await pg.click('[data-a=prof] >> nth=0');ok(await pg.locator('.check.on').count()===0,'people keep separate check-offs');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Program week change keeps history');
 {const{ctx,pg}=await fresh(b,{seed:()=>{const s=JSON.parse(localStorage.getItem('ptc-state'));const p=s.profiles[0];const d=new Date();d.setDate(d.getDate()-20);const k=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
    p.startDate=k;localStorage.setItem('ptc-state',JSON.stringify(s));localStorage.setItem('ptc-days',JSON.stringify({[p.id+'_'+k]:{pid:p.id,date:k,dayTypeId:p.dayTypes[0].id,checked:{[p.dayTypes[0].exercises[0].id]:true},reps:{}}}))}});
  await go(pg,'program');await pg.click('[data-a=editprof]');await pg.fill('#p-wk','1');await pg.click('[data-a=psave]');await go(pg,'week');
  ok(await pg.locator('.hist > div').count()===1,'old day still in History');ok((await pg.locator('text=Earlier weeks').count())===1,'earlier weeks still shown');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Two copies open at once');
 {const{ctx,pg}=await fresh(b);const pg2=await ctx.newPage();await pg2.route(/fonts\.g/,r=>r.abort());await pg2.goto(BASE+'/');await pg2.waitForSelector('.check');
  await pg.click('.check [data-a=check] >> nth=0');await pg.waitForTimeout(600);
  await pg2.click('.check [data-a=check] >> nth=1');await pg2.waitForTimeout(600);
  const s=await stored(pg);const td=Object.values(s.dd).find(x=>x.date===key(0));
  ok(td&&Object.values(td.checked).filter(Boolean).length===2,'ticks from both copies kept');await ctx.close()}

 console.log('Backup and restore');
 {const{ctx,pg}=await fresh(b);await pg.click('.check [data-a=check] >> nth=0');await pg.waitForTimeout(500);
  const s=await stored(pg);const f=path.join(os.tmpdir(),'ptc-backup.json');fs.writeFileSync(f,JSON.stringify({app:'family-pt-coach',state:s.st,days:s.dd}));
  await pg.evaluate(()=>{localStorage.clear()});await pg.reload();await pg.waitForSelector('.check');ok(await pg.locator('.check.on').count()===0,'wiped');
  await go(pg,'program');await pg.click('[data-a=editprof]');await pg.setInputFiles('#f-restore',f);await pg.waitForTimeout(500);
  await go(pg,'today');ok(await pg.locator('.check.on').count()===1,'restore brings check-offs back');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Video upload');
 {const{ctx,pg}=await fresh(b);await go(pg,'program');await pg.click('[data-a=exedit] >> nth=0');
  await pg.setInputFiles('#f-vid',path.join(__dirname,'..','public','demos','clamshell.mp4'));await pg.waitForSelector('[data-a=vremove]');await pg.click('[data-a=exsave]');await pg.waitForTimeout(500);
  await pg.reload();await pg.waitForTimeout(800);await go(pg,'program');ok((await pg.locator('.ex .tag').first().textContent()).includes('▶ Video'),'uploaded video survives reload');
  ok(pg.errs.length===0,'no errors');await ctx.close()}

 console.log('Offline');
 {const{ctx,pg}=await fresh(b);await pg.waitForTimeout(1500);await pg.reload();await pg.waitForTimeout(800);
  await ctx.setOffline(true);await pg.reload();const okOff=await pg.locator('.check').count();ok(okOff>0,'opens with no signal');await ctx.close()}

 await b.close();console.log(`\n${pass} passed, ${fail} failed`);process.exit(fail?1:0);
})().catch(e=>{console.error(e);process.exit(2)});
