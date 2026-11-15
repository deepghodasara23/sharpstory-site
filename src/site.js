/* Sharp Story — one script for every page. Each module only runs when its markup is on the page. */
(function(){
var D=document,H=D.documentElement,$=function(i){return D.getElementById(i)},Q=function(s,r){return[].slice.call((r||D).querySelectorAll(s))};
var RM=matchMedia('(prefers-reduced-motion:reduce)').matches,touch=matchMedia('(hover:none)').matches,cl=function(v,a,b){return Math.max(a,Math.min(b,v))};
var ease=function(x){return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2},eo=function(x){return 1-Math.pow(1-x,3)};
var px=-9999,py=-9999,pin=false,vh=innerHeight,vw=innerWidth;
addEventListener('pointermove',function(e){px=e.clientX;py=e.clientY;pin=true;if(e.pointerType==='mouse')cur.classList.add('on')},{passive:true});
D.addEventListener('pointerleave',function(){pin=false;cur.classList.remove('on')});
addEventListener('resize',function(){vh=innerHeight;vw=innerWidth});

/* ---------- smooth scroll ---------- */
var ln=null;try{if(window.Lenis&&!RM){ln=new Lenis({lerp:.085})}}catch(e){}
function goTo(el){if(ln)ln.scrollTo(el||0,{duration:1.4,offset:el?-80:0});else if(el)el.scrollIntoView({behavior:RM?'auto':'smooth'});else scrollTo({top:0,behavior:RM?'auto':'smooth'})}

/* ---------- page transitions ---------- */
var pt=$('pt'),ptt=$('ptt'),entering=H.classList.contains('ptin');
function leave(url,title){try{sessionStorage.setItem('pt',title||'')}catch(e){}ptt.textContent=title||'';H.classList.remove('ptin');pt.classList.remove('out');void pt.offsetWidth;pt.classList.add('go');setTimeout(function(){location.href=url},RM?0:700)}
D.addEventListener('click',function(e){var a=e.target.closest('a');if(!a||e.defaultPrevented)return;var h=a.getAttribute('href')||'';
 if(h.charAt(0)==='#'){e.preventDefault();closeMenu();goTo(h==='#'?0:D.querySelector(h));return}
 if(e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||e.button||a.target==='_blank'||a.hasAttribute('download'))return;
 var u;try{u=new URL(a.href,location.href)}catch(x){return}
 if(u.origin!==location.origin||/^\/admin/.test(u.pathname)||/\.\w+$/.test(u.pathname))return;
 e.preventDefault();if(u.pathname===location.pathname){closeMenu();if(u.hash)goTo(D.querySelector(u.hash));else goTo(0);return}
 leave(u.href,a.dataset.pt||'')});
if(entering){try{ptt.textContent=sessionStorage.getItem('pt')||''}catch(e){}setTimeout(function(){pt.classList.add('out')},RM?0:140)}
try{sessionStorage.removeItem('pt')}catch(e){}
addEventListener('pageshow',function(e){if(e.persisted){pt.classList.remove('go');pt.classList.add('out')}});
var T0=entering?650:150;

/* ---------- cursor ---------- */
var cur=$('cur'),cx=0,cy=0;
D.addEventListener('pointerover',function(e){var t=e.target;cur.classList.toggle('inv',!!t.closest('[data-inv]'));var w=t.closest('[data-cur]');cur.classList.toggle('big',!!w);cur.firstChild.textContent=w?w.dataset.cur:''});

/* ---------- top bar + menu ---------- */
var top=$('top'),ly=scrollY;
function closeMenu(){if(!H.classList.contains('mo'))return;H.classList.remove('mo');$('mb').setAttribute('aria-expanded','false');$('mb').textContent='Menu';if(ln)ln.start()}
$('mb').addEventListener('click',function(){var o=!H.classList.contains('mo');H.classList.toggle('mo',o);this.setAttribute('aria-expanded',o);this.textContent=o?'Close':'Menu';if(ln){o?ln.stop():ln.start()}});
addEventListener('keydown',function(e){if(e.key==='Escape'){closeMenu();closeBox()}});

/* ---------- reveal when in view ---------- */
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){var el=e.target;setTimeout(function(){el.classList.add('vis')},el.dataset.late?T0:0);io.unobserve(el)}})},{threshold:.12,rootMargin:'0px 0px -6% 0px'});
Q('.rvb,.fu,.ri,.ch2,.cards,.rl').forEach(function(e){io.observe(e)});
Q('.wg .fu,.jl .fu,.pr2 .fu,.bl .fu').forEach(function(e,i){e.style.setProperty('--dl',((i%4)*.07)+'s')});

