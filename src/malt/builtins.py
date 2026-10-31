"""Shared registry of MALT builtin function names.

Kept in one place so that code generation, semantic analysis (for shadowing
warnings), and future tooling (e.g. an LSP) agree on what counts as a builtin.
"""

from __future__ import annotations

# Builtin runtime functions (single output unless listed in MULTIOUT).
BUILTINS = frozenset(
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
        "tf", "ss", "dcgain", "step", "impulse", "lsim", "stepinfo",
        "feedback", "series", "parallel", "pole", "zero",
    }
)

# Builtins with output-count-aware semantics.
MULTIOUT = frozenset({"eig", "svd", "ode45", "lu", "qr"})

# Builtins that produce no meaningful value to display when called without a
# trailing semicolon (commands, plotting, and graphics state setters).
VOID_BUILTINS = frozenset(
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
