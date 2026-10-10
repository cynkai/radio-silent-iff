# Radio-silent IFF — 2-컴포넌트 피아식별 시뮬레이션

**D4D x EDTH · Korean Defense Tech Hackathon · Track 1 / Problem 04**

> ⚠️ **시뮬레이션입니다.** 실기체·실채널·실측값이 없습니다. 모든 암호는 표준 공개 기법
> (HKDF-SHA256 per RFC 5869, HMAC-SHA256, nonce 챌린지-응답)이며, 하드웨어 없이
> 파이썬으로만 동작합니다. 목적은 **프로토콜의 공격 내성을 재현 가능하게 보이는 것**이지
> 성능 수치를 주장하는 것이 아닙니다.

---

## 1. 문제 해석

전파 방출을 최소화한 채 아군·적 무인기를 식별하고 MITM·재전송에 견디는 2-컴포넌트
IFF를 요구한다. 우리는 "2-컴포넌트"를 **서로 다른 채널의 두 인증 요소**로 해석했다.

| | 컴포넌트 1: 광학 챌린지-응답 | 컴포넌트 2: 기동 서명 |
|---|---|---|
| 채널 | 지향성 광학, 질의 시에만 | 미세 기동 패턴, 카메라 관찰 |
| 방출 | 질의 시 지향성만 | **0 (완전 수동)** |
| 강도 | 강함 (HMAC + nonce + 거리검증) | 약함 (관측 노이즈에 민감) |
| 용도 | 확인이 필요할 때 | 무선침묵 기본 모드 |

둘을 묶는 이유: C2는 방출이 0이지만 약하고, C1은 강하지만 질의 시 방출이 있다.
평시엔 C2로 수동 식별하다, 확신이 필요할 때만 C1을 지향성으로 쏜다.

## 2. 위협 모델과 기대 결과

| # | 시나리오 | 공격자 능력 | 차단 단계 |
|---|---|---|---|
| S1 | 정상 아군 | 유효 키 | ACCEPT |
| S2 | 재전송 | 과거 응답 녹화·재생 | **NONCE** |
| S3 | 중계 MITM | 질의를 원거리 아군에 전달 | **RTT** (지연 초과 시) |
| S4 | 포획 기체 | 진짜 키 보유 | **REVOKED** → 다음 epoch **TAG** |
| S5 | 무작위 위조 | 키 없음 | **TAG** |
| S6 | 기동 재현 | 이전 window 기동 모방 | **C2_HAMMING** |

`python scripts/run_all.py` 실행 시 위 기대값과 실제 결과가 전부 일치함을 출력한다
(불일치 시 비정상 종료). 테스트도 이 표를 하드코딩해 검증한다.

추가 시연 S8은 epoch E 키로 만든 응답이 E+1에서도 grace로 수락되고,
같은 유예 구간에서 기체를 폐기하면 즉시 `REVOKED`로 거부되는 것을 보여준다.
CLI와 대시보드는 S8을 포함한다. 기존 S1~S7 결과를 고정한 Python 호출은 유지하며,
`scenarios.run_all(seed=42, include_grace=True)`로 S8을 포함할 수 있다.

## 3. 키 계층과 검증 파이프라인

- `epoch_key = HKDF(master_key, "iff-epoch", epoch)`
- `unit_key  = HKDF(epoch_key, "iff-unit", unit_id)`
- `tag = truncate32(HMAC(unit_key, "C1" ‖ nonce ‖ unit_id ‖ epoch))`
- 폐기: 포획 `unit_id`는 폐기 목록에 즉시 등록, 다음 epoch부터 키 미배포

검증 순서(첫 실패 지점을 `reject_stage`로 기록):
`FORMAT → EPOCH → REVOKED → NONCE → TAG → RTT`

32비트 절단 근거: 광학 채널 대역폭 제약. nonce가 매번 새로우므로 무작위 위조
성공 확률은 시도당 2⁻³². (대역폭/보안 트레이드오프는 파라미터로 조절 가능.)

## 4. 탐지 룰 (판정과 별개의 로그 경보)

- **R1 REPLAY_ATTEMPT** — `reject_stage=NONCE`
- **R2 RELAY_SUSPECT** — `reject_stage=RTT`, 또는 수락됐으나 RTT가 예산의 90% 초과
- **R3 REVOKED_UNIT_ACTIVE** — 폐기된 unit이 여전히 응답 (포획 기체 운용 중, 고가치)
- **R4 CLONE_SUSPECT** — 같은 unit이 동일 epoch 내 양립 불가능한 두 위치에서 수락
- **R5 FAILURE_BURST** — 좁은 방위 섹터에서 60초 내 거부 3회 이상

