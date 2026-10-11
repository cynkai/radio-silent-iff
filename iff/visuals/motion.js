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
if(payload.kind==='protocol')protocol(payload.data);
root.querySelector('#replay')?.addEventListener('click',replay);
replay();document.fonts.ready.then(resize);
