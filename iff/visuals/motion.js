const payload=JSON.parse(document.getElementById('engine-data').textContent);
const root=document.getElementById('visual');
const reduced=matchMedia('(prefers-reduced-motion: reduce)');
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const color=e=>e.decision==='ACCEPT_FRIEND'?'accepted':e.decision==='REJECT'?'rejected':'neutral';
const verdict=e=>e.reject_stage|| (e.decision==='ACCEPT_FRIEND'?'ACCEPT':e.decision);
const resize=()=>parent.postMessage({isStreamlitMessage:true,type:'streamlit:setFrameHeight',height:Math.ceil(document.body.getBoundingClientRect().height)+2},'*');
let draw=()=>{},duration=7000,elapsed=0,previous=0,visible=true,animation=0;
function tick(now){if(!previous)previous=now;if(visible)elapsed+=Math.min(now-previous,80);previous=now;draw(Math.min(elapsed/duration,1));if(elapsed<duration&&!reduced.matches)animation=requestAnimationFrame(tick);}
function replay(){cancelAnimationFrame(animation);previous=0;elapsed=0;root.dataset.progress=reduced.matches?'1':'0';draw(reduced.matches?1:0);if(!reduced.matches)animation=requestAnimationFrame(tick);}
new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;previous=0;}).observe(root);
new ResizeObserver(resize).observe(document.body);
reduced.addEventListener('change',replay);
function protocol(e){
 const rogue=e.decision==='NO_RESPONSE',relay=e.scenario==='S3',replayAttack=e.reject_stage==='NONCE',c2=e.component==='C2';
 const path=relay?'M190 90 L450 135 L710 90':'M190 90 L710 90';
 const mobilePath=relay?'M150 58 L230 125 L150 200':'M150 58 L150 200';
 function scene(mobile){return `<svg class="scene ${mobile?'mobile-scene':'desktop-scene'}" viewBox="${mobile?'0 0 300 250':'0 0 900 170'}" role="img" aria-label="질의기와 드론 사이의 엔진 이벤트 재생">
 <path class="beam" d="${mobile?mobilePath:path}"/><path class="wire" d="${mobile?mobilePath:path}" stroke-dasharray="4 6"/>
 <g transform="translate(${mobile?'150 30':'120 90'})"><rect class="endpoint" x="-53" y="-24" width="106" height="48" rx="9"/><path d="M-35 9V-9h18v18m-14-13h10M-30 13h10" class="wire"/><text class="big" x="-8" y="5">질의기</text></g>
 <g transform="translate(${mobile?'150 226':'780 90'})"><rect class="endpoint" x="-58" y="-24" width="116" height="48" rx="9"/><path class="wire" d="M-34-8l18 16m-18 0l18-16m-10 4h4v8h-4zM-38-10h8m12 0h8m-28 20h8m12 0h8"/><text class="big" x="0" y="5">드론</text></g>
 ${(relay||replayAttack)?`<g transform="translate(${mobile?'243 125':'450 135'})"><path class="attacker" d="M0-18L22 17H-22Z"/><text x="${mobile?'-20':'30'}" y="${mobile?'38':'5'}">${relay?'중계자':'녹화본 삽입'}</text></g>`:''}
 <text x="${mobile?'12':'245'}" y="${mobile?'87':'45'}">${c2?'C2 · 수동 관측':mobile?'CHALLENGE<tspan x="12" dy="17">+ 질의 태그</tspan>':'CHALLENGE + 질의 태그'}</text><text x="${mobile?'12':'535'}" y="${mobile?'174':'122'}">${rogue?'응답 없음':c2?'기동 서명':'RESPONSE'}</text>
 <path class="packet-track" d="${mobile?mobilePath:path}" fill="none" stroke="none"/><circle class="packet" r="6"/>
 </svg>`;}
 const rtt=e.rtt_ns===null?'RTT 기록 없음':`RTT ${(e.rtt_ns/1000).toFixed(3)}µs / 예산 ${(e.budget_ns/1000).toFixed(3)}µs`;
 root.innerHTML=`<section class="panel protocol" data-component="protocol"><div class="top"><div><div class="eyebrow">PROTOCOL / ${esc(e.scenario)}</div><div class="title">침묵을 지키는 인증</div></div><button id="replay" aria-label="프로토콜 다시 재생">다시 재생</button></div>${scene(false)}${scene(true)}<div class="phase" aria-live="off"></div><div class="status"><div class="verdict ${color(e)}"></div><div class="facts">${esc(rtt)}<div class="budget"><div class="budget-fill"></div><i class="budget-marker"></i></div></div></div><div class="caption">시뮬레이션 · 엔진 로그의 설명용 재생, 실제 센서·광학 전파 시간이 아닙니다.</div></section>`;
 const phases=c2?['기동 서명 관측','관측 비트 복원','해밍 검증 결과']:['질의 패킷 전송','드론 · 질의 인증',rogue?'질의 거부 · 응답 방출 0':replayAttack?'공격자 · 녹화 응답 삽입':'응답 패킷 복귀',rogue?'응답기 로컬 기록':'질의기 · 6단계 검증'];
 draw=p=>{root.dataset.progress=p.toFixed(3);const end=p>=1;root.querySelector('.phase').textContent=end?'엔진 이벤트 재생 완료':phases[Math.min(Math.floor(p*phases.length),phases.length-1)];root.querySelector('.verdict').textContent=end?`${e.decision} · ${verdict(e)}${rogue?' · 방출 0':''}`:'이벤트 재생 중';
 root.querySelectorAll('.scene').forEach(svg=>{const track=svg.querySelector('.packet-track'),packet=svg.querySelector('.packet');const progress=p<.35?p/.35:p<.5?1:(replayAttack?.5:1)*(1-Math.min((p-.5)/.3,1));const at=track.getPointAtLength(track.getTotalLength()*progress);packet.setAttribute('transform',`translate(${at.x} ${at.y})`);packet.style.opacity=c2||end||(rogue&&p>=.5)?'0':'1';svg.querySelector('.wire').style.opacity=rogue&&p>=.5?'0':'.8';svg.querySelector('.beam').style.opacity=rogue&&p>=.5?'0':'.06';svg.querySelector('.endpoint').style.stroke=end&&e.decision==='REJECT'?'var(--fail)':'';});
 const ratio=e.rtt_ns===null?0:e.rtt_ns/Math.max(e.rtt_ns,e.budget_ns);root.querySelector('.budget-fill').style.transform=`scaleX(${ratio*Math.min(p/.9,1)})`;root.querySelector('.budget-fill').style.background=e.reject_stage==='RTT'?'var(--fail)':'var(--cyan)';root.querySelector('.budget-marker').style.left=`${e.budget_ns/Math.max(e.rtt_ns||0,e.budget_ns)*100}%`;};
}
function pipeline(e){
 const stages=['FORMAT','EPOCH','REVOKED','NONCE','TAG','RTT'];
 const active=e.component==='C1',failed=e.states.indexOf('차단'),last=failed<0?5:failed;
 root.innerHTML=`<section class="panel pipeline" data-component="pipeline"><div class="top"><div><div class="eyebrow">VERIFY / ${esc(e.scenario)}</div><div class="title">응답이 지나는 관문</div></div><button id="replay" aria-label="파이프라인 다시 재생">다시 재생</button></div><div class="gates">${stages.map((stage,i)=>`<div class="gate" data-stage="${stage}"><div class="gate-dot">${i+1}</div><strong>${stage}</strong><span class="gate-state">대기</span>${stage==='RTT'?'<div class="budget"><div class="budget-fill"></div><i class="budget-marker"></i></div>':''}</div>`).join('')}<i class="traveler"></i></div><div class="verdict ${color(e)}"></div><div class="facts">${e.rtt_ns===null?'검증 RTT 기록 없음':`RTT ${(e.rtt_ns/1000).toFixed(3)}µs / 예산 ${(e.budget_ns/1000).toFixed(3)}µs`}</div><div class="caption">${active?'시뮬레이션 · 엔진 검증 결과를 순서대로 재생합니다.':`시뮬레이션 · ${esc(e.component)} 기록은 C1 관문을 거치지 않습니다.`}</div></section>`;
 const gates=[...root.querySelectorAll('.gate')],packet=root.querySelector('.traveler');
 draw=p=>{root.dataset.progress=p.toFixed(3);const step=p*(last+1);gates.forEach((gate,i)=>{const reached=active&&step>=i+(i===failed?.55:.8),state=reached||p===1?e.states[i]:'대기';gate.classList.toggle('passed',state==='통과');gate.classList.toggle('failed',state==='차단');gate.classList.toggle('flash',state==='차단'&&p<1);gate.querySelector('.gate-state').textContent=active?state:'해당 없음';});
 const index=Math.min(Math.floor(step),last),gate=gates[index];packet.style.left=`${gate.offsetLeft+gate.offsetWidth/2}px`;packet.style.top=`${gate.offsetTop+17}px`;packet.style.opacity=active&&p<1?'1':'0';
 root.querySelector('.verdict').textContent=p===1?`${e.decision} · ${verdict(e)}`:active?'응답 패킷 검증 중':'C1 관문 해당 없음';root.querySelector('.verdict').classList.toggle('stamp',p===1&&e.decision==='ACCEPT_FRIEND');
 const ratio=e.rtt_ns===null?0:e.rtt_ns/Math.max(e.rtt_ns,e.budget_ns);root.querySelector('.budget-fill').style.transform=`scaleX(${ratio*Math.max(0,Math.min(step-5,1))})`;root.querySelector('.budget-fill').style.background=e.reject_stage==='RTT'?'var(--fail)':'var(--pass)';root.querySelector('.budget-marker').style.left=`${e.budget_ns/Math.max(e.rtt_ns||0,e.budget_ns)*100}%`;
 };
}
function radar(data){
 const maximum=data.radialaxis.max||1,cx=300,cy=224,radius=174;
 const xy=(r,a)=>[cx+Math.sin(a*Math.PI/180)*r/maximum*radius,cy-Math.cos(a*Math.PI/180)*r/maximum*radius];
 const eventColor=e=>e.decision==='ACCEPT_FRIEND'?'var(--pass)':e.decision==='REJECT'?'var(--fail)':'var(--muted)';
 const severityColor=s=>s==='high'?'var(--fail)':s==='medium'?'var(--cyan)':'var(--muted)';
 const ordered=[...data.events].sort((a,b)=>a.ts_ns-b.ts_ns||a.id-b.id),rank=new Map(ordered.map((e,i)=>[e.id,i]));
 const contacts=data.events.map(e=>{const [x,y]=xy(e.range_m,e.bearing_deg),shape=e.symbol==='x'?'<path d="M-5-5L5 5M-5 5L5-5" fill="none" stroke="currentColor" stroke-width="3"/>':e.symbol==='diamond'?'<path d="M0-7L7 0L0 7L-7 0Z" fill="currentColor"/>':'<circle r="6" fill="currentColor"/>';
 return `<g class="contact" tabindex="0" data-id="${e.id}" data-order="${rank.get(e.id)}" transform="translate(${x} ${y})" style="color:${eventColor(e)}" aria-label="${esc(`${e.scenario} · ${e.decision_label} · ${e.reject_stage||'ACCEPT'} · ${e.bearing_deg}° · ${e.range_m}m`)}"><title>${esc(`#${e.id} · ${e.scenario} · ${e.decision_label} · ${e.reject_stage||'ACCEPT'} · ${e.bearing_deg}° / ${e.range_m}m`)}</title>${e.severity?`<circle class="alert-pulse" r="11" style="stroke:${severityColor(e.severity)}"/>`:''}${e.id===data.selected?'<circle class="selection-ring" r="15"/>':''}${shape}</g>`;}).join('');
 const labels=data.labels.length<=24?data.labels:[];
 const labelMarkup=[false,true].map(right=>{let previous=18;const lane=labels.map(label=>({...label,point:xy(label.r,label.theta)})).filter(label=>(label.point[0]>=cx)===right).sort((a,b)=>a.point[1]-b.point[1]);return lane.map((label,i)=>{const [x,y]=label.point,lx=right?cx+radius+23:cx-radius-23;let desired=Math.abs(y-cy)<23?cy+25:y;const ly=Math.min(408-(lane.length-i-1)*24,Math.max(previous+24,desired));previous=ly;return `<g class="radar-label"><path d="M${x} ${y}L${right?lx-8:lx+8} ${ly}"/><text x="${lx}" y="${ly+4}" text-anchor="${right?'start':'end'}">${esc(label.text)}</text></g>`;}).join('');}).join('');
 const rings=[.25,.5,.75,1].map(f=>`<circle cx="${cx}" cy="${cy}" r="${radius*f}" class="radar-ring"/><text class="range-label" x="${cx-8}" y="${cy+radius*f-5}" text-anchor="end">${(maximum*f).toLocaleString('en-US',{maximumFractionDigits:1})}m</text>`).join('');
 const bearings=Array.from({length:8},(_,i)=>{const a=i*45,[x,y]=xy(maximum,a),[tx,ty]=xy(maximum*1.1,a);return `<path class="radar-spoke" d="M${cx} ${cy}L${x} ${y}"/><text class="bearing-label" x="${tx}" y="${ty+4}" text-anchor="${a===90?'end':a===270?'start':'middle'}">${a}°</text>`;}).join('');
 root.innerHTML=`<section class="panel radar-panel" data-component="radar"><div class="top"><div><div class="eyebrow">CONTACT GEOMETRY</div><div class="title">로그에서 재생한 접촉</div></div><button id="replay" aria-label="레이더 다시 재생">다시 재생</button></div><svg class="radar-svg" viewBox="0 0 600 440" role="img" aria-label="시뮬레이션 접촉 기하">${rings}${bearings}<g class="sweep" style="transform-origin:${cx}px ${cy}px"><path d="M${cx} ${cy}L${cx} ${cy-radius}"/></g><path d="M${cx-6} ${cy}h12m-6-6v12" stroke="var(--cyan)" stroke-width="2"/>${labelMarkup}${contacts}</svg><div class="radar-tooltip" aria-live="polite">접촉에 포인터를 올리거나 Tab으로 상세를 확인하세요.</div><div class="radar-legend"><span class="accepted">● 수락</span><span class="rejected">● 거부</span><span class="neutral">× 무응답</span><span>◇ C2 관측</span></div><div class="caption">장식 · 시뮬레이션 기하 · 실제 센서 아님<br>스윕은 탐지가 아닙니다. 좌표는 엔진 로그 그대로${labels.length?'':data.events.length?' · 밀집 접촉의 라벨은 상세 툴팁에 표시':''}.</div>${data.events.length?'':'<div class="caption">재생 대기 · 다음을 누르면 첫 엔진 이벤트가 나타납니다.</div>'}</section>`;
 root.querySelectorAll('.range-label').forEach(label=>root.querySelector('.radar-svg').appendChild(label));
 const nodes=[...root.querySelectorAll('.contact')];
 nodes.forEach(node=>{const show=()=>{root.querySelector('.radar-tooltip').textContent=node.getAttribute('aria-label');};node.addEventListener('mouseenter',show);node.addEventListener('focus',show);});
 draw=p=>{root.dataset.progress=p.toFixed(3);nodes.forEach(node=>{const start=Number(node.dataset.order)/Math.max(nodes.length,1)*.85;node.style.opacity=Math.max(0,Math.min((p-start)/.15,1));node.style.pointerEvents=p>=start?'auto':'none';});root.querySelector('.sweep').style.transform=`rotate(${p*240}deg)`;};
}
if(payload.kind==='protocol')protocol(payload.data);
if(payload.kind==='pipeline')pipeline(payload.data);
if(payload.kind==='radar')radar(payload.data);
root.querySelector('#replay')?.addEventListener('click',replay);
replay();document.fonts.ready.then(resize);
