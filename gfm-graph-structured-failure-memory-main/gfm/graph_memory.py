import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import networkx as nx


@dataclass
class FailureEdgeData:
    action: str
    error_type: str
    raw_error: str
    signature: str
    retry_count: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


class GraphFailureMemory:
    """Graph-Structured Failure Memory (GFM) engine.
    
    Tracks agent state transitions, actions, and failures as a directed graph
    to detect execution cycles, prevent infinite error loops, and manage context drift.
    """

    def __init__(self, loop_threshold: int = 2):
        """
        Args:
            loop_threshold: Maximum allowed retries for identical action-error signatures
                           before triggering a cycle detection alert.
        """
        self.graph = nx.DiGraph()
        self.loop_threshold = loop_threshold
        self.current_node: str = "START"
        self.graph.add_node("START", description="Initial Agent State", status="active")

    @staticmethod
    def generate_signature(action: str, error_msg: str) -> str:
        """Generates a deterministic signature by normalizing error strings and actions.
        
        Strips transient noise like timestamps, memory addresses, and variable line numbers.
        """
        # Normalize memory addresses (e.g. 0x7f9a8b2c)
        norm_err = re.sub(r"0x[0-9a-fA-F]+", "<HEX_ADDR>", error_msg)
        # Normalize transient numbers/line numbers
        norm_err = re.sub(r"line \d+", "line <LINE>", norm_err)
        
        composite = f"{action.strip()}||{norm_err.strip()}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()[:10]

    def record_failure(
        self, target_state: str, action: str, error_msg: str, metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """Records an execution failure along a directed edge.

        Args:
            target_state: Label of the intended target node/goal.
            action: Action string or code executed.
            error_msg: Raw error or exception trace returned.
            metadata: Optional dictionary with extra debug data.

        Returns:
            Tuple[is_cycle_detected (bool), edge_signature (str)]
        """
        signature = self.generate_signature(action, error_msg)
        error_type = error_msg.split(":")[0].strip() if ":" in error_msg else "ExecutionError"

        if not self.graph.has_node(target_state):
            self.graph.add_node(target_state, description=target_state, status="pending")

        is_cycle = False
        if self.graph.has_edge(self.current_node, target_state):
            edge_data = self.graph[self.current_node][target_state]
            if edge_data["signature"] == signature:
                edge_data["retry_count"] += 1
                if edge_data["retry_count"] >= self.loop_threshold:
                    is_cycle = True
            else:
                # Update with new signature if error evolved
                edge_data["signature"] = signature
                edge_data["retry_count"] = 1
                edge_data["raw_error"] = error_msg
                edge_data["action"] = action
        else:
            self.graph.add_edge(
                self.current_node,
                target_state,
                action=action,
                error_type=error_type,
                raw_error=error_msg,
                signature=signature,
                retry_count=1,
                metadata=metadata or {},
            )
            if self.graph[self.current_node][target_state]["retry_count"] >= self.loop_threshold:
                is_cycle = True

        return is_cycle, signature

    def transition_success(self, new_state: str, action_summary: str = ""):
        """Updates the active node state upon successful task step execution."""
        if not self.graph.has_node(new_state):
            self.graph.add_node(new_state, description=action_summary, status="completed")
        else:
            self.graph.nodes[new_state]["status"] = "completed"
        
        self.current_node = new_state

    def get_blocked_actions(self) -> List[Dict[str, Any]]:
        """Returns all action-target pairs that have exceeded the loop threshold."""
        blocked = []
        for u, v, data in self.graph.edges(data=True):
            if data.get("retry_count", 0) >= self.loop_threshold:
                blocked.append({
                    "from": u,
                    "to": v,
                    "action": data["action"],
                    "error_type": data["error_type"],
                    "signature": data["signature"]
                })
        return blocked

    def has_detected_cycles(self) -> bool:
        """Returns True if any edge in the graph exceeds the retry threshold."""
        return len(self.get_blocked_actions()) > 0
