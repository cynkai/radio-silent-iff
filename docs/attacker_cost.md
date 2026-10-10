# 공격자 비용 모델

확률은 명시된 조건 아래의 값이다. 실측 운용 비용은 미측정이다.
숫자 칸이 빈 항목은 유도할 근거가 없으며 0을 뜻하지 않는다.

| 공격 | 조건 | 성공 확률 | 필요 역량 | 유효 시간 |
|---|---|---:|---|---|
| S9a 가짜 질의기 | 균등 32비트 iq_tag 추측 | 2^-32 / 시도 | 공개 질의 필드와 송신 역량 | 현재 epoch만 허용; 시도 빈도 미측정 |
| S9b 질의 재방송 | 같은 응답기가 같은 epoch에서 처리한 nonce | 0 | 진짜 질의 녹화·재송신 | 해당 epoch의 nonce 기록 보존 조건 |
| S2 재전송 | 이미 소비된 nonce | 0 | 이전 응답을 관측·저장하고 재송신할 역량 | 소비된 nonce의 유효 시간은 0초; 미소비 질의의 시간 제한은 미측정(TTL 미구현) |
| S3 중계 MITM | 추가 지연 0µs | 1 | 질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량 | 미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현) |
| S3 중계 MITM | 추가 지연 10µs | 1 | 질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량 | 미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현) |
| S3 중계 MITM | 추가 지연 20µs | 1 | 질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량 | 미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현) |
| S3 중계 MITM | 추가 지연 30µs | 0.595 | 질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량 | 미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현) |
| S3 중계 MITM | 추가 지연 40µs | 0 | 질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량 | 미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현) |
| S3 중계 MITM | 추가 지연 60µs | 0 | 질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량 | 미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현) |
| S3 중계 MITM | 추가 지연 100µs | 0 | 질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량 | 미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현) |
| S3 중계 MITM | 추가 지연 200µs | 0 | 질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량 | 미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현) |
| S4 포획 기체 | 폐기 전·현재/유예 epoch | 1 | 해당 기체의 유효 epoch/unit 키 확보 및 정상 응답 생성 역량 | 폐기 시 즉시 무효; 폐기 없으면 현재+유예(1) epoch까지 유효, 최대 약 2×EPOCH_SECONDS = 1,200초 |
| S4 포획 기체 | 폐기 후 | 0 | 해당 기체의 유효 epoch/unit 키 확보 및 정상 응답 생성 역량 | 폐기 시 즉시 무효; 폐기 없으면 현재+유예(1) epoch까지 유효, 최대 약 2×EPOCH_SECONDS = 1,200초 |
| S5 무작위 위조 | 시도당 균등 태그 추측 | 2.3283064e-10 | 공개 질의 nonce를 수신하고 형식에 맞는 응답·무작위 태그를 송신할 역량 | 미측정: 미소비 nonce 질의 동안 시도(TTL·시도 빈도 미구현) |
| S6 기동 재현 | 편대 1대 | 0.0020904541 | 이전 기동을 관측·기록하고 비트 패턴에 대응하는 미세 기동을 재현할 역량 | 현재 패턴 window의 남은 시간 ≤ 60초; 다음 window는 새 패턴 |
| S6 기동 재현 | 편대 5대 | 0.010408662 | 이전 기동을 관측·기록하고 비트 패턴에 대응하는 미세 기동을 재현할 역량 | 현재 패턴 window의 남은 시간 ≤ 60초; 다음 window는 새 패턴 |
| S6 기동 재현 | 편대 10대 | 0.020708983 | 이전 기동을 관측·기록하고 비트 패턴에 대응하는 미세 기동을 재현할 역량 | 현재 패턴 window의 남은 시간 ≤ 60초; 다음 window는 새 패턴 |
| S6 기동 재현 | 편대 25대 | 0.050971125 | 이전 기동을 관측·기록하고 비트 패턴에 대응하는 미세 기동을 재현할 역량 | 현재 패턴 window의 남은 시간 ≤ 60초; 다음 window는 새 패턴 |
| S6 기동 재현 | 편대 50대 | 0.099344194 | 이전 기동을 관측·기록하고 비트 패턴에 대응하는 미세 기동을 재현할 역량 | 현재 패턴 window의 남은 시간 ≤ 60초; 다음 window는 새 패턴 |
| S6 기동 재현 | 편대 100대 | 0.18881912 | 이전 기동을 관측·기록하고 비트 패턴에 대응하는 미세 기동을 재현할 역량 | 현재 패턴 window의 남은 시간 ≤ 60초; 다음 window는 새 패턴 |
| S6 기동 재현 | 편대 200대 | 0.34198558 | 이전 기동을 관측·기록하고 비트 패턴에 대응하는 미세 기동을 재현할 역량 | 현재 패턴 window의 남은 시간 ≤ 60초; 다음 window는 새 패턴 |

