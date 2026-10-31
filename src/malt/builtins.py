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
        # Core math (extended)
        "sec", "csc", "cot", "asec", "acsc", "acot", "sind", "cosd", "tand",
        "asind", "acosd", "atand", "atan2d", "asinh", "acosh", "atanh",
        "deg2rad", "rad2deg", "unwrap", "cplxpair", "complex", "cbrt",
        "realsqrt", "reallog", "hypot", "expm1", "log1p", "nthroot", "power",
        "idivide", "gcd", "lcm", "factorial", "nchoosek", "perms", "primes",
        "isprime", "factor", "cummax", "cummin", "diff", "maxk", "mink",
        "bounds", "range", "rescale", "normalize",
        # Special functions
        "gamma", "gammaln", "beta", "betaln", "erf", "erfc", "erfinv",
        "erfcinv", "psi", "expint", "besselj", "bessely", "besseli", "besselk",
        "airy", "ellipke", "ellipj", "legendre", "cross", "dot", "cumtrapz",
        # Arrays and matrices
        "triu", "tril", "kron", "rot90", "flip", "circshift", "unique", "find",
        "cat", "horzcat", "vertcat", "sortrows", "issorted", "toeplitz",
        "hankel", "vander", "hilb", "invhilb", "magic", "pascal", "blkdiag",
        "repelem", "ndgrid", "squeeze", "permute", "ipermute",
        # Linear algebra (extended)
        "schur", "hess", "expm", "logm", "sqrtm", "funm", "null", "orth",
        "rref", "linsolve", "balance", "rcond", "normest", "condest",
        "issymmetric", "ishermitian", "isdiag", "istril", "istriu", "isbanded",
        # Polynomials / interpolation / calculus / ODE / optimization
        "conv", "deconv", "poly", "polyval", "polyvalm", "polyder", "polyint",
        "residue", "interp1", "interp2", "interp3", "spline", "pchip", "makima",
        "gradient", "del2", "trapz", "integral2", "integral3", "fminsearch",
        "fminbnd", "fsolve", "lsqnonneg", "fminunc", "ode23", "ode113",
        "ode15s", "ode23s",
        # Statistics (base)
        "median", "std", "var", "mad", "skewness", "kurtosis", "mode", "cov",
        "corrcoef", "prctile", "quantile", "iqr", "movmean", "movmedian",
        "movsum", "movstd", "movvar", "movmax", "movmin", "detrend",
        "ismissing", "rmmissing", "fillmissing", "isoutlier", "filloutliers",
        "rms", "meansqr",
        # Control systems (extended)
        "damp", "evalfr", "isstable", "isproper", "bandwidth", "tfdata",
        "ssdata", "tf2ss", "ss2tf", "tf2zp", "zp2tf", "ss2zp", "minreal",
        "append", "c2d", "d2c", "pid", "ctrb", "obsv", "lqr", "dlqr", "place",
        "acker", "lyap", "care", "dare", "bode", "freqresp", "margin",
        "nyquist", "gensig", "initial",
        # Signal processing
        "fft", "ifft", "fft2", "ifft2", "fftn", "ifftn", "fftshift",
        "ifftshift", "nextpow2", "filter", "filtfilt", "conv2", "medfilt1",
        "sgolayfilt", "butter", "cheby1", "cheby2", "ellip", "fir1", "freqz",
        "hilbert", "xcorr", "findpeaks", "resample", "decimate", "upsample",
        "downsample", "spectrogram", "periodogram", "pwelch",
        # Sparse
        "sparse", "full", "speye", "spalloc", "sprand", "sprandn", "spdiags",
        "nnz", "spy", "gmres", "pcg", "bicg", "bicgstab", "cgs", "minres",
        "lsqr", "qmr",
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
