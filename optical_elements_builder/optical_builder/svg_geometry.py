"""Compare SVG geometry across Inkscape's equivalent path/transform rewrites."""
import math
import re

NUMBER = r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?'
IDENTITY = (1, 0, 0, 1, 0, 0)


def rotation_components(degrees):
    angle = degrees % 360
    if angle in (0, 90, 180, 270):
        return ((1, 0), (0, 1), (-1, 0), (0, -1))[int(angle // 90)]
    radians = math.radians(angle)
    return math.cos(radians), math.sin(radians)


def path_geometry(value):
    """Expand relative/shorthand commands, including quadratic Beziers."""
    tokens = re.findall(r'[a-df-zA-DF-Z]|' + NUMBER, value)
    counts = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'T': 2, 'A': 7}
    result = []
    position = start = (0, 0)
    cubic = quadratic = None
    command = None
    i = 0
    while i < len(tokens):
        if tokens[i].isalpha():
            command = tokens[i]
            i += 1
            if command.upper() == 'Z':
                result.append(('Z',))
                position = start
                cubic = quadratic = command = None
                continue
        if command is None or command.upper() not in counts:
            raise ValueError('Unsupported SVG path command.')
        kind = command.upper()
        count = counts[kind]
        values = list(map(float, tokens[i:i + count]))
        if len(values) != count or not all(math.isfinite(v) for v in values):
            raise ValueError('Invalid SVG path coordinates.')
        i += count
        x, y = position
        relative = command.islower()

        def pair(offset):
            return (values[offset] + (x if relative else 0),
                    values[offset + 1] + (y if relative else 0))

        next_cubic = next_quadratic = None
        if kind in ('M', 'L', 'T'):
            end = pair(0)
            if kind == 'T':
                control = (2*x - quadratic[0], 2*y - quadratic[1]) if quadratic else position
            elif kind == 'M':
                start = end
                command = 'l' if relative else 'L'
        elif kind == 'H':
            end = (values[0] + (x if relative else 0), y)
        elif kind == 'V':
            end = (x, values[0] + (y if relative else 0))
        elif kind == 'C':
            first, second, end = pair(0), pair(2), pair(4)
        elif kind == 'S':
            first = (2*x - cubic[0], 2*y - cubic[1]) if cubic else position
            second, end = pair(0), pair(2)
        elif kind == 'Q':
            control, end = pair(0), pair(2)
        else:
            end = pair(5)

        if kind in ('Q', 'T'):
            first = tuple(p + 2*(q-p)/3 for p, q in zip(position, control))
            second = tuple(p + 2*(q-p)/3 for p, q in zip(end, control))
            next_quadratic = control
            result.append(('C', *first, *second, *end))
        elif kind in ('C', 'S'):
            result.append(('C', *first, *second, *end))
            next_cubic = second
        elif kind == 'A':
            result.append(('A', abs(values[0]), abs(values[1]), values[2] % 360,
                           values[3], values[4], *end))
        else:
            result.append(('M' if kind == 'M' else 'L', *end))
        position = end
        cubic, quadratic = next_cubic, next_quadratic
    return result


def multiply(left, right):
    a, b, c, d, e, f = left
    g, h, i, j, k, l = right
    return (a*g+c*h, b*g+d*h, a*i+c*j, b*i+d*j, a*k+c*l+e, b*k+d*l+f)


def transform_geometry(value):
    result = IDENTITY
    for name, arguments in re.findall(r'([a-zA-Z]+)\s*\(([^)]*)\)', value):
        v = list(map(float, re.findall(NUMBER, arguments)))
        if not all(math.isfinite(n) for n in v):
            raise ValueError('Invalid SVG transform.')
        if name == 'matrix' and len(v) == 6:
            matrix = tuple(v)
        elif name == 'translate' and len(v) in (1, 2):
            matrix = (1, 0, 0, 1, v[0], v[1] if len(v) == 2 else 0)
        elif name == 'scale' and len(v) in (1, 2):
            matrix = (v[0], 0, 0, v[1] if len(v) == 2 else v[0], 0, 0)
        elif name == 'rotate' and len(v) in (1, 3):
            c, s = rotation_components(v[0])
            matrix = (c, s, -s, c, 0, 0)
            if len(v) == 3:
                x, y = v[1:]
                matrix = multiply(multiply((1, 0, 0, 1, x, y), matrix), (1, 0, 0, 1, -x, -y))
        elif name in ('skewX', 'skewY') and len(v) == 1:
            tangent = math.tan(math.radians(v[0]))
            matrix = (1, 0, tangent, 1, 0, 0) if name == 'skewX' else (1, tangent, 0, 1, 0, 0)
        else:
            raise ValueError('Unsupported SVG transform.')
        result = multiply(result, matrix)
    return result


def geometry_record(element, root=False):
    attributes = {'transform', 'd', 'x', 'y', 'cx', 'cy', 'r', 'width', 'height',
                  'fill', 'stroke', 'stroke-width', 'font-size', 'font-family',
                  'stroke-linecap', 'stroke-linejoin', 'stroke-dasharray', 'text-anchor',
                  'opacity', 'fill-opacity', 'stroke-opacity', 'display', 'visibility',
                  'filter', 'clip-path', 'mask'}
    values = {key: element.getAttribute(key).strip() for key in attributes if element.hasAttribute(key)}
    for declaration in element.getAttribute('style').split(';'):
        if ':' in declaration:
            key, value = declaration.split(':', 1)
            if key.strip() in attributes:
                values[key.strip()] = value.strip()
    if root:
        values.pop('transform', None)
    else:
        values['transform'] = transform_geometry(values.get('transform', ''))
    for key, value in list(values.items()):
        if key == 'd':
            values[key] = path_geometry(value)
        elif key in {'x', 'y', 'cx', 'cy', 'r', 'width', 'height', 'stroke-width', 'font-size',
                     'opacity', 'fill-opacity', 'stroke-opacity'}:
            values[key] = float(value.removesuffix('px'))
    children = [geometry_record(c) for c in element.childNodes
                if c.nodeType == c.ELEMENT_NODE and c.localName != 'metadata']
    text = ''.join(c.data for c in element.childNodes if c.nodeType == c.TEXT_NODE).strip()
    return element.localName, values, text, children


def equivalent(left, right):
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(left, right, rel_tol=1e-7, abs_tol=1e-5)
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equivalent(left[k], right[k]) for k in left)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return len(left) == len(right) and all(equivalent(a, b) for a, b in zip(left, right))
    return left == right


def same_geometry(left, right):
    return equivalent(geometry_record(left, True), geometry_record(right, True))
