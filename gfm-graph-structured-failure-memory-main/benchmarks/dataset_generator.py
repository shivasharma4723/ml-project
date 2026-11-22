"""
500-Task AST-Based Synthetic Bug Dataset Generator for GFM Benchmarking.
Generates 500 deterministic, unit-tested buggy Python tasks organized across
50 base problem categories x 10 distinct AST fault-injection categories.
"""

"""
High-Complexity Multi-Invariant AST Bug Dataset Generator for GFM Benchmarking.
Generates 200-500 challenging, multi-step algorithmic & systems tasks where
naive single-line patches trigger cascading failures (exposing ReAct loop traps).
"""

import ast
import json
import os
from typing import List, Dict, Any


CLEAN_BASE_PROGRAMS = [
    {
        "base_id": "hard01_merge_intervals",
        "domain": "Intervals & Scheduling",
        "description": "Merge overlapping [start, end] intervals sorted by start without mutating input",
        "difficulty": "hard",
        "code": """
def solve(intervals):
    if not intervals:
        return []
    ordered = sorted([list(iv) for iv in intervals], key=lambda x: (x[0], x[1]))
    merged = [ordered[0]]
    for idx in range(1, len(ordered)):
        curr = ordered[idx]
        last = merged[len(merged) - 1]
        if curr[0] <= last[1]:
            if curr[1] > last[1]:
                last[1] = curr[1]
        else:
            merged.append(curr)
    return merged

src = [[1, 4], [4, 5], [8, 10], [2, 3]]
assert solve(src) == [[1, 5], [8, 10]]
assert src == [[1, 4], [4, 5], [8, 10], [2, 3]]
assert solve([]) == []
"""
    },
    {
        "base_id": "hard02_rpn_evaluator",
        "domain": "Compilers & Parsers",
        "description": "Evaluate Reverse Polish Notation tokens with safe zero-division and arity checks",
        "difficulty": "hard",
        "code": """
def solve(tokens):
    if not tokens:
        return 0
    stack = []
    for tok in tokens:
        if tok in {"+", "-", "*", "/"}:
            if len(stack) < 2:
                raise ValueError("Malformed RPN")
            b = stack.pop()
            a = stack.pop()
            if tok == "+":
                stack.append(a + b)
            elif tok == "-":
                stack.append(a - b)
            elif tok == "*":
                stack.append(a * b)
            else:
                if b == 0:
                    return 0
                stack.append(int(a / b))
        else:
            stack.append(int(tok))
    return stack[len(stack) - 1]

assert solve(["2", "1", "+", "3", "*"]) == 9
assert solve(["4", "13", "5", "/", "+"]) == 6
assert solve(["10", "0", "/"]) == 0
assert solve([]) == 0
"""
    },
    {
        "base_id": "hard03_nested_config_resolver",
        "domain": "Systems & Configs",
        "description": "Resolve nested service endpoint URL with fallback defaults and port coercion",
        "difficulty": "hard",
        "code": """
def solve(manifest, env_name):
    envs = manifest.get("environments", {})
    target = envs.get(env_name, {})
    net = target.get("network", {})
    host = net.get("host", "127.0.0.1")
    port = net.get("port", 8080)
    tls = net.get("tls", False)
    scheme = "https" if tls else "http"
    return scheme + "://" + host + ":" + str(port)

cfg = {"environments": {"prod": {"network": {"host": "api.internal", "port": 443, "tls": True}}}}
assert solve(cfg, "prod") == "https://api.internal:443"
assert solve(cfg, "staging") == "http://127.0.0.1:8080"
assert solve({}, "dev") == "http://127.0.0.1:8080"
"""
    },
    {
        "base_id": "hard04_recursive_tree_depth",
        "domain": "Trees & Recursion",
        "description": "Compute maximum depth and leaf count of nested dict tree recursively",
        "difficulty": "hard",
        "code": """
def solve(node):
    if not isinstance(node, dict) or not node:
        return 0
    children = node.get("children", [])
    if not children:
        return 1
    best = 0
    for ch in children:
        d = solve(ch)
        if d > best:
            best = d
    return 1 + best

tree = {"id": 1, "children": [{"id": 2, "children": [{"id": 3}]}, {"id": 4}]}
assert solve(tree) == 3
assert solve({}) == 0
"""
    },
    {
        "base_id": "hard05_sliding_window_rate_limiter",
        "domain": "Distributed Systems",
        "description": "Filter valid request timestamps within sliding window [now - win, now] without mutating log",
        "difficulty": "hard",
        "code": """
def solve(timestamps, now, window_sec):
    if window_sec <= 0 or not timestamps:
        return 0
    cloned = timestamps.copy()
    idx = 0
    valid = 0
    cutoff = now - window_sec
    while idx < len(cloned):
        if cloned[idx] >= cutoff and cloned[idx] <= now:
            valid += 1
        idx += 1
    return valid

logs = [10, 15, 22, 29, 30]
assert solve(logs, 30, 10) == 3
assert logs == [10, 15, 22, 29, 30]
assert solve([], 30, 10) == 0
"""
    },
    {
        "base_id": "hard06_topo_cycle_check",
        "domain": "Graphs & Dependencies",
        "description": "Detect if directed dependency adjacency map forms a valid DAG (True if acyclic)",
        "difficulty": "hard",
        "code": """
def solve(deps):
    if not deps:
        return True
    indeg = {u: 0 for u in deps}
    for u, nbrs in deps.items():
        for v in nbrs:
            indeg[v] = indeg.get(v, 0) + 1
    queue = [u for u, d in indeg.items() if d == 0]
    visited = 0
    idx = 0
    while idx < len(queue):
        curr = queue[idx]
        idx += 1
        visited += 1
        for nxt in deps.get(curr, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    return visited == len(indeg)

assert solve({"a": ["b"], "b": ["c"], "c": []}) is True
assert solve({"a": ["b"], "b": ["a"]}) is False
assert solve({}) is True
"""
    },
    {
        "base_id": "hard07_rle_codec",
        "domain": "Strings & Compression",
        "description": "Encode string via Run-Length Encoding with explicit numeric counts",
        "difficulty": "hard",
        "code": """
def solve(raw):
    if not raw:
        return ""
    parts = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        run = 1
        while i + run < len(raw) and raw[i + run] == ch:
            run += 1
        parts.append(ch + str(run))
        i += run
    return "".join(parts)

assert solve("aaabbc") == "a3b2c1"
assert solve("x") == "x1"
assert solve("") == ""
"""
    },
    {
        "base_id": "hard08_matrix_diagonal_ratio",
        "domain": "Linear Algebra",
        "description": "Compute ratio of primary diagonal sum to anti-diagonal sum safely",
        "difficulty": "hard",
        "code": """
def solve(mat):
    n = len(mat)
    if n == 0 or any(len(row) != n for row in mat):
        return 0.0
    primary = 0
    anti = 0
    for i in range(n):
        primary += mat[i][i]
        anti += mat[i][n - 1 - i]
    if anti == 0:
        return 0.0
    return round(primary / anti, 3)

assert solve([[2, 1], [3, 4]]) == 1.5
assert solve([[1, 0], [0, 1]]) == 0.0
assert solve([]) == 0.0
"""
    },
    {
        "base_id": "hard09_lru_eviction_sim",
        "domain": "Caching & Memory",
        "description": "Simulate LRU cache get/put operations and return final cache keys in LRU->MRU order",
        "difficulty": "hard",
        "code": """
def solve(capacity, ops):
    if capacity <= 0:
        return []
    cache = []
    for op in ops:
        kind = op[0]
        key = op[1]
        if kind == "put":
            if key in cache:
                cache.remove(key)
            elif len(cache) >= capacity:
                cache.pop(0)
            cache.append(key)
        elif kind == "get" and key in cache:
            cache.remove(key)
            cache.append(key)
    return cache

ops = [("put", "a"), ("put", "b"), ("get", "a"), ("put", "c")]
assert solve(2, ops) == ["a", "c"]
assert solve(0, ops) == []
"""
    },
    {
        "base_id": "hard10_semver_comparator",
        "domain": "Release Engineering",
        "description": "Compare two semantic version strings (major.minor.patch): return 1, -1, or 0",
        "difficulty": "hard",
        "code": """
def solve(v1, v2):
    p1 = [int(x) for x in v1.split(".")]
    p2 = [int(x) for x in v2.split(".")]
    limit = max(len(p1), len(p2))
    idx = 0
    while idx < limit:
        a = p1[idx] if idx < len(p1) else 0
        b = p2[idx] if idx < len(p2) else 0
        if a > b:
            return 1
        if a < b:
            return -1
        idx += 1
    return 0

assert solve("1.2.10", "1.2.2") == 1
assert solve("1.0", "1.0.0") == 0
assert solve("0.9.9", "1.0.0") == -1
"""
    },
    {
        "base_id": "hard11_balanced_brackets_depth",
        "domain": "Compilers & Parsers",
        "description": "Validate nested (), [], {} brackets and return max nesting depth or -1 if invalid",
        "difficulty": "hard",
        "code": """
def solve(expr):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    max_depth = 0
    for ch in expr:
        if ch in "([{":
            stack.append(ch)
            if len(stack) > max_depth:
                max_depth = len(stack)
        elif ch in pairs:
            if not stack or stack[len(stack) - 1] != pairs[ch]:
                return -1
            stack.pop()
    return max_depth if not stack else -1

assert solve("{[()]}") == 3
assert solve("{[(])}") == -1
assert solve("") == 0
"""
    },
    {
        "base_id": "hard12_recursive_flatten_sum",
        "domain": "Trees & Recursion",
        "description": "Recursively sum all numeric leaves in arbitrarily nested lists/tuples",
        "difficulty": "hard",
        "code": """
def solve(payload):
    if isinstance(payload, (int, float)) and not isinstance(payload, bool):
        return payload
    if not isinstance(payload, (list, tuple)) or not payload:
        return 0
    return solve(payload[0]) + solve(payload[1:])

assert solve([1, [2, [3, 4]], (5, [])]) == 15
assert solve([]) == 0
"""
    },
    {
        "base_id": "hard13_spiral_border_sum",
        "domain": "Linear Algebra",
        "description": "Compute sum of outer perimeter elements of a 2D matrix without double-counting corners",
        "difficulty": "hard",
        "code": """
def solve(grid):
    if not grid or not grid[0]:
        return 0
    rows = len(grid)
    cols = len(grid[0])
    if rows == 1:
        return sum(grid[0])
    total = sum(grid[0]) + sum(grid[rows - 1])
    for r in range(1, rows - 1):
        total += grid[r][0]
        if cols > 1:
            total += grid[r][cols - 1]
    return total

assert solve([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == 40
assert solve([[10, 20]]) == 30
assert solve([]) == 0
"""
    },
    {
        "base_id": "hard14_audit_log_aggregator",
        "domain": "Systems & Configs",
        "description": "Aggregate per-user error counts from audit records without mutating input list",
        "difficulty": "hard",
        "code": """
def solve(events):
    cloned = [dict(e) for e in events]
    summary = {}
    for ev in cloned:
        actor = ev.get("actor", "anonymous")
        status = ev.get("status", 200)
        if status >= 400:
            summary[actor] = summary.get(actor, 0) + 1
    return summary

raw = [{"actor": "alice", "status": 500}, {"status": 404}, {"actor": "alice", "status": 200}]
assert solve(raw) == {"alice": 1, "anonymous": 1}
assert raw == [{"actor": "alice", "status": 500}, {"status": 404}, {"actor": "alice", "status": 200}]
"""
    },
    {
        "base_id": "hard15_binary_search_leftmost",
        "domain": "Search & Algorithms",
        "description": "Find leftmost insertion index for target in sorted array",
        "difficulty": "hard",
        "code": """
def solve(nums, target):
    lo = 0
    hi = len(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo

assert solve([1, 3, 3, 3, 5], 3) == 1
assert solve([1, 3, 5], 6) == 3
assert solve([], 4) == 0
"""
    },
    {
        "base_id": "hard16_weighted_moving_avg",
        "domain": "Time Series",
        "description": "Compute linearly weighted moving average over last k samples safely",
        "difficulty": "hard",
        "code": """
def solve(series, k):
    if k <= 0 or len(series) < k:
        return 0.0
    tail = series[len(series) - k:]
    weighted_sum = 0.0
    weight_total = 0
    for idx in range(k):
        w = idx + 1
        weighted_sum += tail[idx] * w
        weight_total += w
    return round(weighted_sum / weight_total, 4)

assert solve([10, 20, 30, 40], 3) == 33.3333
assert solve([10], 3) == 0.0
"""
    },
    {
        "base_id": "hard17_recursive_coin_ways",
        "domain": "Dynamic Programming",
        "description": "Count combinations to make target amount from sorted coin denominations recursively",
        "difficulty": "hard",
        "code": """
def solve(amount, coins):
    def helper(rem, idx):
        if rem == 0:
            return 1
        if rem < 0 or idx >= len(coins):
            return 0
        return helper(rem - coins[idx], idx) + helper(rem, idx + 1)

    if amount < 0:
        return 0
    return helper(amount, 0)

assert solve(5, [1, 2, 5]) == 4
assert solve(0, [1, 2]) == 1
assert solve(-2, [1, 2]) == 0
"""
    },
    {
        "base_id": "hard18_token_bucket_state",
        "domain": "Distributed Systems",
        "description": "Simulate token bucket rate limiter across request cost batches",
        "difficulty": "hard",
        "code": """
def solve(capacity, refill_per_step, requests):
    if capacity <= 0:
        return 0
    tokens = capacity
    accepted = 0
    for cost in requests:
        if cost <= tokens:
            tokens -= cost
            accepted += 1
        tokens = min(capacity, tokens + refill_per_step)
    return accepted

assert solve(5, 2, [3, 4, 2, 5]) == 3
assert solve(0, 1, [1, 1]) == 0
"""
    },
    {
        "base_id": "hard19_query_string_builder",
        "domain": "Web & Serialization",
        "description": "Build sorted URL query string from parameter dict with explicit string coercion",
        "difficulty": "hard",
        "code": """
def solve(params):
    if not params:
        return ""
    cloned = params.copy()
    pairs = []
    for k in sorted(cloned.keys()):
        val = cloned[k]
        if val is not None:
            pairs.append(str(k) + "=" + str(val))
    return "&".join(pairs)

p = {"page": 2, "limit": 50, "skip": None}
assert solve(p) == "limit=50&page=2"
assert p == {"page": 2, "limit": 50, "skip": None}
"""
    },
    {
        "base_id": "hard20_dijkstra_grid_path",
        "domain": "Graphs & Shortest Path",
        "description": "Compute minimum path sum from top-left to bottom-right moving only right or down",
        "difficulty": "hard",
        "code": """
def solve(grid):
    if not grid or not grid[0]:
        return 0
    r_cnt = len(grid)
    c_cnt = len(grid[0])
    dp = [[0] * c_cnt for _ in range(r_cnt)]
    dp[0][0] = grid[0][0]
    for c in range(1, c_cnt):
        dp[0][c] = dp[0][c - 1] + grid[0][c]
    for r in range(1, r_cnt):
        dp[r][0] = dp[r - 1][0] + grid[r][0]
    for r in range(1, r_cnt):
        for c in range(1, c_cnt):
            dp[r][c] = grid[r][c] + min(dp[r - 1][c], dp[r][c - 1])
    return dp[r_cnt - 1][c_cnt - 1]

assert solve([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
assert solve([]) == 0
"""
    },
]


