"""
@Author   :
@Time     : 2024/3/8 15:04
Function: sgf语法
"""
from __future__ import absolute_import
import re
import string

import six


_propident_re = re.compile(r"\A[A-Z]{1,8}\Z".encode('ascii'))
_propvalue_re = re.compile(r"\A [^\\\]]* (?: \\. [^\\\]]* )* \Z".encode('ascii'),
                           re.VERBOSE | re.DOTALL)
_find_start_re = re.compile(r"\(\s*;".encode('ascii'))
_tokenise_re = re.compile(r"""
\s*
(?:
    \[ (?P<V> [^\\\]]* (?: \\. [^\\\]]* )* ) \]   # PropValue
    |
    (?P<I> [A-Z]{1,8} )                           # PropIdent
    |
    (?P<D> [;()] )                                # delimiter
)
""".encode('ascii'), re.VERBOSE | re.DOTALL)


def is_valid_property_identifier(s):
    return bool(_propident_re.search(s))


def is_valid_property_value(s):
    return bool(_propvalue_re.search(s))


def tokenise(s, start_position=0):
    result = []
    m = _find_start_re.search(s, start_position)
    if not m:
        return [], 0
    i = m.start()
    depth = 0
    while True:
        m = _tokenise_re.match(s, i)
        if not m:
            break
        group = m.lastgroup
        token = m.group(m.lastindex)
        result.append((group, token))
        i = m.end()
        if group == 'D':
            if token == b'(':
                depth += 1
            elif token == b')':
                depth -= 1
                if depth == 0:
                    break
    return result, i


class Coarse_game_tree:
    def __init__(self):
        self.sequence = []  # must be at least one node
        self.children = []  # may be empty


def _parse_sgf_game(s, start_position):
    tokens, end_position = tokenise(s, start_position)
    if not tokens:
        return None, None
    stack = []
    game_tree = None
    sequence = None
    properties = None
    index = 0
    try:
        while True:
            token_type, token = tokens[index]
            index += 1
            if token_type == 'V':
                raise ValueError("unexpected value")
            if token_type == 'D':
                if token == b';':
                    if sequence is None:
                        raise ValueError("unexpected node")
                    properties = {}
                    sequence.append(properties)
                else:
                    if sequence is not None:
                        if not sequence:
                            raise ValueError("empty sequence")
                        game_tree.sequence = sequence
                        sequence = None
                    if token == b'(':
                        stack.append(game_tree)
                        game_tree = Coarse_game_tree()
                        sequence = []
                    else:
                        # token == ')'
                        variation = game_tree
                        game_tree = stack.pop()
                        if game_tree is None:
                            break
                        game_tree.children.append(variation)
                    properties = None
            else:
                # token_type == 'I'
                prop_ident = token
                prop_values = []
                while True:
                    token_type, token = tokens[index]
                    if token_type != 'V':
                        break
                    index += 1
                    prop_values.append(token)
                if not prop_values:
                    raise ValueError("property with no values")
                try:
                    if prop_ident in properties:
                        properties[prop_ident] += prop_values
                    else:
                        properties[prop_ident] = prop_values
                except TypeError:
                    raise ValueError("property value outside a node")
    except IndexError:
        raise ValueError("unexpected end of SGF data")
    assert index == len(tokens)
    return variation, end_position


def parse_sgf_game(s):
    game_tree, _ = _parse_sgf_game(s, 0)
    if game_tree is None:
        raise ValueError("no SGF data found")
    return game_tree


def parse_sgf_collection(s):
    position = 0
    result = []
    while True:
        try:
            game_tree, position = _parse_sgf_game(s, position)
        except ValueError as e:
            raise ValueError("error parsing game %d: %s" % (len(result), e))
        if game_tree is None:
            break
        result.append(game_tree)
    if not result:
        raise ValueError("no SGF data found")
    return result


def block_format(pieces, width=79):
    lines = []
    line = b""
    for s in pieces:
        if len(line) + len(s) > width:
            lines.append(line)
            line = b""
        line += s
    if line:
        lines.append(line)
    return b"\n".join(lines)


