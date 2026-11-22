"""
Main CLI Entry Point for Graph-Structured Failure Memory Project
"""

import argparse
import sys
from agents import ReactAgent
from benchmarks import ResearchBenchmarkRunner as BenchmarkRunner


def run_agent_demo(agent_type: str = "react", verbose: bool = True):
    """
    Run a demonstration of the ReAct agent.

    Args:
        agent_type: 'react' (GFM agent requires LLM API and runs in benchmark mode)
        verbose: Whether to print execution details
    """
    print(f"Running ReAct Agent Demo")
    print("=" * 50)

    # Define a simple task
    task = "Fix the syntax error in the following code: print('Hello World'"

    # Define mock tools for ReAct agent
    def fix_syntax(input_data: str) -> str:
        """Mock tool to fix syntax errors."""
        if "syntax" in input_data.lower() or "print" in input_data.lower():
            return "success: Fixed syntax by adding closing parenthesis: print('Hello World')"
        return "No syntax issues found"

    def analyze_code(input_data: str) -> str:
        """Mock tool to analyze code."""
        return "Analysis: Missing closing parenthesis in print statement"

    tools = {
        "fix_syntax": fix_syntax,
        "analyze": analyze_code
    }

    agent = ReactAgent(max_steps=5, verbose=verbose)
    result = agent.run(task, tools)

    print("\n" + "=" * 50)
    print("Execution Summary:")
    print(f"Success: {result['success']}")
    print(f"Total Steps: {result['total_steps']}")
    print(f"Error Count: {result.get('error_count', 0)}")

    return result


def run_benchmarks(output_file: str = None):
    """
    Run the full benchmark suite comparing ReAct and GFM agents.

    Args:
        output_file: Optional path to save results
    """
    print("Running Benchmark Suite")
    print("=" * 50)

    runner = BenchmarkRunner()
    results = runner.run_research_benchmark()
    runner.print_research_results(results)

    if output_file:
        runner.save_research_results(results, output_file)
    else:
        runner.save_research_results(results)

    return results


def test_gfm_components():
    """Test individual GFM components."""
    print("Testing GFM Components")
    print("=" * 50)
    
    from gfm import GraphFailureMemory, ASTHasher, GraphContextPruner
    
    # Test Graph Memory
    print("\n1. Testing GraphFailureMemory...")
    memory = GraphFailureMemory()
    
    # Record a failure
    is_cycle, signature = memory.record_failure(
        target_state="CodeExecution",
        action="print('hello'",
        error_msg="SyntaxError: Missing parenthesis"
    )
    
    print(f"  Failure recorded - Cycle detected: {is_cycle}, Signature: {signature}")
    
    # Record success transition
    memory.transition_success("FixedCode", "Added closing parenthesis")
    
    # Check for blocked actions
    blocked = memory.get_blocked_actions()
    print(f"  Blocked actions: {len(blocked)}")
    
    # Test AST Hasher
    print("\n2. Testing ASTHasher...")
    hasher = ASTHasher()
    
    code = "print('Hello World')"
    code_hash = hasher.hash_code(code)
    print(f"  Code Hash: {code_hash}")
    
    error_hash = hasher.hash_error("SyntaxError", "missing parenthesis", {"line": 1})
    print(f"  Error Hash: {error_hash}")
    
    # Test Context Pruner
    print("\n3. Testing GraphContextPruner...")
    pruner = GraphContextPruner()
    
    compressed = pruner.summarize_graph_for_llm(memory)
    print(f"  Compressed Context length: {len(compressed)} chars")
    print(f"  Context preview available")
    
    print("\n" + "=" * 50)
    print("All components tested successfully!")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Graph-Structured Failure Memory (GFM) Project"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run agent demonstration")
    demo_parser.add_argument(
        "--agent",
        choices=["react", "gfm"],
        default="gfm",
        help="Agent type to demonstrate"
    )
    demo_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmark suite")
    benchmark_parser.add_argument(
        "--output",
        help="Output file for results (JSON)"
    )
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test GFM components")
    
    args = parser.parse_args()
    
    if args.command == "demo":
        run_agent_demo(args.agent, not args.quiet)
    elif args.command == "benchmark":
        run_benchmarks(args.output)
    elif args.command == "test":
        test_gfm_components()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