/* ---------- kinetic hero (home only) ---------- */
var K=[],hk=$('hk');
function spl(el,text){el._t=text;el.innerHTML=text.split('').map(function(ch){return'<span>'+(ch===' '?'&nbsp;':ch.replace('&','&amp;').replace('<','&lt;'))+'</span>'}).join('');var o={el:el,l:Q('span',el).map(function(s){return{el:s,w:500,d:88,x:0,y:0}})};var i=K.indexOf(el._k);if(i>-1)K[i]=o;else K.push(o);el._k=o;fit(o);return o}
function fit(o){var el=o.el;el.style.setProperty('--fs','100px');o.l.forEach(function(s){s.el.style.setProperty('--w',500);s.el.style.setProperty('--d',88);s.w=500;s.d=88});var w=0;o.l.forEach(function(s){w+=s.el.getBoundingClientRect().width});
 var fs=Math.min(100*el.clientWidth/w*(vw<700?.86:.95),vh*.4);el.style.setProperty('--fs',fs.toFixed(1)+'px');measure(o)}
function measure(o){var sy=scrollY;o.l.forEach(function(s){var r=s.el.getBoundingClientRect();s.x=r.left+r.width/2;s.y=r.top+r.height/2+sy})}
if(hk){var WORDS=JSON.parse(hk.dataset.words),wi=0;
 var hero=function(anim){var w=WORDS[wi],a=spl($('h1'),w[0]),b=spl($('h2'),w[1]);
  if(anim)a.l.concat(b.l).forEach(function(s,i){s.el.classList.add('in');setTimeout(function(){s.el.classList.add('rise');s.el.classList.remove('in')},20+i*30)});
  $('hmid').innerHTML=WORDS.map(function(_,k){return'<i'+(k===wi?' class="on"':'')+'></i>'}).join('')+'<em>Tap</em>'};
 hero(false);
 hk.addEventListener('click',function(e){if(e.target.closest('a'))return;var all=$('h1')._k.l.concat($('h2')._k.l);all.forEach(function(s,i){setTimeout(function(){s.el.classList.remove('rise');s.el.classList.add('out')},i*22)});setTimeout(function(){wi=(wi+1)%WORDS.length;hero(true)},300+all.length*22)});
 addEventListener('resize',function(){K.forEach(fit)});
 if(D.fonts)D.fonts.ready.then(function(){K.forEach(fit)});
 addEventListener('scroll',function(){K.forEach(measure)},{passive:true})}

/* ---------- case title: fit the name to the width ---------- */
var ct=D.querySelector('.ct');
function fitCt(){if(!ct)return;var inn=ct.firstElementChild;ct.style.whiteSpace='nowrap';ct.style.setProperty('--fs','100px');var w=inn.offsetWidth,fs=Math.min(100*ct.clientWidth/w*.99,vh*.46);
 if(fs<50){ct.style.whiteSpace='normal';fs=Math.min(vw*.16,90)}ct.style.setProperty('--fs',fs.toFixed(1)+'px')}
if(ct){fitCt();addEventListener('resize',fitCt);if(D.fonts)D.fonts.ready.then(fitCt);setTimeout(function(){ct.classList.add('vis')},T0-100)}

/* ---------- home: studio statement ---------- */
var sayS=$('say-s'),sps=sayS?Q('#sl p'):[],sCur=-1,sbar=sayS?sayS.querySelector('.sbar'):null;
function sayAt(k){if(k===sCur)return;sps.forEach(function(p,i){p.classList.toggle('on',i===k);p.classList.toggle('gone',i<k&&k>=0)});sCur=k;$('sn').textContent='0'+Math.max(1,k+1)}

/* ---------- ticker ---------- */
var tk=$('tk'),tkx=0,tkv=0,lsy=scrollY;

