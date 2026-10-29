<div align="center">

<img src="assets/logo.png" alt="MALT logo" width="180">

# 🧮 MALT

### A MATLAB-compatible language runtime, powered by CPython

A standalone language implementation for a documented MATLAB subset — lexed,
parsed, and compiled to Python **in memory**, then executed on
**NumPy / SciPy / Matplotlib**. No MATLAB license, no Engine API, no transpiler.

<br>

![version](https://img.shields.io/badge/version-0.3.0-2ea44f?style=for-the-badge&logo=semver)
![python](https://img.shields.io/badge/python-3.11%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-3da639?style=for-the-badge&logo=open-source-initiative&logoColor=white)
![nixos](https://img.shields.io/badge/reproducible-NixOS-5277c3?style=for-the-badge&logo=nixos&logoColor=white)
![status](https://img.shields.io/badge/status-early--but--correct-orange?style=for-the-badge)

<sub>Made by **Aferiad Kamal** · assisted by **DeepSeek V4 Pro xHigh**</sub>

</div>

---

## What is MALT?

MALT accepts MATLAB-like `.m` source, parses it into a real, location-annotated
AST, runs explicit semantic analysis, lowers it to **readable Python**, and
executes it in-memory on CPython. It is:

- ✅ **A real compiler** — lexer → recursive-descent parser → immutable AST →
  semantic analysis → codegen → in-memory CPython compilation.
- ✅ **A faithful subset** — one-based indexing, `end`, matrix vs. element-wise
  operators, conjugate vs. plain transpose, column-major `reshape`, MATLAB
  shape conventions (scalars are `1×1`).
- ✅ **A complete toolchain** — CLI, REPL, debugger, language server, source
  maps, differential testing against GNU Octave.
- ❌ **Not** a MATLAB clone, a regex transliterator, or a wrapper around the
  commercial MATLAB Engine.

> See [`docs/language-support.md`](docs/language-support.md) for the precise,
> tested feature surface, and [`docs/compatibility-matrix.md`](docs/compatibility-matrix.md)
> for what is implemented / partial / unsupported / intentionally different.

---

## ✨ Highlights

| Area | What you get |
| --- | --- |
| 🧠 **Language** | Full MATLAB subset: matrices, complex numbers, cells `{}`, structs, function handles `@`, anonymous functions, `switch`, `try/catch` |
| ⚡ **Execution** | Three optimization levels — `0` (1×1-array scalars, reference), `1` (native scalars, default), `2` (JIT-specialized loops) |
| 🧮 **Numerics** | Elementary math, reductions, linear algebra, integration, root-finding, `ode45` (Dormand–Prince), complex arithmetic, seeded RNG |
| 📈 **Graphics** | Matplotlib: 2-D/3-D plots, subplots, legends, `surf`, `imagesc`, `colorbar`, PNG export — plus a headless `Agg` mode for CI |
| 🔧 **DX** | Colored diagnostics with error codes, warnings, source maps, an interactive debugger, a polished REPL, and an LSP server |

---

## 🚀 Quick start

### NixOS (recommended, reproducible)

```bash
nix develop                                    # reproducible dev shell
nix develop -c python -m malt --help
nix develop -c python -m malt eval "1 + 2 * 3"
nix develop -c python -m malt run examples/graphics/sine_plot.m
nix develop -c python -m malt repl
nix develop -c pytest                          # full test suite
```

### pip (needs NumPy / SciPy / Matplotlib)

```bash
pip install .                                  # or: python -m pip install -e .
python -m malt --help
```

> For distributed builds — a Debian `.deb`, a Windows `.exe` installer, or a
> Nix profile install — see [docs/installation.md](docs/installation.md).

### Interactive figures

The default backend is headless `Agg` (safe for tests and CI). To open real
figure windows, select a GUI backend and provide a display server:

```bash
MPLBACKEND=Qt5Agg nix develop -c python -m malt run examples/graphics/sine_plot.m
```

`malt run` auto-displays any open figures on exit (like MATLAB); under `Agg`
that is a silent no-op, so use `saveas`/`exportgraphics` to render PNGs there.

---

## 🖥️ CLI reference

```
malt eval "expr"                 # evaluate a MATLAB expression
malt run program.m               # run a script
malt compile program.m           # emit generated Python to stdout
malt debug program.m             # source-level debugger
malt repl                        # interactive session (terminal)
malt gui                         # Qt6 notebook GUI (Apple-style, editable cells)
malt lsp                         # language server (stdio)
```

### Common flags

| Flag | Description |
| --- | --- |
| `--optimization-level 0\|1\|2` | execution strategy (default `1`) |
| `--show-generated` | print the generated Python and exit |
| `--explain` | print the JIT loop-specialization report |
| `--debug` | re-raise with a raw Python traceback |
| `--color auto\|always\|never` / `--no-color` | ANSI color control |
| `--diagnostic-format text\|json` | human or machine-readable diagnostics |
| `--no-warnings` / `--werror` | suppress warnings / treat them as errors |
| `compile --source-map FILE.map` | emit a V3 source map |
| `debug -b LINE` | set a breakpoint at `LINE` |

### Example

```matlab
% examples/graphics/sine_plot.m
x = linspace(0, 2*pi, 200);
y = sin(x);
plot(x, y, 'b-', 'LineWidth', 2);
title('Sine Wave'); xlabel('Time'); ylabel('Amplitude');
grid on;
```

---

## 🧭 Language features

- **Syntax** — integers, floats, scientific notation, imaginary literals (`4i`,
  `3+4i`), single-quoted strings with escapes, `%` comments.
- **Operators** — `+ - * / \ ^` (matrix), `.* ./ .\ .^` (element-wise),
  `' .'` (conjugate / plain transpose), comparisons, `& | ~`, short-circuit
  `&& ||`, `:` colon.
- **Indexing** — one-based, `end`, `A(i,j)`, `A(:)`, `A(:,j)`, logical and
  vector subscripts, indexed assignment.
- **Control flow** — `if`/`elseif`/`else`, `for`, `while`, `switch`/`case`/
  `otherwise`, `try`/`catch`, `break`/`continue`/`return`.
- **Functions** — multi-output `function [a,b] = f(x,y)`, local scope, script
  functions, function handles `@name`, anonymous functions `@(x) …`, plus
  `feval`/`func2str`/`str2func`.
- **Data** — scalars/vectors/matrices (always ≥2-D), complex and logical arrays,
  cell arrays `{}`, structs (`struct`, `fieldnames`, `isfield`, `isstruct`).
- **Numerics** — elementary math, construction (`zeros ones eye rand …`),
  reductions (`sum prod mean min max …`, `any`/`all`), linear algebra
  (`det inv eig svd lu qr …`, `\`/`/`), calculus/ODE (`integral fzero roots ode45`).
- **Strings** — `lower upper strcmp strcmpi strcat strjoin strsplit num2str`.
- **Predicates** — `isnumeric ischar isempty isscalar isvector ismatrix isrow
  iscolumn isreal isfloat islogical isnan isinf isfinite iscell isstruct`.

Full details: [`docs/language-support.md`](docs/language-support.md) ·
[`docs/compatibility-matrix.md`](docs/compatibility-matrix.md).

---

## 🛠️ Developer experience

MALT is designed to be a pleasant tool to *develop in*, not just run.

### 🔎 Diagnostics

Errors carry stable **codes** (`E1001` lex, `E2001` index, `E2003` undefined
variable, …) and optional `help:` hints. Warnings (`W1001` builtin shadowing,
`W1002` `i`/`j` shadowing) are collected, not raised. Everything renders in
color (or JSON for tooling):

```bash
malt run bad.m --no-color
# bad.m:2:1: index exceeds array dimensions [E2001]: index 10 is outside ...
# 2 | result = A(10, 1);
#   | ^^^^^^^^^^^^^^^^^
# help: ...
```

### 🐛 Debugger

A source-level debugger (no generated-Python exposure) backed by the source map:

```
malt debug program.m -b 12
(maltdbg) n          # next statement
(maltdbg) p x        # evaluate x in the workspace
(maltdbg) c          # continue to the next breakpoint
```

Commands: `break`/`b`, `next`/`n`, `step`/`s`, `continue`/`c`, `print`/`p`,
`list`/`l`, `where`/`w`, `help`, `quit`/`q`.

### 💬 REPL

A persistent terminal session with readline history (persisted to
`~/.malt_history`), tab-completion of builtins and variables, multi-line block
input, and `who`/`whos`/`clear`/`help`:

```
>> A = [1 2; 3 4];
>> for k = 1:2
..   disp(k)
.. end
```

### 📓 Notebook GUI

`malt gui` opens an Apple-style Qt6 notebook (a Jupyter/Colab-like desktop
app): draggable frameless window with traffic lights, editable and re-runnable
cells, syntax highlighting, execution counters (`In [n]:`), **Run all**, and
insert / move / delete cell controls — all sharing one live workspace.

### 🧩 Editor integration

`malt lsp` is a dependency-free **language server** (LSP over stdio) providing
diagnostics, hover, and completion. Wire it into VS Code, Neovim, or Helix —
see [`docs/editor-integration.md`](docs/editor-integration.md).

### 🗺️ Source maps

`malt compile --source-map out.map` emits a standard **V3** (base64-VLQ) source
map mapping generated Python back to MATLAB source, plus a
`sourceMappingURL` directive.

---

## 📚 Documentation

| Doc | Purpose |
| --- | --- |
| [`docs/semantics.md`](docs/semantics.md) | normative language reference |
| [`docs/compatibility-matrix.md`](docs/compatibility-matrix.md) | implemented / partial / unsupported / different |
| [`docs/language-support.md`](docs/language-support.md) | tested feature surface + limitations |
| [`docs/api.md`](docs/api.md) | Python API, compiler options, error model |
| [`docs/architecture.md`](docs/architecture.md) | pipeline, runtime, security model |
| [`docs/nixos.md`](docs/nixos.md) | reproducible environment + graphics |
| [`docs/installation.md`](docs/installation.md) | distributed builds (`.deb`, Windows, Nix) |
| [`docs/testing.md`](docs/testing.md) | test strategy + differential testing |
| [`docs/editor-integration.md`](docs/editor-integration.md) | LSP setup for editors |
| [`docs/specs/`](docs/specs/) | feature specs: try/catch, cell arrays, structs |

---

## 🧪 Testing

```bash
nix develop -c pytest                                    # 547 tests
MALT_REQUIRE_OCTAVE=1 nix develop -c pytest              # include Octave differential
nix develop -c ruff check .                              # lint
nix develop -c mypy src/malt                             # type check
nix flake check                                          # build + package
```

- **Unit** — lexer, parser, codegen, source maps, REPL, LSP, fuzzing.
- **Integration** — CLI (`eval`, `run`, `compile`, `debug`), debugger.
- **Compatibility** — `.m` fixtures run through the real compiler/runtime.
- **Graphics** — inspected via real Matplotlib artists, headless `Agg`.
- **Differential** — same source run through MALT and GNU Octave, compared.

---

## 📦 Project layout

```
src/malt/
  lexer.py tokens.py parser.py ast_nodes.py     # front end
  semantic.py ir.py codegen.py compiler.py      # middle end
  builtins.py sourcemap.py diagnostics.py       # shared registries + DX
  executor.py errors.py debugger.py lsp.py      # execution, errors, tooling
  runtime/                                      # MATLAB-compatible runtime
    arrays.py operators.py indexing.py functions.py
    linear_algebra.py calculus.py ode.py io.py graphics.py
    cells.py compat.py handles.py
  repl/session.py
tests/       unit · integration · compatibility · graphics · errors · security · differential
examples/    basics · linear_algebra · calculus · differential_equations · graphics
benchmarks/  timing suite + before/after workbenches
docs/        architecture · language-support · nixos · testing · api · semantics · specs/
```

---

## ⚖️ Status

MALT is **early but correct**: a deliberately-scoped, tested subset of MATLAB,
not a full reimplementation. The execution namespace is **not** a security
sandbox — see [`docs/architecture.md`](docs/architecture.md).

### Roadmap

- [x] Cell arrays, structs, function handles, compatibility predicates
- [x] Diagnostics (error codes, warnings, color, JSON)
- [x] Source maps (V3) + spans
- [x] Source-level debugger
- [x] Polished REPL
- [x] Language server (LSP)
- [ ] Full editor integration (tree-sitter grammar, richer hover/completion)
- [ ] Broader numerical / I/O surface (`load`/`save`, more toolboxes)

---

## 📄 License

[MIT](LICENSE) © 2026 MALT contributors · Made by **Aferiad Kamal**, assisted by
**DeepSeek V4 Pro xHigh**.
