"""Orient schematic optics to connected rays without changing their positions."""
import math

ANGLE_TOLERANCE = 0.1  # degrees; finite-precision drawings need a small tolerance


def angle_difference(a, b):
    return (a-b+180) % 360-180


def unit(vector):
    length = math.hypot(*vector)
    return tuple(v/length for v in vector) if length > 1e-8 else None


def specifications(state, elements, details, route_builder):
    """Return an angle or a concrete reason a component cannot be aligned."""
    nodes = {n['id']: n for n in state['nodes']}
    attached = {identifier: [] for identifier in nodes}
    for edge in state['edges']:
        vertices = route_builder(state, edge)
        for side, sequence in [('start', vertices), ('end', list(reversed(vertices)))]:
            node = nodes[edge[side]]
            # Use the adjacent segment of a routed line, skipping zero-length legs.
            target = next((p for p in sequence[1:] if math.dist(p, sequence[0]) > 1e-8), None)
            if target is None:
                attached[node['id']].append((edge[side+'_port'], None, 0, 0))
                continue
            vector = (target[0]-node['x'], target[1]-node['y'])
            radius = math.dist(sequence[0], (node['x'], node['y']))
            attached[node['id']].append((edge[side+'_port'], unit(vector), math.hypot(*vector), radius))

    results = {}
    for node in state['nodes']:
        spec = details.get(node['key'], {}).get('alignment')
        beams = attached[node['id']]
        if not spec or not beams or not node.get('auto_align', True):
            continue
        if any(direction is None for _, direction, _, _ in beams):
            results[node['id']] = (None, 'Separate coincident connection points.')
            continue
        if spec['kind'] == 'mirror':
            directions = []
            for _, direction, _, _ in beams:
                if not any(math.dist(direction, previous) < 1e-7 for previous in directions):
                    directions.append(direction)
            if len(directions) > 2:
                results[node['id']] = (None, 'More than two beam directions meet this mirror.')
                continue
            normal = unit(tuple(sum(p[axis] for p in directions) for axis in (0, 1)))
            if normal is None:
                results[node['id']] = (None, 'Opposite beam directions give grazing incidence, not a reflective turn.')
                continue
            # This is the outward normal facing both source and destination.
            target = math.degrees(math.atan2(normal[1], normal[0]))
            results[node['id']] = ((target-spec['front_normal']) % 360, '')
        else:
            desired = []
            problem = ''
            for number, direction, distance, radius in beams:
                local = elements[node['key']][2][number]
                if not unit(local):
                    problem = 'This port has no defined optical axis.'
                    break
                if distance <= radius+1e-6:
                    problem = 'A connected component is too close to this port.'
                    break
                desired.append(math.degrees(math.atan2(direction[1], direction[0])
                                             - math.atan2(local[1], local[0])))
            if problem:
                results[node['id']] = (None, problem)
                continue
            mean = unit((sum(math.cos(math.radians(a)) for a in desired),
                         sum(math.sin(math.radians(a)) for a in desired)))
            target = math.degrees(math.atan2(mean[1], mean[0])) % 360 if mean else None
            if target is None or any(abs(angle_difference(a, target)) > ANGLE_TOLERANCE for a in desired):
                results[node['id']] = (None, 'Connected beams do not match this element’s port angles; move a component or use another port.')
            else:
                results[node['id']] = (target, '')
    return results


def align(state, elements, details, route_builder):
    # Mirror centers do not move under rotation. Axis ports do, so neighboring
    # source/detector/lens orientations may require several updates to settle.
    for _ in range(48):
        proposals = specifications(state, elements, details, route_builder)
        changed = False
        for node in state['nodes']:
            angle, _ = proposals.get(node['id'], (None, ''))
            if angle is not None and abs(angle_difference(angle, node['rotation'])) > 1e-8:
                node['rotation'] = angle
                changed = True
        if not changed:
            break
    return issues(state, elements, details, route_builder)


def issues(state, elements, details, route_builder):
    proposals = specifications(state, elements, details, route_builder)
    result = {}
    for node in state['nodes']:
        if node['id'] not in proposals:
            continue
        angle, problem = proposals[node['id']]
        if problem:
            result[node['id']] = problem
        elif abs(angle_difference(angle, node['rotation'])) > ANGLE_TOLERANCE:
            result[node['id']] = 'The connected orientations have not settled; adjust the layout.'
    return result
