"""Recursive-descent parser for MALT MATLAB-like source."""

from __future__ import annotations

from typing import NoReturn, cast

from . import ast_nodes as ast
from .errors import ParseError, SourceLocation
from .lexer import Lexer
from .tokens import Token, TokenType

_ASSIGN_OPS = {
    TokenType.EQ: "=",
    TokenType.PLUS_EQ: "+=",
    TokenType.MINUS_EQ: "-=",
    TokenType.STAR_EQ: "*=",
    TokenType.DOT_STAR_EQ: ".*=",
    TokenType.SLASH_EQ: "/=",
    TokenType.DOT_SLASH_EQ: "./=",
    TokenType.BACKSLASH_EQ: "\\=",
    TokenType.DOT_BACKSLASH_EQ: ".\\=",
    TokenType.CARET_EQ: "^=",
    TokenType.DOT_CARET_EQ: ".^=",
}

_CONTROL_KEYWORDS = {
    "if",
    "elseif",
    "else",
    "for",
    "while",
    "break",
    "continue",
    "return",
    "function",
    "end",
    "global",
    "switch",
    "case",
    "otherwise",
    "try",
    "catch",
}


class Parser:
    def __init__(self, tokens: list[Token], source: str, filename: str = "<malt>") -> None:
        self.tokens = tokens
        self.source = source
        self.filename = filename
        self.index = 0
        self._matrix_context = 0

    # -- token helpers ------------------------------------------------------
    def peek(self, offset: int = 0) -> Token:
        idx = self.index + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.tokens[self.index]
        if tok.type != TokenType.EOF:
            self.index += 1
        return tok

    def at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def match(self, *types: TokenType) -> Token | None:
        if self.peek().type in types:
            return self.advance()
        return None

    def expect(self, type: TokenType, message: str) -> Token:
        tok = self.peek()
        if tok.type != type:
            raise ParseError(message, tok.location)
        return self.advance()

    def error(self, message: str, tok: Token | SourceLocation | None = None) -> NoReturn:
        t = tok if isinstance(tok, Token) else (tok or self.peek())
        if isinstance(t, Token):
            raise ParseError(message, t.location)
        raise ParseError(message, t)

    def _with_span(self, node: ast.Statement) -> ast.Statement:
        """Attach an end position to ``node`` spanning the just-parsed text."""
        last = self.tokens[self.index - 1] if self.index > 0 else self.peek()
        end = last.end_location
        loc = node.location
        node.location = SourceLocation(
            loc.filename,
            loc.line,
            loc.column,
            end_line=end.line,
            end_column=end.column,
        )
        return node

    # -- newline handling ---------------------------------------------------
    def skip_newlines(self) -> None:
        while self.peek().type == TokenType.NEWLINE:
            self.advance()

    # -- program ------------------------------------------------------------
    def parse_program(self) -> list[ast.Statement]:
        statements: list[ast.Statement] = []
        while not self.at_end():
            self.skip_newlines()
            if self.at_end():
                break
            stmt = self.parse_statement()
            self._with_span(stmt)
            statements.append(stmt)
            # terminators
            if self.match(TokenType.SEMICOLON):
                stmt.suppress = True
                self.skip_newlines()
            elif self.match(TokenType.COMMA):
                self.skip_newlines()
            elif self.peek().type == TokenType.NEWLINE:
                self.skip_newlines()
            elif self.at_end():
                pass
            else:
                self.error(f"unexpected token {self.peek().raw!r}")
        return statements

    # -- statements ---------------------------------------------------------
    def parse_statement(self) -> ast.Statement:
        tok = self.peek()
        if tok.type == TokenType.IDENT:
            name = tok.value
            if name == "function":
                return self.parse_function()
            if name == "if":
                return self.parse_if()
            if name == "for":
                return self.parse_for()
            if name == "while":
                return self.parse_while()
            if name == "switch":
                return self.parse_switch()
            if name == "try":
                return self.parse_try()
            if name == "break":
                return self.parse_break()
            if name == "continue":
                return self.parse_continue()
            if name == "return":
                return self.parse_return()
            if name == "global":
                return self.parse_global()
            # command syntax: `grid on`, `close all`, `axis tight`
            nxt = self.peek(1)
            if nxt.type in (TokenType.IDENT, TokenType.STRING):
                return self.parse_command()

        lhs = self.parse_expression()

        if self.peek().type in _ASSIGN_OPS:
            op_tok = self.advance()
            op = _ASSIGN_OPS[op_tok.type]
            value = self.parse_expression()
            if isinstance(lhs, ast.MatrixLiteral):
                targets: list[ast.Node] = []
                for row in lhs.rows:
                    targets.extend(row)
                if not targets:
                    self.error("empty assignment target list")
                for t in targets:
                    if not isinstance(t, (ast.Identifier, ast.FunctionCall)):
                        self.error("invalid assignment target", t.location)
                return ast.Assignment(targets, value, op, lhs.location)
            if isinstance(lhs, (ast.Identifier, ast.FunctionCall, ast.CellIndexExpression, ast.FieldAccess)):
                return ast.Assignment([lhs], value, op, lhs.location)
            self.error("invalid assignment target", lhs.location)

        return ast.ExpressionStatement(lhs, lhs.location)

    def parse_command(self) -> ast.Statement:
        name_tok = self.advance()
        args: list[ast.Node] = []
        while self.peek().type in (TokenType.IDENT, TokenType.STRING):
            arg_tok = self.advance()
            args.append(
                ast.StringLiteral(str(arg_tok.value), arg_tok.location)
            )
        call = ast.FunctionCall(str(name_tok.value), args, name_tok.location)
        return ast.ExpressionStatement(call, name_tok.location)

    def parse_function(self) -> ast.FunctionDefinition:
        start = self.expect(TokenType.IDENT, "expected 'function'")  # 'function'
        loc = start.location

        outputs: list[str] = []
        if self.match(TokenType.LBRACKET):
            self.skip_newlines()
            while True:
                name_tok = self.expect(TokenType.IDENT, "expected output name")
                outputs.append(str(name_tok.value))
                self.skip_newlines()
                if self.match(TokenType.COMMA):
                    self.skip_newlines()
                    continue
                break
            self.expect(TokenType.RBRACKET, "expected ']'")
            self.skip_newlines()
            self.expect(TokenType.EQ, "expected '=' in function definition")
        elif (
            self.peek().type == TokenType.IDENT
            and self.peek(1).type == TokenType.EQ
        ):
            out_tok = self.advance()
            outputs.append(str(out_tok.value))
            self.advance()  # '='
        self.skip_newlines()

        fname_tok = self.expect(TokenType.IDENT, "expected function name")
        fname = str(fname_tok.value)

        params: list[str] = []
        if self.match(TokenType.LPAREN):
            self.skip_newlines()
            while True:
                p_tok = self.expect(TokenType.IDENT, "expected parameter name")
                params.append(str(p_tok.value))
                self.skip_newlines()
                if self.match(TokenType.COMMA):
                    self.skip_newlines()
                    continue
                break
            self.expect(TokenType.RPAREN, "expected ')'")

        if not outputs:
            outputs = [fname]

        self.skip_newlines()
        body = self.parse_block("function")
        self.expect_block_end("function", start)
        return ast.FunctionDefinition(fname, outputs, params, body, loc)

    def parse_if(self) -> ast.IfStatement:
        start = self.advance()  # 'if'
        branches: list[tuple[ast.Node, list[ast.Statement]]] = []
        cond = self.parse_expression()
        self.skip_newlines()
        body = self.parse_block("if")
        branches.append((cond, body))
        else_body: list[ast.Statement] | None = None

        while True:
            self.skip_newlines()
            tok = self.peek()
            if tok.type == TokenType.IDENT and tok.value == "elseif":
                self.advance()
                self.skip_newlines()
                c = self.parse_expression()
                self.skip_newlines()
                b = self.parse_block("elseif")
                branches.append((c, b))
                continue
            if tok.type == TokenType.IDENT and tok.value == "else":
                self.advance()
                self.skip_newlines()
                else_body = self.parse_block("else")
                break
            break

        self.expect_block_end("if", start)
        return ast.IfStatement(branches, else_body, start.location)

    def parse_for(self) -> ast.ForStatement:
        start = self.advance()  # 'for'
        var_tok = self.expect(TokenType.IDENT, "expected loop variable")
        self.expect(TokenType.EQ, "expected '=' in for statement")
        iterable = self.parse_expression()
        self.skip_newlines()
        body = self.parse_block("for")
        self.expect_block_end("for", start)
        return ast.ForStatement(str(var_tok.value), iterable, body, start.location)

    def parse_while(self) -> ast.WhileStatement:
        start = self.advance()  # 'while'
        cond = self.parse_expression()
        self.skip_newlines()
        body = self.parse_block("while")
        self.expect_block_end("while", start)
        return ast.WhileStatement(cond, body, start.location)

    def parse_switch(self) -> ast.SwitchStatement:
        start = self.advance()  # 'switch'
        value = self.parse_expression()
        self.skip_newlines()
        cases: list[tuple[ast.Node, list[ast.Statement]]] = []
        otherwise: list[ast.Statement] | None = None

        while True:
            self.skip_newlines()
            tok = self.peek()
            if tok.type == TokenType.IDENT and tok.value == "case":
                self.advance()
                self.skip_newlines()
                test = self.parse_expression()
                self.skip_newlines()
                body = self.parse_block("case")
                cases.append((test, body))
                continue
            if tok.type == TokenType.IDENT and tok.value == "otherwise":
                self.advance()
                self.skip_newlines()
                otherwise = self.parse_block("otherwise")
                break
            break

        self.expect_block_end("switch", start)
        return ast.SwitchStatement(value, cases, otherwise, start.location)

    def parse_try(self) -> ast.TryStatement:
        start = self.advance()  # 'try'
        self.skip_newlines()
        try_body = self.parse_block("try")

        catch_var: str | None = None
        self.skip_newlines()
        tok = self.peek()
        if tok.type == TokenType.IDENT and tok.value == "catch":
            self.advance()
            # A catch variable is an identifier on the SAME line as `catch`;
            # a newline before the identifier means it starts the catch body.
            if self.peek().type == TokenType.IDENT:
                catch_var = str(self.advance().value)
            self.skip_newlines()
            catch_body = self.parse_block("catch")
        else:
            catch_body = []

        self.expect_block_end("try", start)
        return ast.TryStatement(try_body, catch_var, catch_body, start.location)

    def parse_break(self) -> ast.BreakStatement:
        tok = self.advance()
        return ast.BreakStatement(tok.location)

    def parse_continue(self) -> ast.ContinueStatement:
        tok = self.advance()
        return ast.ContinueStatement(tok.location)

    def parse_return(self) -> ast.ReturnStatement:
        tok = self.advance()
        return ast.ReturnStatement(tok.location)

    def parse_global(self) -> ast.Statement:
        start = self.advance()
        names: list[str] = []
        while True:
            t = self.expect(TokenType.IDENT, "expected variable name after 'global'")
            names.append(str(t.value))
            if not self.match(TokenType.COMMA):
                break
        # `global` is parsed but treated as a no-op for the supported subset.
        return ast.ExpressionStatement(
            ast.NumberLiteral(0.0, start.location), start.location
        )

    def parse_block(self, owner: str) -> list[ast.Statement]:
        statements: list[ast.Statement] = []
        while True:
            self.skip_newlines()
            tok = self.peek()
            if tok.type == TokenType.EOF:
                self.error(f"missing 'end' for {owner!r} block", tok)
            if tok.type == TokenType.IDENT and tok.value == "end":
                break
            if tok.type == TokenType.IDENT and tok.value in ("elseif", "else", "case", "otherwise", "catch"):
                break
            stmt = self.parse_statement()
            statements.append(stmt)
            if self.match(TokenType.SEMICOLON):
                stmt.suppress = True
            elif self.match(TokenType.COMMA):
                pass
            elif self.peek().type == TokenType.NEWLINE:
                self.skip_newlines()
            elif self.at_end():
                self.error(f"missing 'end' for {owner!r} block")
            else:
                self.error(f"unexpected token {self.peek().raw!r}")
        return statements

    def expect_block_end(self, owner: str, start: Token) -> None:
        tok = self.peek()
        if tok.type == TokenType.IDENT and tok.value == "end":
            self.advance()
            return
        self.error(f"missing 'end' for {owner!r} block", start)

    # -- expressions --------------------------------------------------------
    def parse_expression(self) -> ast.Node:
        return self.parse_or()

    def parse_or(self) -> ast.Node:
        left = self.parse_and()
        while self.peek().type == TokenType.OR_OR:
            op = self.advance()
            right = self.parse_and()
            left = ast.BinaryOperation("||", left, right, op.location)
        return left

    def parse_and(self) -> ast.Node:
        left = self.parse_bitor()
        while self.peek().type == TokenType.AND_AND:
            op = self.advance()
            right = self.parse_bitor()
            left = ast.BinaryOperation("&&", left, right, op.location)
        return left

    def parse_bitor(self) -> ast.Node:
        left = self.parse_bitand()
        while self.peek().type == TokenType.PIPE:
            op = self.advance()
            right = self.parse_bitand()
            left = ast.BinaryOperation("|", left, right, op.location)
        return left

    def parse_bitand(self) -> ast.Node:
        left = self.parse_relational()
        while self.peek().type == TokenType.AMP:
            op = self.advance()
            right = self.parse_relational()
            left = ast.BinaryOperation("&", left, right, op.location)
        return left

    def parse_relational(self) -> ast.Node:
        left = self.parse_colon()
        while self.peek().type in (
            TokenType.EQ_EQ,
            TokenType.NE,
            TokenType.LT,
            TokenType.LE,
            TokenType.GT,
            TokenType.GE,
        ):
            op = self.advance()
            right = self.parse_colon()
            left = ast.BinaryOperation(op.raw, left, right, op.location)
        return left

    def parse_colon(self) -> ast.Node:
        start = self.parse_addsub()
        if self.match(TokenType.COLON):
            step: ast.Node | None = None
            first = start
            colon_loc = self.tokens[self.index - 1].location
            # middle (step) only if there is another colon after the next operand
            mid = self.parse_addsub()
            if self.match(TokenType.COLON):
                step = mid
                end = self.parse_addsub()
                return ast.ColonExpression(first, step, end, colon_loc)
            return ast.ColonExpression(first, None, mid, colon_loc)
        return start

    def parse_addsub(self) -> ast.Node:
        left = self.parse_mul()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.peek()
            # In a matrix literal, a spaced +/- begins a new element.
            if self._matrix_context > 0 and op.spaced:
                break
            self.advance()
            right = self.parse_mul()
            left = ast.BinaryOperation(op.raw, left, right, op.location)
        return left

    def parse_mul(self) -> ast.Node:
        left = self.parse_unary()
        while self.peek().type in (
            TokenType.STAR,
            TokenType.SLASH,
            TokenType.BACKSLASH,
            TokenType.DOT_STAR,
            TokenType.DOT_SLASH,
            TokenType.DOT_BACKSLASH,
        ):
            op = self.advance()
            right = self.parse_unary()
            left = ast.BinaryOperation(op.raw, left, right, op.location)
        return left

    def parse_unary(self) -> ast.Node:
        tok = self.peek()
        if tok.type in (TokenType.PLUS, TokenType.MINUS, TokenType.TILDE):
            self.advance()
            operand = self.parse_unary()
            return ast.UnaryOperation(tok.raw, operand, tok.location)
        return self.parse_power()

    def parse_power(self) -> ast.Node:
        left = self.parse_postfix()
        if self.peek().type in (TokenType.CARET, TokenType.DOT_CARET):
            op = self.advance()
            right = self.parse_unary()  # right-associative
            return ast.BinaryOperation(op.raw, left, right, op.location)
        return left

    def parse_postfix(self) -> ast.Node:
        node = self.parse_primary()
        while True:
            if self.peek().type in (TokenType.TRANSPOSE, TokenType.DOT_TRANSPOSE):
                op = self.advance()
                node = ast.UnaryOperation(op.raw, node, op.location)
                continue
            if self.peek().type == TokenType.DOT:
                dot = self.advance()
                field = self.expect(TokenType.IDENT, "expected field name after '.'")
                node = ast.FieldAccess(node, str(field.value), dot.location)
                continue
            if self.peek().type == TokenType.LBRACE:
                brace = self.advance()
                args = self.parse_brace_args()
                node = ast.CellIndexExpression(node, args, brace.location)
                continue
            break
        return node

    def parse_brace_args(self) -> list[ast.Node]:
        self.skip_newlines()
        args: list[ast.Node] = []
        if self.match(TokenType.RBRACE):
            return args
        while True:
            self.skip_newlines()
            args.append(self.parse_expression())
            self.skip_newlines()
            if self.match(TokenType.COMMA):
                continue
            break
        self.expect(TokenType.RBRACE, "expected '}' after arguments")
        return args

    def parse_primary(self) -> ast.Node:
        tok = self.peek()
        if tok.type == TokenType.INTEGER:
            self.advance()
            return ast.NumberLiteral(float(cast(int, tok.value)), tok.location)
        if tok.type == TokenType.FLOAT:
            self.advance()
            return ast.NumberLiteral(cast("float | complex", tok.value), tok.location)
        if tok.type == TokenType.STRING:
            self.advance()
            return ast.StringLiteral(str(tok.value), tok.location)
        if tok.type == TokenType.LPAREN:
            self.advance()
            self.skip_newlines()
            expr = self.parse_expression()
            self.skip_newlines()
            self.expect(TokenType.RPAREN, "expected ')'")
            return expr
        if tok.type == TokenType.LBRACKET:
            return self.parse_matrix()
        if tok.type == TokenType.LBRACE:
            return self.parse_cell()
        if tok.type == TokenType.AT:
            return self.parse_at()
        if tok.type == TokenType.COLON:
            self.advance()
            return ast.ColonArgument(tok.location)
        if tok.type == TokenType.IDENT:
            name = str(tok.value)
            if name == "true":
                self.advance()
                return ast.LogicalLiteral(True, tok.location)
            if name == "false":
                self.advance()
                return ast.LogicalLiteral(False, tok.location)
            if name == "end":
                self.advance()
                return ast.EndKeyword(tok.location)
            self.advance()
            if self.match(TokenType.LPAREN):
                args = self.parse_call_args()
                return ast.FunctionCall(name, args, tok.location)
            return ast.Identifier(name, tok.location)
        self.error(f"unexpected token {tok.raw!r}", tok)

    def parse_call_args(self) -> list[ast.Node]:
        self.skip_newlines()
        args: list[ast.Node] = []
        if self.match(TokenType.RPAREN):
            return args
        while True:
            self.skip_newlines()
            args.append(self.parse_expression())
            self.skip_newlines()
            if self.match(TokenType.COMMA):
                continue
            break
        self.expect(TokenType.RPAREN, "expected ')' after arguments")
        return args

    def parse_at(self) -> ast.Node:
        at_tok = self.advance()  # '@'
        if self.match(TokenType.LPAREN):
            params: list[str] = []
            self.skip_newlines()
            while True:
                p = self.expect(TokenType.IDENT, "expected anonymous function parameter")
                params.append(str(p.value))
                self.skip_newlines()
                if self.match(TokenType.COMMA):
                    continue
                break
            self.expect(TokenType.RPAREN, "expected ')'")
            self.skip_newlines()
            body = self.parse_expression()
            return ast.AnonymousFunction(params, body, at_tok.location)
        name_tok = self.expect(TokenType.IDENT, "expected function name after '@'")
        return ast.FunctionHandle(str(name_tok.value), at_tok.location)

    def parse_matrix(self) -> ast.MatrixLiteral:
        start = self.expect(TokenType.LBRACKET, "expected '['")
        self._matrix_context += 1
        try:
            rows: list[list[ast.Node]] = [[]]
            while True:
                self.skip_newlines()
                if self.match(TokenType.RBRACKET):
                    break
                if self.match(TokenType.SEMICOLON):
                    rows.append([])
                    self.skip_newlines()
                    continue
                elem = self.parse_expression()
                rows[-1].append(elem)
                self.skip_newlines()
                if self.match(TokenType.COMMA):
                    continue
                if self.peek().type in (TokenType.RBRACKET, TokenType.SEMICOLON):
                    continue
                # whitespace-separated: loop again
        finally:
            self._matrix_context -= 1
        # drop trailing empty rows from e.g. [1 2;]
        while rows and not rows[-1]:
            rows.pop()
        return ast.MatrixLiteral(rows, start.location)

    def parse_cell(self) -> ast.CellLiteral:
        start = self.expect(TokenType.LBRACE, "expected '{'")
        self._matrix_context += 1
        try:
            rows: list[list[ast.Node]] = [[]]
            while True:
                self.skip_newlines()
                if self.match(TokenType.RBRACE):
                    break
                if self.match(TokenType.SEMICOLON):
                    rows.append([])
                    self.skip_newlines()
                    continue
                elem = self.parse_expression()
                rows[-1].append(elem)
                self.skip_newlines()
                if self.match(TokenType.COMMA):
                    continue
                if self.peek().type in (TokenType.RBRACE, TokenType.SEMICOLON):
                    continue
        finally:
            self._matrix_context -= 1
        while rows and not rows[-1]:
            rows.pop()
        return ast.CellLiteral(rows, start.location)


def parse(source: str, filename: str = "<malt>") -> list[ast.Statement]:
    lexer = Lexer(source, filename)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source, filename)
    return parser.parse_program()
