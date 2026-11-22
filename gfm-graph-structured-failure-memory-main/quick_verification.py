from gfm.graph_memory import GraphFailureMemory
from gfm.context_pruner import GraphContextPruner

memory = GraphFailureMemory(loop_threshold=2)
pruner = GraphContextPruner()

# Simulate a repeating database error
action_sql = "db.query('SELECT * FROM user_data')"
err_sql = "DatabaseError: Connection pool exhausted at 0x7f9a8b2c line 42"

# Attempt 1
is_cycle, sig = memory.record_failure("FetchData", action_sql, err_sql)
print(f"Attempt 1 - Cycle Detected: {is_cycle}")

# Attempt 2 (Triggers Cycle Breaker)
is_cycle, sig = memory.record_failure("FetchData", action_sql, err_sql)
print(f"Attempt 2 - Cycle Detected: {is_cycle}")

# Generate Pruned Context for LLM
print("\n" + pruner.summarize_graph_for_llm(memory))
