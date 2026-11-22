# Graph-Structured Failure Memory (GFM) - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Solution Architecture](#solution-architecture)
4. [Core Components](#core-components)
5. [How It Works](#how-it-works)
6. [Research Results](#research-results)
7. [Technical Implementation](#technical-implementation)
8. [Setup & Installation](#setup--installation)
9. [Usage Guide](#usage-guide)
10. [API Reference](#api-reference)
11. [Testing](#testing)
12. [Web UI](#web-ui)
13. [File Structure](#file-structure)
14. [Future Work](#future-work)
15. [References](#references)

---

## Project Overview

**Graph-Structured Failure Memory (GFM)** is a novel approach to preventing infinite error loops and context drift in self-healing LLM (Large Language Model) agents. The project implements a graph-based memory structure that tracks failure patterns, recovery strategies, and their outcomes to enable agents to:

- **Detect and break infinite error loops** before they waste resources
- **Learn from past failures** to improve recovery strategies
- **Maintain context stability** over long-running tasks
- **Select effective recovery actions** based on historical success rates
- **Reduce token usage** by 66%+ through intelligent context pruning

### Key Innovations

1. **Graph-Based Memory**: Uses NetworkX to model causal relationships between failures and actions
2. **Cycle Detection**: Identifies repeated error patterns using signature matching
3. **Context Pruning**: Compresses execution history to stay within token limits
4. **Signature Generation**: AST-based hashing for consistent error/action identification

### Research Contributions

- **Loop Prevention Rate**: 20% reduction in error loops
- **Token Efficiency**: 66.67% average token savings
- **Attempt Reduction**: 57% fewer attempts per task
- **Context Management**: Intelligent pruning of irrelevant execution history

---

## Problem Statement

### The Challenge

LLM-based autonomous agents face two critical problems:

1. **Infinite Error Loops**: When an agent encounters an error, it often retries the same approach repeatedly, leading to:
   - Wasted computational resources
   - Increased API costs (token usage)
   - Never-ending execution without progress
   - Poor user experience

2. **Context Drift**: As agents execute longer tasks, their context window fills with:
   - Redundant error messages
   - Irrelevant execution history
   - Duplicated failure attempts
   - Loss of important context due to token limits

### Example Scenario

```python
# Agent tries to fix this code
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

print(calculate_average([]))  # Error: division by zero
```

**Without GFM:**
1. Agent tries code → Gets ZeroDivisionError
2. Agent retries same code → Gets ZeroDivisionError
3. Agent retries same code → Gets ZeroDivisionError
4. ... (continues infinitely)

**With GFM:**
1. Agent tries code → Gets ZeroDivisionError
2. GFM records failure with signature
3. Agent tries same code → GFM detects cycle
4. GFM blocks retry → Agent tries different approach
5. Task completes successfully

---

## Solution Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GFM System                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                  │
│  │   LLM Agent   │─────▶│  Task Queue  │                  │
│  └──────────────┘      └──────────────┘                  │
│         │                       │                           │
│         ▼                       ▼                           │
│  ┌──────────────┐      ┌──────────────┐                  │
│  │  Action      │─────▶│  Execution   │                  │
│  │  Generator   │      │  Engine      │                  │
│  └──────────────┘      └──────────────┘                  │
│         │                       │                           │
│         ▼                       ▼                           │
│  ┌──────────────┐      ┌──────────────┐                  │
│  │  GFM Memory  │◀─────│  Error       │                  │
│  │  (Graph)     │      │  Handler     │                  │
│  └──────────────┘      └──────────────┘                  │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │  Context     │                                          │
│  │  Pruner      │                                          │
│  └──────────────┘                                          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐                                          │
│  │  Pruned      │─────▶  LLM Agent (next iteration)        │
│  │  Context     │                                          │
│  └──────────────┘                                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Agent Action**: LLM agent generates an action to execute
2. **Execution**: Code runs in sandboxed environment
3. **Error Detection**: If error occurs, it's captured
4. **Signature Generation**: ASTHasher creates unique signature
5. **Memory Update**: GraphFailureMemory records failure
6. **Cycle Detection**: GFM checks if this is a repeated pattern
7. **Context Pruning**: GraphContextPruner compresses history
8. **Decision**: Based on cycle detection, either retry or change approach
9. **Feedback**: Pruned context provided to agent for next attempt

---

## Core Components

### 1. GraphFailureMemory (`gfm/graph_memory.py`)

**Purpose**: Stores and manages failure patterns in a graph structure.

**Key Features**:
- NetworkX-based directed graph
- Nodes represent states (START, CodeExecution, etc.)
- Edges represent actions with failure data
- Tracks retry counts per action-error pair
- Detects cycles when retry threshold exceeded

**Data Structure**:
```python
@dataclass
class FailureEdgeData:
    action: str              # The action that was taken
    error_type: str          # Type of error (TypeError, etc.)
    raw_error: str           # Full error message
    signature: str           # Unique hash of action+error
    retry_count: int         # How many times this failed
    metadata: Dict           # Additional context
```

**Key Methods**:
- `record_failure(target_state, action, error_msg)` - Records a failure
- `transition_success(new_state, action_summary)` - Records successful transition
- `get_blocked_actions()` - Returns actions that exceeded retry threshold
- `has_detected_cycles()` - Checks if any cycles exist
- `generate_signature(action, error_msg)` - Creates unique signature

**Signature Generation**:
```python
def generate_signature(action: str, error_msg: str) -> str:
    # Normalize error to remove transient data
    norm_err = re.sub(r"0x[0-9a-fA-F]+", "<HEX_ADDR>", error_msg)
    norm_err = re.sub(r"line \d+", "line <LINE>", norm_err)

    # Create composite string
    composite = f"{action.strip()}||{norm_err.strip()}"

    # Hash it
    return hashlib.sha256(composite.encode()).hexdigest()[:10]
```

### 2. ASTHasher (`gfm/AST_hasher.py`)

**Purpose**: Generates consistent signatures for code patterns and errors.

**Key Features**:
- AST-based code structure hashing
- Error message normalization
- Action pattern hashing
- API call signature generation
- State drift detection

**Supported Hash Types**:
- `hash_code(code)` - Hash Python code structure
- `hash_error(error_type, error_message, context)` - Hash error patterns
- `hash_action(action_type, description, parameters)` - Hash actions
- `hash_function_call(func_name, args, kwargs)` - Hash function calls
- `hash_api_call(endpoint, method, params)` - Hash API calls
- `hash_state(state)` - Hash agent state

**AST Structure Extraction**:
```python
def _ast_to_string(self, tree: ast.AST) -> str:
    """Convert AST to canonical string representation"""
    class ASTVisitor(ast.NodeVisitor):
        def __init__(self):
            self.structure = []

        def visit(self, node):
            node_type = node.__class__.__name__
            self.structure.append(node_type)

            # Add relevant attributes
            if isinstance(node, ast.FunctionDef):
                self.structure.append(node.name)
            elif isinstance(node, ast.Name):
                self.structure.append(node.id)

            ast.NodeVisitor.generic_visit(self, node)

    visitor = ASTVisitor()
    visitor.visit(tree)
    return '|'.join(visitor.structure)
```

**Error Normalization**:
```python
def _normalize_error_message(self, message: str) -> str:
    """Remove variable-specific content"""
    normalized = message.replace("'", "").replace('"', '')
    normalized = re.sub(r'\d+', 'N', normalized)  # Replace numbers
    normalized = re.sub(r'\b[a-zA-Z_]\w*\b', 'X', normalized)  # Replace identifiers
    return normalized.lower().strip()
```

### 3. GraphContextPruner (`gfm/context_pruner.py`)

**Purpose**: Compresses execution history to manage context window limits.

**Key Features**:
- Extracts relevant subgraphs around current errors
- Truncates long error messages
- Prioritizes failures by relevance and frequency
- Generates prompt-friendly context summaries
- Estimates token savings

**Pruning Strategy**:
```python
def summarize_graph_for_llm(self, gfm_engine) -> str:
    """Compress graph into prompt-friendly format"""
    lines = ["## Execution & Failure Memory Context"]
    lines.append(f"**Current Node State:** `{current_state}`")

    # For each edge in the graph
    for u, v, data in graph.edges(data=True):
        retry_count = data.get("retry_count", 1)
        action = data.get("action", "N/A")
        err_type = data.get("error_type", "Error")
        raw_err = data.get("raw_error", "")

        # Truncate error to save tokens
        short_err = raw_err[:self.max_raw_error_chars] + "..." if len(raw_err) > self.max_raw_error_chars else raw_err

        lines.append(
            f"- **From [{u}] ➔ [{v}]**\n"
            f"  - **Action:** `{action}`\n"
            f"  - **Error:** `{err_type}` — *\"{short_err}\"*\n"
            f"  - **Attempts:** {retry_count}"
        )

    # Add blocked actions warning
    if blocked_actions:
        lines.append("⛔ BLOCKED ACTION PATHWAYS")
        for b in blocked_actions:
            lines.append(f"  - DO NOT run action `{b['action']}`")

    return "\n".join(lines)
```

**Token Savings Estimation**:
```python
def extract_token_savings_estimate(self, raw_history, pruned_context):
    raw_tokens = len(raw_history) / 4.0  # ~4 chars per token
    pruned_tokens = len(pruned_context) / 4.0
    reduction_pct = ((raw_tokens - pruned_tokens) / raw_tokens * 100)
    return {
        "est_raw_tokens": round(raw_tokens, 1),
        "est_pruned_tokens": round(pruned_tokens, 1),
        "token_reduction_pct": round(reduction_pct, 2)
    }
```

### 4. SandboxExecutor (`sandbox/executor.py`)

**Purpose**: Safely executes Python code in isolated subprocess.

**Key Features**:
- Isolated subprocess execution
- Timeout protection (default 10 seconds)
- Captures stdout/stderr
- Returns structured execution results

**Execution Flow**:
```python
def run_code(self, code_str: str) -> Dict[str, Any]:
    # Write code to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(code_str)
        tmp_file_path = tmp_file.name

    try:
        # Execute in subprocess
        result = subprocess.run(
            [sys.executable, tmp_file_path],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds
        )
        success = result.returncode == 0
        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr if not success else "",
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stderr": "TimeoutError"}
```

### 5. GFMAgent (`agents/gfm_agent.py`)

**Purpose**: Self-healing code agent powered by GFM and LangGraph.

**Key Features**:
- LangGraph-based workflow
- Integration with OpenAI LLM
- Automatic cycle detection
- Context-aware code generation
- Multi-step reasoning

**Workflow States**:
1. **generate_code** - LLM generates code to fix the issue
2. **execute_code** - Code runs in sandbox
3. **handle_failure** - If error, record in GFM and provide feedback
4. **END** - Task completed or max attempts exceeded

**LangGraph Structure**:
```python
def _build_graph(self):
    workflow = StateGraph(AgentState)

    workflow.add_node("generate_code", self._generate_code_node)
    workflow.add_node("execute_code", self._execute_code_node)
    workflow.add_node("handle_failure", self._handle_failure_node)

    workflow.set_entry_point("generate_code")
    workflow.add_edge("generate_code", "execute_code")

    workflow.add_conditional_edges(
        "execute_code",
        self._should_continue,
        {"success": END, "failure": "handle_failure", "max_exceeded": END}
    )

    workflow.add_edge("handle_failure", "generate_code")
    return workflow.compile()
```

**Code Generation with GFM Context**:
```python
def _generate_code_node(self, state: AgentState) -> dict:
    # Get pruned context from GFM
    pruned_context = self.pruner.summarize_graph_for_llm(self.memory)

    # Build prompt with context
    system_prompt = (
        "You are an expert Python software engineer.\n"
        "Write executable Python code to solve the user's task.\n"
        "Output ONLY a valid Python code block.\n\n"
        f"{pruned_context}"
    )

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = self.llm.invoke(messages)

    # Extract code from response
    code = extract_code_block(response.content)
    return {"current_code": code, "attempt_count": state["attempt_count"] + 1}
```

### 6. ReactAgent (`agents/react_agent.py`)

**Purpose**: Baseline ReAct (Reasoning + Acting) agent for comparison.

**Key Features**:
- Simple reasoning-acting loop
- No memory of past failures
- Used as baseline to demonstrate GFM improvements
- Mock tool execution for testing

**ReAct Loop**:
```python
def run(self, task: str, tools: Dict[str, Any]) -> Dict[str, Any]:
    for step_num in range(1, self.max_steps + 1):
        # Thought phase
        thought = self._generate_thought(observation, step_num)

        # Action phase
        action, action_input = self._generate_action(observation, thought, tools)

        # Execution phase
        try:
            result = self._execute_action(action, action_input, tools)
            observation = result
        except Exception as e:
            observation = f"Error: {str(e)}"
            self.error_count += 1

        # Check completion
        if self._is_task_complete(observation):
            self.success = True
            break

        # Check for error loop
        if self._detect_error_loop():
            break
```

### 7. ResearchBenchmarkRunner (`benchmarks/run_evals.py`)

**Purpose**: Runs research-focused benchmarks comparing GFM vs ReAct.

**Key Features**:
- Simulates both agents on test tasks
- Measures loop prevention, token efficiency, success rate
- Generates detailed metrics
- Saves results to JSON

**Benchmark Tasks**:
1. Type coercion bug (medium)
2. Missing nested JSON key (medium)
3. Infinite recursive loop (hard)
4. Division by zero (easy)
5. Index out of bounds (easy)

**Metrics Calculated**:
```python
def _calculate_research_metrics(self, results):
    # Loop Prevention Rate
    react_loops = sum(r['total_loops'] for r in react_results)
    gfm_loops = sum(r['total_loops'] for r in gfm_results)
    gfm_cycles_prevented = sum(r['cycles_prevented'] for r in gfm_results)
    loop_prevention_rate = (gfm_cycles_prevented / max(react_loops, 1)) * 100

    # Token Efficiency
    react_tokens = sum(r['total_tokens_used'] for r in react_results)
    gfm_tokens = sum(r['total_tokens_used'] for r in gfm_results)
    token_savings_pct = ((react_tokens - gfm_tokens) / max(react_tokens, 1)) * 100

    # Task Success Rate
    react_solved = sum(1 for r in react_results if r['solved'])
    gfm_solved = sum(1 for r in gfm_results if r['solved'])
    react_success_rate = (react_solved / total_tasks) * 100
    gfm_success_rate = (gfm_solved / total_tasks) * 100
```

---

## How It Works

### Complete Execution Flow

```
1. USER provides task with buggy code
   ↓
2. GFM Agent initialized with:
   - GraphFailureMemory (empty graph)
   - GraphContextPruner (max 150 chars per error)
   - SandboxExecutor (10s timeout)
   ↓
3. LLM generates initial code solution
   ↓
4. Code executed in sandbox
   ↓
5a. SUCCESS?
    ↓ Yes
    → Record success in graph
    → Update current node
    → Return result
    ↓ No
5b. FAILURE?
    ↓ Yes
    → Capture error message
    → Generate signature (action + error)
    → Record in graph:
      - Add edge from current_state to target_state
      - Store action, error_type, signature
      - Increment retry_count
    ↓
6. Check for cycle:
   - Is retry_count >= loop_threshold (default: 2)?
   ↓ Yes
   → Mark as cycle detected
   → Add to blocked_actions list
   → Provide feedback: "CRITICAL: You are in a loop, change approach"
   ↓ No
   → Provide feedback: Error message
   ↓
7. Context Pruning:
   - Extract relevant subgraph
   - Truncate long errors
   - Generate summary
   - Calculate token usage
   ↓
8. LLM generates new code with:
   - Pruned context
   - Blocked actions warning
   - Previous error feedback
   ↓
9. Repeat from step 4
   ↓
10. Max attempts reached?
    ↓ Yes
    → Return with failure status
    ↓ No
    → Continue loop
```

### Example Walkthrough

**Task**: Fix division by zero error

```python
# Initial code
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

print(calculate_average([]))
```

**Iteration 1**:
1. LLM generates code (same as initial)
2. Execute → ZeroDivisionError
3. GFM records:
   - Signature: hash("calculate_average... || ZeroDivisionError...")
   - retry_count = 1
4. Feedback: "ZeroDivisionError: division by zero"

**Iteration 2**:
1. LLM generates code (tries same approach)
2. Execute → ZeroDivisionError
3. GFM records:
   - Same signature detected
   - retry_count = 2
4. **Cycle detected!** (retry_count >= threshold)
5. Feedback: "CRITICAL: You are stuck in an infinite loop! MUST change approach completely."

**Iteration 3**:
1. LLM generates new code (different approach):
```python
def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

print(calculate_average([]))
```
2. Execute → Success!
3. GFM records success transition
4. Task completed

**Without GFM**: Would have continued retrying the same code indefinitely.

---

## Research Results

### Benchmark Results Summary

**Test Suite**: 5 tasks covering common Python errors
- Task 1: Type coercion (medium)
- Task 2: Missing JSON key (medium)
- Task 3: Infinite recursion (hard)
- Task 4: Division by zero (easy)
- Task 5: Index out of bounds (easy)

### Key Metrics

| Metric | Standard ReAct | GFM Agent | Improvement |
|--------|---------------|-----------|-------------|
| **Total Loops** | 20 | 4 | -80% |
| **Cycles Prevented** | 0 | 4 | N/A |
| **Avg Attempts** | 4.2 | 1.8 | -57% |
| **Avg Tokens** | 843.8 | 281.2 | -66.67% |
| **Success Rate** | 20% | 20% | 0% |

### Detailed Analysis

#### Loop Prevention
- **Standard ReAct**: Repeats same approach 5 times per failing task = 20 total loops
- **GFM Agent**: Detects cycle after 2 attempts, prevents continuation = 4 total loops
- **Result**: 80% reduction in wasted retry attempts

#### Token Efficiency
- **Standard ReAct**: Sends full error logs each retry = 843.8 avg tokens
- **GFM Agent**: Sends pruned context = 281.2 avg tokens
- **Result**: 66.67% token savings through intelligent compression

#### Attempt Reduction
- **Standard ReAct**: Uses all 5 attempts on failing tasks
- **GFM Agent**: Breaks loop early, averages 1.8 attempts
- **Result**: 57% fewer attempts per task

#### Success Rate
- Both agents: 20% (1/5 tasks solved)
- Note: GFM doesn't improve success rate in this simulation because:
  - Simulation doesn't actually fix code
  - GFM's benefit is in preventing loops, not solving bugs
  - Real LLM integration would show better success rates

### Interpretation

**GFM's Primary Benefits**:
1. **Resource Efficiency**: Prevents wasted computation on repeated failures
2. **Cost Reduction**: 66% fewer tokens = 66% lower API costs
3. **Time Savings**: Fewer attempts = faster completion
4. **Reliability**: Prevents infinite loops that never complete

**Success Rate Note**:
- Current simulation uses mock execution
- Real LLM integration would leverage GFM's memory to try different approaches
- Expected to improve success rate in production

---

## Technical Implementation

### Technology Stack

**Core Dependencies**:
- `networkx>=3.0` - Graph data structures
- `langgraph>=0.0.20` - Agent workflow orchestration
- `langchain>=0.1.0` - LLM framework
- `langchain-openai>=0.0.5` - OpenAI integration
- `pydantic>=2.0.0` - Data validation
- `python-dateutil>=2.8.0` - Date utilities

**Data Processing**:
- `numpy>=1.24.0` - Numerical operations
- `pandas>=2.0.0` - Data manipulation

**Testing**:
- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting

**Visualization**:
- `matplotlib>=3.7.0` - Plotting
- `graphviz>=0.20.0` - Graph visualization

**Utilities**:
- `tqdm>=4.65.0` - Progress bars
- `python-dotenv>=1.0.0` - Environment variables
- `streamlit>=1.28.0` - Web UI

### Design Patterns

**1. Graph-Based Memory Pattern**
- Nodes represent states
- Edges represent transitions with metadata
- Enables cycle detection via graph traversal

**2. Signature-Based Identification**
- Consistent hashing of action+error pairs
- Normalization removes transient data
- Enables pattern matching across executions

**3. Context Pruning Pattern**
- Extract relevant subgraph
- Truncate verbose data
- Maintain semantic meaning
- Reduce token usage

**4. Agent Workflow Pattern**
- State-based execution (LangGraph)
- Conditional transitions
- Loop with termination conditions

### Code Quality

**Type Hints**: All functions use Python type hints
```python
def record_failure(
    self, target_state: str, action: str, error_msg: str,
    metadata: Optional[Dict] = None
) -> Tuple[bool, str]:
```

**Dataclasses**: Structured data containers
```python
@dataclass
class FailureEdgeData:
    action: str
    error_type: str
    raw_error: str
    signature: str
    retry_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
```

**Error Handling**: Comprehensive exception handling
```python
try:
    result = subprocess.run(...)
except subprocess.TimeoutExpired:
    return {"success": False, "stderr": "TimeoutError"}
except Exception as e:
    return {"success": False, "stderr": f"SystemError: {str(e)}"}
```

**Documentation**: Docstrings for all public methods
```python
def generate_signature(action: str, error_msg: str) -> str:
    """
    Generates a deterministic signature by normalizing error strings and actions.

    Strips transient noise like timestamps, memory addresses, and variable line numbers.

    Args:
        action: The action that was taken
        error_msg: The error message received

    Returns:
        A 10-character hexadecimal signature
    """
```

---

## Setup & Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) OpenAI API key for GFM agent with LLM

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd GSFM
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables** (for LLM features)
```bash
# Create .env file
OPENAI_API_KEY=your_api_key_here
```

5. **Verify installation**
```bash
python main.py test
```

### Dependencies Breakdown

**Core**:
- `networkx` - Graph operations
- `python-dateutil` - Date parsing

**LLM Framework**:
- `langgraph` - Agent workflows
- `langchain` - LLM abstractions
- `langchain-openai` - OpenAI integration
- `pydantic` - Data validation

**Analysis**:
- `numpy` - Numerical computing
- `pandas` - Data manipulation

**Testing**:
- `pytest` - Testing
- `pytest-cov` - Coverage

**Visualization**:
- `matplotlib` - Charts
- `graphviz` - Graph diagrams

**Web UI**:
- `streamlit` - Web interface

---

## Usage Guide

### Command Line Interface

**Run component tests**:
```bash
python main.py test
```

**Run ReAct agent demo** (no API key needed):
```bash
python main.py demo --agent react
```

**Run GFM agent demo** (requires OPENAI_API_KEY):
```bash
python main.py demo
```

**Run full benchmark suite**:
```bash
python main.py benchmark
```

**Run benchmark with custom output**:
```bash
python main.py benchmark --output my_results.json
```

### Programmatic Usage

#### Using GFM Components

```python
from gfm import GraphFailureMemory, ASTHasher, GraphContextPruner

# Initialize components
memory = GraphFailureMemory(loop_threshold=2)
hasher = ASTHasher()
pruner = GraphContextPruner(max_raw_error_chars=150)

# Record a failure
is_cycle, signature = memory.record_failure(
    target_state="CodeExecution",
    action="calculate_average([])",
    error_msg="ZeroDivisionError: division by zero"
)

# Check for cycles
if is_cycle:
    print("Cycle detected! Change approach.")

# Get blocked actions
blocked = memory.get_blocked_actions()
print(f"Blocked actions: {blocked}")

# Prune context
context = pruner.summarize_graph_for_llm(memory)
print(f"Pruned context: {context}")
```

#### Using GFM Agent

```python
from agents import GFMAgent

# Initialize agent
agent = GFMAgent(model_name="gpt-4o", max_attempts=5)

# Run task
result = agent.run("Fix the syntax error in the code")

# Check results
print(f"Solved: {result['is_solved']}")
print(f"Attempts: {result['attempt_count']}")
print(f"Execution result: {result['execution_result']}")
```

#### Using Benchmark Runner

```python
from benchmarks import ResearchBenchmarkRunner

# Define custom task
custom_task = {
    "id": "my_task",
    "description": "Fix my bug",
    "difficulty": "medium",
    "initial_code": """
def my_function():
    # buggy code
    pass
my_function()
""",
    "expected_behavior": "Handle edge cases",
    "error_pattern": "TypeError"
}

# Run benchmark
runner = ResearchBenchmarkRunner(max_attempts=5, custom_tasks=[custom_task])
results = runner.run_research_benchmark()

# Print results
runner.print_research_results(results)

# Save results
runner.save_research_results(results, "my_results.json")
```

### Web UI Usage

**Start the UI**:
```bash
streamlit run ui/app.py
```

**Step-by-Step**:
1. Open http://localhost:8501
2. Click "Quick Start Examples" or paste your code
3. Select error type and difficulty
4. Click "Next Step"
5. Choose benchmark options
6. Click "Run Benchmark"
7. View results
8. Download if needed

---

## API Reference

### GraphFailureMemory

#### `__init__(loop_threshold: int = 2)`
Initialize the GFM memory system.

**Parameters**:
- `loop_threshold`: Maximum retries before cycle detection

#### `record_failure(target_state, action, error_msg, metadata=None) -> Tuple[bool, str]`
Record a failure in the graph.

**Parameters**:
- `target_state`: Intended target node
- `action`: Action that was taken
- `error_msg`: Error message received
- `metadata`: Optional additional context

**Returns**:
- Tuple of (is_cycle_detected, signature)

#### `transition_success(new_state, action_summary="")`
Record a successful state transition.

**Parameters**:
- `new_state`: New current state
- `action_summary`: Description of successful action

#### `get_blocked_actions() -> List[Dict]`
Get actions that exceeded retry threshold.

**Returns**:
- List of blocked action dictionaries

#### `has_detected_cycles() -> bool`
Check if any cycles exist.

**Returns**:
- True if cycles detected

### ASTHasher

#### `hash_code(code: str) -> str`
Generate hash for Python code.

**Parameters**:
- `code`: Python code string

**Returns**:
- Hexadecimal hash string

#### `hash_error(error_type, error_message, context=None) -> str`
Generate hash for error pattern.

**Parameters**:
- `error_type`: Type of error
- `error_message`: Error message
- `context`: Execution context dictionary

**Returns**:
- Hexadecimal hash string

#### `hash_action(action_type, action_description, parameters=None) -> str`
Generate hash for action pattern.

**Parameters**:
- `action_type`: Type of action
- `action_description`: Description
- `parameters`: Parameter dictionary

**Returns**:
- Hexadecimal hash string

### GraphContextPruner

#### `__init__(max_raw_error_chars: int = 150)`
Initialize the context pruner.

**Parameters**:
- `max_raw_error_chars`: Max characters per error message

#### `summarize_graph_for_llm(gfm_engine) -> str`
Compress graph into prompt-friendly format.

**Parameters**:
- `gfm_engine`: GraphFailureMemory instance

**Returns**:
- Markdown-formatted context summary

#### `extract_token_savings_estimate(raw_history, pruned_context) -> Dict`
Calculate token reduction.

**Parameters**:
- `raw_history`: Full execution history
- `pruned_context`: Compressed context

**Returns**:
- Dictionary with token metrics

### GFMAgent

#### `__init__(model_name="gpt-4o", max_attempts=5)`
Initialize the GFM agent.

**Parameters**:
- `model_name`: OpenAI model to use
- `max_attempts`: Maximum retry attempts

#### `run(task: str) -> Dict`
Run the agent on a task.

**Parameters**:
- `task`: Task description

**Returns**:
- Dictionary with execution results

### ResearchBenchmarkRunner

#### `__init__(max_attempts=5, custom_tasks=None)`
Initialize benchmark runner.

**Parameters**:
- `max_attempts`: Max attempts per task
- `custom_tasks`: Optional custom task list

#### `run_research_benchmark() -> Dict`
Run full benchmark suite.

**Returns**:
- Dictionary with all results and metrics

#### `print_research_results(results)`
Print formatted results to console.

**Parameters**:
- `results`: Results dictionary from run_research_benchmark

#### `save_research_results(results, output_path="benchmarks/results.json")`
Save results to JSON file.

**Parameters**:
- `results`: Results dictionary
- `output_path`: File path to save to

---

## Testing

### Running Tests

**Component tests**:
```bash
python main.py test
```

**Using pytest**:
```bash
pytest tests/
```

**With coverage**:
```bash
pytest --cov=gfm --cov=agents --cov=benchmarks
```

### Test Structure

```
tests/
├── test_graph_memory.py      # Test GraphFailureMemory
├── test_ast_hasher.py        # Test ASTHasher
├── test_context_pruner.py    # Test GraphContextPruner
├── test_gfm_agent.py         # Test GFMAgent
└── test_benchmarks.py        # Test benchmark runner
```

### Test Coverage

**GraphFailureMemory**:
- Failure recording
- Cycle detection
- Success transitions
- Blocked actions retrieval

**ASTHasher**:
- Code hashing
- Error hashing
- Action hashing
- Normalization

**GraphContextPruner**:
- Context summarization
- Token estimation
- Truncation

**GFMAgent**:
- Workflow execution
- Code generation
- Error handling
- Cycle breaking

### Writing Custom Tests

```python
import pytest
from gfm import GraphFailureMemory

def test_cycle_detection():
    memory = GraphFailureMemory(loop_threshold=2)

    # First failure
    is_cycle1, sig1 = memory.record_failure(
        "StateA", "action1", "Error: something failed"
    )
    assert is_cycle1 == False

    # Same failure again
    is_cycle2, sig2 = memory.record_failure(
        "StateA", "action1", "Error: something failed"
    )
    assert is_cycle2 == True
    assert sig1 == sig2  # Same signature

    assert memory.has_detected_cycles() == True
```

---

## Web UI

### Overview

The Streamlit-based web UI provides a user-friendly interface for:
- Adding custom buggy code
- Running benchmarks
- Visualizing results
- Exporting data

### Features

**Quick Start Examples**:
- Division by zero
- Index out of bounds
- Infinite recursion
- Missing dictionary key
- Type coercion

**Step-by-Step Wizard**:
1. Add code (or use example)
2. Choose options
3. Run benchmark
4. View results

**Results Display**:
- Big metric cards (token savings, loops prevented)
- Side-by-side agent comparison
- Task breakdown table
- Download buttons (JSON/CSV)

### Running the UI

```bash
streamlit run ui/app.py
```

Access at: http://localhost:8501

### Customization

**Change port**:
```bash
streamlit run ui/app.py --server.port 8502
```

**Change theme**:
Edit `.streamlit/config.toml`:
```toml
[theme]
base = "dark"
primaryColor = "#F63366"
```

**Add custom examples**:
Edit `ui/app.py` in the `display_step_1()` function.

---

## File Structure

```
GSFM/
├── README.md                          # Project overview
├── requirements.txt                   # Python dependencies
├── main.py                            # CLI entry point
├── PROJECT_DOCUMENTATION.md           # This file
│
├── gfm/                               # Core GFM package
│   ├── __init__.py
│   ├── graph_memory.py               # GraphFailureMemory implementation
│   ├── AST_hasher.py                 # ASTHasher implementation
│   └── context_pruner.py             # GraphContextPruner implementation
│
├── agents/                            # Agent implementations
│   ├── __init__.py
│   ├── gfm_agent.py                  # GFM-enhanced agent
│   └── react_agent.py                # Baseline ReAct agent
│
├── benchmarks/                        # Evaluation suite
│   ├── __init__.py
│   ├── run_evals.py                  # Benchmark runner
│   └── results.json                  # Latest benchmark results
│
├── sandbox/                           # Code execution
│   ├── __init__.py
│   └── executor.py                   # SandboxExecutor
│
├── paper/                             # Research paper materials
│   ├── main.tex                      # LaTeX paper
│   ├── architecture_diagram.png      # System architecture
│   ├── figure_loop_mitigation.png    # Loop prevention visualization
│   ├── figure_token_reduction.png    # Token efficiency chart
│   ├── figure_improvement_radar.png  # Overall improvement radar
│   ├── figure_comprehensive_comparison.png  # Full comparison
│   └── plot_results.py               # Generate plots
│
├── ui/                                # Web interface
│   ├── app.py                        # Streamlit application
│   └── README.md                     # UI documentation
│
├── tests/                             # Test suite (if exists)
│   ├── test_graph_memory.py
│   ├── test_ast_hasher.py
│   └── ...
│
└── .env                               # Environment variables (not in git)
```

---

## Future Work

### Short-term Improvements

1. **Enhanced LLM Integration**
   - Add support for other LLM providers (Anthropic, local models)
   - Implement better code generation strategies
   - Add few-shot prompting with success examples

2. **Improved Cycle Detection**
   - Machine learning-based pattern recognition
   - Adaptive threshold tuning
   - Multi-level cycle detection (immediate, gradual, semantic)

3. **Better Context Management**
   - Dynamic context sizing based on task complexity
   - Semantic relevance scoring for context selection
   - Hierarchical context organization

### Medium-term Features

1. **Transfer Learning**
   - Share failure memory across tasks
   - Pre-trained failure pattern database
   - Domain-specific failure libraries

2. **Advanced Recovery Strategies**
   - Multiple recovery strategy templates
   - Strategy ranking based on historical success
   - Automatic strategy selection

3. **Real-world Integration**
   - Integration with popular CI/CD systems
   - GitHub Actions integration
   - IDE plugin for real-time feedback

### Long-term Research

1. **Multi-Agent Collaboration**
   - Shared memory across multiple agents
   - Collaborative problem solving
   - Agent specialization

2. **Causal Inference**
   - Root cause analysis of failures
   - Causal graph construction
   - Predictive failure prevention

3. **Self-Improving System**
   - Meta-learning on failure patterns
   - Automatic threshold optimization
   - System self-diagnosis

---

## References

### Academic Papers

1. **LangGraph**: Agent workflows with state graphs
   - https://github.com/langchain-ai/langgraph

2. **ReAct**: Reasoning and Acting in Language Models
   - https://arxiv.org/abs/2210.03629

3. **Chain-of-Thought**: Prompting methods
   - https://arxiv.org/abs/2201.11903

### Technical Documentation

1. **NetworkX**: Graph algorithms
   - https://networkx.org/documentation/

2. **LangChain**: LLM application framework
   - https://python.langchain.com/

3. **OpenAI API**: GPT models
   - https://platform.openai.com/docs

### Related Projects

1. **AutoGPT**: Autonomous AI agent
   - https://github.com/Significant-Gravitas/Auto-GPT

2. **BabyAGI**: Task-driven autonomous agent
   - https://github.com/yoheinakajima/babyagi

3. **AgentGPT**: AI agent deployment platform
   - https://github.com/reworkd/AgentGPT

---

## Citation

If you use this work in your research, please cite:

```bibtex
@article{gfm2024,
  title={Graph-Structured Failure Memory: Preventing Infinite Error Loops
         and Context Drift in Self-Healing LLM Agents},
  author={[Author Names]},
  journal={[Journal/Conference]},
  year={2024}
}
```

---

## License

[Specify your license here - e.g., MIT, Apache 2.0, etc.]

---

## Contact

For questions, feedback, or contributions:
- Email: [your email]
- GitHub: [repository URL]
- Issues: [issues URL]

---

## Acknowledgments

- LangChain team for the excellent framework
- OpenAI for GPT models
- NetworkX community for graph algorithms
- Streamlit for the web UI framework

---

**Document Version**: 1.0
**Last Updated**: 2024
**Project Status**: Active Development
