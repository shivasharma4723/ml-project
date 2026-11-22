from typing import Dict, Any, List
import networkx as nx
from gfm.graph_memory import GraphFailureMemory


class GraphContextPruner:
    """Prunes bloated error logs and stack traces into a compact, structured
    graph traversal prompt summary to mitigate context drift in LLMs.
    """

    def __init__(self, max_raw_error_chars: int = 150):
        self.max_raw_error_chars = max_raw_error_chars

    def summarize_graph_for_llm(self, gfm_engine: GraphFailureMemory) -> str:
        """Adaptive graph serializer: ultra-compact on single failures, explicit cycle-breaker on loops."""
        graph = gfm_engine.graph
        if graph.number_of_edges() == 0:
            return "State: START (No prior failures)."

        blocked_actions = gfm_engine.get_blocked_actions()
        lines = []

        # Compact edge summary (strips verbose stack frames and boilerplate)
        for u, v, data in graph.edges(data=True):
            if data.get("edge_kind", "FAILURE") != "FAILURE":
                continue
            err_type = data.get("error_type", "Error")
            raw_err = data.get("raw_error", "").strip().splitlines()[-1] if data.get("raw_error") else ""
            short_err = raw_err[:80]
            sig = data.get("signature", "")
            retries = data.get("retry_count", 1)
            lines.append(f"• [{err_type}] {short_err} (sig:{sig}, tries:{retries})")

        if blocked_actions:
            lines.append("\n⛔ CYCLE DETECTED — DO NOT REPEAT:")
            for b in blocked_actions:
                lines.append(f"  - Blocked pattern `{b['signature']}` ({b['error_type']}): use a completely different fix strategy.")

        return "\n".join(lines)

    def extract_token_savings_estimate(self, raw_history_text: str, pruned_context_text: str) -> Dict[str, float]:
        """Provides an estimated token reduction ratio comparing raw execution traces
        against the pruned graph output.
        """
        raw_tokens = len(raw_history_text) / 4.0
        pruned_tokens = len(pruned_context_text) / 4.0
        reduction_pct = ((raw_tokens - pruned_tokens) / raw_tokens * 100) if raw_tokens > 0 else 0.0

        return {
            "est_raw_tokens": round(raw_tokens, 1),
            "est_pruned_tokens": round(pruned_tokens, 1),
            "token_reduction_pct": round(reduction_pct, 2),
        }