def serialise_game_tree(game_tree, wrap=79):
    l = []
    to_serialise = [game_tree]
    while to_serialise:
        game_tree = to_serialise.pop()
        if game_tree is None:
            l.append(b")")
            continue
        l.append(b"(")
        for properties in game_tree.sequence:
            l.append(b";")
            # Force FF to the front, largely to work around a Quarry bug which
            # makes it ignore the first few bytes of the file.
            for prop_ident, prop_values in sorted(
                    list(properties.items()),
                    key=lambda pair: (-(pair[0] == b"FF"), pair[0])):
                # Make a single string for each property, to get prettier
                # block_format output.
                m = [prop_ident]
                for value in prop_values:
                    m.append(b"[" + value + b"]")
                l.append(b"".join(m))
        to_serialise.append(None)
        to_serialise.extend(reversed(game_tree.children))
    l.append(b"\n")
    if wrap is None:
        return b"".join(l)
    else:
        return block_format(l, wrap)


def make_tree(game_tree, root, node_builder, node_adder):
    to_build = [(root, game_tree, 0)]
    while to_build:
        node, game_tree, index = to_build.pop()
        if index < len(game_tree.sequence) - 1:
            child = node_builder(node, game_tree.sequence[index + 1])
            node_adder(node, child)
            to_build.append((child, game_tree, index + 1))
        else:
            node._children = []
            for child_tree in game_tree.children:
                child = node_builder(node, child_tree.sequence[0])
                node_adder(node, child)
                to_build.append((child, child_tree, 0))


def make_coarse_game_tree(root, get_children, get_properties):
    result = Coarse_game_tree()
    to_serialise = [(result, root)]
    while to_serialise:
        game_tree, node = to_serialise.pop()
        while True:
            game_tree.sequence.append(get_properties(node))
            children = get_children(node)
            if len(children) != 1:
                break
            node = children[0]
        for child in children:
            child_tree = Coarse_game_tree()
            game_tree.children.append(child_tree)
            to_serialise.append((child_tree, child))
    return result


def main_sequence_iter(game_tree):
    while True:
        for properties in game_tree.sequence:
            yield properties
        if not game_tree.children:
            break
        game_tree = game_tree.children[0]


_split_compose_re = re.compile(
    r"( (?: [^\\:] | \\. )* ) :".encode('ascii'),
    re.VERBOSE | re.DOTALL)


def parse_compose(s):
    m = _split_compose_re.match(s)
    if not m:
        return s, None
    return m.group(1), s[m.end():]


def compose(s1, s2):
    return s1.replace(b":", b"\\:") + b":" + s2


_newline_re = re.compile(r"\n\r|\r\n|\n|\r".encode('ascii'))
if six.PY2:
    _binary_maketrans = string.maketrans
else:
    _binary_maketrans = bytes.maketrans
_whitespace_table = _binary_maketrans(b"\t\f\v", b"   ")
_chunk_re = re.compile(r" [^\n\\]+ | [\n\\] ".encode('ascii'), re.VERBOSE)


def simpletext_value(s):
    s = _newline_re.sub(b"\n", s)
    s = s.translate(_whitespace_table)
    is_escaped = False
    result = []
    for chunk in _chunk_re.findall(s):
        if is_escaped:
            if chunk != b"\n":
                result.append(chunk)
            is_escaped = False
        elif chunk == b"\\":
            is_escaped = True
        elif chunk == b"\n":
            result.append(b" ")
        else:
            result.append(chunk)
    return b"".join(result)


def text_value(s):
    s = _newline_re.sub(b"\n", s)
    s = s.translate(_whitespace_table)
    is_escaped = False
    result = []
    for chunk in _chunk_re.findall(s):
        if is_escaped:
            if chunk != b"\n":
                result.append(chunk)
            is_escaped = False
        elif chunk == b"\\":
            is_escaped = True
        else:
            result.append(chunk)
    return b"".join(result)


def escape_text(s):
    return s.replace(b"\\", b"\\\\").replace(b"]", b"\\]")