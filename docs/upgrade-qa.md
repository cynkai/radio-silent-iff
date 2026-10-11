# 대시보드 고도화 Phase 검증

## Phase 1

- PASS: 네 프리셋을 실제 엔진으로 실행하여 ACCEPT_FRIEND / REJECT(RTT) /
  ACCEPT_FRIEND / NO_RESPONSE(IQ_TAG)를 확인. 첫 진입에서도 첫 프리셋을 실행.
- PASS: 공격별 입력을 조건부 표시하고 BER·시드는 항상 유지.
- PASS: 레이더 반경 눈금은 왼쪽 수평 표시, 중앙 0 제외, 접촉 좌표 유지.
- PASS: 1440×900 및 390×844 캡처 직접 확인. 페이지 가로 넘침 없음,
  겹치는 라벨 없음, 첫 진입 결과 영역이 비어 있지 않음.
- pytest: **139 passed** (기존 및 신규 AppTest 포함).
- run_all: S1~S9 기대값 모두 일치. 기존 테스트 파일 변경 없음.
- 캡처: [데스크톱](img/phase1-desktop.png), [결과](img/phase1-result.png),
  [모바일](img/phase1-mobile.png), [모바일 결과](img/phase1-mobile-result.png),
  [레이더](img/phase1-radar.png).

## Phase 2

- PASS: 문제부터 정직한 한계까지 9장면, 이전/다음·진행 표시·종료 동작.
- PASS: 각 장면에서 기존 시나리오를 실행하고 레이더·파이프라인 표시.
  포획 장면의 S4/S8 타임라인, 직접 공격 장면의 프리셋 이동 확인.
- PASS: 장면별 이벤트 선택 키 분리로 이전 장면 라벨 잔류 해결.
- PASS: 데스크톱/390px 캡처에서 넘침·겹치는 라벨·빈 결과 없음.
- pytest **140 passed**, AppTest 포함; run_all S1~S9 모두 기대값 일치.
- 캡처: [S1](img/phase2-scene3.png), [포획](img/phase2-scene6.png),
  [한계](img/phase2-scene9.png), [모바일](img/phase2-mobile.png),
  [모바일 상세](img/phase2-mobile-detail.png).

## Phase 3

- PASS: 201개 지연 입력을 실제 엔진으로 sweep. 현재점과 예산−기본 왕복 경계 표시.
- PASS: epoch·폐기 시점 변경에 따라 엔진의 수락/거부 구간과 선택 판정 갱신.
- PASS: 두 설정을 독립 실행하고 6단계 파이프라인 비교. 모바일에서는 세로 배치.
- PASS: 1440×900, 390×844 캡처를 직접 확인. 가로 넘침·라벨 겹침·빈 결과 없음.
- pytest **143 passed** (AppTest 포함), run_all S1~S9 기대값 일치.
- 캡처: [경계](img/phase3-desktop.png), [타임라인](img/phase3-desktop-capture.png),
  [비교](img/phase3-desktop-compare.png), [모바일](img/phase3-mobile.png),
  [모바일 타임라인](img/phase3-mobile-capture.png), [모바일 비교](img/phase3-mobile-compare.png).

## Phase 4

- PASS: LLM은 엄격한 JSON 필터만 반환. 실제 조회와 문장 구성은 코드가 실행.
- PASS: 방위·시간·기체·판정·룰 필터 검증. 모든 사실 문장에 이벤트 ID 표시.
  문장은 조회 범위 내 원본 이벤트의 정규 문장과 정확히 대조한다.
- PASS: 없는 ID, 범위 밖 ID, 원문과 다른 문장 차단을 네트워크 없는 모킹 테스트로 확인.
- PASS: 버튼 클릭 때만 외부 호출, 브리핑과 세션 한도 5회 및 세션 캐시 공유.
  세 예시는 현재 엔진 로그로 생성·캐시·재검증하며 외부 호출하지 않는다.
- PASS: 1440×900 / 390×844 직접 검토. 넘침·겹침·빈 첫 결과 없음.
- pytest **157 passed**, AppTest 포함; run_all S1~S9 기대값 일치.
- 캡처: [데스크톱](img/phase4-desktop.png), [답변](img/phase4-desktop-answer.png),
  [모바일](img/phase4-mobile.png), [모바일 답변](img/phase4-mobile-answer.png).

## Phase 5

- PASS: 교전 시간 스크러버가 엔진 이벤트의 시간순 누적 레이더와 해당 접두 로그의 경보에 연동.
- PASS: 룰별 탐지율·오탐률 막대와 BER 오탐 곡선을 한 그림에 배치. 룰별 곡선 선택 가능.
- PASS: 정답 sidecar는 탐지 입력에서 계속 분리. 차트 수치는 기존 measure/sweep의 실행 결과.
- PASS: 1440×900 / 390×844 직접 검토. 초기·최종 시각 화면과 성능 차트에서 가로 넘침,
  겹치는 라벨, 빈 초기 결과 없음. 경보 0건은 엔진 결과에 따라 명시적으로 표시.
- pytest **160 passed**, AppTest 포함; run_all S1~S9 기대값 일치.
- 캡처: [전체 트래픽](img/phase5-desktop-traffic.png), [초기 시각](img/phase5-desktop-early.png),
  [성능 비교](img/phase5-desktop-metrics.png), [모바일](img/phase5-mobile-traffic.png),
  [모바일 성능](img/phase5-mobile-metrics.png).

## Phase 6

- PASS: README 상단 3분 데모 가이드와 9장면·원클릭 프리셋 사용법 반영.
- PASS: Mermaid에 질의 인증, 판정/룰/정답 분리, JSON 필터→코드 조회→문장/ID 검증 경로 반영.
  Mermaid 파싱 및 Chromium 렌더링 확인.
- PASS: 최신 1440×900 / 390×844 첫 화면·프리셋 캡처와 README 미리보기 직접 확인.
  가로 넘침·라벨 겹침·빈 첫 결과 없음. 새 기능 스크린샷을 README에 연결.
- pytest **160 passed** (전체 AppTest 포함), `python3 scripts/run_all.py --seed 42`:
  **ALL SCENARIOS MATCH EXPECTED: True**.
- 기존 테스트·판정 엔진·시나리오·탐지 룰·기대값·경보 원문 변경 없음.
- 캡처: [첫 화면](img/phase6-first.png), [프리셋](img/phase6-presets.png),
  [모바일](img/phase6-mobile.png), [모바일 프리셋](img/phase6-mobile-presets.png),
  [구조도 렌더](img/phase6-architecture.png), [README](img/phase6-readme-desktop.png),
  [모바일 README](img/phase6-readme-mobile.png).