## S9 유도와 출처

질의 태그는 32비트 HMAC 절단값으로 질의 +4바이트입니다. S9a의 잘못된 태그와
S9b의 소비된 nonce는 무응답입니다. 포획 드론에서 iq_key 유출 시 해당 epoch 동안
가짜 질의가 가능하므로 공유 키 회전·폐기와 신규 키 배포 제외로 제한합니다.
unit ID 폐기만으로 공유 iq_key를 폐기할 수 없습니다. 캐시는 메모리에 있으므로
재시작 시 nonce 기록 보존은 별도로 필요하며, 처음 전달되는 녹화 질의는 구분할 수 없습니다.

출처: `iff/crypto.py:iq_key,challenge_tag`, `iff/protocol.py:Responder.respond`,
`iff/scenarios.py:s9_rogue_interrogator`.

## S2 유도와 출처

소비된 nonce 재전송은 0. 새 nonce와의 단일 충돌 확률은 2^-64 = 5.42101e-20 (독립·균등 생성 가정; 공격 성공률과 구분).

소비된 nonce의 유효 시간은 0초; 미소비 질의의 시간 제한은 미측정(TTL 미구현)

nonce가 다시 발급되는 충돌은 별도 조건이며, 다른 검증 단계도 통과해야 한다.

출처: iff/config.py:NONCE_BYTES; iff/protocol.py:Interrogator.verify NONCE; iff/scenarios.py:s2_replay

## S3 유도와 출처

지연별 성공률 = 1 − reject_rate; 유효한 아군 응답을 중계한 시뮬레이션 비율

미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현)

명목 탐지 경계 ≈ (RTT 예산 − 기본 왕복) ≈ 30.674µs (약 31µs). 명목 경계는 지터와 무관하며, 경계 주변 성공률은 지터의 영향을 받는다. 기준 거리 400.0m, 시드 42, 지연별 200회. 지연 분포가 없어 단일 종합 성공률은 미측정.

출처: relay_sweep.csv:relay_overhead_ns,reject_rate,budget_ns,nominal_rtt_ns; scripts/sweep_noise.py:relay_sweep; iff/config.py:rtt_budget_ns

## S4 유도와 출처

폐기 후 0; 폐기 전 1은 유효 키·새 nonce·허용 RTT를 모두 갖춘 조건부 수락

폐기 시 즉시 무효; 폐기 없으면 현재+유예(1) epoch까지 유효, 최대 약 2×EPOCH_SECONDS = 1,200초

해당 epoch의 키만 보유하고 신규 키가 배포되지 않으며, EPOCH_SECONDS마다 정상 회전한다는 조건. 포획 시점에 따라 남은 시간은 짧아진다. 검증기는 epoch를 입력받으며 자동 시간 회전은 구현하지 않는다. S8은 E+1 수락 후 폐기 시 REVOKED를 시연한다.

출처: iff/config.py:EPOCH_SECONDS,EPOCH_GRACE; iff/protocol.py:Interrogator.verify EPOCH/REVOKED/TAG; iff/scenarios.py:s8_captured_key_grace

## S5 유도와 출처

시도당 2^-TAG_BITS = 2^-32; 다른 검증 조건을 통과한 태그 추측

미측정: 미소비 nonce 질의 동안 시도(TTL·시도 빈도 미구현)

반복 시도 누적 성공률은 시도 수가 주어지지 않아 미측정. 키 보유는 필요하지 않다.

