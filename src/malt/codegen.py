"""Code generation: lower the MATLAB AST to executable Python source.

Generated code calls into the ``_ml`` runtime namespace for every operation
whose MATLAB semantics differ from Python, and never uses raw string
concatenation of untrusted identifiers. Identifiers are validated and
emitted verbatim only after a Python-keyword check.
"""

from __future__ import annotations

import keyword

from . import ast_nodes as ast
from .errors import CodegenError, SemanticError

# MATLAB operator -> runtime function
_BINOP = {
    "+": "plus",
    "-": "minus",
    "*": "mtimes",
    "/": "mrdivide",
    "\\": "mldivide",
    "^": "mpower",
    ".*": "times",
    "./": "rdivide",
    ".\\": "ldivide",
    ".^": "power",
    "==": "eq",
    "~=": "ne",
    "<": "lt",
    "<=": "le",
    ">": "gt",
    ">=": "ge",
    "&": "and_",
    "|": "or_",
    "&&": "short_and",
    "||": "short_or",
}

_UNARY = {
    "-": "uneg",
    "+": "uplus",
    "~": "logical_not",
    "'": "ctranspose",
    ".'": "transpose",
}

# Native Python operators for inlined scalar arithmetic inside JIT-specialized
# loop bodies. ``\`` and ``.\`` are excluded (left division is not a Python
# binary operator) and fall back to the runtime dispatch.
_SCALAR_INLINE_BINOP = {
    "+": "+",
    "-": "-",
    "*": "*",
    ".*": "*",
    "./": "/",
    "/": "/",
    ".^": "**",
    "^": "**",
}

_AUGMENT_BASE = {
    "+=": "+",
    "-=": "-",
    "*=": "*",
    ".*=": ".*",
    "/=": "/",
    "./=": "./",
    "\\=": "\\",
    ".\\=": ".\\",
    "^=": "^",
    ".^=": ".^",
}

# Builtin runtime functions (single output unless listed in _MULTIOUT).
_BUILTINS = frozenset(
    {
        "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sinh", "cosh",
        "tanh", "exp", "log", "log10", "log2", "sqrt", "abs", "real", "imag",
        "conj", "angle", "floor", "ceil", "round", "sign", "fix", "rem", "mod",
        "zeros", "ones", "eye", "rand", "randn", "rng", "reshape", "repmat",
        "diag", "flipud", "fliplr", "sum", "prod", "mean", "min", "max",
        "cumsum", "cumprod", "sort", "size", "length", "numel", "ndims",
        "isequal", "linspace", "logspace", "meshgrid", "peaks",
        "det", "inv", "rank", "trace", "norm", "cond", "eigvals", "pinv",
        "chol", "polyfit", "integral", "fzero", "roots",
        "disp", "fprintf", "sprintf", "clc", "clear", "display",
        "plot", "figure", "gcf", "gca", "clf", "close", "hold", "subplot",
        "title", "xlabel", "ylabel", "zlabel", "legend", "grid", "xlim",
        "ylim", "zlim", "axis", "scatter", "bar", "histogram", "stem",
        "stairs", "semilogy", "semilogx", "loglog", "errorbar", "fill",
        "imagesc", "image", "colorbar", "contour", "contourf", "mesh", "surf",
        "view", "saveas", "exportgraphics", "who", "whos", "help",
        "show", "drawnow",
        "struct", "fieldnames", "isfield", "iscell", "isstruct", "getfield",
        "setfield", "feval", "func2str", "str2func", "any", "all",
        "isnumeric", "ischar", "isempty", "isscalar", "isvector", "ismatrix",
        "isrow", "iscolumn", "isreal", "isfloat", "islogical", "isnan",
        "isinf", "isfinite", "lower", "upper", "strcmp", "strcmpi", "strcat",
        "strjoin", "strsplit", "num2str",
    }
)

# Builtins with output-count-aware semantics.
_MULTIOUT = frozenset({"eig", "svd", "ode45", "lu", "qr"})

