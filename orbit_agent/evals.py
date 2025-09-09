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
    persona: str | None = None
    stage: str | None = None
    rubric: List[str] | None = None


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
    overlap_ratio: float | None = None


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
                persona=item.get("persona"),
                stage=item.get("stage"),
                rubric=item.get("rubric"),
            )
        )
    return scenarios


def _split_lines(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [ln.strip() for ln in value.split("\n") if ln.strip()]
    return []


def _format_eval(
    advice: str, actions_lines: List[str], risks_lines: List[str]
) -> Tuple[bool, int, int]:
    # Clean bullet prefixes
    a_clean = [
        ln.lstrip("123456789. -•*").strip() for ln in actions_lines if ln.strip()
    ]
    r_clean = [ln.lstrip("123456789. -•*").strip() for ln in risks_lines if ln.strip()]
    actions_count = len(a_clean)
    risks_count = len(r_clean)
    # Format rules: 3-5 actions, exactly 3 risks, advice non-empty
    format_ok = (
        (3 <= actions_count <= 5)
        and (risks_count == 3)
        and bool(advice and advice.strip())
    )
    return format_ok, actions_count, risks_count


def _ngram_set(text: str, n: int = 3) -> set[str]:
    tokens = [t for t in text.lower().split() if t]
    return set(
        [" ".join(tokens[i : i + n]) for i in range(0, max(0, len(tokens) - n + 1))]
    )


def _overlap_ratio(a: str, b: str, n: int = 3) -> float:
    if not a or not b:
        return 0.0
    A = _ngram_set(a, n)
    B = _ngram_set(b, n)
    if not A or not B:
        return 0.0
    inter = len(A & B)
    union = len(A | B)
    return inter / union


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
        format_ok, a_count, r_count = _format_eval(
            res.advice or "", actions_lines, risks_lines
        )

        overlap = _overlap_ratio(res.advice or "", playbook) if playbook else 0.0

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
                overlap_ratio=overlap,
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
    avg_overlap = sum((r.overlap_ratio or 0.0) for r in records) / n
    return {
        "count": n,
        "format_ok_rate": fmt_ok / n,
        "avg_critic_score": avg_score,
        "avg_latency_ms": avg_latency,
        "avg_playbook_overlap": avg_overlap,
    }


# Optional: experimental grading with an explicit rubric using LLM
try:
    import dspy

    class RubricGrade(dspy.Signature):
        """You are grading a startup advice response against a rubric.
        Return a JSON object strictly with fields: overall (0-10), feedback, criteria.
        'criteria' maps each rubric item to pass/fail and a brief note.
        """

        persona: str = dspy.InputField()
        stage: str = dspy.InputField()
        prompt: str = dspy.InputField()
        rubric: str = dspy.InputField(desc="Bulleted list of rubric items")
        advice: str = dspy.InputField()

        grade_json: str = dspy.OutputField()

    _rubric_grader = dspy.Predict(RubricGrade)

    def grade_with_rubric(
        records: List[EvalRecord], scenarios: List[Scenario]
    ) -> List[Dict[str, Any]]:
        id_to_scn = {s.id: s for s in scenarios}
        graded: List[Dict[str, Any]] = []
        for r in records:
            sc = id_to_scn.get(r.scenario_id)
            if not sc or not sc.rubric:
                continue
            rubric_text = "\n".join(f"- {item}" for item in sc.rubric)
            out = _rubric_grader(
                persona=sc.persona or "",
                stage=sc.stage or "",
                prompt=sc.prompt,
                rubric=rubric_text,
                advice=r.advice,
            )
            graded.append(
                {
                    "scenario_id": r.scenario_id,
                    "grade_json": out.grade_json,
                }
            )
        return graded

except Exception:  # pragma: no cover

    def grade_with_rubric(records: List[EvalRecord], scenarios: List[Scenario]):
        return []


def save_eval_results(records: List[EvalRecord], out_path: str | Path) -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        for r in records:
            f.write(json.dumps(asdict(r)) + "\n")
