"""
Test script for production GFM implementations
Tests the new GraphFailureMemory and GraphContextPruner
"""

from gfm import GraphFailureMemory, GraphContextPruner


def test_production_graph_memory():
    """Test the production GraphFailureMemory implementation."""
    print("Testing Production GraphFailureMemory...")
    
    gfm = GraphFailureMemory(loop_threshold=2)
    
    # Test signature generation
    action = "fix_syntax"
    error_msg = "SyntaxError: invalid syntax at line 42"
    signature = gfm.generate_signature(action, error_msg)
    print(f"✓ Generated signature: {signature}")
    
    # Test recording failures
    is_cycle, sig = gfm.record_failure("FIXED_STATE", action, error_msg)
    print(f"✓ First failure recorded - Cycle detected: {is_cycle}")
    
    # Record same failure again (should trigger cycle)
    is_cycle, sig = gfm.record_failure("FIXED_STATE", action, error_msg)
    print(f"✓ Second failure recorded - Cycle detected: {is_cycle}")
    assert is_cycle, "Should detect cycle after threshold exceeded"
    
    # Test successful transition
    gfm.transition_success("COMPLETED_STATE", "Task completed successfully")
    print(f"✓ State transition successful - Current node: {gfm.current_node}")
    
    # Test blocked actions
    blocked = gfm.get_blocked_actions()
    print(f"✓ Blocked actions: {len(blocked)}")
    assert len(blocked) > 0, "Should have blocked actions"
    
    # Test cycle detection
    has_cycles = gfm.has_detected_cycles()
    print(f"✓ Has detected cycles: {has_cycles}")
    assert has_cycles, "Should have detected cycles"
    
    print("✓ Production GraphFailureMemory test passed!\n")


def test_production_context_pruner():
    """Test the production GraphContextPruner implementation."""
    print("Testing Production GraphContextPruner...")
    
    gfm = GraphFailureMemory(loop_threshold=2)
    pruner = GraphContextPruner(max_raw_error_chars=50)
    
    # Add some failures to the graph
    gfm.record_failure("STATE_A", "action1", "Error: Something went wrong at line 123")
    gfm.record_failure("STATE_A", "action1", "Error: Something went wrong at line 123")
    gfm.record_failure("STATE_B", "action2", "TypeError: invalid type at line 456")
    
    # Test summarization
    summary = pruner.summarize_graph_for_llm(gfm)
    print(f"✓ Generated summary ({len(summary)} chars)")
    print(f"  Summary preview: {summary[:100]}...")
    
    assert "Execution & Failure Memory Context" in summary, "Should contain context header"
    assert "Pruned Attempt History" in summary, "Should contain attempt history"
    assert "BLOCKED ACTION PATHWAYS" in summary, "Should contain blocked actions warning"
    
    # Test token savings estimate
    raw_text = "This is a very long error message that would normally take many tokens " * 10
    pruned_text = "Compressed error message..."
    savings = pruner.extract_token_savings_estimate(raw_text, pruned_text)
    
    print(f"✓ Token savings estimate:")
    print(f"  - Raw tokens: {savings['est_raw_tokens']}")
    print(f"  - Pruned tokens: {savings['est_pruned_tokens']}")
    print(f"  - Reduction: {savings['token_reduction_pct']}%")
    
    assert savings['token_reduction_pct'] > 0, "Should show token reduction"
    
    print("✓ Production GraphContextPruner test passed!\n")


def test_signature_normalization():
    """Test that signature generation normalizes transient data."""
    print("Testing Signature Normalization...")
    
    gfm = GraphFailureMemory()
    
    # Test memory address normalization
    action = "execute_code"
    error1 = "Error at 0x7f9a8b2c: invalid syntax"
    error2 = "Error at 0x12345678: invalid syntax"
    
    sig1 = gfm.generate_signature(action, error1)
    sig2 = gfm.generate_signature(action, error2)
    
    print(f"✓ Memory address normalization:")
    print(f"  - Error 1 signature: {sig1}")
    print(f"  - Error 2 signature: {sig2}")
    assert sig1 == sig2, "Should normalize memory addresses"
    
    # Test line number normalization
    error3 = "Error at line 42: invalid syntax"
    error4 = "Error at line 99: invalid syntax"
    
    sig3 = gfm.generate_signature(action, error3)
    sig4 = gfm.generate_signature(action, error4)
    
    print(f"✓ Line number normalization:")
    print(f"  - Error 3 signature: {sig3}")
    print(f"  - Error 4 signature: {sig4}")
    assert sig3 == sig4, "Should normalize line numbers"
    
    print("✓ Signature normalization test passed!\n")


def main():
    """Run all production tests."""
    print("=" * 60)
    print("PRODUCTION GFM IMPLEMENTATION TESTING")
    print("=" * 60 + "\n")
    
    test_production_graph_memory()
    test_production_context_pruner()
    test_signature_normalization()
    
    print("=" * 60)
    print("All production tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