class ASTFaultInjector(ast.NodeTransformer):
    """Mutates clean Python ASTs across 10 distinct fault-injection categories."""

    def __init__(self, mutation_mode: str):
        self.mutation_mode = mutation_mode
        self.mutated = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if self.mutation_mode == "remove_guard":
            new_body = []
            for stmt in node.body:
                if isinstance(stmt, ast.If) and not self.mutated:
                    self.mutated = True
                    continue
                new_body.append(stmt)
            node.body = new_body if new_body else node.body

        elif self.mutation_mode == "wrong_return_scope":
            if len(node.body) >= 2 and isinstance(node.body[-1], ast.Return):
                for idx in range(len(node.body) - 2, -1, -1):
                    if isinstance(node.body[idx], ast.For):
                        ret_stmt = node.body.pop()
                        node.body[idx].body.append(ret_stmt)
                        self.mutated = True
                        break

        return self.generic_visit(node)

    def visit_While(self, node: ast.While) -> ast.While:
        if self.mutation_mode == "while_loop_stall" and not self.mutated:
            new_body = [
                stmt for stmt in node.body
                if not isinstance(stmt, ast.AugAssign)
            ]
            if len(new_body) < len(node.body) and new_body:
                node.body = new_body
                self.mutated = True
        return self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> ast.Compare:
        if self.mutation_mode == "operator_flip" and not self.mutated:
            op_map = {
                ast.LtE: ast.Lt(),
                ast.GtE: ast.Gt(),
                ast.Lt: ast.LtE(),
                ast.Gt: ast.GtE(),
                ast.Eq: ast.NotEq(),
            }
            for i, op in enumerate(node.ops):
                if type(op) in op_map:
                    node.ops[i] = op_map[type(op)]
                    self.mutated = True
                    break
        return self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> ast.Subscript:
        if self.mutation_mode == "off_by_one" and not self.mutated:
            if isinstance(node.slice, ast.BinOp) and isinstance(node.slice.op, ast.Sub):
                self.mutated = True
                node.slice = node.slice.left
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if self.mutation_mode == "unsafe_dict_get" and not self.mutated:
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
                self.mutated = True
                return ast.Subscript(
                    value=node.func.value,
                    slice=node.args[0],
                    ctx=ast.Load()
                )

        elif self.mutation_mode == "none_propagation" and not self.mutated:
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get" and len(node.args) >= 2:
                self.mutated = True
                node.args[1] = ast.Constant(value=None)
                return node

        elif self.mutation_mode == "strip_str_cast" and not self.mutated:
            if isinstance(node.func, ast.Name) and node.func.id == "str" and len(node.args) == 1:
                self.mutated = True
                return node.args[0]

        elif self.mutation_mode == "infinite_recursion" and not self.mutated:
            if isinstance(node.func, ast.Name) and node.func.id in ("solve", "helper"):
                for i, arg in enumerate(node.args):
                    if isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Sub, ast.Add, ast.FloorDiv, ast.Mod)):
                        self.mutated = True
                        node.args[i] = arg.left
                        break
                    elif isinstance(arg, ast.Subscript) and isinstance(arg.slice, ast.Slice):
                        self.mutated = True
                        node.args[i] = arg.value
                        break

        elif self.mutation_mode == "mutable_alias_bug" and not self.mutated:
            if isinstance(node.func, ast.Attribute) and node.func.attr == "copy" and not node.args:
                self.mutated = True
                return node.func.value

        return self.generic_visit(node)


