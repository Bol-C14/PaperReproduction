"""Independent QF_BV oracle. No import of reconstruction arithmetic/ranges.

Original/proposed formulas are encoded directly from the reviewed protocol,
separately from the optimizer's interval operations and guard recognition.
"""
import z3


def query(formula):
    solver = z3.SolverFor("QF_BV")
    solver.set(timeout=5000, random_seed=0)
    solver.add(formula)
    verdict = solver.check()
    record = {"verdict": str(verdict)}
    if verdict == z3.sat:
        model = solver.model()
        record["model_unsigned"] = {
            str(v): (z3.is_true(model[v]) if z3.is_bool(model[v]) else model[v].as_long())
            for v in model.decls()}
        record["model_replays_formula"] = z3.is_true(model.eval(formula, model_completion=True))
    elif verdict == z3.unknown:
        record["reason_unknown"] = solver.reason_unknown()
    return record


def membership(value, ranges):
    return z3.Or(*(z3.And(z3.UGE(value, lo), z3.ULE(value, hi)) for lo, hi in ranges))


def candidate_bv(ast):
    """Independent interpreter of the optimizer's emitted replacement AST."""
    op, width, *args = ast
    if op == "var":
        return z3.BitVec(args[0], width)
    if op == "const":
        return z3.BitVecVal(args[0], width)
    values = [candidate_bv(a) for a in args]
    if op == "zext":
        if width < values[0].size():
            raise ValueError("zext cannot narrow")
        return z3.ZeroExt(width - values[0].size(), values[0])
    if op == "low":
        return z3.Extract(width - 1, 0, values[0])
    if any(v.size() != width for v in values):
        raise ValueError("operator inputs must be explicitly sized")
    if op == "add":
        return values[0] + values[1]
    if op == "mul":
        return values[0] * values[1]
    if op == "lshr":
        return z3.LShR(values[0], values[1])
    raise ValueError(op)


def defined_equal(a, b):
    da, va = a
    db, vb = b
    return z3.And(da == db, z3.Implies(da, va == vb))


def translate_assume_ast(node, variables):
    """Separate symbolic definedness interpreter; bottom has no BV encoding."""
    # Duck-typed to avoid importing optimizer implementation.
    if hasattr(node, "condition") and hasattr(node, "expression"):
        defined, value = translate_assume_ast(node.expression, variables)
        _, condition = translate_assume_ast(node.condition, variables)
        return z3.And(defined, condition), value
    if isinstance(node, str):
        return z3.BoolVal(True), variables[node]
    if node[0] == "and":
        a, b = (translate_assume_ast(x, variables) for x in node[1:])
        return z3.And(a[0], b[0]), z3.And(a[1], b[1])
    if node[0] == "add":
        a, b = (translate_assume_ast(x, variables) for x in node[1:])
        return z3.And(a[0], b[0]), a[1] + b[1]
    if node[0] == "mux":
        c, a, b = (translate_assume_ast(x, variables) for x in node[1:])
        return z3.And(c[0], z3.If(c[1], a[0], b[0])), z3.If(c[1], a[1], b[1])
    raise ValueError(node)


def assume_controls(created, propagated, combined, nested):
    x, y = z3.BitVecs("assume_x assume_y", 4)
    g, h = z3.Bools("assume_g assume_h")
    env = {"x": x, "y": y, "g": g, "h": h, "zero": z3.BitVecVal(0, 4)}
    create = translate_assume_ast(created, env)
    original = (z3.BoolVal(True), z3.If(g, x, 0))
    prop = translate_assume_ast(propagated, env)
    expected = (g, x + y)
    comb = translate_assume_ast(combined, env)
    nested_value = translate_assume_ast(nested, env)
    return {"create": query(z3.Not(defined_equal(create, original))),
            "propagate": query(z3.Not(defined_equal(prop, expected))),
            "combine": query(z3.Not(defined_equal(comb, nested_value))),
            "bottom_is_not_zero": query(z3.Not(defined_equal((g, x), (z3.BoolVal(True), z3.If(g, x, 0)))))}


def check(fixture, proposal):
    kind = fixture["kind"]
    x = z3.BitVec("x", 4)
    guard = z3.BoolVal(True)
    if kind in ("abs", "context_escape"):
        lhs = z3.If(x < 0, -x, x)
        if kind == "abs":
            label = fixture["guard"]
            guard = x > 0 if label == "signed_positive" else z3.UGT(x, 0)
            if label == "empty":
                guard = z3.And(z3.UGT(x, 3), z3.ULT(x, 2))
    elif kind == "shift":
        x, y = z3.BitVec("x", 8), z3.BitVec("y", 4)
        guard = z3.ULE(y, fixture["guard_max"])
        lhs = z3.LShR(x, z3.ZeroExt(4, y))
    elif kind == "fma_shrink":
        a, b, c = z3.BitVecs("a b c", 3)
        lhs = z3.ZeroExt(4, a)*z3.ZeroExt(4, b)+z3.ZeroExt(4, c)
    elif kind == "early_truncation":
        a, b = z3.BitVecs("a b", 4)
        lhs = z3.ZeroExt(1, a)+z3.ZeroExt(1, b)
    elif kind == "comparison":
        a, b = z3.BitVecs("a b", 4)
        guard = z3.And(z3.UGE(a, 8), z3.ULE(b, 7))
        lhs = z3.If(z3.UGT(a, b), z3.BitVecVal(1, 1), z3.BitVecVal(0, 1))
    elif kind == "signed_range":
        a, b = z3.BitVec("a", 8), z3.BitVec("b", 4)
        value = z3.SignExt(1, z3.Extract(4, 0, a)) + z3.SignExt(2, b)
        ranges = proposal["ranges"]["result"]
        return {"range_escape": query(z3.Not(membership(value, ranges))),
                "range_matches_paper": ranges == [(0, 22), (40, 63)]}
    else:
        raise ValueError(kind)
    rhs = candidate_bv(proposal["candidate"])
    if rhs.size() != lhs.size():
        raise ValueError("candidate changed observable width")
    result = {"guard": query(guard)}
    if result["guard"]["verdict"] == "unsat":
        return result
    result["local_mismatch"] = query(z3.And(guard, lhs != rhs))
    # Preserve full output domain for every guarded rewrite, with an arbitrary
    # unchanged fallback rather than assuming guard true at the module input.
    fallback = z3.BitVec("fallback", lhs.size())
    result["full_mismatch"] = query(z3.If(guard, lhs, fallback) != z3.If(guard, rhs, fallback))
    if kind == "fma_shrink":
        result["range_escape"] = query(z3.Not(membership(lhs, proposal["ranges"]["result"])))
    if kind == "context_escape":
        result["valid_local_guard_mismatch"] = query(z3.And(x > 0, lhs != rhs))
    return result
