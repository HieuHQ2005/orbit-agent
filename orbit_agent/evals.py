from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Tuple

import yaml

from .advisor import HighOrbitAdvisor
from .config import configure_lm


@dataclass
class Scenario:
    id: str
    prompt: str
    playbook_path: str | None = None


@dataclass
class EvalRecord:
    scenario_id: str
    prompt: str
    timestamp: float
    latency_ms: float
    advice: str
    actions: List[str]
    metric_to_watch: str
    risks: List[str]
    critic_score: int
    critic_feedback: str
    format_ok: bool
    actions_count: int
    risks_count: int


def load_scenarios(path: str | Path) -> List[Scenario]:
    p = Path(path)
    data = yaml.safe_load(p.read_text())
    scenarios: List[Scenario] = []
    for i, item in enumerate(data.get("scenarios", [])):
        scenarios.append(
            Scenario(
                id=item.get("id") or f"s{i+1}",
                prompt=item["prompt"],
                playbook_path=item.get("playbook"),
            )
        )
    return scenarios


def _split_lines(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [ln.strip() for ln in value.split("\n") if ln.strip()]
    return []


def _format_eval(advice: str, actions_lines: List[str], risks_lines: List[str]) -> Tuple[bool, int, int]:
    # Clean bullet prefixes
    a_clean = [ln.lstrip("123456789. -•*").strip() for ln in actions_lines if ln.strip()]
    r_clean = [ln.lstrip("123456789. -•*").strip() for ln in risks_lines if ln.strip()]
    actions_count = len(a_clean)
    risks_count = len(r_clean)
    # Format rules: 3-5 actions, exactly 3 risks, advice non-empty
    format_ok = (3 <= actions_count <= 5) and (risks_count == 3) and bool(advice and advice.strip())
    return format_ok, actions_count, risks_count


def run_evals(scenarios: List[Scenario]) -> List[EvalRecord]:
    # Ensure LM is configured for online evals
    configure_lm()
    advisor = HighOrbitAdvisor()
    records: List[EvalRecord] = []

    for sc in scenarios:
        playbook = ""
        if sc.playbook_path and Path(sc.playbook_path).exists():
            playbook = Path(sc.playbook_path).read_text()

        history = [{"role": "user", "content": sc.prompt}]
        start = time.time()
        res = advisor(history=history, playbook=playbook)
        latency_ms = (time.time() - start) * 1000.0

        actions_lines = _split_lines(res.actions_48h)
        risks_lines = _split_lines(res.risks)
        format_ok, a_count, r_count = _format_eval(res.advice or "", actions_lines, risks_lines)

        records.append(
            EvalRecord(
                scenario_id=sc.id,
                prompt=sc.prompt,
                timestamp=time.time(),
                latency_ms=latency_ms,
                advice=res.advice or "",
                actions=[ln.lstrip("123456789. -•*").strip() for ln in actions_lines],
                metric_to_watch=res.metric_to_watch or "",
                risks=[ln.lstrip("123456789. -•*").strip() for ln in risks_lines],
                critic_score=int(getattr(res, "score", 0) or 0),
                critic_feedback=str(getattr(res, "critique", "") or ""),
                format_ok=format_ok,
                actions_count=a_count,
                risks_count=r_count,
            )
        )

    return records


def summarize_results(records: List[EvalRecord]) -> Dict[str, Any]:
    n = len(records)
    if n == 0:
        return {"count": 0}
    fmt_ok = sum(1 for r in records if r.format_ok)
    avg_score = sum(r.critic_score for r in records) / n
    avg_latency = sum(r.latency_ms for r in records) / n
    return {
        "count": n,
        "format_ok_rate": fmt_ok / n,
        "avg_critic_score": avg_score,
        "avg_latency_ms": avg_latency,
    }


def save_eval_results(records: List[EvalRecord], out_path: str | Path) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        for r in records:
            f.write(json.dumps(asdict(r)) + "\n")

