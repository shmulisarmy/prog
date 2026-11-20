"""Parse source text into the AST used by the compiler: parse(source) -> Program."""

import re

from ast_ import (
    Assignment, Block, ClassDef, Deref, FieldAccess, FunctionCall, FunctionDef, Ident, IfStatement, Number,
    Operation, Pointer, Program, ReturnStmt, Type, Variable,
)
from builtInFunctions import BuiltInFunction


_TOKEN = re.compile(r"[ \t\r]+|\#[^\n]*|\n|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|:=|//|[.&+*/%<>=(),\[\]{};:\-]")
_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")
_PRECEDENCE = {"<": 1, ">": 1, "+": 2, "-": 2, "*": 3, "/": 3, "//": 3, "%": 3}


class Parser:
    def __init__(self, source: str, filename: str = "<source>"):
        self.source = source
        self.filename = filename
        self.tokens = []
        offset = 0
        while offset < len(source):
            match = _TOKEN.match(source, offset)
            if match is None:
                self.error(f"Unexpected character {source[offset]!r}", offset)
            token = match.group()
            if not token.isspace() or token == "\n":
                if not token.startswith("#"):
                    self.tokens.append((token, offset))
            offset = match.end()
        self.tokens.append(("", len(source)))
        self.position = 0

    @property
    def token(self):
        return self.tokens[self.position][0]

    def error(self, message, offset=None):
        if offset is None:
            offset = self.tokens[self.position][1]
        line = self.source.count("\n", 0, offset) + 1
        line_start = self.source.rfind("\n", 0, offset) + 1
        line_end = self.source.find("\n", offset)
        if line_end == -1:
            line_end = len(self.source)
        raise SyntaxError(message, (self.filename, line, offset - line_start + 1,
                                    self.source[line_start:line_end]))

    def accept(self, token):
        if self.token == token:
            self.position += 1
            return True
        return False

    def expect(self, token):
        if not self.accept(token):
            self.error(f"Expected {token!r}, got {self.token or 'end of input'!r}")

    def name(self):
        token = self.token
        if not _NAME.fullmatch(token) or token in {"class", "function", "if", "else", "return"}:
            self.error(f"Expected a name, got {token or 'end of input'!r}")
        self.position += 1
        return token

    def newlines(self):
        while self.accept("\n"):
            pass

    def separators(self):
        while self.token in ("\n", ";"):
            self.position += 1

    def end_statement(self):
        if self.token not in ("\n", ";", "}", ""):
            self.error("Expected a newline or ';' after statement")
        self.separators()

    def parse(self):
        symbols = []
        self.separators()
        while self.token:
            symbols.append(self.variable())
            self.end_statement()
        return Program(symbols)

    def class_def(self):
        self.newlines()
        self.expect("{")
        fields = []
        self.separators()
        while not self.accept("}"):
            if not self.token:
                self.error("Expected '}' before end of input")
            fields.append(self.variable())
            self.end_statement()
        return ClassDef(fields)

    def type(self):
        if self.token in ("class", "function"):
            name = self.token
            self.position += 1
        else:
            name = self.name()
        subtypes = []
        if self.accept("["):
            self.newlines()
            while not self.accept("]"):
                subtypes.append(self.type())
                self.newlines()
                if not self.accept(","):
                    self.expect("]")
                    break
                self.newlines()
        return Type(name, subtypes)

    def variable(self):
        name = self.name()
        if self.accept(":="):
            value = self.expression()
            return Variable(name, Type("class") if isinstance(value, ClassDef) else None, value)
        type_ = self.type()
        value = self.expression() if self.accept("=") else None
        return Variable(name, type_, value)

    def block(self):
        self.newlines()
        self.expect("{")
        statements = []
        self.separators()
        while not self.accept("}"):
            if not self.token:
                self.error("Expected '}' before end of input")
            statements.append(self.statement())
            self.end_statement()
        return Block(statements)

    def statement(self):
        if self.accept(":"):
            return BuiltInFunction(self.name())
        if self.token == "{":
            return self.block()
        if self.accept("return"):
            return ReturnStmt(self.expression())
        if self.accept("if"):
            self.expect("(")
            self.newlines()
            condition = self.expression()
            self.newlines()
            self.expect(")")
            then = self.block()
            # Only consume intervening newlines when an else follows.
            saved = self.position
            self.newlines()
            if self.accept("else"):
                return IfStatement(condition, then, self.block())
            self.position = saved
            return IfStatement(condition, then)
        if _NAME.fullmatch(self.token) and (
            _NAME.fullmatch(self.tokens[self.position + 1][0])
            or self.tokens[self.position + 1][0] == ":="
        ):
            return self.variable()
        expression = self.expression()
        if self.accept("="):
            if not isinstance(expression, (Ident, FieldAccess, Deref)):
                self.error("Assignment target must be a name, field access, or dereference")
            return Assignment(expression, self.expression())
        if not isinstance(expression, FunctionCall):
            self.error("Expected a declaration, assignment, or function call")
        return expression

    def expression(self, minimum=0):
        left = self.primary()
        while self.token in _PRECEDENCE and _PRECEDENCE[self.token] >= minimum:
            op = self.token
            self.position += 1
            self.newlines()
            right = self.expression(_PRECEDENCE[op] + 1)
            left = Operation(op, left, right)
        return left

    def primary(self):
        if self.accept("&"):
            value = Pointer(self.primary())
        elif self.accept("*"):
            value = Deref(self.primary())
        elif self.accept("class"):
            value = self.class_def()
        elif self.accept("function"):
            self.expect("(")
            params = []
            self.newlines()
            while not self.accept(")"):
                params.append(Variable(self.name(), self.type()))
                self.newlines()
                if not self.accept(","):
                    self.expect(")")
                    break
                self.newlines()
            value = FunctionDef(params, self.type(), self.block())
        elif self.accept("("):
            self.newlines()
            value = self.expression()
            self.newlines()
            self.expect(")")
        elif self.token.isdigit():
            value = Number(int(self.token))
            self.position += 1
        elif self.token in ("+", "-"):
            negative = self.accept("-")
            if not negative:
                self.expect("+")
            operand = self.primary()
            value = Operation("-", Number(0), operand) if negative else operand
        else:
            value = Ident(self.name())
        while self.token in (".", "("):
            if self.accept("."):
                value = FieldAccess(value, self.name())
                continue
            self.expect("(")
            args = []
            self.newlines()
            while not self.accept(")"):
                args.append(self.expression())
                self.newlines()
                if not self.accept(","):
                    self.expect(")")
                    break
                self.newlines()
            value = FunctionCall(value, args)
        return value


def parse(source: str, filename: str = "<source>") -> Program:
    return Parser(source, filename).parse()

def parse_file(filename: str = "<source>") -> Program:
    with open(filename, "r") as f:
        return parse(f.read(), filename)
