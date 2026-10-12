from app.evaluation.benchmark import IncidentTwinBenchmark
from app.evaluation.scenarios import create_initial_scenarios


def main() -> None:
    benchmark = IncidentTwinBenchmark()
    results, metrics = benchmark.run_all(create_initial_scenarios())

    for result in results:
        print(
            f"{result.scenario_name}: "
            f"RCA={result.root_cause_correct}, "
            f"CANDIDATE_COVERAGE={result.recovery_action_covered}, "
            f"SELECTED_ACTION_CORRECT={result.selected_action_correct}, "
            f"SAFETY={result.safety_approved}, "
            f"BLOCKED={result.safety_blocked_candidates}, "
            f"EXECUTION={result.execution_successful}, "
            f"VERIFY={result.verification_successful}, "
            f"REGRESSION={result.regression_free}, "
            f"RECOVERY={result.recovery_successful}, "
            f"RETRY={result.retry_requested}, "
            f"FAILURE={result.failure_stage}"
        )

    print("\n===== FINAL BENCHMARK SUMMARY =====")
    print(f"Incidents evaluated:        {metrics.total_incidents}")
    print(f"Root-cause accuracy:        {metrics.root_cause_accuracy:.0%}")
    print(f"Selected-action accuracy:   {metrics.recovery_action_accuracy:.0%}")
    print(f"Candidate action coverage:  {metrics.candidate_action_coverage:.0%}")
    print(f"Safety approval rate:       {metrics.safety_approval_rate:.0%}")
    print(f"Candidate safety block rate: {metrics.safety_candidate_block_rate:.1%}")
    print(f"Safety candidates evaluated: {metrics.safety_candidates_evaluated}")
    print(f"Safety candidates blocked:   {metrics.safety_blocked_candidates}")
    print(f"Execution success rate:     {metrics.execution_success_rate:.0%}")
    print(f"Verification success rate:  {metrics.verification_success_rate:.0%}")
    print(f"Regression-free rate:       {metrics.regression_free_rate:.0%}")
    print(f"Overall recovery success:   {metrics.recovery_success_rate:.0%}")

    retry_requests = sum(result.retry_requested for result in results)
    print(f"Retry requests:             {retry_requests}/{metrics.total_incidents}")


if __name__ == "__main__":
    main()
