import csv
import io
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from . import config
from .maneuver import random_match_prob


@dataclass(frozen=True, slots=True)
class AttackCost:
    scenario: str
    attack: str
    condition: str
    success_probability: float | None
    probability_note: str
    capability: str
    valid_window_upper_s: float | None
    valid_window: str
    source: str
    notes: str
    relay_overhead_ns: float | None = None
    fleet_size: int | None = None


def captured_window_text() -> str:
    duration = (1 + config.EPOCH_GRACE) * config.EPOCH_SECONDS
    return (f"폐기 시 즉시 무효; 폐기 없으면 현재+유예({config.EPOCH_GRACE}) epoch까지 유효, "
            f"최대 약 {1 + config.EPOCH_GRACE}×EPOCH_SECONDS = {duration:,}초")


def _read_csv(path: Path) -> list[Mapping[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def relay_boundary_text(row: Mapping[str, str]) -> str:
    if not row.get("nominal_rtt_ns") or not row.get("budget_ns"):
        return "명목 탐지 경계 미측정: 기준 RTT가 포함된 relay_sweep.csv가 필요하다."
    boundary_us = (float(row["budget_ns"]) - float(row["nominal_rtt_ns"])) / 1000
    return (f"명목 탐지 경계 ≈ (RTT 예산 − 기본 왕복) ≈ {boundary_us:.3f}µs "
            f"(약 {boundary_us:.0f}µs). 명목 경계는 지터와 무관하며, 경계 주변 성공률은 지터의 영향을 받는다.")


def build_costs(out_dir: Path) -> list[AttackCost]:
    """Derive conditional attack costs from configuration and existing sweep CSVs."""
    nonce_bits = 8 * config.NONCE_BYTES
    rows = [AttackCost(
        "S2", "재전송", "이미 소비된 nonce", 0.0,
        f"소비된 nonce 재전송은 0. 새 nonce와의 단일 충돌 확률은 2^-{nonce_bits} "
        f"= {2.0 ** -nonce_bits:.6g} (독립·균등 생성 가정; 공격 성공률과 구분).",
        "이전 응답을 관측·저장하고 재송신할 역량", 0.0,
        "소비된 nonce의 유효 시간은 0초; 미소비 질의의 시간 제한은 미측정(TTL 미구현)",
        "iff/config.py:NONCE_BYTES; iff/protocol.py:Interrogator.verify NONCE; iff/scenarios.py:s2_replay",
        "nonce가 다시 발급되는 충돌은 별도 조건이며, 다른 검증 단계도 통과해야 한다.",
    )]
    for point in _read_csv(out_dir / "relay_sweep.csv") or [{}]:
        overhead = float(point["relay_overhead_ns"]) if point else None
        rows.append(AttackCost(
            "S3", "중계 MITM", f"추가 지연 {overhead / 1000:g}µs" if overhead is not None else "미측정",
            1 - float(point["reject_rate"]) if point else None,
            "지연별 성공률 = 1 − reject_rate; 유효한 아군 응답을 중계한 시뮬레이션 비율",
            "질의를 아군에 전달하고 유효 응답을 낮은 지연으로 중계할 역량", None,
            "미측정: 새 nonce 질의에 대한 응답 시간 창(TTL 미구현)",
            "relay_sweep.csv:relay_overhead_ns,reject_rate,budget_ns,nominal_rtt_ns; "
            "scripts/sweep_noise.py:relay_sweep; iff/config.py:rtt_budget_ns",
            relay_boundary_text(point)
            + f" 기준 거리 {point.get('distance_m', '미측정')}m, "
            f"시드 {point.get('seed', '미측정')}, 지연별 {point.get('trials', '미측정')}회. "
            "지연 분포가 없어 단일 종합 성공률은 미측정.",
            relay_overhead_ns=overhead,
        ))
    duration = (1 + config.EPOCH_GRACE) * config.EPOCH_SECONDS
    captured_notes = (
        "해당 epoch의 키만 보유하고 신규 키가 배포되지 않으며, EPOCH_SECONDS마다 정상 회전한다는 조건. "
        "포획 시점에 따라 남은 시간은 짧아진다. 검증기는 epoch를 입력받으며 자동 시간 회전은 구현하지 않는다. "
        "S8은 E+1 수락 후 폐기 시 REVOKED를 시연한다."
    )
    for revoked in (False, True):
        rows.append(AttackCost(
            "S4", "포획 기체", "폐기 후" if revoked else "폐기 전·현재/유예 epoch",
            0.0 if revoked else 1.0,
            "폐기 후 0; 폐기 전 1은 유효 키·새 nonce·허용 RTT를 모두 갖춘 조건부 수락",
            "해당 기체의 유효 epoch/unit 키 확보 및 정상 응답 생성 역량",
            0.0 if revoked else float(duration), captured_window_text(),
            "iff/config.py:EPOCH_SECONDS,EPOCH_GRACE; iff/protocol.py:Interrogator.verify EPOCH/REVOKED/TAG; "
            "iff/scenarios.py:s8_captured_key_grace",
            captured_notes,
        ))
    rows.append(AttackCost(
        "S5", "무작위 위조", "시도당 균등 태그 추측", 2.0 ** -config.TAG_BITS,
        f"시도당 2^-TAG_BITS = 2^-{config.TAG_BITS}; 다른 검증 조건을 통과한 태그 추측",
        "공개 질의 nonce를 수신하고 형식에 맞는 응답·무작위 태그를 송신할 역량", None,
        "미측정: 미소비 nonce 질의 동안 시도(TTL·시도 빈도 미구현)",
        "iff/config.py:TAG_BITS; iff/crypto.py:response_tag; iff/attacks.py:forge",
        "반복 시도 누적 성공률은 시도 수가 주어지지 않아 미측정. 키 보유는 필요하지 않다.",
    ))
    for point in _read_csv(out_dir / "list_size.csv") or [{}]:
        fleet_size = int(point["fleet_size"]) if point else 1
        per_unit = float(point["per_unit_prob"]) if point else random_match_prob()
        probability = float(point["analytic_any_false_match"]) if point else per_unit
        rows.append(AttackCost(
            "S6", "기동 재현", f"편대 {fleet_size}대" if point else "단일 대상(편대 목록 미측정)",
            probability, f"p = random_match_prob = {per_unit:.12g}; 편대 오수락 = 1 − (1 − p)^m",
            "이전 기동을 관측·기록하고 비트 패턴에 대응하는 미세 기동을 재현할 역량",
            float(config.MANEUVER_WINDOW_S),
            f"현재 패턴 window의 남은 시간 ≤ {config.MANEUVER_WINDOW_S}초; 다음 window는 새 패턴",
            "list_size.csv:fleet_size,analytic_any_false_match,per_unit_prob; "
            "iff/maneuver.py:random_match_prob; iff/config.py:MANEUVER_BITS,MANEUVER_HAMMING_K,MANEUVER_WINDOW_S",
            "독립·균등 패턴 가정의 해석적 오수락이며 특정 S6 재현 실험의 성공률은 아니다. "
            f"n={point.get('n_bits', str(config.MANEUVER_BITS))}, "
            f"K={point.get('hamming_k', str(config.MANEUVER_HAMMING_K))}. "
            "window를 주기적으로 갱신하는 조건이며 관측·재현 비용과 실제 운용 시간은 미측정.",
            fleet_size=fleet_size,
        ))
    rows.extend([
        AttackCost("S9", "가짜 질의기", "키 없는 질의 태그 추측", 2.0 ** -32,
                   "시도당 균등 32비트 iq_tag 추측 확률 2^-32; S9a의 잘못된 태그는 무응답.",
                   "공개 nonce·질의기 ID·epoch와 질의 송신 역량", None,
                   "현재 epoch만 허용; 시도 빈도 미측정",
                   "iff/crypto.py:iq_key,challenge_tag; iff/protocol.py:Responder.respond",
                   "질의 +4바이트. 포획 드론에서 iq_key 유출 시 해당 epoch 동안 가짜 질의 가능. "
                   "공유 iq_key 폐기·교체와 다음 epoch 키 배포 제외로 제한; unit ID 폐기만으로는 부족."),
        AttackCost("S9", "질의 재방송", "같은 응답기가 같은 epoch에서 처리한 nonce", 0.0,
                   "S9b: 인증된 질의도 이미 본 nonce면 무응답.",
                   "진짜 질의를 녹화하고 재송신할 역량", 0.0,
                   "소비된 nonce는 해당 epoch 동안 재사용 불가",
                   "iff/scenarios.py:s9_rogue_interrogator; iff/protocol.py:Responder.seen",
                   "응답기가 보지 못한 질의의 최초 전달은 재방송 캐시로 구분할 수 없음. "
                   "재시작 시에도 해당 epoch의 nonce 기록을 보존해야 함."),
    ])
    return rows


def probability_text(row: AttackCost) -> str:
    return "미측정" if row.success_probability is None else f"{row.success_probability:.8g}"


def cost_csv(rows: Sequence[AttackCost]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=[field.name for field in fields(AttackCost)])
    writer.writeheader()
    writer.writerows(asdict(row) for row in rows)
    return stream.getvalue()


def cost_markdown(rows: Sequence[AttackCost]) -> str:
    lines = ["# 공격자 비용 모델", "", "확률은 명시된 조건 아래의 값이다. 실측 운용 비용은 미측정이다.",
             "숫자 칸이 빈 항목은 유도할 근거가 없으며 0을 뜻하지 않는다.", "",
             "| 공격 | 조건 | 성공 확률 | 필요 역량 | 유효 시간 |",
             "|---|---|---:|---|---|"]
    for row in rows:
        lines.append(f"| {row.scenario} {row.attack} | {row.condition} | {probability_text(row)} | "
                     f"{row.capability} | {row.valid_window} |")
    for scenario in ("S2", "S3", "S4", "S5", "S6", "S9"):
        first = next(row for row in rows if row.scenario == scenario)
        lines.extend(["", f"## {scenario} 유도와 출처", "", first.probability_note,
                      "", first.valid_window, "", first.notes, "", f"출처: {first.source}"])
    return "\n".join(lines) + "\n"


def write_attacker_cost(out_dir: Path) -> list[AttackCost]:
    """Export the same derived rows as CSV and explanatory Markdown."""
    rows = build_costs(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "attacker_cost.csv").write_text(cost_csv(rows), encoding="utf-8")
    (out_dir / "attacker_cost.md").write_text(cost_markdown(rows), encoding="utf-8")
    return rows
