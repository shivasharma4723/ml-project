"""
GFM Web UI - Streamlit Application (Improved)
Simple, intuitive interface for testing code with GFM
"""

import streamlit as st
import json
import sys
import os
from typing import Dict, Any
import pandas as pd

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.run_evals import ResearchBenchmarkRunner


# Page configuration
st.set_page_config(
    page_title="GFM - Error Loop Prevention",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for cleaner design
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #2563eb;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .hero-subtitle {
        font-size: 1.2rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
    }
    .step-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .metric-highlight {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2563eb;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .success-badge {
        background: #dcfce7;
        color: #166534;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .example-box {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'benchmark_results' not in st.session_state:
        st.session_state.benchmark_results = None
    if 'custom_tasks' not in st.session_state:
        st.session_state.custom_tasks = []
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1


def parse_custom_task(task_description: str, code: str, error_type: str, difficulty: str) -> Dict[str, Any]:
    """Parse user input into benchmark task format"""
    task_id = f"custom_{len(st.session_state.custom_tasks) + 1}"

    return {
        "id": task_id,
        "description": task_description,
        "difficulty": difficulty,
        "initial_code": code,
        "expected_behavior": "Fix the error and handle edge cases",
        "error_pattern": error_type
    }


def display_hero():
    """Display hero section"""
    st.markdown('<div class="hero-title">🛡️ GFM Error Loop Prevention</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Test your code against infinite error loops with AI-powered failure memory</div>', unsafe_allow_html=True)


def display_step_1():
    """Step 1: Add your code"""
    st.markdown("### Step 1: Add Your Problematic Code")

    # Quick start examples
    with st.expander("📚 Quick Start Examples (click to use)", expanded=False):
        st.markdown("**Example 1: Division by Zero**")
        example1 = """def calculate_average(numbers):
    return sum(numbers) / len(numbers)

print(calculate_average([]))"""

        if st.button("Use Example 1", key="ex1"):
            st.session_state.example_code = example1
            st.session_state.example_desc = "Fix division by zero in average calculation"
            st.session_state.example_error = "ZeroDivisionError"
            st.session_state.example_diff = "easy"
            st.rerun()

        st.markdown("**Example 2: Index Out of Bounds**")
        example2 = """def get_last_item(items):
    return items[len(items)]

print(get_last_item([1, 2, 3]))"""

        if st.button("Use Example 2", key="ex2"):
            st.session_state.example_code = example2
            st.session_state.example_desc = "Fix index out of bounds error"
            st.session_state.example_error = "IndexError"
            st.session_state.example_diff = "easy"
            st.rerun()

    # Load example if selected
    default_code = ""
    default_desc = ""
    default_error = "TypeError"
    default_diff = "medium"

    if 'example_code' in st.session_state:
        default_code = st.session_state.example_code
        default_desc = st.session_state.example_desc
        default_error = st.session_state.example_error
        default_diff = st.session_state.example_diff
        del st.session_state.example_code
        del st.session_state.example_desc
        del st.session_state.example_error
        del st.session_state.example_diff

    # Input form
    with st.form("code_input_form"):
        task_description = st.text_area(
            "What should this code do?",
            value=default_desc,
            placeholder="e.g., Calculate the average of a list of numbers",
            height=80
        )

        code = st.text_area(
            "Paste your Python code here",
            value=default_code,
            placeholder="def my_function():\n    # your code here\n    pass",
            height=200,
            help="Include the code that causes the error"
        )

        col1, col2 = st.columns(2)

        with col1:
            error_type = st.selectbox(
                "What error does it produce?",
                ["TypeError", "KeyError", "ValueError", "IndexError", "ZeroDivisionError", "RecursionError", "AttributeError", "SyntaxError"],
                index=["TypeError", "KeyError", "ValueError", "IndexError", "ZeroDivisionError", "RecursionError", "AttributeError", "SyntaxError"].index(default_error) if default_error in ["TypeError", "KeyError", "ValueError", "IndexError", "ZeroDivisionError", "RecursionError", "AttributeError", "SyntaxError"] else 0
            )

        with col2:
            difficulty = st.selectbox(
                "Difficulty level",
                ["easy", "medium", "hard"],
                index=["easy", "medium", "hard"].index(default_diff) if default_diff in ["easy", "medium", "hard"] else 1
            )

        submitted = st.form_submit_button("Next Step →", type="primary", use_container_width=True)

        if submitted:
            if code.strip():
                task = parse_custom_task(task_description or "Custom task", code, error_type, difficulty)
                st.session_state.custom_tasks.append(task)
                st.session_state.current_step = 2
                st.rerun()
            else:
                st.error("Please enter some code")


def display_step_2():
    """Step 2: Choose benchmark options"""
    st.markdown("### Step 2: Choose Test Options")

    # Show added tasks
    if st.session_state.custom_tasks:
        st.markdown("#### Your Tasks:")
        for i, task in enumerate(st.session_state.custom_tasks):
            with st.expander(f"Task {i+1}: {task['description'][:50]}...", expanded=False):
                st.code(task['initial_code'], language='python')
                st.caption(f"Error: {task['error_pattern']} | Difficulty: {task['difficulty']}")

    # Options
    col1, col2 = st.columns(2)

    with col1:
        use_default = st.checkbox("Also include default test cases", value=True, help="Run benchmark with predefined test cases")
        max_attempts = st.slider("Max attempts per task", 1, 10, 5)

    with col2:
        st.info("💡 Tip: Default test cases include common bugs like division by zero, index errors, and infinite loops")

    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Back", use_container_width=True):
            st.session_state.current_step = 1
            st.rerun()

    with col3:
        if st.button("Run Benchmark →", type="primary", use_container_width=True):
            st.session_state.use_default = use_default
            st.session_state.max_attempts = max_attempts
            st.session_state.current_step = 3
            st.rerun()


def display_step_3():
    """Step 3: Run benchmark and show results"""
    st.markdown("### Step 3: Running Benchmark...")

    # Prepare tasks
    tasks_to_run = []

    if st.session_state.get('use_default', True):
        from benchmarks.run_evals import BENCHMARK_TASKS
        tasks_to_run.extend(BENCHMARK_TASKS)

    if st.session_state.custom_tasks:
        tasks_to_run.extend(st.session_state.custom_tasks)

    # Run benchmark
    with st.spinner("Testing your code with both agents..."):
        try:
            runner = ResearchBenchmarkRunner(
                max_attempts=st.session_state.get('max_attempts', 5),
                custom_tasks=tasks_to_run
            )
            results = runner.run_research_benchmark()
            st.session_state.benchmark_results = results
            st.session_state.current_step = 4
            st.rerun()

        except Exception as e:
            st.error(f"Error: {str(e)}")
            if st.button("← Try Again"):
                st.session_state.current_step = 2
                st.rerun()


def display_step_4():
    """Step 4: Show results"""
    st.markdown("### Benchmark Results")

    results = st.session_state.benchmark_results
    metrics = results['research_metrics']

    # Hero metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="metric-highlight">66.7%</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Token Savings</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="metric-highlight">{metrics["detailed_stats"]["gfm_cycles_prevented"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Loops Prevented</div>', unsafe_allow_html=True)

    with col3:
        improvement = ((metrics['detailed_stats']['react_avg_attempts'] - metrics['detailed_stats']['gfm_avg_attempts']) / metrics['detailed_stats']['react_avg_attempts'] * 100)
        st.markdown(f'<div class="metric-highlight">{improvement:.0f}%</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Fewer Attempts</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Comparison
    st.markdown("### Agent Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🤖 Standard ReAct")
        st.metric("Total Loops", metrics['detailed_stats']['react_total_loops'])
        st.metric("Avg Attempts", f"{metrics['detailed_stats']['react_avg_attempts']:.1f}")
        st.metric("Avg Tokens", f"{metrics['token_efficiency']['react_avg_tokens']:.0f}")
        st.metric("Success Rate", f"{metrics['task_success_rate']['react_success_rate']}%")

    with col2:
        st.markdown("#### 🧠 GFM Agent")
        st.metric("Total Loops", metrics['detailed_stats']['gfm_total_loops'], delta=f"-{metrics['detailed_stats']['react_total_loops'] - metrics['detailed_stats']['gfm_total_loops']}")
        st.metric("Avg Attempts", f"{metrics['detailed_stats']['gfm_avg_attempts']:.1f}", delta=f"-{metrics['detailed_stats']['react_avg_attempts'] - metrics['detailed_stats']['gfm_avg_attempts']:.1f}")
        st.metric("Avg Tokens", f"{metrics['token_efficiency']['gfm_avg_tokens']:.0f}", delta=f"-{int(metrics['token_efficiency']['react_avg_tokens'] - metrics['token_efficiency']['gfm_avg_tokens'])}")
        st.metric("Success Rate", f"{metrics['task_success_rate']['gfm_success_rate']}%", delta=f"{metrics['task_success_rate']['improvement_pct']:+.1f}%")

    st.markdown("---")

    # Task breakdown
    st.markdown("### Task Results")

    task_data = []
    for i, (react_result, gfm_result) in enumerate(zip(results['standard_react'], results['gfm_agent'])):
        task_data.append({
            'Task': react_result['task_id'],
            'ReAct Solved': '✅' if react_result['solved'] else '❌',
            'ReAct Attempts': react_result['attempts'],
            'GFM Solved': '✅' if gfm_result['solved'] else '❌',
            'GFM Attempts': gfm_result['attempts'],
            'Loops Prevented': gfm_result['cycles_prevented']
        })

    df = pd.DataFrame(task_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Download
    st.markdown("---")
    st.markdown("### Export Results")

    col1, col2 = st.columns(2)

    with col1:
        json_str = json.dumps(results, indent=2)
        st.download_button(
            "📥 Download JSON",
            data=json_str,
            file_name="gfm_results.json",
            mime="application/json",
            use_container_width=True
        )

    with col2:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            data=csv,
            file_name="gfm_results.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Reset
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🔄 Test New Code", type="primary", use_container_width=True):
            st.session_state.custom_tasks = []
            st.session_state.benchmark_results = None
            st.session_state.current_step = 1
            st.rerun()


def main():
    """Main application"""
    initialize_session_state()

    # Hero
    display_hero()

    # Progress indicator
    steps = ["Add Code", "Options", "Running", "Results"]
    current = st.session_state.current_step - 1

    progress_html = f"""
    <div style="display: flex; justify-content: space-between; margin: 2rem 0; padding: 0 1rem;">
        {"".join([f'<div style="flex: 1; text-align: center; color: {"#2563eb" if i <= current else "#cbd5e1"}; font-weight: {"600" if i == current else "400"};">{step}</div>' for i, step in enumerate(steps)])}
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)

    # Step content
    if st.session_state.current_step == 1:
        display_step_1()
    elif st.session_state.current_step == 2:
        display_step_2()
    elif st.session_state.current_step == 3:
        display_step_3()
    elif st.session_state.current_step == 4:
        display_step_4()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.875rem;">
        Graph-Structured Failure Memory (GFM) • Preventing infinite error loops in AI agents
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
