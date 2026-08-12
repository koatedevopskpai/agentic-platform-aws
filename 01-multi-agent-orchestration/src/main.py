import argparse
import json
from .orchestrator import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description="AgenticOps - Brand Intelligence Multi-Agent Orchestrator"
    )
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="Natural language query for brand analysis",
    )
    parser.add_argument(
        "--client-id",
        default="demo-client",
        help="Client identifier for session tracking",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed agent outputs",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"AgenticOps Brand Intelligence Agent")
    print(f"Session: demo-client")
    print(f"{'='*60}")
    print(f"\nQuery: {args.query}")
    print(f"\nStarting analysis...\n")

    result = run_analysis(query=args.query, client_id=args.client_id)

    print(f"\n{'='*60}")
    print(f"BRAND ANALYSIS RESULT")
    print(f"{'='*60}\n")

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(result.get("final_output", "No output generated"))

    if args.verbose:
        print(f"\n{'='*60}")
        print(f"AGENT TRACE")
        print(f"{'='*60}")
        print(f"Parsed query: {json.dumps(result.get('parsed_query'), indent=2)}")
        print(f"\nPlan reasoning: {result.get('plan_reasoning')}")
        print(f"\nWorker outputs: {len(result.get('worker_outputs', []))}")
        for i, w in enumerate(result.get("worker_outputs", [])):
            print(f"  {i+1}. {w.get('worker_type')}: {w.get('status')} (confidence: {w.get('confidence_score')})")
        print(f"\nCritique: {json.dumps(result.get('critique'), indent=2)}")
        print(f"\nErrors: {result.get('errors', [])}")


if __name__ == "__main__":
    main()
