from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, List, Optional


class SExpressionError(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    value: str
    quoted: bool = False


def tokenize(text: str) -> Iterator[Token]:
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char == ";":
            newline = text.find("\n", index)
            index = length if newline < 0 else newline + 1
            continue
        if char in "()":
            yield Token(char)
            index += 1
            continue
        if char == '"':
            index += 1
            value: List[str] = []
            while index < length:
                char = text[index]
                if char == '"':
                    index += 1
                    break
                if char == "\\" and index + 1 < length:
                    index += 1
                    escaped = text[index]
                    value.append({"n": "\n", "r": "\r", "t": "\t"}.get(escaped, escaped))
                    index += 1
                    continue
                value.append(char)
                index += 1
            else:
                raise SExpressionError("Unterminated quoted string")
            yield Token("".join(value), quoted=True)
            continue
        start = index
        while index < length and not text[index].isspace() and text[index] not in "()":
            index += 1
        yield Token(text[start:index])


def parse(text: str) -> List[Any]:
    stack: List[List[Any]] = []
    roots: List[Any] = []
    for token in tokenize(text):
        if token.value == "(" and not token.quoted:
            node: List[Any] = []
            if stack:
                stack[-1].append(node)
            else:
                roots.append(node)
            stack.append(node)
        elif token.value == ")" and not token.quoted:
            if not stack:
                raise SExpressionError("Unexpected closing parenthesis")
            stack.pop()
        else:
            if not stack:
                raise SExpressionError("Atom outside root expression")
            stack[-1].append(token.value)
    if stack:
        raise SExpressionError("Unclosed parenthesis")
    if len(roots) != 1 or not isinstance(roots[0], list):
        raise SExpressionError("Expected exactly one root expression")
    return roots[0]


def head(node: Any) -> Optional[str]:
    return str(node[0]) if isinstance(node, list) and node else None


def child(node: Any, name: str) -> Optional[List[Any]]:
    if not isinstance(node, list):
        return None
    for item in node[1:]:
        if isinstance(item, list) and head(item) == name:
            return item
    return None


def children(node: Any, name: str) -> List[List[Any]]:
    if not isinstance(node, list):
        return []
    return [item for item in node[1:] if isinstance(item, list) and head(item) == name]


def walk(node: Any) -> Iterable[List[Any]]:
    if not isinstance(node, list):
        return
    yield node
    for item in node[1:]:
        if isinstance(item, list):
            yield from walk(item)


def find(node: Any, name: str) -> List[List[Any]]:
    return [item for item in walk(node) if head(item) == name]


def atom(node: Optional[List[Any]], index: int = 1, default: str = "") -> str:
    if not node or len(node) <= index or isinstance(node[index], list):
        return default
    return str(node[index])


def property_value(node: Any, name: str) -> str:
    for item in children(node, "property"):
        if atom(item, 1) == name:
            return atom(item, 2)
    return ""
