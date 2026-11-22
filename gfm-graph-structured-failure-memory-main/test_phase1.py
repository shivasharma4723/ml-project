"""
Test script for Phase 1 enhancements to GraphFailureMemory
Tests execution states, action hashes, and cycle detection with loop_threshold
"""

from gfm import GraphFailureMemory, StateNode, ActionNode
import hashlib


def test_execution_states():
    """Test storing and tracking execution states."""
    print("Testing Execution States...")
    
    memory = GraphFailureMemory(loop_threshold=3)
    
    # Add some execution states
    state1_data = {"task": "fix_syntax", "step": 1, "context": "initial"}
    state1_hash = hashlib.md5(str(state1_data).encode()).hexdigest()
    state1_id = memory.add_state(state1_hash, state1_data)
    
    state2_data = {"task": "fix_syntax", "step": 2, "context": "analyzing"}
    state2_hash = hashlib.md5(str(state2_data).encode()).hexdigest()
    state2_id = memory.add_state(state2_hash, state2_data)
    
    # Visit the same state again
    memory.add_state(state1_hash, state1_data)
    
    # Check visit counts
    assert memory.get_state_visit_count(state1_hash) == 2, "State 1 should have 2 visits"
    assert memory.get_state_visit_count(state2_hash) == 1, "State 2 should have 1 visit"
    
    print(f"✓ State 1 visited {memory.get_state_visit_count(state1_hash)} times")
    print(f"✓ State 2 visited {memory.get_state_visit_count(state2_hash)} times")
    print("✓ Execution states test passed!\n")


def test_action_hashes_and_edges():
    """Test action hash storage and edge visit tracking."""
    print("Testing Action Hashes and Edge Tracking...")
    
    memory = GraphFailureMemory(loop_threshold=3)
    
    # Add states
    state1_hash = "state_abc"
    state2_hash = "state_def"
    memory.add_state(state1_hash, {"step": 1})
    memory.add_state(state2_hash, {"step": 2})
    
    # Add actions
    action1_hash = "action_123"
    action1_id = memory.add_action(action1_hash, "code_execution", "Fix syntax", {}, "success")
    
    action2_hash = "action_456"
    action2_id = memory.add_action(action2_hash, "api_call", "Get data", {}, "failure")
    
    # Add edges between nodes
    state1_id = f"state_{state1_hash}"
    state2_id = f"state_{state2_hash}"
    
    memory.add_edge(state1_id, action1_id, "executes")
    memory.add_edge(action1_id, state2_id, "leads_to")
    
    # Traverse the same edge multiple times to test threshold
    for _ in range(4):
        memory.add_edge(state1_id, action1_id, "executes")
    
    # Check edge visit counts
    edge_count = memory.get_edge_visit_count(state1_id, action1_id)
    print(f"✓ Edge {state1_id} -> {action1_id} visited {edge_count} times")
    
    # Test cycle detection by threshold
    is_cycle = memory.detect_cycle_by_edge_threshold(state1_id, action1_id)
    print(f"✓ Cycle detection for edge (threshold=3): {is_cycle}")
    assert is_cycle, "Should detect cycle when edge exceeds threshold"
    
    # Check action execution count
    action_node = memory.action_index[action1_id]
    print(f"✓ Action executed {action_node.execution_count} times")
    
    print("✓ Action hashes and edge tracking test passed!\n")


def test_cycle_detection():
    """Test cycle detection in the graph."""
    print("Testing Cycle Detection...")
    
    memory = GraphFailureMemory(loop_threshold=2)
    
    # Create a cycle: state1 -> action1 -> state2 -> action2 -> state1
    state1_hash = "s1"
    state2_hash = "s2"
    action1_hash = "a1"
    action2_hash = "a2"
    
    memory.add_state(state1_hash, {"step": 1})
    memory.add_state(state2_hash, {"step": 2})
    memory.add_action(action1_hash, "exec", "Action 1", {}, "success")
    memory.add_action(action2_hash, "exec", "Action 2", {}, "success")
    
    s1_id = f"state_{state1_hash}"
    s2_id = f"state_{state2_hash}"
    a1_id = f"action_{action1_hash}"
    a2_id = f"action_{action2_hash}"
    
    # Create cycle edges
    memory.add_edge(s1_id, a1_id)
    memory.add_edge(a1_id, s2_id)
    memory.add_edge(s2_id, a2_id)
    memory.add_edge(a2_id, s1_id)
    
    # Detect cycles in graph
    cycles = memory.detect_cycles_in_graph()
    print(f"✓ Detected {len(cycles)} cycle(s) in graph")
    
    if cycles:
        print(f"✓ Cycle path: {cycles[0]}")
    
    # Test edge threshold detection
    # Traverse one edge multiple times
    for _ in range(3):
        memory.add_edge(s1_id, a1_id)
    
    is_threshold_exceeded = memory.detect_cycle_by_edge_threshold(s1_id, a1_id)
    print(f"✓ Edge threshold exceeded (threshold=2): {is_threshold_exceeded}")
    assert is_threshold_exceeded, "Should detect threshold exceeded"
    
    print("✓ Cycle detection test passed!\n")


def test_enhanced_statistics():
    """Test enhanced statistics with Phase 1 features."""
    print("Testing Enhanced Statistics...")
    
    memory = GraphFailureMemory(loop_threshold=3)
    
    # Add various nodes
    memory.add_state("s1", {"data": "test"})
    memory.add_state("s2", {"data": "test2"})
    memory.add_action("a1", "exec", "Test action", {}, "success")
    memory.add_action("a2", "exec", "Test action 2", {}, "failure")
    
    # Add edges
    s1_id = "state_s1"
    a1_id = "action_a1"
    memory.add_edge(s1_id, a1_id)
    
    # Get statistics
    stats = memory.get_failure_statistics()
    
    print(f"✓ Total states: {stats['total_states']}")
    print(f"✓ Total actions: {stats['total_actions']}")
    print(f"✓ Unique actions: {stats['unique_actions']}")
    print(f"✓ Loop threshold: {stats['loop_threshold']}")
    print(f"✓ Edges exceeding threshold: {stats['edges_exceeding_threshold']}")
    
    assert stats['total_states'] == 2, "Should have 2 states"
    assert stats['total_actions'] == 2, "Should have 2 total actions"
    assert stats['unique_actions'] == 2, "Should have 2 unique actions"
    
    print("✓ Enhanced statistics test passed!\n")


def main():
    """Run all Phase 1 tests."""
    print("=" * 60)
    print("PHASE 1: Enhanced Graph Memory Testing")
    print("=" * 60 + "\n")
    
    test_execution_states()
    test_action_hashes_and_edges()
    test_cycle_detection()
    test_enhanced_statistics()
    
    print("=" * 60)
    print("All Phase 1 tests passed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
