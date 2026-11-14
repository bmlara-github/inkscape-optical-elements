"""Native Tk editor using the Python runtime selected by Inkscape."""
import copy
import json
import math
import os
import sys
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .model import CATALOG, DETAILS, ELEMENTS, LAYOUTS, GRID, layout_offset, ports, route, snap
from .svg_geometry import rotation_components
from .alignment import angle_difference

PREVIEWS = json.loads((Path(__file__).resolve().parents[1] / 'optical_previews.json').read_text())
INK_COLOR = '#263442'
PORT_COLOR = '#176db0'


def create_window():
    if sys.platform != 'darwin':
        return tk.Tk()
    # An effect has already consumed its SVG input. Give Tk a regular input
    # channel during startup so TkAqua does not create a replacement console
    # or redirect the SVG output stream when Inkscape supplies /dev/null.
    with tempfile.TemporaryFile() as gui_input:
        saved_stdin = os.dup(0)
        try:
            os.dup2(gui_input.fileno(), 0)
            return tk.Tk()
        finally:
            os.dup2(saved_stdin, 0)
            os.close(saved_stdin)


def draw_symbol(canvas, key, x, y, scale, rotation=0):
    c, s = rotation_components(rotation)
    for curve in PREVIEWS[key]:
        coordinates = []
        for dx, dy in curve:
            coordinates.extend((x + scale * (c*dx - s*dy), y + scale * (s*dx + c*dy)))
        if len(coordinates) >= 4:
            canvas.create_line(*coordinates, fill=INK_COLOR, width=max(1, 0.12 * scale),
                               capstyle=tk.ROUND, joinstyle=tk.ROUND)


def draw_layout(canvas, key, x, y, scale):
    layout = LAYOUTS[key]
    state = {'nodes': [dict(n, id=i) for i, n in enumerate(layout['nodes'])], 'edges': layout['edges']}
    for edge in state['edges']:
        coordinates = [value for px, py in route(state, edge) for value in (x+px*scale, y+py*scale)]
        canvas.create_line(*coordinates, fill=INK_COLOR, width=max(1, 2*scale))
    for node in state['nodes']:
        draw_symbol(canvas, node['key'], x+node['x']*scale, y+node['y']*scale,
                    GRID*scale, node['rotation'])


def item_thumbnail(canvas, key, x, y):
    if key.startswith('layout:'):
        name = key.split(':', 1)[1]
        nodes = LAYOUTS[name]['nodes']
        left, right = min(n['x'] for n in nodes)-50, max(n['x'] for n in nodes)+50
        top, bottom = min(n['y'] for n in nodes)-50, max(n['y'] for n in nodes)+50
        scale = min(94/(right-left), 58/(bottom-top))
        draw_layout(canvas, name, x-(left+right)*scale/2, y-(top+bottom)*scale/2, scale)
    else:
        draw_symbol(canvas, key, x, y, 12)


