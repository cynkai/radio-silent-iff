# 대시보드 표현·배치 검증

2026-10-11, 로컬 Streamlit / Playwright Chromium 헤드리스. 데스크톱 1440×900,
모바일 390×844, device scale factor 1. 최종 스크린샷을 직접 열어 확인했다.

| 번호 | 요청 | 결과와 근거 |
|---|---|---|
| 1 | 가치 제안과 3단계 안내 | PASS. 첫 화면에 한 줄 가치 제안과 3개 이동 버튼. 클릭으로 공격 재생·공격 실험·한계 분석 이동 확인. |
| 2 | 공격 실험 진입 노출 | PASS. 상단 버튼과 작업 공간 선택에 노출. `http://localhost:8501/`에서 쿼리 파라미터 없이 진입. |
| 3 | S4 REVOKED 기본 상세 | PASS. 최초 선택 `#6 · S4 · REVOKED`, FORMAT/EPOCH 통과와 REVOKED 차단 표시. |
| 4 | 얇은 회색 고지 | PASS. 데스크톱 한 줄 회색 띠. 기존 고지 문자열과 문자 단위 일치 확인. 모바일은 내용을 보존하며 줄바꿈. |
| 5 | 첫 화면 레이더 | PASS. 레이더 영역 y=499.39, 높이 400px, 하단 899.39px. 범례까지 900px 화면 안에 표시. |
| 6 | IBM 글꼴과 고정폭 숫자 | PASS. Google Fonts Sans KR/Mono 로드 확인. 본문 Sans KR, KPI·ID·hex·차트·데이터 표 Mono. KPI `tabular-nums` 확인. |
| 7 | 다크 톤과 판정색 | PASS. 배경/카드 2단계, 시안 강조. 수락 초록·거부 빨강·무응답 회색. 한계 분석 곡선은 시안과 선 모양으로 구분. |
| 8 | KPI 설명과 high 테두리 | PASS. 숫자 아래 각각 한 줄 설명. high 경보 카드에만 빨간 테두리. |
| 9 | 레이더 범위·마커·라벨 | PASS. 최대 거리 900m에 맞춰 축 상한 1035m. 마커 17px, 라벨 리더 라인. 원래 접촉 좌표는 그대로이며 기존 좌표 검증 테스트 통과. |
| 10 | 한글 경보 우선 | PASS. 큰 한글 제목 아래 작은 회색 영어 원문. 표시 원문 8건 모두 엔진 원문과 정확히 일치. |
| 11 | Streamlit 장식 숨김 | PASS. 헤더·메뉴·푸터 CSS 숨김. 최초 사이드바 `aria-expanded=false`. |
| 12 | 모바일 배치 | PASS. KPI 두 열, 레이더→상세 순서의 세로 배치. 콘솔과 공격 실험 모두 페이지 폭/scrollWidth=390px. |

## 스크린샷

- [첫 화면](img/dashboard-first.png)
- [스크롤 후 이벤트·경보](img/dashboard-scroll.png)
- [공격 실험](img/dashboard-experiments.png)
- [390px 첫 화면](img/dashboard-mobile.png)
- [390px 레이더와 상세](img/dashboard-mobile-radar.png)
- [390px 상세와 피드](img/dashboard-mobile-detail.png)
- [390px 공격 실험](img/dashboard-mobile-experiments.png)
- [한계 분석](img/dashboard-limits.png)
- [이벤트 로그](img/dashboard-events.png)
- [포획 기체 타임라인](img/dashboard-timeline.png)
- [공격자 비용](img/dashboard-cost.png)

## 실행 검증

- `python3 -m pip install playwright && python3 -m playwright install chromium`: 성공.
- `python3 -m streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false`: 성공.
- `python3 -m pytest -q`: **134 passed in 14.80s**, 기존 AppTest 포함.
- `python3 scripts/run_all.py --seed 42`: S1~S9 모두 MATCH=True,
  `ALL SCENARIOS MATCH EXPECTED: True`.
- 추가 임시 AppTest: 예외 없음, S4 REVOKED 기본 선택, 고지 원문 일치,
  경보 원문 8/8 일치. 저장소 테스트 파일은 추가·수정하지 않았다.
- 브라우저 클릭: 세 안내 버튼의 도착 화면, 공격 재생 첫 이벤트 1건,
  샌드박스 기본 입력의 실제 `ACCEPT_FRIEND` 출력 확인.
- `git diff --check`: 통과. 판정·시나리오·룰·테스트·기대값 파일의 diff 없음.
- 독립 읽기 전용 화면 검토: 최종 스크린샷 11장과 전체 diff 확인 후
  **PASS / APPROVE**, 12개 항목 모두 통과, 남은 차단 사항 없음.

## 검토 범위

변경 파일은 화면 진입·배치, 차트 표현, CSS/테마, 문서와 캡처다.
차트의 접촉 데이터와 계산식, 시나리오 실행, 탐지 입력과 원문은 유지했다.
수정 Python 모듈은 모두 비공백·비주석 기준 200줄 미만이다.
새 데이터 파싱 계층이나 타입 검사 우회는 추가하지 않았다.

기존 `use_container_width` 사용에 대한 Streamlit 폐기 예정 경고는 남아 있다.
스킬 정적 검사의 기존 pandas import 및 기존 파이프라인 if/elif 지적은
이번 표현·배치 작업 범위 밖이므로 변경하지 않았다. LSP는 설치되어 있지 않아
실행하지 않았으며, 기존 사용자의 설치 거절 설정을 유지했다.
