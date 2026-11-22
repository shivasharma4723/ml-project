"""
GFM Research Evaluation Suite
Compares GFM Agent vs Standard ReAct Agent across Loop Prevention, Token Efficiency, and Task Success Rate
"""


"""
GFM Research Evaluation Suite
Compares GFM Agent vs Standard ReAct Agent across Loop Prevention,
Token Efficiency, Task Success Rate (Pass@K), and Per-Category Performance.
"""

import json
from typing import List, Dict, Any
from agents.gfm_agent import GFMAgent
from benchmarks.dataset_generator import generate_benchmark_dataset
from sandbox.executor import SandboxExecutor


class ResearchBenchmarkRunner:
    """Runs research-focused benchmarks comparing GFM vs Standard ReAct."""

    def __init__(
        self,
        max_attempts: int = 5,
        custom_tasks: List[Dict] = None,
        default_task_count: int = 20,
        model_name: str = "qwen2.5-coder:3b",
    ):
        self.max_attempts = max_attempts
        self.model_name = model_name
        self.executor = SandboxExecutor(timeout_seconds=2)
        self.tasks = custom_tasks if custom_tasks else generate_benchmark_dataset(default_task_count)

    def simulate_standard_react(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run Standard ReAct baseline (raw error tracebacks, no cycle breaker)."""
        print(f"  [ReAct] {task['id']}...")
        agent = GFMAgent(max_attempts=self.max_attempts, model_name=self.model_name, timeout_seconds=2)
        res = agent.solve_task(task["description"], task["initial_code"], use_gfm=False)
        return {
            "task_id": task["id"],
            "mutation_category": task.get("mutation_category", "general"),
            "agent_type": "standard_react",
            "solved": res["solved"],
            "attempts": res["attempts"],
            "total_loops": res["total_loops"],
            "total_tokens_used": res["total_tokens_used"],
            "error_history": res["error_history"],
        }

    def simulate_gfm_agent(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Run GFM-enhanced agent with AST cycle breaking and pruned context."""
        print(f"  [GFM]   {task['id']}...")
        agent = GFMAgent(
            max_attempts=self.max_attempts,
            loop_threshold=2,
            model_name=self.model_name,
            timeout_seconds=2,
        )
        res = agent.solve_task(task["description"], task["initial_code"], use_gfm=True)
        return {
            "task_id": task["id"],
            "mutation_category": task.get("mutation_category", "general"),
            "agent_type": "gfm_agent",
            "solved": res["solved"],
            "attempts": res["attempts"],
            "total_loops": res["total_loops"],
            "cycles_prevented": res["cycles_prevented"],
            "total_tokens_used": res["total_tokens_used"],
            "error_history": res["error_history"],
        }

    def run_research_benchmark(self) -> Dict[str, Any]:
        print(f"Starting GFM Research Evaluation Suite ({len(self.tasks)} tasks)...\n")

        results = {
            "standard_react": [],
            "gfm_agent": [],
            "research_metrics": {},
        }

        for task in self.tasks:
            print(f"\nTask: {task['description']} ({task['difficulty']})")
            results["standard_react"].append(self.simulate_standard_react(task))
            results["gfm_agent"].append(self.simulate_gfm_agent(task))

        results["research_metrics"] = self._calculate_research_metrics(results)
        return results

    def _calculate_research_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        react_results = results["standard_react"]
        gfm_results = results["gfm_agent"]
        total_tasks = max(len(react_results), 1)

        react_loops = sum(r["total_loops"] for r in react_results)
        gfm_loops = sum(r["total_loops"] for r in gfm_results)
        gfm_cycles_prevented = sum(r["cycles_prevented"] for r in gfm_results)
        loop_prevention_rate = (gfm_cycles_prevented / max(react_loops, 1)) * 100

        react_tokens = sum(r["total_tokens_used"] for r in react_results)
        gfm_tokens = sum(r["total_tokens_used"] for r in gfm_results)
        token_savings_pct = ((react_tokens - gfm_tokens) / max(react_tokens, 1)) * 100

        react_solved = sum(1 for r in react_results if r["solved"])
        gfm_solved = sum(1 for r in gfm_results if r["solved"])
        react_success_rate = (react_solved / total_tasks) * 100
        gfm_success_rate = (gfm_solved / total_tasks) * 100

        category_breakdown: Dict[str, Dict[str, Any]] = {}
        for r_res, g_res in zip(react_results, gfm_results):
            cat = g_res.get("mutation_category", "general")
            entry = category_breakdown.setdefault(
                cat,
                {
                    "tasks": 0,
                    "react_solved": 0,
                    "gfm_solved": 0,
                    "cycles_prevented": 0,
                    "react_tokens": 0.0,
                    "gfm_tokens": 0.0,
                },
            )
            entry["tasks"] += 1
            entry["react_solved"] += int(r_res["solved"])
            entry["gfm_solved"] += int(g_res["solved"])
            entry["cycles_prevented"] += g_res["cycles_prevented"]
            entry["react_tokens"] += r_res["total_tokens_used"]
            entry["gfm_tokens"] += g_res["total_tokens_used"]

        for cat, entry in category_breakdown.items():
            n = entry["tasks"]
            entry["react_pass_pct"] = round((entry["react_solved"] / n) * 100, 1)
            entry["gfm_pass_pct"] = round((entry["gfm_solved"] / n) * 100, 1)
            entry["token_savings_pct"] = round(
                ((entry["react_tokens"] - entry["gfm_tokens"]) / max(entry["react_tokens"], 1)) * 100, 1
            )

        return {
            "loop_prevention_rate": round(loop_prevention_rate, 2),
            "token_efficiency": {
                "react_avg_tokens": round(react_tokens / total_tasks, 1),
                "gfm_avg_tokens": round(gfm_tokens / total_tasks, 1),
                "token_savings_pct": round(token_savings_pct, 2),
            },
            "task_success_rate": {
                "react_success_rate": round(react_success_rate, 1),
                "gfm_success_rate": round(gfm_success_rate, 1),
                "improvement_pct": round(gfm_success_rate - react_success_rate, 1),
            },
            "detailed_stats": {
                "total_tasks": total_tasks,
                "react_total_loops": react_loops,
                "gfm_total_loops": gfm_loops,
                "gfm_cycles_prevented": gfm_cycles_prevented,
                "react_avg_attempts": round(sum(r["attempts"] for r in react_results) / total_tasks, 1),
                "gfm_avg_attempts": round(sum(r["attempts"] for r in gfm_results) / total_tasks, 1),
            },
            "category_breakdown": category_breakdown,
        }

    def print_research_results(self, results: Dict[str, Any]) -> None:
        metrics = results["research_metrics"]
        print("\n" + "=" * 75)
        print(f"GFM RESEARCH EVALUATION RESULTS ({metrics['detailed_stats']['total_tasks']} TASKS)")
        print("=" * 75)

        print(f"\n1. Loop Prevention: {metrics['detailed_stats']['gfm_cycles_prevented']} cycles prevented "
              f"(Loops: {metrics['detailed_stats']['react_total_loops']} -> {metrics['detailed_stats']['gfm_total_loops']})")
        print(f"2. Token Efficiency: {metrics['token_efficiency']['token_savings_pct']}% savings "
              f"({metrics['token_efficiency']['react_avg_tokens']} -> {metrics['token_efficiency']['gfm_avg_tokens']} avg tokens)")
        print(f"3. Task Success Rate (Pass@{self.max_attempts}): "
              f"ReAct {metrics['task_success_rate']['react_success_rate']}% vs "
              f"GFM {metrics['task_success_rate']['gfm_success_rate']}% "
              f"({metrics['task_success_rate']['improvement_pct']:+.1f}%)")

        print("\nPer-Category Breakdown:")
        print(f"{'Fault Category':<22} | {'Tasks':>5} | {'ReAct Pass%':>11} | {'GFM Pass%':>9} | {'Cycles Brk':>10} | {'Tok Save%':>9}")
        print("-" * 75)
        for cat, stats in metrics.get("category_breakdown", {}).items():
            print(
                f"{cat:<22} | {stats['tasks']:>5} | {stats['react_pass_pct']:>10.1f}% | "
                f"{stats['gfm_pass_pct']:>8.1f}% | {stats['cycles_prevented']:>10} | {stats['token_savings_pct']:>8.1f}%"
            )
        print("=" * 75)

    def save_research_results(self, results: Dict[str, Any], output_path: str = "benchmarks/results.json") -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nResearch results saved to {output_path}")


def run_benchmark():
    runner = ResearchBenchmarkRunner(max_attempts=5, default_task_count=20)
    results = runner.run_research_benchmark()
    runner.print_research_results(results)
    runner.save_research_results(results)


if __name__ == "__main__":
    run_benchmark()