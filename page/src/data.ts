export const REPO = 'https://github.com/NacreousDawn596/MALT';
export const RAW_DOC = `${REPO}/blob/master/`;
export const RELEASES = `${REPO}/releases/latest`;
export const VERSION = '0.4.3';

export type Example = {
  id: string;
  label: string;
  eyebrow: string;
  code: string;
  output: string;
  description: string;
  kind: 'matrix' | 'loop' | 'plot';
};

export const examples: Example[] = [
  {
    id: 'matrix', label: 'Matrices', eyebrow: 'LINEAR ALGEBRA', kind: 'matrix',
    code: `A = [1 2; 3 4];\nB = A^2;\ndisp(B);`,
    output: `7   10\n15  22`,
    description: 'Matrix power follows matrix multiplication, not element-wise multiplication. The result keeps MATLAB-style two-dimensional shape conventions.',
  },
  {
    id: 'loop', label: 'Control flow', eyebrow: 'SCALAR COMPUTATION', kind: 'loop',
    code: `total = 0;\nfor k = 1:100\n    total = total + k;\nend\ndisp(total);`,
    output: `5050`,
    description: 'A familiar MATLAB loop. Eligible scalar-accumulation patterns can use MALT’s conservative level-2 loop specialization.',
  },
  {
    id: 'plot', label: 'Graphics', eyebrow: 'NUMERICAL VISUALIZATION', kind: 'plot',
    code: `x = linspace(0, 2*pi, 200);\ny = sin(x);\nplot(x, y, 'LineWidth', 2);\ntitle('A function, in motion');\ngrid on;`,
    output: 'A two-dimensional sine curve',
    description: 'MALT’s graphics layer maps MATLAB-like plotting calls to Matplotlib. This browser preview illustrates the function; it is not executing MALT in the browser.',
  },
];

export const docs = [
  { title: 'Project overview', group: 'Start here', path: 'README.md', description: 'What MALT is, quick start, CLI commands, and the complete toolchain.', tags: 'overview introduction getting started readme' },
  { title: 'Installation', group: 'Start here', path: 'docs/installation.md', description: 'Debian, portable Linux, Nix, and Windows installation instructions.', tags: 'install download linux windows deb nix' },
  { title: 'Language support', group: 'Language', path: 'docs/language-support.md', description: 'The tested MATLAB subset, syntax, operators, numerical functions, and limitations.', tags: 'features syntax functions numerics graphics' },
  { title: 'Language semantics', group: 'Language', path: 'docs/semantics.md', description: 'The normative reference for types, shapes, indexing, operators, and runtime behavior.', tags: 'semantics arrays shapes indexing operators' },
  { title: 'Compatibility matrix', group: 'Language', path: 'docs/compatibility-matrix.md', description: 'Implemented, partial, unsupported, and intentionally different behavior.', tags: 'matlab octave compatibility support' },
  { title: 'Cell arrays', group: 'Language', path: 'docs/specs/cell-arrays.md', description: 'Cell literals, content indexing, assignment, and current limitations.', tags: 'cell arrays braces' },
  { title: 'Structs', group: 'Language', path: 'docs/specs/structs.md', description: 'Scalar struct construction and field access semantics.', tags: 'struct fields' },
  { title: 'Try / catch', group: 'Language', path: 'docs/specs/try-catch.md', description: 'Error handling, error values, and control-flow semantics.', tags: 'exceptions errors try catch' },
  { title: 'Architecture', group: 'Internals', path: 'docs/architecture.md', description: 'The compiler pipeline, generated Python, runtime namespace, source maps, and optimization.', tags: 'compiler lexer parser ast codegen cpython runtime' },
  { title: 'Python API', group: 'Internals', path: 'docs/api.md', description: 'Embedding MALT, compile_source, execution, errors, diagnostics, and API guarantees.', tags: 'python api library embed' },
  { title: 'Testing and correctness', group: 'Internals', path: 'docs/testing.md', description: 'Unit tests, semantic regressions, and differential testing methodology.', tags: 'tests testing octave correctness' },
  { title: 'Benchmarks', group: 'Internals', path: 'benchmarks/README.md', description: 'Benchmark methodology, environment metadata, and performance measurements.', tags: 'performance speed benchmark' },
  { title: 'Editor integration', group: 'Tooling', path: 'docs/editor-integration.md', description: 'Connect the MALT language server to VS Code, Neovim, and Helix.', tags: 'lsp vscode neovim helix editor' },
  { title: 'NixOS', group: 'Tooling', path: 'docs/nixos.md', description: 'Native flake usage, profile installation, and development shell.', tags: 'nix nixos flake' },
  { title: 'Packaging guide', group: 'Tooling', path: 'packaging/README.md', description: 'How platform distributions are built and verified.', tags: 'debian windows pyinstaller installer packaging' },
  { title: 'Changelog', group: 'Project', path: 'CHANGELOG.md', description: 'Version-by-version release history and fixes.', tags: 'release versions history' },
  { title: 'License', group: 'Project', path: 'LICENSE', description: 'MALT is distributed under the MIT License.', tags: 'mit legal license' },
];

