# Graph-Structured Failure Memory (GFM)

A novel approach to preventing infinite error loops and context drift in self-healing LLM agents using graph-based memory structures.

## Overview

Graph-Structured Failure Memory (GFM) is a research project that implements a systematic approach to error recovery in LLM-based autonomous agents. By maintaining a graph-based memory of failure patterns, recovery strategies, and their outcomes, GFM enables agents to:

- Detect and break infinite error loops
- Learn from past failures to improve recovery strategies
- Maintain context stability over long-running tasks
- Select effective recovery actions based on historical success rates

## Project Structure

```
graph-failure-memory/
├── gfm/                       # Core Python Package
│   ├── __init__.py
│   ├── graph_memory.py        # NetworkX GraphFailureMemory implementation
│   ├── AST_hasher.py          # Error/Action signature hashing engine
│   └── context_pruner.py      # Subgraph-to-Prompt compression logic
├── agents/                    # LLM Agent Orchestration
│   ├── __init__.py
│   ├── react_agent.py         # Baseline ReAct agent loop (for comparison)
│   └── gfm_agent.py           # Self-healing agent using LangGraph + GFM
├── benchmarks/                # Evaluation & Research Metrics
│   ├── __init__.py
│   ├── test_tasks.json        # Synthetic code/API failure test suite
│   └── run_evals.py           # Benchmark script (Token usage, cycles, recovery rate)
├── paper/                     # Research Paper Deliverables
│   ├── architecture_diagram.png
│   └── main.tex               # LaTeX source for conference submission
├── requirements.txt
├── main.py                    # Quick CLI runner
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd graph-failure-memory
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: No API keys required! The project runs in simulation mode and demonstrates all core functionality without needing LLM API access.

## Usage

### CLI Commands

The project provides a CLI interface through `main.py`:

#### Run Agent Demo
```bash
# Demo GFM agent (default)
python main.py demo

# Demo ReAct baseline agent
python main.py demo --agent react

# Quiet mode
python main.py demo --quiet
```

#### Run Benchmarks
```bash
# Run full benchmark suite
python main.py benchmark

# Save results to file
python main.py benchmark --output results.json
```

#### Test Components
```bash
# Test individual GFM components
python main.py test
```

### Programmatic Usage

#### Using GFM Components

```python
from gfm import GraphFailureMemory, ASTHasher, ContextPruner

# Initialize components
memory = GraphFailureMemory()
hasher = ASTHasher()
pruner = ContextPruner()

# Add a failure to memory
error_hash = hasher.hash_error("SyntaxError", "missing parenthesis", {"line": 1})
memory.add_failure(error_hash, "syntax", "missing parenthesis", {"line": 1})

# Record successful recovery
memory.record_recovery(f"failure_{error_hash}", "Add closing parenthesis", success=True)

# Get recovery suggestions
suggestions = memory.get_recovery_suggestions(error_hash)
```

#### Using GFM Agent

```python
from agents import GFMAgent

# Initialize agent
agent = GFMAgent(max_steps=10, verbose=True)

# Define tools
tools = {
    "execute": my_execute_function,
    "analyze": my_analyze_function
}

# Run task
result = agent.run("Fix the syntax error", tools)
```

## Core Components

### GraphFailureMemory
NetworkX-based graph structure that stores:
- Failure nodes with error signatures and context
- Action nodes with execution outcomes
- Causal relationships between failures and actions
- Success/failure statistics for recovery strategies

### ASTHasher
Generates consistent signatures for:
- Code patterns using AST parsing
- Error messages with normalization
- API calls and function signatures
- Agent states for drift detection

### ContextPruner
Manages context window limitations by:
- Extracting relevant subgraphs around current errors
- Compressing graph structures into prompt-friendly format
- Prioritizing failures by relevance and frequency
- Maintaining context within token limits

## Benchmarking

The project includes a comprehensive benchmark suite comparing:

- **ReAct Agent**: Baseline reasoning-acting loop without GFM
- **GFM Agent**: Enhanced agent with graph-structured failure memory

### Metrics
- Success rate on error-prone tasks
- Recovery rate from failures
- Average steps to completion
- Error loop prevention
- Context drift score

### Test Tasks
The benchmark suite includes 10 synthetic tasks covering:
- Syntax errors
- API failures
- Logical errors
- Context drift scenarios
- Error loop patterns
- Resource management errors

## Research Paper

The project includes a LaTeX paper (`paper/main.tex`) suitable for conference submission, covering:

- Introduction and motivation
- Related work on LLM agents and error recovery
- Methodology and architecture
- Implementation details
- Experimental results
- Discussion and future work

## Contributing

Contributions are welcome! Areas for future work:
- Advanced graph compression techniques
- Transfer learning across tasks
- Integration with additional memory architectures
- Real-world deployment studies

## License

[Specify your license here]

## Citation

If you use this work in your research, please cite:

```bibtex
@article{gfm2024,
  title={Graph-Structured Failure Memory: Preventing Infinite Error Loops and Context Drift in Self-Healing LLM Agents},
  author={[Author Names]},
  journal={[Journal/Conference]},
  year={2024}
}
```

## Contact

For questions and feedback, please contact [your email].
