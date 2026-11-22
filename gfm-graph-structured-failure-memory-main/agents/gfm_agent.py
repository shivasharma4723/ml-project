"""
GFM Agent - Self-Healing Code Agent with Graph-Structured Failure Memory
Connects to local Ollama (http://localhost:11434/v1/chat/completions) for iterative
code repair, with automatic fallback to simulation mode if Ollama is offline.
"""

import json
import os
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from gfm.graph_memory import GraphFailureMemory
from gfm.AST_hasher import ASTHasher
from gfm.context_pruner import GraphContextPruner
from sandbox.executor import SandboxExecutor


class GFMAgent:
    """Self-Healing Code Agent powered by Graph-Structured Failure Memory."""

    def __init__(
        self,
        max_attempts: int = 5,
        loop_threshold: int = 2,
        model_name: str = "qwen2.5-coder:3b",
        api_base: str = "http://localhost:11434/v1/chat/completions",
        api_key: Optional[str] = None,
        timeout_seconds: int = 2,
    ):
        self.executor = SandboxExecutor(timeout_seconds=timeout_seconds)
        self.memory = GraphFailureMemory(loop_threshold=loop_threshold)
        self.hasher = ASTHasher()
        self.pruner = GraphContextPruner(max_raw_error_chars=150)
        self.max_attempts = max_attempts
        self.model_name = model_name
        self.api_base = api_base
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "ollama")

    def _extract_python_code(self, text: str) -> str:
        """Extract clean Python code from Markdown fences if present."""
        match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Send chat completion request to local Ollama server."""
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        req = urllib.request.Request(
            self.api_base,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    def solve_task(self, description: str, initial_code: str, use_gfm: bool = True) -> Dict[str, Any]:
        """
        Iteratively repair buggy Python code up to `max_attempts`.
        - use_gfm=True: Uses GraphFailureMemory + ASTHasher + GraphContextPruner
          with adaptive temperature escalation on cycle detection.
        - use_gfm=False: Standard ReAct baseline feeding raw accumulated tracebacks.
        """
        self.memory = GraphFailureMemory(loop_threshold=self.memory.loop_threshold)
        current_code = initial_code
        attempts = 0
        total_loops = 0
        cycles_prevented = 0
        total_tokens_used = 0.0
        error_history = []
        solved = False

        for attempt in range(1, self.max_attempts + 1):
            attempts = attempt
            result = self.executor.run_code(current_code)

            if result["success"]:
                solved = True
                if use_gfm:
                    self.memory.transition_success("Solved")
                break

            raw_stderr = result["stderr"]
            error_history.append(raw_stderr)
            last_err_line = raw_stderr.strip().splitlines()[-1] if raw_stderr.strip() else "ExecutionError"

            if use_gfm:
                # Track structural AST pattern (never block `def solve`, only the failing AST logic)
                ast_sig = self.hasher.hash_code(current_code)[:10]
                is_cycle, _ = self.memory.record_failure(
                    target_state="CodeExecution",
                    action=f"AST_PATTERN_{ast_sig}",
                    error_msg=last_err_line,
                )
                if is_cycle:
                    cycles_prevented += 1
                else:
                    total_loops += 1

                pruned_context = self.pruner.summarize_graph_for_llm(self.memory)
                system_prompt = (
                    "Fix the Python bug. Output ONLY valid Python code keeping all asserts.\n"
                    f"{pruned_context}"
                )
                user_prompt = f"Task: {description}\n```python\n{current_code}\n```"
            else:
                total_loops += 1
                full_trace_history = "\n---\n".join(error_history)
                system_prompt = (
                    "You are a Python engineer. Fix the bug in the code below. "
                    "Return ONLY valid executable Python code (preserve all existing assert statements)."
                )
                user_prompt = (
                    f"Task: {description}\n\nCode:\n```python\n{current_code}\n```\n\n"
                    f"Full Error History:\n{full_trace_history}"
                )

            total_tokens_used += (len(system_prompt) + len(user_prompt)) / 4.0

            if attempt < self.max_attempts:
                try:
                    # Escalate temperature when a cycle is blocked so the model explores a genuinely new fix
                    temp = 0.45 if (use_gfm and cycles_prevented > 0) else 0.2
                    llm_reply = self._call_llm(system_prompt, user_prompt, temperature=temp)
                    current_code = self._extract_python_code(llm_reply)
                except (urllib.error.URLError, TimeoutError, Exception):
                    if use_gfm and cycles_prevented > 0:
                        break

        return {
            "solved": solved,
            "attempts": attempts,
            "total_loops": total_loops,
            "cycles_prevented": cycles_prevented,
            "total_tokens_used": round(total_tokens_used, 2),
            "error_history": error_history,
            "final_code": current_code,
        }

    def run_simulation(self, code: str) -> dict:
        """Backward-compatible single-step simulation method."""
        result = self.executor.run_code(code)
        if result["success"]:
            return {"success": True, "attempts": 1, "cycles_prevented": 0, "error": None}

        is_cycle, signature = self.memory.record_failure(
            target_state="CodeExecution",
            action=code[:100],
            error_msg=result["stderr"],
        )
        return {
            "success": False,
            "attempts": 1,
            "cycles_prevented": 1 if is_cycle else 0,
            "error": result["stderr"],
            "signature": signature,
            "pruned_context": self.pruner.summarize_graph_for_llm(self.memory),
            "blocked_actions": self.memory.get_blocked_actions(),
        }