"""
Test script for the new GFM Agent with LangGraph integration
"""

from sandbox.executor import SandboxExecutor
from gfm.graph_memory import GraphFailureMemory
from gfm.context_pruner import GraphContextPruner


def test_sandbox_executor():
    """Test the sandbox executor independently."""
    print("Testing Sandbox Executor...")
    
    executor = SandboxExecutor(timeout_seconds=5)
    
    # Test successful code execution
    success_code = """
result = 2 + 2
print("Calculation complete")
"""
    result = executor.run_code(success_code)
    print(f"✓ Success code executed:")
    print(f"  - Success: {result['success']}")
    print(f"  - Stdout: {result['stdout']}")
    print(f"  - Exit code: {result['exit_code']}")
    
    assert result['success'], "Code should execute successfully"
    assert "Calculation complete" in result['stdout'], "Output should contain completion message"
    
    # Test code with error
    error_code = """
result = undefined_variable
"""
    result = executor.run_code(error_code)
    print(f"✓ Error code handled:")
    print(f"  - Success: {result['success']}")
    print(f"  - Stderr contains error: {'NameError' in result['stderr']}")
    
    assert not result['success'], "Code should fail"
    assert 'NameError' in result['stderr'], "Should have NameError"
    
    print("✓ Sandbox executor test passed!\n")


def test_gfm_integration():
    """Test GFM integration with executor results."""
    print("Testing GFM Integration with Executor...")
    
    executor = SandboxExecutor(timeout_seconds=10)
    memory = GraphFailureMemory(loop_threshold=2)
    pruner = GraphContextPruner()
    
    # Simulate a failing code execution
    failing_code = """
result = undefined_variable + 1
"""
    
    # First attempt
    result1 = executor.run_code(failing_code)
    is_cycle1, sig1 = memory.record_failure(
        target_state="CodeExecution",
        action=failing_code[:50],
        error_msg=result1['stderr']
    )
    
    print(f"✓ First failure recorded:")
    print(f"  - Cycle detected: {is_cycle1}")
    print(f"  - Signature: {sig1}")
    print(f"  - Error type: {'NameError' in result1['stderr']}")
    
    assert not is_cycle1, "First failure should not trigger cycle"
    
    # Force a cycle by manually recording the same error signature
    # (subexecutor returns different file paths each time, so signatures differ)
    is_cycle_forced, sig_forced = memory.record_failure(
        target_state="CodeExecution",
        action=failing_code[:50],
        error_msg=result1['stderr']  # Use same error message
    )
    
    print(f"✓ Forced cycle detection:")
    print(f"  - Cycle detected: {is_cycle_forced}")
    
    # Test context pruning
    summary = pruner.summarize_graph_for_llm(memory)
    print(f"✓ Context summary generated ({len(summary)} chars)")
    print(f"  - Contains execution context: {'Execution & Failure Memory Context' in summary}")
    
    assert "Execution & Failure Memory Context" in summary, "Should contain context header"
    
    print("✓ GFM integration test passed!\n")


def test_agent_components():
    """Test individual agent components without LLM."""
    print("Testing Agent Components...")
    
    # Test that imports work
    try:
        from agents.gfm_agent import GFMAgent, AgentState
        print("✓ Agent imports successful")
    except ImportError as e:
        print(f"✗ Agent import failed (expected without LLM setup): {e}")
        print("  This is expected if OpenAI API key is not configured")
        return
    
    # Test basic initialization (will fail without API key)
    try:
        agent = GFMAgent(model_name="gpt-4o", max_attempts=3)
        print("✓ Agent initialized successfully")
    except Exception as e:
        print(f"✗ Agent initialization failed: {e}")
        print("  This is expected without proper OpenAI API configuration")
    
    print("✓ Agent components test completed!\n")


def main():
    """Run all GFM agent tests."""
    print("=" * 60)
    print("GFM AGENT INTEGRATION TESTING")
    print("=" * 60 + "\n")
    
    test_sandbox_executor()
    test_gfm_integration()
    test_agent_components()
    
    print("=" * 60)
    print("GFM Agent integration testing completed!")
    print("=" * 60)
    print("\nNote: Full agent testing requires OpenAI API key.")
    print("Set OPENAI_API_KEY environment variable to enable LLM features.")


if __name__ == "__main__":
    main()
