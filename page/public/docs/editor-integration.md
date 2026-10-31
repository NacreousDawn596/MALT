# Editor integration

MALT ships a language server (`malt lsp`) that speaks the Language Server
Protocol over stdio. It provides:

- **Diagnostics** — parse/semantic errors and warnings (e.g. shadowing a
  builtin) as you type, with error codes (`E####`, `W####`).
- **Hover** — one-line help for builtin functions, keywords, and constants.
- **Completion** — builtin functions, control keywords, and constants.

It has no external dependencies, so it works anywhere `malt` runs. Any LSP
client can attach to it; the commands below are the common ones.

## VS Code

Create `.vscode/extensions.json`-style client config (or use a generic
extension that launches a command). With the
[`malt-ls` or a generic "language server" runner], configure:

```jsonc
// .vscode/settings.json
{
  "malt.server.path": "malt",
  "malt.server.args": ["lsp"]
}
```

Alternatively, use the *"LSP"* family of generic extensions and point the
command at `nix develop -c python -m malt lsp` (inside the dev shell) or at a
wrapper script that runs `malt lsp` from the Nix environment.

## Neovim (native LSP client)

```lua
vim.api.nvim_create_autocmd("FileType", {
  pattern = "matlab",
  callback = function()
    vim.lsp.start({
      name = "malt",
      cmd = { "malt", "lsp" },
      root_dir = vim.fs.dirname(vim.fs.find({ ".git" }, { upward = true })[1]),
    })
  end,
})
```

Set the filetype to `matlab` for `.m` files (e.g. via
`vim.filetype.add({ extension = { m = "matlab" } })`).

## Helix

```toml
# languages.toml
[[language]]
name = "matlab"
language-servers = ["malt"]

[language-server.malt]
command = "malt"
args = ["lsp"]
```

## Testing the server by hand

The server speaks JSON-RPC with `Content-Length` framing on stdin/stdout:

```bash
printf 'Content-Length: 41\r\n\r\n{"jsonrpc":"2.0","id":1,"method":"initialize"}' | malt lsp
```

See `tests/unit/test_lsp.py` for the framing and message-handling contract.

## Current limitations

- Diagnostics are published on the whole document; a syntax error stops
  compilation, so warnings are not reported alongside a parse error in the
  same document.
- Completion is static (builtins + keywords + constants); workspace-variable
  completion requires executing the program, which the server does not do.
