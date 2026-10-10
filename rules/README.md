# YAML 탐지 룰

`detect.run_rules(events, revoked_hex=None, d_max_m=...)`는 이 폴더의
`*.yaml`을 파일명 순서대로 읽는다. 파일 하나가 룰 하나이며, 매 호출마다 다시 읽으므로
YAML 추가가 다음 호출부터 반영된다. `rules_dir=Path(...)`로 다른 폴더를 지정할 수 있다.

지원하는 처리는 기존 R1~R5에 필요한 아래 세 가지뿐이다.

| kind | 사용 룰 | YAML 필드와 동작 |
|---|---|---|
| `event` | R1, R2, R3 | `cases`의 각 `match`는 필드의 문자열 동등 조건을 AND로 결합한다. 이벤트마다 첫 일치 case의 `severity`, `message`로 경보를 출력한다. R2의 `rtt_above_budget_fraction`은 RTT가 거리 예산 × 비율을 **초과**하는 조건이다. |
| `pair` | R4 | `match`로 선택하고 `group_by`로 묶는다. 같은 그룹의 모든 쌍을 비교해 `difference_gt` 중 하나라도 절대 차이가 임계값을 **초과**하면 경보를 출력한다. |
| `window` | R5, 예시 R6 | `match`로 선택하고 시간순으로 정렬한다. 기준 이벤트로부터 `bearing_tolerance_deg` 이내, 앞쪽 `window_ns` 이내에 `min_count`개 이상이면 전체 집계를 evidence로 출력한다. 경계값을 포함하며 첫 집계만 출력한다. |

공통 필드는 `id`와 `kind`다. `severity`는 `low`, `medium`, `high` 중 하나다.
`message`는 문자열이며 `{unit_id}`만 치환한다. 임의 식이나 Python 코드는 실행하지 않는다.
필드 조건, 임계값, 경보 문구는 YAML에 있고, 별도의 룰 ID 등록 코드는 없다.

## 경보 출력 규칙

- 경보는 파일명 순서(R1→R5), 이벤트 룰은 입력 이벤트 순서다.
- R4는 그룹 최초 등장 순서와 그룹 안의 입력 순서에 따른 모든 쌍을 유지한다.
- R5의 시간 정렬은 동률에서 입력 순서를 유지한다. evidence는 기준 이벤트가 먼저다.
  같은 객체의 중복 참조는 자기 자신으로 제외하고, 값만 같은 별도 이벤트는 센다.
- 방위 차이는 원형 각도 보정 없이 절대 차이로 계산한다.
- `revoked_hex` 인자는 호출 호환성을 위해 유지한다. 기존 R3처럼 실제 경보 조건은
  `reject_stage: REVOKED`이며, 폐기 목록 포함만으로 경보가 생기지는 않는다.
- 경보 키 순서는 `rule`, `severity`, `message`, `evidence`이고 evidence는 `ts_ns` 목록이다.

## R6 추가 시연

저장소 루트에서 실행한다.

```bash
python3 scripts/demo_r6.py
```

데모는 현재 epoch 100에서 epoch 98 키로 만든 응답 세 건을 실제 인증기에 넣는다.
1초·5초·11초, 방위 30°·35°·40°에서 모두 `REJECT/EPOCH`가 된다.
임시 폴더의 R1~R5로 먼저 탐지한 뒤, `examples/rules/06-epoch-probe.yaml`만 복사하고
동일한 입력을 다시 탐지한다. 기존 경보는 유지되고 `R6_STALE_KEY_PROBE`가 추가된다.
임시 폴더는 실행 후 정리되며 기본 룰 폴더에는 R1~R5가 유지된다.

기본 룰에 실제로 활성화할 때 필요한 변경도 파일 복사 하나다.

```bash
cp examples/rules/06-epoch-probe.yaml rules/
```

R6는 같은 방위 범위에서 10초 내 EPOCH 거부가 3회 이상 반복되면 오래된 키 탐색을
**의심**하는 경보다. EPOCH 거부만으로 키 보유나 공격 의도를 확정하지 않는다.

## 검증 기준

`tests/fixtures/detect_legacy_alerts.json`은 엔진 교체 전 구현으로 생성한 고정 기대값이다.
25개 케이스의 경보를 동일 설정(`ensure_ascii=False`, `separators=(",", ":")`)으로
JSON 직렬화한 UTF-8 바이트와 비교한다. 경보 및 키 순서, 문구, evidence 순서를 포함한다.
고유 타임스탬프를 사용한 케이스와 동률·동일 객체 중복 케이스를 따로 둔다.
