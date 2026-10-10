# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy==2.5.3", "PyYAML==6.0.3", "streamlit==1.65.0", "openai==2.45.0"]
# ///
# How to run: uv run scripts/make_sample_brief.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iff import detect, scenarios
from iff.briefing import Brief, Finding, SAMPLE_PATH, event_id, verify_brief
from iff.events import to_dicts


def main() -> None:
    results = scenarios.run_all(seed=42, include_grace=True, include_rogue=True)
    events = [event for result in results.values() for event in result["events"]]
    alerts = detect.run_rules(to_dicts(events), revoked_hex=[scenarios.CAP.hex()])
    findings = []
    for prefix, stage, explanation in [
        ("R2_", "RTT", "RTT 단계 거부와 중계 의심 경보가 기록되었습니다."),
        ("R3_", "REVOKED", "폐기 기체 활동 경보와 REVOKED 거부 기록을 확인하세요."),
        ("R7_", "IQ_TAG", "질의 인증 관련 경보가 기록되었습니다."),
    ]:
        alert = next(alert for alert in alerts if alert["rule"].startswith(prefix))
        event = next(event for event in events
                     if event.reject_stage == stage and event.ts_ns in alert["evidence"])
        findings.append(Finding(text=f"unit_id={event.unit_id} · {explanation}",
                                evidence_event_ids=[event_id(event)], rule=alert["rule"]))
    brief = Brief(summary="중계 의심, 폐기 기체 활동, 질의 인증 경보를 우선 검토하세요.",
                  findings=findings, recommendations=[
                      "근거 이벤트의 상세 패널과 원본 경보를 함께 확인하세요.",
                      "이 해석으로 식별 판정이나 인증 설정을 자동 변경하지 마세요.",
                  ])
    verification = verify_brief(brief, events, alerts)
    if verification.passed != verification.total:
        raise RuntimeError(verification)
    SAMPLE_PATH.write_text(brief.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"Generated offline example: {verification.passed}/{verification.total} verified")


if __name__ == "__main__":
    main()
