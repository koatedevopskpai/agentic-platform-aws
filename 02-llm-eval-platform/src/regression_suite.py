import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path


class RegressionResult:
    def __init__(
        self,
        test_name: str,
        passed: bool,
        score: float,
        baseline_score: Optional[float] = None,
        regression_detected: bool = False,
        details: Optional[dict] = None,
    ):
        self.test_name = test_name
        self.passed = passed
        self.score = score
        self.baseline_score = baseline_score
        self.regression_detected = regression_detected
        self.details = details or {}

    def dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "score": self.score,
            "baseline_score": self.baseline_score,
            "regression_detected": self.regression_detected,
            "details": self.details,
        }


class RegressionThresholds:
    def __init__(
        self,
        score_drop_threshold: float = 0.1,
        min_acceptable_score: float = 0.7,
        latency_increase_threshold_pct: float = 50.0,
    ):
        self.score_drop_threshold = score_drop_threshold
        self.min_acceptable_score = min_acceptable_score
        self.latency_increase_threshold_pct = latency_increase_threshold_pct


class RegressionSuite:
    def __init__(
        self,
        thresholds: Optional[RegressionThresholds] = None,
        baseline_path: Optional[str] = None,
    ):
        self.thresholds = thresholds or RegressionThresholds()
        self.baseline_path = baseline_path
        self.results: List[RegressionResult] = []

    def load_baseline(self) -> dict:
        if not self.baseline_path:
            return {}
        path = Path(self.baseline_path)
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def save_baseline(self, results: List[dict], path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        baseline = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
        }
        with open(path, "w") as f:
            json.dump(baseline, f, indent=2, default=str)

    def check_regression(
        self,
        test_name: str,
        current_score: float,
        current_latency_ms: float,
        baseline: dict,
    ) -> RegressionResult:
        baseline_result = baseline.get("results", {}).get(test_name)
        if not baseline_result:
            return RegressionResult(
                test_name=test_name,
                passed=True,
                score=current_score,
                baseline_score=None,
                regression_detected=False,
                details={"message": "No baseline available — new test"},
            )

        baseline_score = baseline_result.get("score", 0.0)
        baseline_latency = baseline_result.get("latency_ms", 0)

        regressions = []

        score_drop = baseline_score - current_score
        if score_drop > self.thresholds.score_drop_threshold:
            regressions.append(
                f"Score dropped by {score_drop:.3f} "
                f"(baseline: {baseline_score:.3f}, current: {current_score:.3f})"
            )

        if current_score < self.thresholds.min_acceptable_score:
            regressions.append(
                f"Score {current_score:.3f} below minimum {self.thresholds.min_acceptable_score}"
            )

        if baseline_latency > 0:
            latency_increase = (
                (current_latency_ms - baseline_latency) / baseline_latency * 100
            )
            if latency_increase > self.thresholds.latency_increase_threshold_pct:
                regressions.append(
                    f"Latency increased by {latency_increase:.1f}% "
                    f"(baseline: {baseline_latency:.0f}ms, current: {current_latency_ms:.0f}ms)"
                )

        return RegressionResult(
            test_name=test_name,
            passed=len(regressions) == 0,
            score=current_score,
            baseline_score=baseline_score,
            regression_detected=len(regressions) > 0,
            details={"regressions": regressions} if regressions else {"message": "Passed"},
        )

    def run(
        self,
        eval_results: List[dict],
        baseline: Optional[dict] = None,
    ) -> List[RegressionResult]:
        if baseline is None:
            baseline = self.load_baseline()

        results = []
        for eval_result in eval_results:
            result = self.check_regression(
                test_name=eval_result.get("dataset_item_id", "unknown"),
                current_score=eval_result.get("judge_score", 0.0),
                current_latency_ms=eval_result.get("latency_ms", 0),
                baseline=baseline,
            )
            results.append(result)
            self.results.append(result)

        return results

    def summary(self) -> dict:
        if not self.results:
            return {"passed": 0, "failed": 0, "regressions": 0, "total": 0}

        return {
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "regressions": sum(1 for r in self.results if r.regression_detected),
            "total": len(self.results),
            "pass_rate": round(
                sum(1 for r in self.results if r.passed) / len(self.results) * 100, 1
            ),
        }