/* ---------- row previews (home work, work list, journal) ---------- */
var pv=$('pv'),pvx=0,pvy=0;
if(pv)Q('[data-pv]').forEach(function(r){r.addEventListener('pointerenter',function(){pv.classList.add('on');Q('img',pv).forEach(function(m){m.classList.toggle('on',m.dataset.i===r.dataset.pv)})});r.addEventListener('pointerleave',function(){pv.classList.remove('on')})});

/* ---------- cards: the fill grows from where the cursor enters ---------- */
Q('.card').forEach(function(c){var f=function(e){var r=c.getBoundingClientRect();c.style.setProperty('--mx',(e.clientX-r.left)+'px');c.style.setProperty('--my',(e.clientY-r.top)+'px')};c.addEventListener('pointerenter',f);c.addEventListener('pointerleave',f)});

/* ---------- process: plays once as a sequence ---------- */
var pl=$('pl'),sts=pl?Q('.step',pl):[],ph=$('phead'),plp=0;
if(pl)new IntersectionObserver(function(es,ob){es.forEach(function(e){if(!e.isIntersecting)return;ob.disconnect();var t0=performance.now(),Dd=RM?1:3200;(function f(t){var x=Math.min(1,(t-t0)/Dd);plp=x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2;if(x<1)requestAnimationFrame(f)})(t0)})},{threshold:.45}).observe(pl);

/* ---------- footer: wordmark in and out, spinning badge ---------- */
var ewm=$('ewm'),btt=$('btt'),brot=0,bspd=.35,bhov=false;
if(btt){btt.addEventListener('pointerenter',function(){bhov=true});btt.addEventListener('pointerleave',function(){bhov=false});new IntersectionObserver(function(es){es.forEach(function(e){btt.classList.toggle('in',e.isIntersecting)})},{threshold:.6}).observe(btt)}
if(ewm){var ews=Q('path,polygon',ewm);ews.sort(function(a,b){return a.getBBox().x-b.getBBox().x});ews.forEach(function(p,i){p.style.setProperty('--d',(i*55)+'ms')});
 new IntersectionObserver(function(es){es.forEach(function(e){ewm.classList.toggle('in',e.isIntersecting)})},{threshold:.35}).observe(ewm)}

/* ---------- magnetic buttons ---------- */
if(!touch)Q('.mag').forEach(function(m){m.addEventListener('pointermove',function(e){var r=m.getBoundingClientRect();m.style.transition='background .3s,color .3s';m.style.transform='translate('+((e.clientX-r.left-r.width/2)*.25)+'px,'+((e.clientY-r.top-r.height/2)*.35)+'px)'});m.addEventListener('pointerleave',function(){m.style.transition='transform .7s cubic-bezier(.16,1,.3,1),background .3s,color .3s';m.style.transform=''})});

/* ---------- work: filter and view ---------- */
var wk=D.querySelector('.wk');
if(wk){var items=Q('.wc,.wl2 .wr'),cnt=$('wcount');
 $('wf').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;Q('button',this).forEach(function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b)});var f=b.dataset.f,n=0;
  items.forEach(function(it){var show=f==='all'||(' '+it.dataset.t+' ').indexOf(' '+f+' ')>-1;if(show){if(it.classList.contains('wc'))n++;if(it.classList.contains('gone')){it.classList.add('hide');it.classList.remove('gone');void it.offsetWidth}setTimeout(function(){it.classList.remove('hide')},30)}else{it.classList.add('hide');setTimeout(function(){if(it.classList.contains('hide'))it.classList.add('gone')},450)}});
  if(cnt)cnt.textContent=(n<10?'0':'')+n;setTimeout(function(){if(ln)ln.resize()},500)});
 $('wv').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;Q('button',this).forEach(function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b)});wk.dataset.m=b.dataset.m;try{sessionStorage.setItem('wv',b.dataset.m)}catch(x){}if(ln)ln.resize()});
 try{var sv=sessionStorage.getItem('wv');if(sv){var bb=D.querySelector('#wv [data-m="'+sv+'"]');if(bb)bb.click()}}catch(x){}}

