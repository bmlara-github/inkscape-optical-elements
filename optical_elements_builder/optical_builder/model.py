"""Diagram state, grid geometry, and lossless SVG document integration."""
import copy
import hashlib
import json
import math
import re
import uuid
from pathlib import Path
from xml.dom import minidom

from .svg_geometry import rotation_components, same_geometry
from . import alignment

SVG = 'http://www.w3.org/2000/svg'
INK = 'http://www.inkscape.org/namespaces/inkscape'
XMLNS = 'http://www.w3.org/2000/xmlns/'
GRID = 20
DATA = Path(__file__).resolve().parents[1]
CATALOG = json.loads((DATA / 'optical_elements.json').read_text(encoding='utf-8'))
DETAILS = json.loads((DATA / 'optical_details.json').read_text(encoding='utf-8'))
LAYOUTS = json.loads((DATA / 'optical_layouts.json').read_text(encoding='utf-8'))
# Read old drawings without offering the retired categories in the gallery.
ELEMENTS = json.loads((DATA / 'optical_legacy.json').read_text(encoding='utf-8'))
ELEMENTS.update({key: value for family in CATALOG.values() for key, value in family.items()})


def snap(value):
    return GRID * math.floor(value / GRID + 0.5)


def layout_offset(layout, x, y):
    return (max(snap(x), GRID*3 - min(n['x'] for n in layout['nodes'])),
            max(snap(y), GRID*3 - min(n['y'] for n in layout['nodes'])))


def point(node, local):
    x, y = (coordinate * GRID for coordinate in local)
    c, s = rotation_components(node['rotation'])
    return node['x'] + c*x - s*y, node['y'] + s*x + c*y


def ports(node):
    return [point(node, p) for p in ELEMENTS[node['key']][2]]


def route(state, edge):
    nodes = {node['id']: node for node in state['nodes']}
    start = ports(nodes[edge['start']])[edge['start_port']]
    end = ports(nodes[edge['end']])[edge['end_port']]
    if edge['route'] == 'straight' or start[0] == end[0] or start[1] == end[1]:
        return [start, end]
    middle = snap((start[0] + end[0]) / 2)
    return [start, (middle, start[1]), (middle, end[1]), end]