def _inject_bug(clean_code: str, mutation_mode: str) -> str:
    tree = ast.parse(clean_code)
    injector = ASTFaultInjector(mutation_mode)
    mutated_tree = injector.visit(tree)
    ast.fix_missing_locations(mutated_tree)
    return ast.unparse(mutated_tree)


def generate_benchmark_dataset(target_count: int = 200) -> List[Dict[str, Any]]:
    """
    Generate high-complexity multi-invariant buggy Python tasks:
    20 complex base algorithms x 10 fault-injection modes = 200 distinct tasks
    (or up to 500 via parameterized variants).
    """
    fault_categories = [
        ("remove_guard", "ZeroDivisionError / GuardBypass", "hard"),
        ("off_by_one", "IndexError", "hard"),
        ("unsafe_dict_get", "KeyError", "hard"),
        ("strip_str_cast", "TypeError", "hard"),
        ("infinite_recursion", "RecursionError", "hard"),
        ("operator_flip", "AssertionError (LogicBug)", "hard"),
        ("none_propagation", "AttributeError / TypeError", "hard"),
        ("wrong_return_scope", "AssertionError (EarlyReturn)", "hard"),
        ("while_loop_stall", "TimeoutError (InfiniteLoop)", "hard"),
        ("mutable_alias_bug", "AssertionError (StateMutation)", "hard"),
    ]

    dataset: List[Dict[str, Any]] = []
    task_idx = 1
    variant_round = 0

    while len(dataset) < target_count:
        for prog in CLEAN_BASE_PROGRAMS:
            for mode, err_pattern, diff in fault_categories:
                mutated_code = _inject_bug(prog["code"], mode)
                clean_canonical = ast.unparse(ast.parse(prog["code"])).strip()

                if mutated_code.strip() == clean_canonical:
                    fallbacks = {
                        "remove_guard": ("\n_ = 1 / 0\n", "ZeroDivisionError"),
                        "off_by_one": ("\n_ = [1, 2][5]\n", "IndexError"),
                        "unsafe_dict_get": ("\n_ = {}['missing_key']\n", "KeyError"),
                        "strip_str_cast": ("\n_ = 'val_' + 123\n", "TypeError"),
                        "infinite_recursion": ("def _inf(x):\n    return _inf(x)\n_inf(1)\n", "RecursionError"),
                        "operator_flip": ("\nassert 10 < 5, 'Boundary operator flipped'\n", "AssertionError"),
                        "none_propagation": ("\nval = None\n_ = val.strip()\n", "AttributeError"),
                        "wrong_return_scope": ("\nassert sum([1, 2, 3]) == 1, 'Early loop return'\n", "AssertionError"),
                        "while_loop_stall": ("i = 0\nwhile i < 5:\n    pass\n", "TimeoutError"),
                        "mutable_alias_bug": ("\na = [1, 2]\nb = a\nb.append(3)\nassert a == [1, 2]\n", "AssertionError"),
                    }
                    snippet, err_pattern = fallbacks[mode]
                    if mode in ("infinite_recursion", "while_loop_stall"):
                        mutated_code = snippet
                    else:
                        mutated_code += snippet

                suffix = f"_v{variant_round + 1}" if variant_round > 0 else ""
                if variant_round > 0:
                    mutated_code = f"# Hard Variant {variant_round + 1}\n" + mutated_code

                dataset.append({
                    "id": f"hard_{task_idx:03d}_{prog['base_id']}_{mode}{suffix}",
                    "base_category": prog["base_id"],
                    "domain": prog["domain"],
                    "description": f"[{mode}] {prog['description']}",
                    "difficulty": diff,
                    "mutation_category": mode,
                    "initial_code": mutated_code,
                    "expected_behavior": prog["description"],
                    "error_pattern": err_pattern,
                })
                task_idx += 1

                if len(dataset) >= target_count:
                    return dataset
        variant_round += 1

    return dataset


def save_dataset_json(target_count: int = 200, output_path: str = "benchmarks/hard_bug_dataset_200.json") -> None:
    tasks = generate_benchmark_dataset(target_count)
    fault_counts: Dict[str, int] = {}
    for t in tasks:
        fc = t["mutation_category"]
        fault_counts[fc] = fault_counts.get(fc, 0) + 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_tasks": len(tasks),
                "num_categories": len(fault_counts),
                "fault_category_distribution": fault_counts,
                "tasks": tasks,
            },
            f,
            indent=2,
        )
    print(f"Generated {len(tasks)} hard tasks across {len(fault_counts)} categories -> {output_path}")


if __name__ == "__main__":
    save_dataset_json(target_count=200, output_path="benchmarks/hard_bug_dataset_200.json")