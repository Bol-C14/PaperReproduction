"""Our bounded paper-method reconstruction. No Z3, RTL parser or e-graph.

Intervals are inclusive, stored as finite unions. The proposal engine only
matches the fixed, reviewed expression families; it is not a general optimizer.
"""
from dataclasses import dataclass


def normalize(ranges):
    out = []
    for lo, hi in sorted(ranges):
        if lo > hi:
            continue
        if out and lo <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(hi, out[-1][1]))
        else:
            out.append((lo, hi))
    return out


def intersect(a, b):
    return normalize((max(l, p), min(u, q)) for l, u in a for p, q in b)


def truncate(ranges, width):
    """Paper's conservative interval mod: crossing a block returns full."""
    p = 1 << width
    return normalize((lo % p, hi % p) if lo // p == hi // p else (0, p - 1)
                     for lo, hi in ranges)


def signed(ranges, width):
    p, half = 1 << width, 1 << (width - 1)
    out = []
    for lo, hi in ranges:
        if not 0 <= lo <= hi < p:
            raise ValueError("signed conversion requires in-width unsigned ranges")
        if hi < half:
            out.append((lo, hi))
        elif lo >= half:
            out.append((lo - p, hi - p))
        else:
            out.extend([(lo, half - 1), (-half, hi - p)])
    return normalize(out)


def unsigned(ranges, width):
    """U_n in paper: preserve one wrap as a union, collapse >=2 wraps."""
    p = 1 << width
    out = []
    for lo, hi in ranges:
        if lo // p < hi // p - 1:
            out.append((0, p - 1))
        elif lo // p < hi // p:
            out.extend([(0, hi % p), (lo % p, p - 1)])
        else:
            out.append((lo % p, hi % p))
    return normalize(out)


def arithmetic(a, b, op):
    out = []
    for l, u in a:
        for p, q in b:
            if op == "add":
                out.append((l + p, u + q))
            elif op == "mul":
                corners = [l*p, l*q, u*p, u*q]
                out.append((min(corners), max(corners)))
            else:
                raise ValueError(op)
    return normalize(out)


def bits(ranges):
    if not ranges or ranges[0][0] < 0:
        raise ValueError("bitwidth requires nonempty unsigned ranges")
    return max(1, max(hi for _, hi in ranges).bit_length())


def variable(name, width):
    return ["var", width, name]


def fma_at_width(width):
    a, b, c = (variable(n, 3) for n in ["a", "b", "c"])
    return ["add", width, ["mul", width, ["zext", width, a], ["zext", width, b]], ["zext", width, c]]


@dataclass(frozen=True)
class Assume:
    expression: object
    condition: object


def create_true_branch(condition, expression, otherwise):
    return ("mux", condition, Assume(expression, condition), otherwise)


def propagate(node):
    op, *args = node.expression
    if op != "add":
        raise ValueError("pilot propagation supports add only")
    return (op, *(Assume(arg, node.condition) for arg in args))


def combine(node):
    if not isinstance(node.expression, Assume):
        raise ValueError("nested assumption required")
    return Assume(node.expression.expression,
                  ("and", node.expression.condition, node.condition))


def propose(fixture):
    """Rule application with explicit side conditions, independent of SMT.

    Negative fixtures also ask the checker to inspect the deliberately invalid
    requested rewrite, even though this proposal engine refuses to apply it.
    """
    kind = fixture["kind"]
    result = {"applied": False, "rule": None, "ranges": {}, "reason": ""}
    if kind == "abs":
        if fixture["guard"] == "signed_positive":
            r = intersect([(0, 15)], [(1, 7)])
            result.update(applied=True, rule="signed_abs_to_x_in_same_context",
                          ranges={"x": r}, reason="signed x > 0 excludes negatives")
        elif fixture["guard"] == "empty":
            r = intersect([(4, 15)], [(0, 1)])
            result.update(ranges={"x": r}, reason="empty domain; not a success")
        else:
            result.update(ranges={"x": [(1, 15)]}, reason="unsigned positivity does not imply signed positivity")
    elif kind == "shift":
        r = intersect([(0, 15)], [(0, fixture["guard_max"])])
        result.update(ranges={"y": r}, reason="low1 preserves amount only if max(y)<=1")
        if max(hi for _, hi in r) <= 1:
            result.update(applied=True, rule="shift_amount_low1_in_same_context")
    elif kind == "fma_shrink":
        product = arithmetic([(0, 7)], [(0, 7)], "mul")
        value = arithmetic(product, [(0, 7)], "add")
        result.update(applied=bits(value) <= 6, rule="unsigned_fma_result_shrink6",
                      ranges={"product": product, "result": value},
                      target_width=bits(value), reason="complete output maximum fits six bits")
    elif kind == "early_truncation":
        value = arithmetic([(0, 15)], [(0, 15)], "add")
        result.update(ranges={"result": value}, target_width=bits(value),
                      reason="output maximum 30 does not fit four bits")
    elif kind == "comparison":
        a, b = intersect([(0, 15)], [(8, 15)]), intersect([(0, 15)], [(0, 7)])
        result.update(applied=a[0][0] > b[-1][1], rule="unsigned_compare_true",
                      ranges={"a": a, "b": b}, reason="min(a)>max(b)")
    elif kind == "signed_range":
        a = signed(truncate([(0, 255)], 5), 5)
        b = signed([(0, 15)], 4)
        value = unsigned(arithmetic(a, b, "add"), 6)
        result.update(rule="signed_range_analysis_only", ranges={"a_signed": a, "b_signed": b, "result": value}, reason="analysis only; no rewrite")
    elif kind == "context_escape":
        result["reason"] = "contextual equality cannot be exported globally"
    else:
        raise ValueError(kind)
    # Emit the actual replacement AST. Rejected fixtures intentionally inject a
    # bad proposal for the independent oracle, rather than applying it.
    result["candidate_origin"] = "rewrite_emission" if result["applied"] else "negative_control_injection"
    if kind in ["abs", "context_escape"]:
        result["candidate"] = variable("x", 4)
    elif kind == "shift":
        result["candidate"] = ["lshr", 8, variable("x", 8),
                               ["zext", 8, ["low", 1, variable("y", 4)]]]
    elif kind == "fma_shrink":
        result["candidate"] = ["zext", 7, fma_at_width(result["target_width"])]
    elif kind == "early_truncation":
        result["candidate"] = ["zext", 5, ["add", 4, variable("a", 4), variable("b", 4)]]
    elif kind == "comparison":
        result["candidate"] = ["const", 1, 1]
    else:
        result["candidate_origin"] = "analysis_only"
    return result