def distance_to_segment(p, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = dx * dx + dy * dy
    t = max(0, min(1, ((p[0] - start[0]) * dx + (p[1] - start[1]) * dy) / length)) if length else 0
    return math.hypot(p[0] - start[0] - t * dx, p[1] - start[1] - t * dy)


class Editor:
    @property
    def selected(self):
        return next(iter(self.selection)) if len(self.selection) == 1 else None

    @selected.setter
    def selected(self, value):
        self.selection = {value} if value else set()

    def __init__(self, session):
        self.session = session
        self.diagram = session.diagram
        # SVG validation has already completed. Align the editable copy only;
        # Cancel still returns the original bytes, and this change is undoable.
        self.diagram.align_optics()
        self.selected = None
        self.gesture = None
        self.applied = False
        self.zoom = 1.0
        self.width = max(1200, session.page[3], *(n['x'] + 100 for n in self.diagram.state['nodes']))
        self.height = max(800, session.page[4], *(n['y'] + 100 for n in self.diagram.state['nodes']))
        self.window = create_window()
        self.window.withdraw()
        self.window.title('Optical Elements — Build System')
        self.window.geometry('1180x780')
        self.window.minsize(960, 600)
        self.window.protocol('WM_DELETE_WINDOW', self.cancel)
        self.family = tk.StringVar(value='All items')
        self.search = tk.StringVar()
        self.routing = tk.StringVar(value='Straight')
        self.label = tk.StringVar()
        self.angle = tk.StringVar()
        self.follow = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value='Drag a symbol onto the grid. Shift-click or drag a rectangle to select several.')
        self.zoom_text = tk.StringVar(value='100%')
        outer = ttk.Frame(self.window, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(outer)
        toolbar.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        for text, command in [('Undo', lambda: self.history(False)), ('Redo', lambda: self.history(True)),
                              ('Select all', self.select_all), ('Delete', self.delete),
                              ('Align optics', self.align_optics)]:
            ttk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(toolbar, text='Connections').pack(side=tk.LEFT, padx=(12, 5))
        ttk.Combobox(toolbar, textvariable=self.routing, values=['Straight', 'Right angles'],
                     state='readonly', width=12).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='−', width=3, command=lambda: self.change_zoom(-0.2)).pack(side=tk.LEFT, padx=(12, 0))
        ttk.Label(toolbar, textvariable=self.zoom_text, width=5, anchor='center').pack(side=tk.LEFT)
        ttk.Button(toolbar, text='+', width=3, command=lambda: self.change_zoom(0.2)).pack(side=tk.LEFT)
        body = ttk.Frame(outer)
        body.grid(row=1, column=0, sticky='nsew')
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        sidebar = ttk.Frame(body, width=245)
        sidebar.grid(row=0, column=0, sticky='ns', padx=(0, 12))
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(2, weight=1)
        ttk.Combobox(sidebar, textvariable=self.family, state='readonly',
                     values=['All items', *CATALOG, 'Cavities and layouts'], width=25).grid(row=0, column=0, columnspan=2, sticky='ew')
        ttk.Entry(sidebar, textvariable=self.search).grid(row=1, column=0, columnspan=2, sticky='ew', pady=8)
        self.palette = tk.Canvas(sidebar, width=224, background='#f5f6f7', highlightthickness=0)
        self.palette.grid(row=2, column=0, sticky='ns')
        palette_scroll = ttk.Scrollbar(sidebar, orient=tk.VERTICAL, command=self.palette.yview)
        palette_scroll.grid(row=2, column=1, sticky='ns')
        self.palette.configure(yscrollcommand=palette_scroll.set)
        self.palette.bind('<ButtonPress-1>', self.palette_press)
        self.palette.bind('<B1-Motion>', self.palette_motion)
        self.palette.bind('<ButtonRelease-1>', self.palette_release)
        self.palette.bind('<MouseWheel>', lambda event: self.wheel(event, self.palette))
        self.palette.bind('<Motion>', self.palette_hover)
        drawing = ttk.Frame(body)
        drawing.grid(row=0, column=1, sticky='nsew')
        drawing.rowconfigure(0, weight=1)
        drawing.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(drawing, background='#edf0f2', highlightthickness=1,
                                highlightbackground='#c4cbd0', takefocus=True)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        horizontal = ttk.Scrollbar(drawing, orient=tk.HORIZONTAL, command=lambda *args: self.scroll('x', *args))
        vertical = ttk.Scrollbar(drawing, orient=tk.VERTICAL, command=lambda *args: self.scroll('y', *args))
        horizontal.grid(row=1, column=0, sticky='ew')
        vertical.grid(row=0, column=1, sticky='ns')
        self.canvas.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set,
                              scrollregion=(0, 0, self.width, self.height))
        self.canvas.bind('<Configure>', lambda event: self.draw())
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.motion)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.bind('<MouseWheel>', lambda event: self.wheel(event, self.canvas))
        ttk.Label(outer, textvariable=self.status, anchor='w').grid(row=2, column=0, sticky='ew', pady=8)
        footer = ttk.Frame(outer)
        footer.grid(row=3, column=0, sticky='ew')
        ttk.Label(footer, text='Label').pack(side=tk.LEFT, padx=(0, 8))
        self.label_entry = ttk.Entry(footer, textvariable=self.label, state='disabled')
        self.label_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.label_entry.bind('<Return>', lambda event: self.rename())
        ttk.Label(footer, text='Angle °').pack(side=tk.LEFT, padx=(12, 5))
        self.angle_entry = ttk.Entry(footer, textvariable=self.angle, width=8, state='disabled')
        self.angle_entry.pack(side=tk.LEFT)
        self.angle_entry.bind('<Return>', lambda event: self.rotate(manual=True))
        self.angle_button = ttk.Button(footer, text='Set angle', command=lambda: self.rotate(manual=True), state='disabled')
        self.angle_button.pack(side=tk.LEFT, padx=(5, 0))
        self.follow_button = ttk.Checkbutton(footer, text='Follow beams', variable=self.follow,
                                              command=self.follow_beams, state='disabled')
        self.follow_button.pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(footer, text='Cancel', command=self.cancel).pack(side=tk.LEFT, padx=8)
        ttk.Button(footer, text='Apply to Inkscape', command=self.apply).pack(side=tk.LEFT)
        self.family.trace_add('write', lambda *_: self.populate())
        self.search.trace_add('write', lambda *_: self.populate())
        self.window.bind('<KeyPress>', self.key_press)
        self.populate()
        self.refresh()

    def populate(self):
        self.palette.delete('all')
        self.palette_keys = []
        query = self.search.get().casefold()
        families = {family: [(key, entry[0]) for key, entry in entries.items()]
                    for family, entries in CATALOG.items()}
        families['Cavities and layouts'] = [('layout:'+key, value['title']) for key, value in LAYOUTS.items()]
        for family, entries in families.items():
            if self.family.get() not in ('All items', family):
                continue
            for key, title in entries:
                keywords = f"{title} {DETAILS.get(key, {}).get('label', '')} {family}"
                if query not in keywords.casefold():
                    continue
                index = len(self.palette_keys)
                self.palette_keys.append(key)
                x, y = (index % 2) * 112, (index // 2) * 110
                self.palette.create_rectangle(x + 4, y + 4, x + 108, y + 106, fill='white', outline='#dce1e5')
                item_thumbnail(self.palette, key, x + 56, y + 37)
                self.palette.create_text(x + 56, y + 82, text=title, width=100, fill=INK_COLOR,
                                         font=('TkDefaultFont', 10), justify=tk.CENTER)
        self.palette.configure(scrollregion=(0, 0, 224, max(110, math.ceil(len(self.palette_keys) / 2) * 110)))
        self.palette.yview_moveto(0)

    def palette_hover(self, event):
        if self.gesture:
            return
        column = int(self.palette.canvasx(event.x) // 112)
        index = int(self.palette.canvasy(event.y) // 110)*2 + column
        if column in (0, 1) and 0 <= index < len(self.palette_keys):
            key = self.palette_keys[index]
            if key.startswith('layout:'):
                self.status.set(LAYOUTS[key.split(':', 1)[1]]['title'] + ' — drag to insert editable components.')
            else:
                self.status.set(DETAILS.get(key, {}).get('description', ELEMENTS[key][0]))

    def canvas_point(self, event):
        x = event.x_root - self.canvas.winfo_rootx()
        y = event.y_root - self.canvas.winfo_rooty()
        inside = 0 <= x < self.canvas.winfo_width() and 0 <= y < self.canvas.winfo_height()
        return self.canvas.canvasx(x) / self.zoom, self.canvas.canvasy(y) / self.zoom, inside

    def palette_press(self, event):
        if not self.rotate():
            return
        self.rename()
        column = int(self.palette.canvasx(event.x) // 112)
        index = int(self.palette.canvasy(event.y) // 110) * 2 + column
        if column in (0, 1) and 0 <= index < len(self.palette_keys):
            self.gesture = {'kind': 'palette', 'key': self.palette_keys[index], 'cursor': None}
            self.palette.configure(cursor='fleur')
            self.status.set('Release the symbol on the grid to place it.')

    def palette_motion(self, event):
        if self.gesture and self.gesture['kind'] == 'palette':
            x, y, inside = self.canvas_point(event)
            self.gesture['cursor'] = (snap(x), snap(y)) if inside else None
            self.draw()

    def palette_release(self, event):
        if self.gesture and self.gesture['kind'] == 'palette':
            x, y, inside = self.canvas_point(event)
            if inside:
                key = self.gesture['key']
                if key.startswith('layout:'):
                    self.selection = self.diagram.add_layout(key.split(':', 1)[1], x, y)
                else:
                    self.selected = self.diagram.add_node(key, x, y)
                self.status.set('Component placed on the grid. Drag its blue ports to connect.')
            self.gesture = None
            self.palette.configure(cursor='')
            self.canvas.focus_set()
            self.refresh()

    def node(self):
        return next((node for node in self.diagram.state['nodes'] if node['id'] == self.selected), None)

    def refresh(self):
        node = self.node()
        self.label_entry.configure(state='normal' if node else 'disabled')
        self.label.set(node['label'] if node else '')
        self.angle_entry.configure(state='normal' if node else 'disabled')
        self.angle_button.configure(state='normal' if node else 'disabled')
        self.angle.set(format(node['rotation'], '.12g') if node else '')
        can_align = bool(node and DETAILS.get(node['key'], {}).get('alignment'))
        self.follow_button.configure(state='normal' if can_align else 'disabled')
        self.follow.set(bool(can_align and node.get('auto_align', True)))
        selected_nodes = [n for n in self.diagram.state['nodes'] if n['id'] in self.selection]
        if len(selected_nodes) > 1:
            self.status.set(f'{len(selected_nodes)} components selected. Drag a selected component to move them together.')
        self.width = max(self.width, *(n['x'] + 100 for n in self.diagram.state['nodes']), 1200)
        self.height = max(self.height, *(n['y'] + 100 for n in self.diagram.state['nodes']), 800)
        self.canvas.configure(scrollregion=(0, 0, self.width*self.zoom, self.height*self.zoom))
        problems = self.diagram.alignment_issues()
        if problems:
            identifier = self.selected if self.selected in problems else next(iter(problems))
            item = next(n for n in self.diagram.state['nodes'] if n['id'] == identifier)
            self.status.set(f"{item['label'] or ELEMENTS[item['key']][0]}: {problems[identifier]}")
        self.draw()

    def port_at(self, x, y):
        for node in reversed(self.diagram.state['nodes']):
            for number, (px, py) in enumerate(ports(node)):
                if math.hypot(px - x, py - y) <= 9 / self.zoom:
                    return node['id'], number
        return None

    def press(self, event):
        if not self.rotate():
            return
        self.rename()
        self.canvas.focus_set()
        x, y, _ = self.canvas_point(event)
        additive = bool(getattr(event, 'state', 0) & 1)
        hit = next((n for n in reversed(self.diagram.state['nodes'])
                    if abs(n['x']-x) <= 2.5*GRID and abs(n['y']-y) <= 2.5*GRID), None)
        if additive and hit:
            self.selection.symmetric_difference_update({hit['id']})
            self.gesture = None
            self.refresh()
            return
        port = self.port_at(x, y)
        if port and not additive and not (len(self.selection) > 1 and port[0] in self.selection):
            self.gesture = {'kind': 'wire', 'start': port, 'cursor': (x, y)}
            self.status.set('Release over another blue port to complete the connection.')
            return
        if hit:
            if hit['id'] not in self.selection:
                self.selected = hit['id']
            self.gesture = {'kind': 'move', 'before': copy.deepcopy(self.diagram.state),
                            'origin': (x, y), 'ids': set(self.selection)}
        else:
            edge_hit = None
            for edge in reversed(self.diagram.state['edges']):
                vertices = route(self.diagram.state, edge)
                if any(distance_to_segment((x, y), a, b) <= 6 / self.zoom
                       for a, b in zip(vertices, vertices[1:])):
                    edge_hit = edge['id']
                    break
            if edge_hit:
                if additive:
                    self.selection.symmetric_difference_update({edge_hit})
                else:
                    self.selected = edge_hit
                self.gesture = None
            else:
                base = set(self.selection) if additive else set()
                self.selection = base.copy()
                self.gesture = {'kind': 'marquee', 'origin': (x, y), 'cursor': (x, y), 'base': base}
        self.refresh()

    def motion(self, event):
        if not self.gesture:
            return
        x, y, _ = self.canvas_point(event)
        if self.gesture['kind'] == 'wire':
            self.gesture['cursor'] = (x, y)
        elif self.gesture['kind'] == 'move':
            ox, oy = self.gesture['origin']
            self.diagram.translate_selection(self.gesture['ids'], x-ox, y-oy, self.gesture['before'])
        elif self.gesture['kind'] == 'marquee':
            self.gesture['cursor'] = (x, y)
            ox, oy = self.gesture['origin']
            self.selection = self.gesture['base'] | {n['id'] for n in self.diagram.state['nodes']
                              if min(x,ox) <= n['x'] <= max(x,ox) and min(y,oy) <= n['y'] <= max(y,oy)}
        self.draw()

    def release(self, event):
        if not self.gesture:
            return
        if self.gesture['kind'] == 'wire':
            x, y, inside = self.canvas_point(event)
            target = self.port_at(x, y) if inside else None
            if target:
                routing = 'straight' if self.routing.get() == 'Straight' else 'orthogonal'
                self.diagram.connect(*self.gesture['start'], *target, routing)
                self.status.set('Connection attached. Move either component to reshape the line.')
            else:
                self.status.set('Release on a blue port circle to attach a connection.')
        elif self.gesture['kind'] == 'move':
            self.motion(event)
            self.diagram.remember(self.gesture['before'])
            self.status.set('Selection snapped to the grid.')
        elif self.gesture['kind'] == 'marquee':
            self.motion(event)
        self.gesture = None
        self.refresh()

    def draw(self):
        canvas = self.canvas
        canvas.delete('all')
        zoom = self.zoom
        problems = self.diagram.alignment_issues()
        _, _, _, page_width, page_height = self.session.page
        canvas.create_rectangle(0, 0, page_width * zoom, page_height * zoom, fill='white', outline='#c4cbd0')
        left, top = canvas.canvasx(0) / zoom, canvas.canvasy(0) / zoom
        right, bottom = left + canvas.winfo_width() / zoom, top + canvas.winfo_height() / zoom
        for x in range(int(left // GRID) * GRID, int(right) + GRID, GRID):
            canvas.create_line(x * zoom, top * zoom, x * zoom, bottom * zoom, fill='#e4e9ed')
        for y in range(int(top // GRID) * GRID, int(bottom) + GRID, GRID):
            canvas.create_line(left * zoom, y * zoom, right * zoom, y * zoom, fill='#e4e9ed')
        for edge in self.diagram.state['edges']:
            coordinates = [coordinate * zoom for p in route(self.diagram.state, edge) for coordinate in p]
            highlighted = edge['id'] in self.selection or {edge['start'], edge['end']} <= self.selection
            canvas.create_line(*coordinates, fill=PORT_COLOR if highlighted else INK_COLOR,
                               width=max(1, 2 * zoom), joinstyle=tk.ROUND)
        for node in self.diagram.state['nodes']:
            x, y = node['x'] * zoom, node['y'] * zoom
            if node['id'] in self.selection or node['id'] in problems:
                radius = 2.6 * GRID * zoom
                canvas.create_rectangle(x - radius, y - radius, x + radius, y + radius,
                                        outline='#b66b00' if node['id'] in problems else PORT_COLOR, dash=(4, 3))
                if node['id'] in problems:
                    canvas.create_text(x+radius, y-radius, text='!', fill='#b66b00', anchor='se',
                                       font=('TkDefaultFont', 13, 'bold'))
            draw_symbol(canvas, node['key'], x, y, GRID * zoom, node['rotation'])
            for px, py in ports(node):
                px, py = px * zoom, py * zoom
                canvas.create_oval(px - 4, py - 4, px + 4, py + 4, fill='white', outline=PORT_COLOR, width=2)
            if node['label']:
                dx, dy = node.get('label_offset', (0, 3*GRID))
                canvas.create_text(x + dx * zoom, y + dy * zoom, text=node['label'], fill=INK_COLOR,
                                   font=('TkDefaultFont', max(7, round(14 * zoom))))
        if self.gesture and self.gesture['kind'] == 'wire':
            node_id, number = self.gesture['start']
            node = next(n for n in self.diagram.state['nodes'] if n['id'] == node_id)
            start, end = ports(node)[number], self.gesture['cursor']
            canvas.create_line(*(c * zoom for p in (start, end) for c in p), fill=PORT_COLOR, width=2, dash=(5, 4))
        if self.gesture and self.gesture['kind'] == 'palette' and self.gesture['cursor']:
            x, y = self.gesture['cursor']
            key = self.gesture['key']
            if key.startswith('layout:'):
                name = key.split(':', 1)[1]
                x, y = layout_offset(LAYOUTS[name], x, y)
                draw_layout(canvas, name, x*zoom, y*zoom, zoom)
            else:
                draw_symbol(canvas, key, x * zoom, y * zoom, GRID * zoom)
        if self.gesture and self.gesture['kind'] == 'marquee':
            canvas.create_rectangle(*(c*zoom for p in (self.gesture['origin'], self.gesture['cursor']) for c in p),
                                    outline=PORT_COLOR, dash=(4, 3), width=2)

    def rename(self):
        node = self.node()
        if node and node['label'] != self.label.get():
            previous = copy.deepcopy(self.diagram.state)
            node['label'] = self.label.get()
            self.diagram.remember(previous)
            self.draw()

    def rotate(self, manual=False):
        node = self.node()
        if node:
            try:
                angle = float(self.angle.get())
                if not math.isfinite(angle):
                    raise ValueError('Invalid angle')
                if manual or abs(angle_difference(angle, node['rotation'])) > 1e-8:
                    self.diagram.set_rotation(self.selected, angle)
            except ValueError:
                self.status.set('Enter a finite angle in degrees, for example 22.5 or -30.')
                self.angle_entry.focus_set()
                return False
            self.angle.set(format(node['rotation'], '.12g'))
            self.follow.set(bool(DETAILS.get(node['key'], {}).get('alignment') and node.get('auto_align', True)))
            self.draw()
        return True

    def align_optics(self):
        self.rename()
        selected_nodes = {n['id'] for n in self.diagram.state['nodes'] if n['id'] in self.selection}
        self.diagram.align_optics(selected_nodes or None, enable=True)
        self.status.set('Optics aligned to connected beams. Positions stay on the grid.')
        self.refresh()

    def follow_beams(self):
        if self.node():
            self.rename()
            self.diagram.follow_beams(self.selected, self.follow.get())
            self.refresh()

    def delete(self):
        self.diagram.delete(self.selection)
        self.selected = None
        self.refresh()

    def select_all(self):
        if not self.rotate():
            return
        self.rename()
        self.selection = {item['id'] for kind in ('nodes', 'edges') for item in self.diagram.state[kind]}
        self.refresh()

    def history(self, redo):
        self.gesture = None
        self.diagram.redo() if redo else self.diagram.undo()
        self.selected = None
        self.refresh()

    def scroll(self, axis, *args):
        self.canvas.xview(*args) if axis == 'x' else self.canvas.yview(*args)
        self.draw()

    def wheel(self, event, canvas):
        step = -1 if event.delta > 0 else 1
        canvas.yview_scroll(step * 3, 'units')
        if canvas is self.canvas:
            self.draw()
        return 'break'

    def change_zoom(self, step):
        self.zoom = max(0.4, min(2, round(self.zoom + step, 1)))
        self.zoom_text.set(f'{self.zoom:.0%}')
        self.canvas.configure(scrollregion=(0, 0, self.width * self.zoom, self.height * self.zoom))
        self.draw()

    def key_press(self, event):
        if isinstance(self.window.focus_get(), (tk.Entry, ttk.Entry, ttk.Combobox)):
            return
        key = event.keysym.lower()
        command = event.state & (8 if sys.platform == 'darwin' else 4)
        if key == 'z' and command:
            self.history(bool(event.state & 1))
        elif key == 'a' and command:
            self.select_all()
        elif key in ('delete', 'backspace'):
            self.delete()
        elif key == 'r':
            if self.node():
                self.angle_entry.focus_set()
                self.angle_entry.selection_range(0, tk.END)
        elif key == 'escape':
            if self.gesture and self.gesture['kind'] == 'move':
                self.diagram.state = self.gesture['before']
            self.gesture = None
            self.selected = None
            self.palette.configure(cursor='')
            self.refresh()

    def cancel(self):
        self.window.destroy()

    def apply(self):
        if not self.rotate():
            return
        self.rename()
        self.applied = True
        self.window.destroy()

    def run(self):
        self.window.deiconify()
        self.window.mainloop()
        return self.applied
