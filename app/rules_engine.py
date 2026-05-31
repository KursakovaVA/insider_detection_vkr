from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml
from datetime import datetime, timezone, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Rule:
    id: str
    description: str
    weight: float
    action: set[str]
    object_contains_any: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuleSet:
    rules: tuple[Rule, ...]
    alert_threshold: float
    severity_medium: float
    severity_high: float
    severity_critical: float

    tz: str
    work_start: str
    work_end: str
    work_weekdays: tuple[int, ...]
    off_hours_multiplier: float
    off_hours_actions: tuple[str, ...]

    decay_tau_seconds: float
    alert_cooldown_minutes: float
    default_weight: float


def load_rules(path: str = "rules/rules.yaml") -> RuleSet:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    thresholds = data.get("thresholds", {})
    sev = thresholds.get("severity", {})

    ctx = (data or {}).get("context") or {}
    wh = ctx.get("work_hours") or {}
    oh = ctx.get("off_hours") or {}

    decay = (data or {}).get("decay") or {}
    tau_seconds = float(decay.get("tau_seconds") or 3600.0)

    alert_cfg = (data or {}).get("alert") or {}
    cooldown_minutes = float(
        alert_cfg.get("cooldown_minutes")
        if alert_cfg.get("cooldown_minutes") is not None
        else 10.0
    )

    default_weight = float(
        data.get("default_weight") if data.get("default_weight") is not None else 0.5
    )

    tz = ctx.get("timezone") or "Europe/Moscow"
    work_start = wh.get("start") or "09:00"
    work_end = wh.get("end") or "19:00"
    weekdays = tuple(wh.get("weekdays") or [1, 2, 3, 4, 5])

    off_mult = float(oh.get("multiplier") or 1.0)
    off_actions = tuple(oh.get("actions") or ["login_failed", "login_success"])

    rules_raw: list[dict[str, Any]] = data.get("rules", []) or []
    rules: list[Rule] = []

    for r in rules_raw:
        match = r.get("match", {}) or {}
        actions = set(match.get("action", []) or [])
        obj_any = tuple(match.get("object_contains_any", []) or [])
        rules.append(
            Rule(
                id=str(r["id"]),
                description=str(r.get("description", "")),
                weight=float(r.get("weight", 0.0)),
                action=actions,
                object_contains_any=obj_any,
            )
        )

    return RuleSet(
        rules=tuple(rules),
        alert_threshold=float(thresholds.get("alert", 10.0)),
        severity_medium=float(sev.get("medium", 6.0)),
        severity_high=float(sev.get("high", 12.0)),
        severity_critical=float(sev.get("critical", 20.0)),
        tz=tz,
        work_start=work_start,
        work_end=work_end,
        work_weekdays=weekdays,
        off_hours_multiplier=off_mult,
        off_hours_actions=off_actions,
        decay_tau_seconds=tau_seconds,
        alert_cooldown_minutes=cooldown_minutes,
        default_weight=default_weight,
    )


def match_rule(event_action: str, event_object: str | None, rule: Rule) -> bool:
    if rule.action and event_action not in rule.action:
        return False

    if rule.object_contains_any:
        obj = (event_object or "").lower()
        if not any(substr.lower() in obj for substr in rule.object_contains_any):
            return False

    return True


def _context_multiplier(
    event_action: str, ts: datetime | None, ruleset: RuleSet
) -> tuple[float, str | None]:
    if (
        ts is not None
        and ruleset.off_hours_multiplier > 1.0
        and event_action in set(ruleset.off_hours_actions)
        and is_off_hours(ts, ruleset)
    ):
        return (
            ruleset.off_hours_multiplier,
            f"off-hours x{ruleset.off_hours_multiplier:g}",
        )
    return 1.0, None


def evaluate_rules(
    event_action: str,
    event_object: str | None,
    ruleset: RuleSet,
    ts: datetime | None = None,
) -> tuple[float, list[dict[str, Any]]]:
    hits: list[dict[str, Any]] = []
    delta = 0.0

    m_i, context_reason = _context_multiplier(event_action, ts, ruleset)

    for rule in ruleset.rules:
        if match_rule(event_action, event_object, rule):
            contribution = m_i * rule.weight
            delta += contribution
            hit: dict[str, Any] = {
                "rule_id": rule.id,
                "weight": rule.weight,
                "multiplier": m_i,
                "contribution": contribution,
                "description": rule.description,
            }
            if context_reason is not None:
                hit["context"] = context_reason
            hits.append(hit)

    if delta == 0.0:
        contribution = m_i * ruleset.default_weight
        delta = contribution
        hit = {
            "rule_id": "default",
            "weight": ruleset.default_weight,
            "multiplier": m_i,
            "contribution": contribution,
            "description": "default weight (no rule matched)",
        }
        if context_reason is not None:
            hit["context"] = context_reason
        hits.append(hit)

    return delta, hits


def severity_from_risk(risk: float, ruleset: RuleSet) -> str:
    if risk >= ruleset.severity_critical:
        return "critical"
    if risk >= ruleset.severity_high:
        return "high"
    if risk >= ruleset.severity_medium:
        return "medium"
    return "low"


def is_off_hours(ts: datetime, ruleset: RuleSet) -> bool:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)

    local = ts.astimezone(ZoneInfo(ruleset.tz))
    wd = local.isoweekday()

    if wd not in set(ruleset.work_weekdays):
        return True

    start_t = time.fromisoformat(ruleset.work_start)
    end_t = time.fromisoformat(ruleset.work_end)
    t = local.time()

    if start_t <= end_t:
        return not (start_t <= t < end_t)

    return not (t >= start_t or t < end_t)