# Builtins that produce no meaningful value to display when called without a
# trailing semicolon (commands, plotting, and graphics state setters).
_VOID_BUILTINS = frozenset(
    {
        "disp", "fprintf", "clc", "clear", "clf", "hold", "grid", "rng",
        "who", "whos", "help", "close", "view", "drawnow", "show", "axis",
        "xlim", "ylim", "zlim", "title", "xlabel", "ylabel", "zlabel",
        "legend", "colorbar", "subplot", "figure", "saveas", "exportgraphics",
        "plot", "scatter", "bar", "histogram", "stem", "stairs", "semilogy",
        "semilogx", "loglog", "errorbar", "fill", "imagesc", "image",
        "contour", "contourf", "mesh", "surf",
    }
)

_RESERVED = frozenset({"_ml", "_ans", "_malt_ns"})

# Bare identifiers that MATLAB treats as zero-argument function calls
# (command syntax), e.g. ``saveas(gcf, ...)``.
_BARE_FUNCTIONS = frozenset({"gcf", "gca"})


class CodeGenerator:
    def __init__(self, filename: str = "<malt>", optimization_level: int = 1) -> None:
        self.filename = filename
        self.lines: list[str] = []
        self.indent = 0
        self.user_functions: dict[str, int] = {}
        self._temp_counter = 0
        self._end_base: str | None = None
        self._end_dim: int = 0
        self._function_outputs: list[str] | None = None
        self.source_map: list[tuple[int, object]] = []  # (generated line, location)
        self.diagnostics: list[dict] = []  # per-loop JIT specialization decisions
        self.optimization_level = optimization_level
        self.inline_scalar = False

    # -- low-level emission -------------------------------------------------
    def emit(self, line: str = "") -> None:
        if line:
            self.lines.append("    " * self.indent + line)
        else:
            self.lines.append("")

    def new_temp(self) -> str:
        t = f"_t{self._temp_counter}"
        self._temp_counter += 1
        return t

    def _check_identifier(self, name: str, node: ast.Node) -> None:
        if keyword.iskeyword(name) or name in _RESERVED:
            raise SemanticError(
                f"identifier '{name}' is a reserved word and cannot be used",
                node.location,
            )
        if not name or not (name[0].isalpha() or name[0] == "_"):
            raise SemanticError(f"invalid identifier '{name}'", node.location)

    # -- expression generation ---------------------------------------------
    def gen_expr(self, node: ast.Node) -> str:
        if isinstance(node, ast.NumberLiteral):
            return self._num(node.value)
        if isinstance(node, ast.StringLiteral):
            return repr(node.value)
        if isinstance(node, ast.LogicalLiteral):
            return "1.0" if node.value else "0.0"
        if isinstance(node, ast.Identifier):
            self._check_identifier(node.name, node)
            if node.name in _BARE_FUNCTIONS:
                return f"_ml.{node.name}()"
            return node.name
        if isinstance(node, ast.EndKeyword):
            if self._end_base is None:
                raise SemanticError("'end' used outside an indexing context", node.location)
            return f"_ml.end_({self._end_base}, {self._end_dim})"
        if isinstance(node, ast.MatrixLiteral):
            return self._gen_matrix(node)
        if isinstance(node, ast.CellLiteral):
            return self._gen_cell(node)
        if isinstance(node, ast.CellIndexExpression):
            return self._gen_cell_index(node)
        if isinstance(node, ast.UnaryOperation):
            if self.inline_scalar and node.op in ("-", "+"):
                return f"({node.op}{self.gen_expr(node.operand)})"
            fn = _UNARY.get(node.op)
            if fn is None:
                raise CodegenError(f"unknown unary operator {node.op!r}", node.location)
            return f"_ml.{fn}({self.gen_expr(node.operand)})"
        if isinstance(node, ast.BinaryOperation):
            if node.op in ("&&", "||"):
                # Short-circuit scalar logical operators: MATLAB evaluates the
                # right operand only if needed and returns a logical scalar.
                la = self.gen_expr(node.left)
                rb = self.gen_expr(node.right)
                op = "and" if node.op == "&&" else "or"
                return (
                    f"(1.0 if (_ml.is_true({la}) {op} _ml.is_true({rb})) else 0.0)"
                )
            if self.inline_scalar and node.op in _SCALAR_INLINE_BINOP:
                la = self.gen_expr(node.left)
                rb = self.gen_expr(node.right)
                return f"({la} {_SCALAR_INLINE_BINOP[node.op]} {rb})"
            fn = _BINOP.get(node.op)
            if fn is None:
                raise CodegenError(f"unknown operator {node.op!r}", node.location)
            return f"_ml.{fn}({self.gen_expr(node.left)}, {self.gen_expr(node.right)})"
        if isinstance(node, ast.ColonExpression):
            s = self.gen_expr(node.start)
            e = self.gen_expr(node.end)
            if node.step is not None:
                return f"_ml.colon({s}, {self.gen_expr(node.step)}, {e})"
            return f"_ml.colon({s}, {e})"
        if isinstance(node, ast.FunctionCall):
            return self._gen_call(node, nout=1)
        if isinstance(node, ast.AnonymousFunction):
            return self._gen_anon(node)
        if isinstance(node, ast.FunctionHandle):
            if isinstance(node.target, ast.AnonymousFunction):
                return self._gen_anon(node.target)
            name = node.target
            if name in self.user_functions:
                self._check_identifier(name, node)
                return name
            if name in _BUILTINS or name in _MULTIOUT:
                return f"_ml.make_handle({name!r}, _ml.{name})"
            raise SemanticError(f"unknown function '{name}'", node.location)
        if isinstance(node, ast.FieldAccess):
            self._check_identifier(node.field, node)
            return f"_ml.getfield({self.gen_expr(node.base)}, {node.field!r})"
        raise CodegenError(f"cannot generate code for {type(node).__name__}", node.location)

    def _num(self, value: object) -> str:
        if isinstance(value, complex):
            return repr(value)
        return repr(value)

    def _gen_matrix(self, node: ast.MatrixLiteral) -> str:
        rows = []
        for row in node.rows:
            elems = ", ".join(self.gen_expr(e) for e in row)
            rows.append(f"[{elems}]")
        return f"_ml.matrix([{', '.join(rows)}])"

    def _gen_cell(self, node: ast.CellLiteral) -> str:
        rows = []
        for row in node.rows:
            elems = ", ".join(self.gen_expr(e) for e in row)
            rows.append(f"[{elems}]")
        return f"_ml.cell_literal([{', '.join(rows)}])"

    def _gen_cell_index(self, node: ast.CellIndexExpression) -> str:
        base = self.gen_expr(node.base)
        subs = []
        if len(node.indices) == 1:
            subs.append(self._gen_subscript(node.indices[0], base, 0))
        else:
            for i, a in enumerate(node.indices):
                subs.append(self._gen_subscript(a, base, i + 1))
        return f"_ml.cell_index({base}, {', '.join(subs)})"

    def _gen_anon(self, node: ast.AnonymousFunction) -> str:
        for p in node.params:
            self._check_identifier(p, node)
        body = self.gen_expr(node.body)
        return f"(lambda {', '.join(node.params)}: {body})"

    def _gen_call(self, node: ast.FunctionCall, nout: int) -> str:
        name = node.name
        if name in self.user_functions:
            args = ", ".join(self.gen_expr(a) for a in node.args)
            if nout >= 2:
                return f"{name}({args})"
            if nout == 1:
                return f"{name}({args})[0]"
            return f"{name}({args})"
        if name in _MULTIOUT:
            args = ", ".join(self.gen_expr(a) for a in node.args)
            return f"_ml.{name}({args}, {nout})"
        if name in _BUILTINS:
            args = ", ".join(self.gen_expr(a) for a in node.args)
            return f"_ml.{name}({args})"
        # Not a known function: treat as indexing or a dynamic call on a
        # function-handle variable.
        self._check_identifier(name, node)
        return self._gen_index_base(name, node.args)

    def _gen_index_base(self, base_expr: str, args: list[ast.Node]) -> str:
        subs: list[str] = []
        if len(args) == 1:
            subs.append(self._gen_subscript(args[0], base_expr, 0))
        else:
            for i, a in enumerate(args):
                subs.append(self._gen_subscript(a, base_expr, i + 1))
        return f"_ml.call({base_expr}, {', '.join(subs)})"

    def _gen_subscript(self, node: ast.Node, base: str, dim: int) -> str:
        # A bare colon is represented as None in the AST? No — the parser
        # produces ColonArgument for a lone ':'? We represent ':' via a
        # ColonExpression only when it has operands. A bare ':' is detected
        # here by checking for an identifier named ':' — handled in parser as
        # ColonArgument.
        if isinstance(node, ast.ColonArgument):
            return "_ml.COLON"
        old_base, old_dim = self._end_base, self._end_dim
        self._end_base, self._end_dim = base, dim
        try:
            return self.gen_expr(node)
        finally:
            self._end_base, self._end_dim = old_base, old_dim

    # -- statement generation ----------------------------------------------
    def gen_program(self, statements: list[ast.Statement]) -> str:
        # Hoist all function definitions first so script code can call them.
        for s in statements:
            if isinstance(s, ast.FunctionDefinition):
                self._gen_function(s)
        for s in statements:
            if isinstance(s, ast.FunctionDefinition):
                continue
            self.gen_statement(s)
        return "\n".join(self.lines) + "\n"

    def _gen_function(self, node: ast.FunctionDefinition) -> None:
        self._check_identifier(node.name, node)
        if node.name in self.user_functions:
            raise SemanticError(f"duplicate function '{node.name}'", node.location)
        self.user_functions[node.name] = len(node.outputs)
        for p in node.params:
            self._check_identifier(p, node)
        params = ", ".join(node.params)
        self.emit(f"def {node.name}({params}):")
        self.indent += 1
        self._function_outputs = list(node.outputs)
        for s in node.body:
            self.gen_statement(s)
        outs = ", ".join(node.outputs)
        self.emit(f"return ({outs},)")
        self._function_outputs = None
        self.indent -= 1
        self.emit()

    def gen_statement(self, node: ast.Statement) -> None:
        # Record a source mapping from the next generated line to the MATLAB
        # source location, for source-aware runtime diagnostics.
        self.source_map.append((len(self.lines) + 1, node.location))
        if isinstance(node, ast.Assignment):
            self._gen_assignment(node)
        elif isinstance(node, ast.ExpressionStatement):
            self._gen_expr_statement(node)
        elif isinstance(node, ast.IfStatement):
            self._gen_if(node)
        elif isinstance(node, ast.ForStatement):
            self._gen_for(node)
        elif isinstance(node, ast.WhileStatement):
            self._gen_while(node)
        elif isinstance(node, ast.SwitchStatement):
            self._gen_switch(node)
        elif isinstance(node, ast.TryStatement):
            self._gen_try(node)
        elif isinstance(node, ast.BreakStatement):
            self.emit("break")
        elif isinstance(node, ast.ContinueStatement):
            self.emit("continue")
        elif isinstance(node, ast.ReturnStatement):
            self._gen_return(node)
        elif isinstance(node, ast.FunctionDefinition):
            pass  # hoisted earlier
        else:
            raise CodegenError(
                f"cannot generate statement {type(node).__name__}", node.location
            )

    def _display_rhs(self, expr: str) -> str:
        return f"_ml.display(_ml.as_array({expr}))"

    def _gen_assignment(self, node: ast.Assignment) -> None:
        targets = node.targets
        value = node.value
        nout = len(targets)

        if node.op != "=":
            # Augmented assignment: x += expr  ->  x = x + expr
            if len(targets) != 1:
                raise SemanticError("augmented assignment requires a single target", node.location)
            t = targets[0]
            base_op = _AUGMENT_BASE[node.op]
            self._assign_single(t, node, f"_ml.{_BINOP[base_op]}({self._target_ref(t)}, {self.gen_expr(value)})")
            return

        if nout == 1:
            t = targets[0]
            rhs = self._gen_rhs(value, nout)
            self._assign_single(t, node, rhs)
            return

        # Multi-output assignment [a, b] = f(...)
        if isinstance(value, ast.FunctionCall):
            rhs = self._gen_call(value, nout)
        else:
            raise SemanticError(
                "multiple-output assignment requires a function call", node.location
            )
        names = []
        for t in targets:
            if not isinstance(t, ast.Identifier):
                raise SemanticError("multi-output targets must be identifiers", t.location)
            self._check_identifier(t.name, t)
            names.append(t.name)
        self.emit(f"{', '.join(names)} = {rhs}")
        if not node.suppress:
            self.emit(f"_ml.display({names[0]})")

    def _target_ref(self, t: ast.Node) -> str:
        if isinstance(t, ast.Identifier):
            return t.name
        raise SemanticError("invalid augmented-assignment target", t.location)

    def _assign_single(self, t: ast.Node, node: ast.Assignment, rhs: str) -> None:
        if isinstance(t, ast.Identifier):
            self._check_identifier(t.name, t)
            # Runtime operations already return MATLAB-visible values (arrays or
            # native scalars); literals are native Python numbers. No extra
            # wrapping is required — ``as_array`` normalizes at boundaries.
            self.emit(f"{t.name} = {rhs}")
            if not node.suppress:
                self.emit(f"_ml.display({t.name})")
        elif isinstance(t, ast.FunctionCall):
            # indexed assignment: A(i, j) = value
            self._check_identifier(t.name, t)
            self._gen_index_assign(t.name, t.args, rhs, node.suppress)
        elif isinstance(t, ast.CellIndexExpression):
            # brace assignment: c{i} = value
            base = self.gen_expr(t.base)
            subs = []
            if len(t.indices) == 1:
                subs.append(self._gen_subscript(t.indices[0], base, 0))
            else:
                for i, a in enumerate(t.indices):
                    subs.append(self._gen_subscript(a, base, i + 1))
            self.emit(f"_ml.cell_assign({base}, {rhs}, {', '.join(subs)})")
        elif isinstance(t, ast.FieldAccess):
            # struct field assignment: s.field = value
            base = self.gen_expr(t.base)
            self._check_identifier(t.field, t)
            self.emit(f"_ml.setfield({base}, {t.field!r}, {rhs})")
        else:
            raise SemanticError("invalid assignment target", t.location)

    def _gen_index_assign(self, base: str, args: list[ast.Node], rhs: str, suppress: bool) -> None:
        subs: list[str] = []
        if len(args) == 1:
            subs.append(self._gen_subscript(args[0], base, 0))
        else:
            for i, a in enumerate(args):
                subs.append(self._gen_subscript(a, base, i + 1))
        self.emit(f"_ml.assign({base}, {rhs}, {', '.join(subs)})")

    def _gen_rhs(self, value: ast.Node, nout: int) -> str:
        if isinstance(value, ast.FunctionCall):
            return self._gen_call(value, nout)
        return self.gen_expr(value)

    def _gen_expr_statement(self, node: ast.ExpressionStatement) -> None:
        expr = node.expr
        if isinstance(expr, ast.FunctionCall):
            name = expr.name
            if name in _VOID_BUILTINS:
                self.emit(self._gen_call(expr, 0))
                return
            rhs = self._gen_call(expr, 1)
            if node.suppress:
                self.emit(rhs)
            else:
                self.emit(f"_ans = _ml.as_array({rhs})")
                self.emit("_ml.display(_ans)")
            return
        if isinstance(expr, ast.Identifier):
            name = expr.name
            if name in _BUILTINS or name in _MULTIOUT:
                # bare command with no arguments: `clc`, `clf`, `colorbar`
                self.emit(f"_ml.{name}()")
                return
            if not node.suppress:
                self.emit(f"_ml.display({name})")
            return
        rhs = self.gen_expr(expr)
        if not node.suppress:
            self.emit(f"_ans = _ml.as_array({rhs})")
            self.emit("_ml.display(_ans)")

    def _gen_if(self, node: ast.IfStatement) -> None:
        for i, (cond, body) in enumerate(node.branches):
            kw = "if" if i == 0 else "elif"
            self.emit(f"{kw} _ml.is_true({self.gen_expr(cond)}):")
            self.indent += 1
            if not body:
                self.emit("pass")
            for s in body:
                self.gen_statement(s)
            self.indent -= 1
        if node.else_body is not None:
            self.emit("else:")
            self.indent += 1
            if not node.else_body:
                self.emit("pass")
            for s in node.else_body:
                self.gen_statement(s)
            self.indent -= 1

    def _gen_for(self, node: ast.ForStatement) -> None:
        self._check_identifier(node.var, node)
        if self.optimization_level >= 2:
            reason = self._try_gen_for_jit(node)
            self.diagnostics.append(
                {
                    "line": node.location.line,
                    "var": node.var,
                    "jit": reason is None,
                    "reason": reason,
                }
            )
            if reason is None:
                return
        it = self.gen_expr(node.iterable)
        self.emit(f"{node.var} = _ml.for_init()")
        self.emit(f"for {node.var} in _ml.for_columns({it}):")
        self.indent += 1
        if not node.body:
            self.emit("pass")
        for s in node.body:
            self.gen_statement(s)
        self.indent -= 1

    def _try_gen_for_jit(self, node: ast.ForStatement) -> str | None:
        """JIT-specialize ``for k = a:s:b`` scalar reduction loops.

        Each body statement must be a scalar accumulation ``X = X op f(k)``
        where the RHS references only the loop variable and numeric literals
        (never the accumulator, so a matrix ``X`` only ever combines with a
        scalar, which is element-wise in both MATLAB and native Python).
        Single accumulators use ``_ml.jit_for``; multiple distinct accumulators
        use ``_ml.jit_loop``. Everything else falls back to the general loop.

        Returns ``None`` on success, or a human-readable reason for falling
        back.
        """
        if not isinstance(node.iterable, ast.ColonExpression):
            return "iterable is not a colon range (a:s:b)"
        if not node.body:
            return "empty loop body"
        accs: list[tuple[str, ast.BinaryOperation]] = []
        for stmt in node.body:
            if not isinstance(stmt, ast.Assignment) or stmt.op != "=":
                return f"non-assignment statement in body ({type(stmt).__name__})"
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Identifier):
                return "multi-target or non-identifier assignment target"
            target = stmt.targets[0].name
            if target == node.var:
                return "assigns the loop variable"
            if target in [a for a, _ in accs]:
                return f"accumulator '{target}' assigned more than once"
            self._check_identifier(target, stmt)
            value = stmt.value
            if not isinstance(value, ast.BinaryOperation):
                return f"body value is not an accumulation ({type(value).__name__})"
            if value.op not in _SCALAR_INLINE_BINOP:
                return f"operator '{value.op}' is not inlinable"
            if not isinstance(value.left, ast.Identifier) or value.left.name != target:
                return "accumulation is not of the form X = X op …"
            if not self._is_scalar_expr(value.right, {node.var}):
                return f"RHS references variables other than '{node.var}'"
            accs.append((target, value))

        names = [a for a, _ in accs]
        fn_name = self.new_temp()
        self.emit(f"def {fn_name}({', '.join(names)}, {node.var}):")
        self.indent += 1
        old_inline = self.inline_scalar
        self.inline_scalar = True
        try:
            for target, value in accs:
                self.emit(f"{target} = {self.gen_expr(value)}")
        finally:
            self.inline_scalar = old_inline
        if len(accs) == 1:
            self.emit(f"return {names[0]}")
        else:
            self.emit(f"return ({', '.join(names)},)")
        self.indent -= 1

        start = self.gen_expr(node.iterable.start)
        end = self.gen_expr(node.iterable.end)
        step = self.gen_expr(node.iterable.step) if node.iterable.step is not None else "1.0"

        if len(accs) == 1:
            self.emit(
                f"{names[0]}, {node.var} = _ml.jit_for({names[0]}, {start}, {step}, {end}, {fn_name})"
            )
        else:
            tup = "(" + ", ".join(names) + ")"
            tmp = self.new_temp()
            self.emit(
                f"{tmp}, {node.var} = _ml.jit_loop({tup}, {start}, {step}, {end}, {fn_name})"
            )
            self.emit(f"{', '.join(names)} = {tmp}")
        return None

    def _is_scalar_expr(self, node: ast.Node, allowed: set[str]) -> bool:
        if isinstance(node, (ast.NumberLiteral, ast.LogicalLiteral)):
            return True
        if isinstance(node, ast.Identifier):
            return node.name in allowed
        if isinstance(node, ast.UnaryOperation):
            return node.op in ("-", "+") and self._is_scalar_expr(node.operand, allowed)
        if isinstance(node, ast.BinaryOperation):
            if node.op not in _SCALAR_INLINE_BINOP:
                return False
            return self._is_scalar_expr(node.left, allowed) and self._is_scalar_expr(
                node.right, allowed
            )
        return False

    def _gen_while(self, node: ast.WhileStatement) -> None:
        self.emit(f"while _ml.is_true({self.gen_expr(node.condition)}):")
        self.indent += 1
        if not node.body:
            self.emit("pass")
        for s in node.body:
            self.gen_statement(s)
        self.indent -= 1

    def _gen_switch(self, node: ast.SwitchStatement) -> None:
        t = self.new_temp()
        self.emit(f"{t} = {self.gen_expr(node.value)}")
        for i, (test, body) in enumerate(node.cases):
            kw = "if" if i == 0 else "elif"
            self.emit(f"{kw} {self._switch_cond(t, test)}:")
            self.indent += 1
            if not body:
                self.emit("pass")
            for s in body:
                self.gen_statement(s)
            self.indent -= 1
        if node.otherwise is not None:
            self.emit("else:")
            self.indent += 1
            if not node.otherwise:
                self.emit("pass")
            for s in node.otherwise:
                self.gen_statement(s)
            self.indent -= 1

    def _switch_cond(self, t: str, test: ast.Node) -> str:
        if isinstance(test, ast.CellLiteral):
            parts = []
            for row in test.rows:
                for e in row:
                    parts.append(f"_ml.is_true(_ml.isequal({t}, {self.gen_expr(e)}))")
            return " or ".join(parts) if parts else "False"
        return f"_ml.is_true(_ml.isequal({t}, {self.gen_expr(test)}))"

    def _gen_try(self, node: ast.TryStatement) -> None:
        self.emit("try:")
        self.indent += 1
        for s in node.try_body:
            self.gen_statement(s)
        self.indent -= 1
        self.emit("except Exception as _err:")
        self.indent += 1
        if node.catch_var is not None:
            self._check_identifier(node.catch_var, node)
            self.emit(f"{node.catch_var} = _ml.catch_error(_err)")
        if not node.catch_body:
            self.emit("pass")
        for s in node.catch_body:
            self.gen_statement(s)
        self.indent -= 1

    def _gen_return(self, node: ast.ReturnStatement) -> None:
        if self._function_outputs is not None:
            outs = ", ".join(self._function_outputs)
            self.emit(f"return ({outs},)")
        else:
            self.emit("raise _ml.ReturnSignal()")


def generate(
    statements: list[ast.Statement],
    filename: str = "<malt>",
    optimization_level: int = 1,
) -> tuple[str, list[tuple[int, object]], list[dict]]:
    gen = CodeGenerator(filename, optimization_level=optimization_level)
    source = gen.gen_program(statements)
    return source, gen.source_map, gen.diagnostics