룰 정의는 `rules/*.yaml`에 있으며, 엔진은 필드 매칭·쌍 비교·시간창 집계를 지원한다.
`python3 scripts/demo_r6.py`로 YAML 파일만 추가해 **R6 STALE_KEY_PROBE**
(같은 방위 범위에서 10초 내 EPOCH 거부 3회)를 활성화하는 시연을 실행할 수 있다.
자세한 사용법과 기존 경보의 바이트 비교 기준은 [rules/README.md](rules/README.md)에 있다.

## 5. 가정과 한계 (정직하게)

**측정하지 않은 가정값 (`iff/config.py`의 `ASSUMPTION_*`)**
- `ASSUMPTION_PROC_NS = 50 µs` — 응답기 처리 지연 (가정)
- `ASSUMPTION_PROC_JITTER_NS = 5 µs` — 처리 지연 지터 (가정)
- `ASSUMPTION_PROC_MAX_NS = 70 µs` — RTT 검증에 허용한 처리 성분 (가정)

**설계상 한계**
- **거리 검증**: 기본 설정의 명목 탐지 경계는 **RTT 예산 − 기본 왕복 ≈ 30.674µs (약 31µs)**다.
  명목 경계는 지터와 무관하며, 경계 주변 성공률은 지터의 영향을 받는다.
  `out/relay_sweep.csv`의 지연별 성공률은 `1 − reject_rate`다.
- **포획 키 유효 구간**: 폐기 시 즉시 무효; 폐기 없으면 현재+유예(`EPOCH_GRACE=1`)
  epoch까지 유효하며 최대 약 `2×EPOCH_SECONDS = 1,200초`다. 해당 epoch 키만 보유하고
  새 키를 받지 않으며 정상적으로 epoch가 회전하는 조건이다. 코드가 벽시계로 epoch를
  자동 회전시키지는 않는다. S4의 다음 epoch TAG 거부는 **새 epoch를 주장하며 옛 키로 서명한 경우**이고,
  이전 epoch를 그대로 제시하는 grace 수락과 즉시 폐기는 S8이 증명한다.
- **C2 목록 크기**: C2는 `unit_id`를 모른 채 관측만 하므로 아군 목록 전체와 대조한다.
  목록이 커질수록 오수락 확률이 올라간다 (`out/list_size.csv`). 따라서 C2 단독
  식별은 소규모 편대용이며, 대규모·고신뢰 식별은 C1 확인이 필요하다.
- **C2 노이즈 민감도**: 관측 σ가 커지면 정상 아군 수락률이 떨어진다
  (`out/roc.csv`). 단, 재전송(이전 window 모방)은 노이즈와 무관하게 거부된다.
- 광학/음향 채널의 물리 계층은 모델링하지 않았다. 프로토콜은 채널 독립적이다.

## 6. 실행 방법

```bash
python3 -m venv .venv && source .venv/bin/activate   # 선택
pip install -r requirements.txt

python -m pytest -q                 # 전체 테스트
python scripts/run_all.py --seed 42 # 시나리오 → out/events.jsonl, out/summary.csv
python scripts/sweep_noise.py       # 한계 분석 → out/roc.csv, relay_sweep.csv, list_size.csv
streamlit run app.py                # 대시보드
```

대시보드의 **⑤ 공격자 비용** 패널은 S2~S6의 성공 확률, 필요 역량, 유효 시간과 출처를 보여준다.
`scripts/sweep_noise.py`는 기존 분석 CSV에 유도 출처를 덧붙이고,
`out/attacker_cost.csv`와 [설명 글](out/attacker_cost.md)을 함께 생성한다.
`run_all.py`와 패널에서도 같은 비용 모델로 내보낸다. sweep 파일이 없으면 해당 값은 미측정으로 남는다.
유도 불가능한 수치는 CSV 숫자 칸을 비우며, S6은 독립·균등 패턴 가정의 편대별 해석적 오수락이다.
CSV·패널·설명 글은 동일한 데이터와 유효 구간 문구를 사용한다.

## 7. 해커톤 기간 중 새로 개발한 범위

**전부 신규.** 기존 코드·사전 작업물 없음. 이 레포의 모든 파일
(프로토콜, 검증 파이프라인, 채널·기동 모델, 공격 시나리오, 탐지 룰, 대시보드,
테스트)이 본 해커톤 기간 중 작성되었다.
