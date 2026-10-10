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