/* ---------- FAQ: smooth open and close ---------- */
Q('.fqi').forEach(function(d){var s=d.querySelector('summary');if(d.open)d.classList.add('op');s.addEventListener('click',function(e){e.preventDefault();if(d.open){d.classList.remove('op');setTimeout(function(){d.open=false;if(ln)ln.resize()},550)}else{d.open=true;void d.offsetWidth;d.classList.add('op');setTimeout(function(){if(ln)ln.resize()},650)}})});

/* ---------- lightbox ---------- */
var lbx=$('lbx');
function closeBox(){if(lbx&&lbx.classList.contains('on')){lbx.classList.remove('on');if(ln)ln.start()}}
if(lbx){Q('[data-zoom]').forEach(function(f){f.addEventListener('click',function(){var im=f.querySelector('img');lbx.querySelector('img').src=im.dataset.full||im.currentSrc||im.src;lbx.querySelector('img').alt=im.alt;lbx.classList.add('on');if(ln)ln.stop()})});lbx.addEventListener('click',closeBox)}

/* ---------- case study: chapters, strip ---------- */
var cx2=D.querySelector('.cx'),cxi=cx2?cx2.querySelector('.cxi'):null,cxt=cx2?cx2.querySelector('.cxt'):null;
var strip=D.querySelector('.strip'),trk=strip?strip.querySelector('.trk'):null,stb=strip?strip.querySelector('.stb'):null;
function sizeStrip(){if(!strip)return;if(vw<=800){strip.style.height='';return}strip.style.height=(trk.scrollWidth-vw+vh*1.15)+'px'}
if(strip){sizeStrip();addEventListener('resize',sizeStrip);Q('img',strip).forEach(function(m){if(!m.complete)m.addEventListener('load',sizeStrip)})}
var cnx=D.querySelector('.cnx'),nxs=cnx?cnx.querySelector('.nxs'):null;
var chp=$('chp'),chs=Q('[data-chap]'),chi=-1,chEnd=D.querySelector('[data-chapend]');
var rp=$('rp');
var pys=Q('[data-py]'),scs=Q('.sc').map(function(el){return{el:el,w:Q('.sw',el),n:-1}});
var dks=Q('[data-dk]');

/* ---------- contact form ---------- */
var bf=$('bf');
if(bf){var pick=function(id){var b=D.querySelector('#'+id+' .chip.on');return b?b.textContent:''};
 Q('.fld input,.fld textarea',bf).forEach(function(i){var u=function(){i.closest('.fld').classList.toggle('f',!!i.value)};i.addEventListener('input',function(){u();i.closest('.fld').classList.remove('err')});u()});
 Q('[data-g]',bf).forEach(function(g){g.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;var on=!b.classList.contains('on');Q('.chip',g).forEach(function(x){x.classList.remove('on');x.setAttribute('aria-pressed','false')});if(on){b.classList.add('on');b.setAttribute('aria-pressed','true')}})});
 var o=new URLSearchParams(location.search).get('offer');if(o)Q('#need .chip').forEach(function(x){x.classList.toggle('on',x.textContent===o)});
 var chk=function(id,ok){$(id).closest('.fld').classList.toggle('err',!ok);return ok};
 bf.addEventListener('submit',function(ev){ev.preventDefault();var a=chk('fn',$('fn').value.trim()),b=chk('fe',/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test($('fe').value.trim())),c=chk('fm',$('fm').value.trim().length>3);
  if(!(a&&b&&c)){var f=D.querySelector('.fld.err input,.fld.err textarea');if(f)f.focus();return}
  var n=pick('need');$('fneeds').value=n;$('fskus').value=pick('skus');$('ftime').value=pick('tml');
  var q=new URLSearchParams(new FormData(bf)).toString(),btn=$('snd'),em=bf.dataset.email;btn.disabled=true;btn.firstChild.textContent='Sending… ';
  var mail=function(){var body='Name: '+$('fn').value+'\nEmail: '+$('fe').value+'\nCompany: '+$('fc').value+'\nNeed: '+n+($('fskus').value?'\nSKUs: '+$('fskus').value:'')+($('ftime').value?'\nLaunch: '+$('ftime').value:'')+'\n\n'+$('fm').value;location.href='mailto:'+em+'?subject='+encodeURIComponent('New '+(n&&n!=='Not sure yet'?n:'project')+' brief'+($('fc').value?' - '+$('fc').value:''))+'&body='+encodeURIComponent(body)};
  fetch('/',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:q}).then(function(r){if(!r.ok)throw 0;$('ok').classList.add('on');btn.firstChild.textContent='Sent ';Q('input:not([type=hidden]),textarea',bf).forEach(function(i){i.value='';i.closest('.fld')&&i.closest('.fld').classList.remove('f')});Q('.chip.on',bf).forEach(function(b){b.classList.remove('on')})})
  .catch(function(){btn.disabled=false;btn.firstChild.textContent=btn.dataset.l+' ';mail()})})}