출처: iff/config.py:TAG_BITS; iff/crypto.py:response_tag; iff/attacks.py:forge

## S6 유도와 출처

p = random_match_prob = 0.00209045410156; 편대 오수락 = 1 − (1 − p)^m

현재 패턴 window의 남은 시간 ≤ 60초; 다음 window는 새 패턴

독립·균등 패턴 가정의 해석적 오수락이며 특정 S6 재현 실험의 성공률은 아니다. n=16, K=2. window를 주기적으로 갱신하는 조건이며 관측·재현 비용과 실제 운용 시간은 미측정.

출처: list_size.csv:fleet_size,analytic_any_false_match,per_unit_prob; iff/maneuver.py:random_match_prob; iff/config.py:MANEUVER_BITS,MANEUVER_HAMMING_K,MANEUVER_WINDOW_S
# 추가 실험: 샌드박스와 교전 트래픽

`작업 공간 → 공격 실험`에서 직접 재현합니다. 기존 비용 모델 값은 유지하며,
아래 값은 `python3 scripts/traffic.py --benign 200 --attacks 100 --seed 42`의 실험 결과입니다.
금전·장비·연산 비용은 측정하지 않았습니다. 단일 시도 결과를 성공 확률로 해석하지 않습니다.

| 공격 / 측정 조건 | 관측 결과 | 필요한 역량 / 한계 | 측정 출처 |
|---|---|---|---|
| 중계 25µs, 400m, BER=0, seed=42 | ACCEPT_FRIEND, RTT 79.214µs | 유효 응답을 예산 내 전달; 방어 실패 | out/traffic/sandbox.csv |
| 중계 40µs, 같은 조건 | REJECT / RTT, 94.214µs | 같은 유효 태그여도 예산 초과 시 거부 | out/traffic/sandbox.csv |
| 포획 후 1epoch, 미폐기 | ACCEPT_FRIEND, 54.214µs | 유예 중 유효 unit 키; 방어 실패 | out/traffic/sandbox.csv |
| 포획 후 1epoch, 폐기 | REVOKED | 동일 키도 폐기 후 무효 | out/traffic/sandbox.csv |
| 가짜 질의기 / 질의 재방송 | IQ_TAG / IQ_NONCE, 무응답 | 질의 태그 또는 미소비 nonce 필요 | out/traffic/sandbox.csv |
| 혼합 N=200, M=100, BER=0 | 차단율 94%, 경보율 75%; TP=75, FP=0, FN=25 | 공격 6종 무작위 혼합; 아래 무경보 분해 참조 | out/traffic/events.jsonl, truth.jsonl, metrics.csv |
| 동일 트래픽 BER=0.1 | ANY_RULE TP=63, FP=2, FN=37 | 응답 태그 손상; 오탐률 1% | out/traffic/ber_sweep.csv |

| 무경보 공격 유형 | 차단됐지만 룰 없음 | 알려진 한계로 통과 | 기타 |
|---|---:|---:|---:|
| 무작위 위조 | 18 (TAG) | 0 | 0 |
| 포획 기체 | 3 (EPOCH) | 4 (유효 키·미폐기) | 0 |
| 재전송 / 중계 / 가짜 질의기 / 질의 재방송 | 0 | 0 | 0 |
| 합계 | 21 | 4 | 0 |

무경보 25/100 중 21건은 차단됐습니다. 전체 통과 6건 중 중계 2건에는 경보가 붙었습니다.
차단율은 공격 중 REJECT/NO_RESPONSE 비율, 경보율은 하나 이상의 룰 경보 근거가 붙은 비율입니다.
기타는 두 범주에 속하지 않는 무경보 공격입니다. 기존 CSV의 `detection_rate`는 경보율입니다.
경보율 분모는 각 룰이 맡는 유형만이 아니라 전체 공격 100건입니다. 실제 운영 유병률이나
공격 비용을 추정하지 않습니다. 정답 라벨은 탐지 후에만 결합하며, 룰에는 전달하지 않습니다.
첫 실패 창을 반환하는 R5 특성상 오탐 곡선은 단조 증가를 보장하지 않습니다.