class Diagram:
    def __init__(self, state=None):
        self.state = copy.deepcopy(state or {'version': 1, 'nodes': [], 'edges': []})
        self.undo_stack = []
        self.redo_stack = []
        self.validate()

    def validate(self):
        if self.state.get('version') != 1:
            raise ValueError('This diagram was saved by an unsupported extension version.')
        nodes = {node['id']: node for node in self.state['nodes']}
        if len(nodes) != len(self.state['nodes']):
            raise ValueError('Duplicate component IDs in the diagram.')
        for node in nodes.values():
            if node['key'] not in ELEMENTS:
                raise ValueError('Unknown component.')
            if not isinstance(node['rotation'], (int, float)) or not math.isfinite(node['rotation']):
                raise ValueError('The rotation angle must be a finite number.')
            if not all(math.isfinite(node[k]) for k in ('x', 'y')):
                raise ValueError('Component coordinates must be finite.')
        edge_ids = set()
        for edge in self.state['edges']:
            if edge['id'] in edge_ids or edge['route'] not in ('straight', 'orthogonal'):
                raise ValueError('Invalid connection in the diagram.')
            edge_ids.add(edge['id'])
            for side in ('start', 'end'):
                if edge[side] not in nodes or not 0 <= edge[side + '_port'] < len(ports(nodes[edge[side]])):
                    raise ValueError('A connection refers to a missing port.')

    def remember(self, previous):
        if previous != self.state:
            self.undo_stack.append(previous)
            self.redo_stack.clear()

    def _align(self):
        return alignment.align(self.state, ELEMENTS, DETAILS, route)

    def alignment_issues(self):
        return alignment.issues(self.state, ELEMENTS, DETAILS, route)

    def align_optics(self, selected=None, enable=False):
        previous = copy.deepcopy(self.state)
        if enable:
            for node in self.state['nodes']:
                if (selected is None or node['id'] in selected) and DETAILS.get(node['key'], {}).get('alignment'):
                    node['auto_align'] = True
        problems = self._align()
        self.remember(previous)
        return problems

    def follow_beams(self, selected, enabled):
        previous = copy.deepcopy(self.state)
        node = next(n for n in self.state['nodes'] if n['id'] == selected)
        node['auto_align'] = bool(enabled)
        self._align()
        self.remember(previous)

    def add_node(self, key, x, y):
        if key not in ELEMENTS:
            raise ValueError('Unknown component.')
        previous = copy.deepcopy(self.state)
        node = {'id': 'oe-' + uuid.uuid4().hex, 'key': key, 'x': snap(x), 'y': snap(y),
                'rotation': 0, 'label': DETAILS.get(key, {}).get('label', '')}
        self.state['nodes'].append(node)
        self.remember(previous)
        return node['id']

    def add_layout(self, key, x, y):
        layout = LAYOUTS[key]
        dx, dy = layout_offset(layout, x, y)
        previous = copy.deepcopy(self.state)
        identifiers = []
        try:
            for source in layout['nodes']:
                node = copy.deepcopy(source)
                node.update(id='oe-' + uuid.uuid4().hex, x=source['x']+dx, y=source['y']+dy)
                node.setdefault('label', DETAILS.get(node['key'], {}).get('label', ''))
                identifiers.append(node['id'])
                self.state['nodes'].append(node)
            for source in layout['edges']:
                edge = copy.deepcopy(source)
                edge.update(id='oe-wire-' + uuid.uuid4().hex,
                            start=identifiers[edge['start']], end=identifiers[edge['end']])
                self.state['edges'].append(edge)
            self.validate()
            self._align()
        except (ValueError, KeyError, IndexError, TypeError):
            self.state = previous
            raise
        self.remember(previous)
        return set(identifiers)

    def translate_selection(self, selected, dx, dy, origin=None):
        """Use one grid-snapped displacement for all selected components."""
        origin = origin or self.state
        original = {n['id']: n for n in origin['nodes'] if n['id'] in selected}
        if not original:
            return
        dx = max(snap(dx), -min(n['x'] for n in original.values()))
        dy = max(snap(dy), -min(n['y'] for n in original.values()))
        for node in self.state['nodes']:
            if node['id'] in original:
                node['x'] = original[node['id']]['x'] + dx
                node['y'] = original[node['id']]['y'] + dy
        self._align()

    def connect(self, start, start_port, end, end_port, routing):
        if (start, start_port) == (end, end_port):
            return
        previous = copy.deepcopy(self.state)
        edge = {'id': 'oe-wire-' + uuid.uuid4().hex, 'start': start, 'start_port': start_port,
                'end': end, 'end_port': end_port, 'route': routing}
        self.state['edges'].append(edge)
        try:
            self.validate()
            self._align()
        except (ValueError, KeyError, TypeError):
            self.state = previous
            raise
        self.remember(previous)

    def set_rotation(self, selected, angle):
        if not math.isfinite(angle):
            raise ValueError('Enter a finite angle in degrees.')
        node = next(n for n in self.state['nodes'] if n['id'] == selected)
        previous = copy.deepcopy(self.state)
        node['rotation'] = angle % 360
        if DETAILS.get(node['key'], {}).get('alignment'):
            node['auto_align'] = False
        self._align()
        self.remember(previous)

    def delete(self, selected):
        selected = {selected} if isinstance(selected, str) else set(selected or ())
        previous = copy.deepcopy(self.state)
        self.state['nodes'] = [n for n in self.state['nodes'] if n['id'] not in selected]
        self.state['edges'] = [e for e in self.state['edges']
                               if not selected.intersection((e['id'], e['start'], e['end']))]
        self._align()
        self.remember(previous)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(self.state))
            self.state = self.undo_stack.pop()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(self.state))
            self.state = self.redo_stack.pop()


def add(parent, tag, attributes=None, text=None):
    child = parent.ownerDocument.createElementNS(SVG, tag)
    for key, value in (attributes or {}).items():
        child.setAttribute(key, str(value))
    if text is not None:
        child.appendChild(parent.ownerDocument.createTextNode(text))
    parent.appendChild(child)
    return child


def geometry_signature(group):
    """Ignore XML formatting, generated IDs, and path-number formatting on save."""
    attributes = {'transform', 'd', 'x', 'y', 'cx', 'cy', 'r', 'width', 'height',
                  'fill', 'stroke', 'stroke-width', 'font-size', 'font-family'}
    def record(element, root=False):
        values = {}
        for key in attributes:
            if element.hasAttribute(key) and not (root and key == 'transform'):
                value = element.getAttribute(key)
                if key in {'d', 'transform'}:
                    tokens = re.findall(r'[a-zA-Z]+|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?', value)
                    value = [round(float(t), 7) if re.match(r'[-+.\d]', t) else t for t in tokens]
                values[key] = value
        if element.hasAttribute('style'):
            for declaration in element.getAttribute('style').split(';'):
                if ':' in declaration:
                    key, value = declaration.split(':', 1)
                    if key.strip() in attributes:
                        values[key.strip()] = value.strip()
        # SVG editor saves can add a px suffix to font sizes.
        if 'font-size' in values:
            values['font-size'] = str(values['font-size']).removesuffix('px')
        children = [record(c) for c in element.childNodes if c.nodeType == c.ELEMENT_NODE
                    and c.localName != 'metadata']
        text = ''.join(c.data for c in element.childNodes if c.nodeType == c.TEXT_NODE).strip()
        return element.localName, values, text, children
    return hashlib.sha256(json.dumps(record(group, True), sort_keys=True).encode()).hexdigest()


