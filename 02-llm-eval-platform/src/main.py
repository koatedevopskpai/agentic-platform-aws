import argparse
import asyncio
import json
from .eval_runner import EvalRunner
from .dataset_generator import DatasetGenerator
from .guardrails import GuardrailEngine
from .dashboard import EvalDashboard
from .prompt_registry import PromptRegistry
from .regression_suite import RegressionSuite


async def run_eval(args):
    runner = EvalRunner()
    registry = PromptRegistry()

    prompt = registry.get_prompt(
        args.prompt, overlay=args.overlay
    )

    dataset = DatasetGenerator.load_curated(args.dataset)

    if not dataset:
        print(f"No dataset items found in {args.dataset}")
        return

    print(f"Running {len(dataset)} evals with prompt '{args.prompt}' on model '{args.model or prompt['model']}'...")

    results = []
    for i, item in enumerate(dataset):
        result = await runner.run_eval(
            dataset_item=item,
            prompt_template=prompt["system"],
            model=args.model or prompt["model"],
            dataset_version=args.dataset.split("/")[-2] if "/" in args.dataset else args.dataset,
        )
        results.append(result)
        if args.verbose:
            print(f"  [{i+1}/{len(dataset)}] {result.dataset_item_id}: score={result.judge_score:.3f} cost=${result.cost_usd:.6f} latency={result.latency_ms:.0f}ms")

    if args.regression_check:
        suite = RegressionSuite(baseline_path=args.regression_baseline)
        reg_results = suite.run([r.model_dump() for r in results])
        summary = suite.summary()
        print(f"\nRegression Check: {summary['passed']}/{summary['total']} passed "
              f"({summary['pass_rate']}%)")
        if summary["regressions"] > 0:
            print(f"⚠️  {summary['regressions']} regressions detected")
            for r in reg_results:
                if r.regression_detected:
                    print(f"  - {r.test_name}: {r.details.get('regressions', [])}")

    avg_score = sum(r.judge_score for r in results) / len(results)
    total_cost = sum(r.cost_usd for r in results)
    avg_latency = sum(r.latency_ms for r in results) / len(results)

    print(f"\nResults: {len(results)} evals")
    print(f"  Avg score:  {avg_score:.3f}")
    print(f"  Total cost: ${total_cost:.4f}")
    print(f"  Avg latency: {avg_latency:.0f}ms")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                [r.model_dump() for r in results],
                f,
                indent=2,
                default=str,
            )
        print(f"Results saved to {args.output}")

    if args.update_baseline:
        suite = RegressionSuite()
        suite.save_baseline([r.model_dump() for r in results], args.update_baseline)
        print(f"Baseline saved to {args.update_baseline}")


def generate_dataset(args):
    items = DatasetGenerator.generate_full_dataset(
        synthetic_count=args.count,
        curated_path=args.curated or "",
        output_path=args.output,
    )
    print(f"Generated {len(items)} dataset items -> {args.output}")


def run_guard(args):
    engine = GuardrailEngine()
    text = args.text
    if not text:
        text = input("Enter text to scan: ")

    result = engine.scan_input(text)
    print(json.dumps(result, indent=2))

    should_block, reasons = engine.should_block(result, threshold=args.threshold)
    if should_block:
        print(f"\n  BLOCKED: {', '.join(reasons)}")
    else:
        print("\n  PASSED all guardrails")


def run_dashboard(args):
    dashboard = EvalDashboard()
    if args.load:
        with open(args.load) as f:
            data = json.load(f)
            for item in data:
                dashboard.add_result(item)
    dashboard.render(hours=args.hours)


def list_prompts(args):
    registry = PromptRegistry()
    prompts = registry.list_prompts()
    if not prompts:
        print("No prompts found in registry")
        return
    print(f"\nPrompt Registry ({len(prompts)} prompts):")
    print(f"{'─'*60}")
    for p in prompts:
        overlays = f" [{', '.join(p['overlays'])}]" if p["overlays"] else ""
        print(f"  {p['name']:30s} v{p['version']:8s} {p['author']:20s}{overlays}")


def main():
    parser = argparse.ArgumentParser(
        description="AgenticOps LLM Eval Platform"
    )
    subparsers = parser.add_subparsers(dest="command")

    eval_parser = subparsers.add_parser(
        "eval", help="Run evaluation suite against a dataset"
    )
    eval_parser.add_argument(
        "--dataset", default="prompts/golden_v1/dataset.yaml"
    )
    eval_parser.add_argument("--prompt", default="brand_sentiment_v2")
    eval_parser.add_argument("--model", default=None)
    eval_parser.add_argument("--overlay", default=None)
    eval_parser.add_argument("--output", default=None)
    eval_parser.add_argument("--verbose", "-v", action="store_true")
    eval_parser.add_argument("--regression-check", action="store_true")
    eval_parser.add_argument("--regression-baseline", default=None)
    eval_parser.add_argument("--update-baseline", default=None)

    gen_parser = subparsers.add_parser(
        "generate-dataset", help="Generate synthetic eval dataset"
    )
    gen_parser.add_argument(
        "--count", type=int, default=60, help="Number of synthetic items"
    )
    gen_parser.add_argument("--curated", default=None)
    gen_parser.add_argument(
        "--output", default="prompts/golden_v1/dataset.yaml"
    )

    guard_parser = subparsers.add_parser(
        "guard", help="Scan text with guardrails"
    )
    guard_parser.add_argument("--text", default=None)
    guard_parser.add_argument("--threshold", type=float, default=0.7)

    dash_parser = subparsers.add_parser(
        "dashboard", help="Show eval dashboard"
    )
    dash_parser.add_argument("--hours", type=int, default=24)
    dash_parser.add_argument("--load", default=None)

    list_parser = subparsers.add_parser(
        "list-prompts", help="List available prompts"
    )

    args = parser.parse_args()

    if args.command == "eval":
        asyncio.run(run_eval(args))
    elif args.command == "generate-dataset":
        generate_dataset(args)
    elif args.command == "guard":
        run_guard(args)
    elif args.command == "dashboard":
        run_dashboard(args)
    elif args.command == "list-prompts":
        list_prompts(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