/* ---------- booking calendar ---------- */
var cal=D.querySelector('.cal iframe[data-src]');
if(cal){cal.addEventListener('load',function(){var l=D.querySelector('.cal .ld');if(l)l.remove()});setTimeout(function(){cal.src=cal.dataset.src},T0)}

/* ---------- the frame loop ---------- */
var lastM=0;
function frame(t){
 if(ln)ln.raf(t);
 var sy=scrollY,R=vw*(touch?.3:.17),dsy=sy-lsy;lsy=sy;
 /* kinetic hero */
 if(hk){var hp=cl(sy/vh,0,1);K.forEach(function(o){var r=o.el.getBoundingClientRect();if(r.bottom<-50||r.top>vh+50)return;
  for(var i=0;i<o.l.length;i++){var s=o.l[i],dy=s.y-sy,f;
   if(pin&&!touch){var d=Math.hypot(px-s.x,(py-dy)*1.25);f=Math.exp(-Math.pow(d/R,2))}else f=.5+.5*Math.sin(t/700-i*.55);
   var tw=(200+600*f)*(1-hp*.6)+200*hp*.6,td=100-25*f-hp*20;
   s.w+=(tw-s.w)*.12;s.d+=(td-s.d)*.12;s.el.style.setProperty('--w',s.w.toFixed(0));s.el.style.setProperty('--d',cl(s.d,75,100).toFixed(1))}});
  hk.style.opacity=(1-hp*.9).toFixed(3);hk.style.transform='translateY('+(hp*-6)+'vh)';
  if(t-lastM>800){lastM=t;K.forEach(measure)}}
 /* ticker */
 if(tk){tkv+=(Math.abs(dsy)*.6-tkv)*.08;tkx-=(.6+tkv);var half=tk.scrollWidth/2;if(-tkx>half)tkx+=half;tk.style.transform='translate3d('+tkx.toFixed(1)+'px,0,0)'}
 /* badge */
 if(btt){bspd+=(((bhov?2.4:.35)+Math.min(6,Math.abs(dsy)*.15))-bspd)*.06;brot+=bspd;btt.style.setProperty('--rot',brot.toFixed(2)+'deg')}
 /* top bar: hide going down, logo light over dark sections */
 if(!H.classList.contains('mo')){if(dsy>6&&sy>200)top.classList.add('hide');else if(dsy<-6||sy<120)top.classList.remove('hide')}
 var dk=false;for(var k=0;k<dks.length;k++){var b=dks[k].getBoundingClientRect();if(b.top<=40&&b.bottom>40){dk=true;break}}
 /* studio */
 if(sayS){var sr=sayS.getBoundingClientRect(),spp=cl(-sr.top/(sr.height-vh),0,1);sbar.style.setProperty('--sp',spp.toFixed(3));sayAt(sr.top<vh*.4?Math.min(sps.length-1,Math.floor(spp*sps.length)):-1)}
 /* process */
 if(pl){pl.style.setProperty('--p',plp.toFixed(3));for(var q=0;q<sts.length;q++)sts[q].classList.toggle('on',plp>q/sts.length+.02);var mob=vw<=800;ph.style.setProperty(mob?'--hy':'--hx',(plp*(mob?pl.clientHeight:pl.clientWidth)).toFixed(1)+'px');ph.style.setProperty('--ho',plp>0&&plp<1?1:0)}
 /* parallax */
 for(var j=0;j<pys.length;j++){var el=pys[j],r=el.parentNode.getBoundingClientRect();if(r.bottom<-100||r.top>vh+100)continue;el.style.setProperty('--py',((r.top+r.height/2-vh/2)*-(+el.dataset.py)).toFixed(1)+'px')}
 /* words light up as you read */
 for(var m=0;m<scs.length;m++){var o=scs[m],rr=o.el.getBoundingClientRect();if(rr.bottom<-50||rr.top>vh+50)continue;var p=cl((vh*.88-rr.top)/(rr.height+vh*.38),0,1),nn=Math.round(p*o.w.length);if(nn!==o.n){for(var z=0;z<o.w.length;z++)o.w[z].classList.toggle('on',z<nn);o.n=nn}}
 /* case: cover grows to full bleed */
 if(cxi){var cr=cx2.getBoundingClientRect(),cp=cl(-cr.top/(cr.height-vh),0,1),ce=ease(cl(cp/.72,0,1)),side=vw<=800?7:24,tb=vw<=800?22:15;
  cxi.style.setProperty('--ci',(tb*(1-ce)).toFixed(2)+'%');cxi.style.setProperty('--cj',(side*(1-ce)).toFixed(2)+'%');cxi.style.setProperty('--cr',(18*(1-ce)).toFixed(1)+'px');cxi.style.setProperty('--cs',(1.28-.28*ce).toFixed(3));cxt.style.setProperty('--co',cl((cp-.7)/.2,0,1).toFixed(2));if(ce>.85&&cr.top<=40&&cr.bottom>40)dk=true}
 /* case: the system strip moves sideways */
 if(strip&&vw>800){var str=strip.getBoundingClientRect(),stp=cl(-str.top/(str.height-vh),0,1),mx=trk.scrollWidth-vw;trk.style.setProperty('--tx',(-stp*mx).toFixed(1)+'px');stb.style.setProperty('--sp',stp.toFixed(3))}
 /* case: next project opens up */
 if(nxs){var nr=cnx.getBoundingClientRect(),np=cl(-nr.top/(nr.height-vh),0,1),ne=ease(np),sd=vw<=800?8:30;
  nxs.style.setProperty('--ni',(28*(1-ne)).toFixed(2)+'%');nxs.style.setProperty('--nj',(sd*(1-ne)).toFixed(2)+'%');nxs.style.setProperty('--nr',(16*(1-ne)).toFixed(1)+'px');nxs.style.setProperty('--ns',(1.25-.25*ne).toFixed(3));nxs.style.setProperty('--no',cl((np-.45)/.4,0,1).toFixed(2))}
 /* chapter pill + reading progress */
 if(chp&&chs.length){var a0=chs[0].getBoundingClientRect().top,ae=chEnd?chEnd.getBoundingClientRect().top:1e9,on=a0<vh*.6&&ae>vh*.55,ci=-1;
  for(var c=0;c<chs.length;c++)if(chs[c].getBoundingClientRect().top<vh*.55)ci=c;
  chp.classList.toggle('on',on);if(ci!==chi&&ci>-1){chi=ci;var em=chp.querySelector('em'),lab=chs[ci].dataset.chap;em.classList.add('sw');setTimeout(function(){em.textContent=lab;em.classList.remove('sw')},220)}
  chp.style.setProperty('--cp',cl((vh*.6-a0)/Math.max(1,ae-a0+vh*.05),0,1).toFixed(3))}
 H.classList.toggle('dk',dk);
 if(rp){var dh=D.documentElement.scrollHeight-vh;rp.style.setProperty('--rp',cl(sy/Math.max(1,dh),0,1).toFixed(4))}
 /* preview + cursor */
 if(pv){pvx+=(px-pvx)*.12;pvy+=(py-pvy)*.12;pv.style.transform='translate('+(pvx+(pvx>vw*.6?-pv.offsetWidth-30:30))+'px,'+(pvy-pv.offsetHeight/2)+'px) rotate('+((px-pvx)*.03).toFixed(2)+'deg)'}
 cx+=(px-cx)*.2;cy+=(py-cy)*.2;cur.style.transform='translate('+cx.toFixed(1)+'px,'+cy.toFixed(1)+'px)';
 requestAnimationFrame(frame)}
requestAnimationFrame(frame);
})();