export type Feature = { name: string; group: string; status: 'Implemented' | 'Partial' | 'Unsupported' | 'Different'; note: string; doc: string };
export const compatibility: Feature[] = [
  { name: 'One-based indexing, end, colon ranges', group: 'Arrays', status: 'Implemented', note: 'Includes linear, multidimensional, vector, and logical indexing.', doc: 'docs/semantics.md' },
  { name: 'Column-major reshape and traversal', group: 'Arrays', status: 'Implemented', note: 'MATLAB-style column-major semantics.', doc: 'docs/semantics.md' },
  { name: 'N-dimensional arrays', group: 'Arrays', status: 'Partial', note: 'Constructible, with more limited indexing coverage.', doc: 'docs/language-support.md' },
  { name: 'Cell arrays', group: 'Data', status: 'Partial', note: 'Literals and c{idx} content access/assignment; no cell slicing, c{:}, or cell(n).', doc: 'docs/specs/cell-arrays.md' },
  { name: 'Structs', group: 'Data', status: 'Partial', note: 'Scalar structs and dot fields; struct arrays are not supported.', doc: 'docs/specs/structs.md' },
  { name: 'Function handles and anonymous functions', group: 'Functions', status: 'Implemented', note: 'Includes feval, func2str, and builtin-only str2func resolution.', doc: 'docs/language-support.md' },
  { name: 'Nested functions', group: 'Functions', status: 'Unsupported', note: 'Not part of the current supported subset.', doc: 'docs/language-support.md' },
  { name: 'Control flow and try/catch', group: 'Language', status: 'Implemented', note: 'if, for, while, switch, try/catch, break, continue, return.', doc: 'docs/semantics.md' },
  { name: '2-D and 3-D graphics', group: 'Graphics', status: 'Implemented', note: 'Matplotlib-backed plots, surfaces, images, subplots, and PNG export.', doc: 'docs/language-support.md' },
  { name: 'Numerical integration and ode45', group: 'Numerics', status: 'Implemented', note: 'SciPy-backed numerical routines; ode45 uses RK45 / Dormand–Prince.', doc: 'docs/language-support.md' },
  { name: 'File I/O functions (load/save/fopen)', group: 'I/O', status: 'Unsupported', note: 'These file I/O APIs are not currently implemented.', doc: 'docs/language-support.md' },
  { name: 'Case sensitivity', group: 'Differences', status: 'Different', note: 'MALT identifiers are case-sensitive by design.', doc: 'docs/compatibility-matrix.md' },
  { name: 'Numeric type model', group: 'Differences', status: 'Different', note: 'A single double/complex numeric type rather than MATLAB’s full type system.', doc: 'docs/semantics.md' },
  { name: 'Array auto-growth', group: 'Differences', status: 'Different', note: 'Indexed assignment does not automatically grow arrays.', doc: 'docs/compatibility-matrix.md' },
];

export const pipeline = [
  { name: 'Source', tag: '.m', detail: 'A MATLAB-like program is read as source text, with original file and location information preserved throughout compilation.' },
  { name: 'Lexer', tag: 'TOKENS', detail: 'The lexer turns source characters into location-aware tokens. Whitespace and source positions remain available for accurate diagnostics.' },
  { name: 'Parser', tag: 'AST', detail: 'A recursive-descent parser builds immutable, structured syntax nodes while applying operator precedence and block structure.' },
  { name: 'Semantics', tag: 'CHECKS', detail: 'Semantic analysis validates language rules such as loop-control placement and duplicate function definitions.' },
  { name: 'Code generation', tag: 'PYTHON', detail: 'MALT lowers the language AST into readable Python source and emits a source map linking generated lines to the original .m file.' },
  { name: 'CPython', tag: 'CODE OBJECT', detail: 'Generated Python is compiled in memory with CPython. MALT does not write an intermediate Python program to disk as the execution mechanism.' },
  { name: 'Runtime', tag: 'NUMPY · SCIPY · MPL', detail: 'A dedicated runtime supplies MATLAB-specific semantics for arrays, indexing, operators, functions, numerical routines, and graphics.' },
];