def page_geometry(svg):
    box = svg.getAttribute('viewBox')
    factors = {'': 1, 'px': 1, 'mm': 96 / 25.4, 'cm': 96 / 2.54, 'in': 96,
               'pt': 96 / 72, 'pc': 16}
    def pixels(value, default):
        match = re.fullmatch(r'\s*([\d.+-]+)\s*([a-z]*)\s*', value)
        if not match or match[2] not in factors:
            return default
        return float(match[1]) * factors[match[2]]
    width = pixels(svg.getAttribute('width'), 1200)
    height = pixels(svg.getAttribute('height'), 800)
    if box:
        x, y, w, h = map(float, re.split(r'[\s,]+', box.strip()))
        if w <= 0 or h <= 0 or width <= 0:
            raise ValueError('The SVG has invalid page dimensions.')
        scale = w / width
        return x, y, scale, width, h / scale
    return 0, 0, 1, width, height


class SvgSession:
    def __init__(self, data, selected_ids=()):
        self.original = data
        self.document = minidom.parseString(data)
        svg = self.document.documentElement
        if svg.namespaceURI != SVG or svg.localName != 'svg':
            raise ValueError('An SVG document is required.')
        groups = [g for g in svg.getElementsByTagNameNS(SVG, 'g') if g.hasAttribute('data-optical-builder')]
        selected = []
        for group in groups:
            ids = {e.getAttribute('id') for e in [group, *group.getElementsByTagName('*')]}
            if ids.intersection(selected_ids):
                selected.append(group)
        if len(selected) > 1 or (len(groups) > 1 and not selected):
            raise ValueError('Select one optical system in Inkscape before reopening the builder.')
        self.group = selected[0] if selected else (groups[0] if groups else None)
        state = None
        if self.group:
            metadata = next((c for c in self.group.childNodes if c.nodeType == c.ELEMENT_NODE
                             and c.localName == 'metadata'), None)
            if metadata is None:
                raise ValueError('The selected system has no editable builder data.')
            saved = json.loads(''.join(c.data for c in metadata.childNodes if c.nodeType == c.TEXT_NODE))
            # Inkscape changes path commands, style syntax and transform spelling
            # on save. Compare actual geometry with the saved model, including
            # legacy files whose fingerprint was based on the original spelling.
            reference = SvgSession(b'<svg xmlns="http://www.w3.org/2000/svg"/>')
            reference.diagram = Diagram(saved['state'])
            reference.result(True)
            if not same_geometry(self.group, reference.group):
                raise ValueError('This system was edited outside the builder. Its SVG edits have been preserved. '
                                 'Undo those edits before reopening it in the builder.')
            state = saved['state']
        self.diagram = Diagram(state)
        self.page = page_geometry(svg)

    def result(self, applied):
        if not applied:
            return self.original
        self.diagram.validate()
        root = self.document.documentElement
        group = self.document.createElementNS(SVG, 'g')
        group.setAttributeNS(XMLNS, 'xmlns', SVG)
        group.setAttributeNS(XMLNS, 'xmlns:inkscape', INK)
        group.setAttribute('id', self.group.getAttribute('id') if self.group else 'optical-system-' + uuid.uuid4().hex)
        group.setAttribute('data-optical-builder', '1')
        group.setAttributeNS(INK, 'inkscape:label', 'Optical system')
        if self.group:
            group.setAttribute('transform', self.group.getAttribute('transform'))
        else:
            x, y, scale, _, _ = self.page
            group.setAttribute('transform', f'translate({x:g},{y:g}) scale({scale:.12g})')
        state = self.diagram.state
        for edge in state['edges']:
            vertices = route(state, edge)
            path = 'M ' + ' L '.join(f'{x:g},{y:g}' for x, y in vertices)
            add(group, 'path', {'id': edge['id'], 'd': path, 'fill': 'none', 'stroke': '#263442',
                               'stroke-width': 2, 'stroke-linejoin': 'round'})
        for node in state['nodes']:
            item = add(group, 'g', {'id': node['id'], 'data-optical-element': node['key'],
                                    'transform': f"translate({node['x']:g},{node['y']:g}) rotate({node['rotation']})"})
            item.setAttributeNS(INK, 'inkscape:label', node['label'] or ELEMENTS[node['key']][0])
            add(item, 'path', {'d': ELEMENTS[node['key']][1], 'transform': f'scale({GRID})',
                               'fill': 'none', 'stroke': '#263442', 'stroke-width': 0.12,
                               'stroke-linecap': 'round', 'stroke-linejoin': 'round'})
            if node['label']:
                dx, dy = node.get('label_offset', (0, 3*GRID))
                add(group, 'text', {'x': node['x'] + dx, 'y': node['y'] + dy, 'text-anchor': 'middle',
                                   'font-family': 'sans-serif', 'font-size': 14, 'fill': '#263442'}, node['label'])
        saved = {'state': state, 'geometry': geometry_signature(group)}
        add(group, 'metadata', {'data-optical-model': '1'}, json.dumps(saved, ensure_ascii=False))
        if self.group:
            self.group.parentNode.replaceChild(group, self.group)
            self.group = group
        else:
            root.appendChild(group)
            self.group = group
        return self.document.toxml(encoding='utf-8')
