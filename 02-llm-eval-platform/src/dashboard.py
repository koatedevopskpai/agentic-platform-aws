import json
from datetime import datetime, timedelta
from typing import Optional


class EvalDashboard:
    def __init__(self, results_store: Optional[list] = None):
        self.results = results_store or []

    def add_result(self, result: dict):
        self.results.append(result)

    def _filter(
        self, hours: int = 24, model: Optional[str] = None
    ) -> list:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        filtered = []
        for r in self.results:
            try:
                ts = datetime.fromisoformat(r["timestamp"])
                if ts > cutoff:
                    if model is None or r["model"] == model:
                        filtered.append(r)
            except (KeyError, ValueError):
                continue
        return filtered

    def cost_summary(self, hours: int = 24) -> dict:
        recent = self._filter(hours)
        total_cost = sum(r.get("cost_usd", 0) for r in recent)
        by_model = {}
        for r in recent:
            m = r.get("model", "unknown")
            by_model[m] = by_model.get(m, 0) + r.get("cost_usd", 0)

        return {
            "period_hours": hours,
            "total_cost": round(total_cost, 4),
            "by_model": {
                k: round(v, 4)
                for k, v in sorted(by_model.items(), key=lambda x: -x[1])
            },
            "total_evals": len(recent),
        }

    def latency_summary(self, hours: int = 24) -> dict:
        recent = self._filter(hours)
        if not recent:
            return {}

        latencies = [r.get("latency_ms", 0) for r in recent]
        sorted_lat = sorted(latencies)
        n = len(sorted_lat)

        return {
            "p50": sorted_lat[n // 2],
            "p95": sorted_lat[int(n * 0.95)],
            "p99": sorted_lat[int(n * 0.99)],
            "avg": round(sum(latencies) / n, 1),
            "min": min(latencies),
            "max": max(latencies),
        }

    def quality_summary(self, hours: int = 24) -> dict:
        recent = self._filter(hours)
        if not recent:
            return {}

        scores = [r.get("judge_score", 0) for r in recent]
        by_model = {}
        for r in recent:
            m = r.get("model", "unknown")
            if m not in by_model:
                by_model[m] = []
            by_model[m].append(r.get("judge_score", 0))

        return {
            "overall_avg": round(sum(scores) / len(scores), 3),
            "by_model": {
                k: round(sum(v) / len(v), 3)
                for k, v in sorted(by_model.items())
            },
            "min_score": min(scores),
            "max_score": max(scores),
            "samples": len(scores),
        }

    def token_summary(self, hours: int = 24) -> dict:
        recent = self._filter(hours)
        if not recent:
            return {}

        total_tokens = sum(
            r.get("token_usage", {}).get("total", 0) for r in recent
        )
        by_model = {}
        for r in recent:
            m = r.get("model", "unknown")
            tokens = r.get("token_usage", {}).get("total", 0)
            by_model[m] = by_model.get(m, 0) + tokens

        return {
            "total_tokens": total_tokens,
            "by_model": dict(sorted(by_model.items(), key=lambda x: -x[1])),
        }

    def render(self, hours: int = 24):
        cost = self.cost_summary(hours)
        latency = self.latency_summary(hours)
        quality = self.quality_summary(hours)
        tokens = self.token_summary(hours)

        period = f"last {hours}h" if hours < 168 else f"last {hours//24}d"

        print(f"\n{'='*60}")
        print(f"  AgenticOps Eval Dashboard ({period})")
        print(f"{'='*60}")

        print(f"\n  COST SUMMARY")
        print(f"  {'─'*56}")
        print(f"    Total cost:     ${cost.get('total_cost', 0):.4f}")
        print(f"    Total evals:    {cost.get('total_evals', 0)}")
        print(f"    By model:")
        for model, c in cost.get("by_model", {}).items():
            print(f"      {model:30s} ${c:.4f}")

        print(f"\n  TOKEN USAGE")
        print(f"  {'─'*56}")
        print(f"    Total tokens:   {tokens.get('total_tokens', 0):,}")
        for model, t in tokens.get("by_model", {}).items():
            print(f"      {model:30s} {t:,}")

        print(f"\n  LATENCY (ms)")
        print(f"  {'─'*56}")
        print(f"    p50:  {latency.get('p50', 0):>8.0f}ms")
        print(f"    p95:  {latency.get('p95', 0):>8.0f}ms")
        print(f"    p99:  {latency.get('p99', 0):>8.0f}ms")
        print(f"    avg:  {latency.get('avg', 0):>8.1f}ms")
        print(f"    min:  {latency.get('min', 0):>8.0f}ms")
        print(f"    max:  {latency.get('max', 0):>8.0f}ms")

        print(f"\n  QUALITY SCORES")
        print(f"  {'─'*56}")
        print(f"    Overall avg:    {quality.get('overall_avg', 0):.3f}")
        print(f"    Range:          {quality.get('min_score', 0):.3f} - {quality.get('max_score', 0):.3f}")
        print(f"    By model:")
        for model, s in quality.get("by_model", {}).items():
            print(f"      {model:30s} {s:.3f}")
        print()
