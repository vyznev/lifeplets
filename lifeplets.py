#!/usr/bin/python3
"""
This program exhaustively enumerates all (orthogonally or diagonally)
connected still life patterns in a Life-like cellular automaton with a
given maximum cell count.  (By inverting the survival rule, it can
also be used to find connected patterns that vanish in one step.)
"""

from math import floor, ceil
from sys import stdout

# Parameters: (TODO: use argparse instead of hardcoded params)

# maximum number of live cells
max_n = 16

# rule (B3/S23 = Conway's Game of Life; invert to find disappearing patterns)
rule = [[0]*9, [1]*9]  # start with b-/s012345678
rule[0][3] = 1  # add b3
rule[1][2] = 0  # remove s2
rule[1][3] = 0  # remove s3

# basic backtracking search
width = max_n + 2
depth = max_n + 1
pattern = [None] * (depth * width)
live_count = 0
start = width

# Moore neighborhood
neighbors = [-width-1, -width, -width+1, -1, +1, width-1, width, width+1]

# component tracking variables
components = set()
parents = [-1] * len(pattern)
comp_size = [0] * len(pattern)
merge_undo_list = {}
close_undo_list = {}
# columns on which each component could be extended
freedoms = {}

def set_pattern(i, state):
    global pattern, width, start, live_count, max_n, components
    if i < 0 or i >= len(pattern): return False

    old_state = pattern[i]
    pattern[i] = state
    if state == old_state: return True  # should not happen...

    if old_state: live_count -= 1
    if state: live_count += 1
    
    # do component updates and check if we've completed a polyplet
    # XXX: it would be faster to do the simple checks below first,
    # but that would make it harder to ensure consistency
    if old_state == True: undo_component_merge(i)
    if old_state == False: undo_component_close(i)
    if state == True:
        merge_components(i)
        # XXX: len(components)-1 is a lower bound on the number of cells needed to connect the pattern
        if live_count + len(components) - 1 > max_n: return False
        if live_count + minimum_bridge_length() > max_n: return False
    if state == False:
        if not close_components(i):
            # we've fully closed off a component!
            # if it was the only one, we may have found a match
            if len(components) == 1 and final_rule_check(i):
                print_pattern(i)
            # either way, we should backtrack
            return False
    
    # cells 0 and 1 must always be dead
    if state and i < start: return False
    # cell 2 in row 0 must always be live!
    if not state and i == start: return False
    
    # finally check that the CA rule can be satisfied
    if not check_rule_near(i): return False
    return True
    
def check_rule_near(i):
    global neighbors
    """Check whether cell i and its neighbors can possibly be part of a still life."""
    if not check_rule_at(i):
        return False
    for delta in neighbors:
        if not check_rule_at(i + delta):
            return False
    return True

def final_rule_check(i):
    global width
    """Do a more stringent rules check on the last two rows, knowing that no new live cells will be added."""
    for j in range(i-width-1, i+width+2):
        if not check_rule_at(j, True):
            return False
    return True

def check_rule_at(i, final=False):
    global pattern, width, neighbors, rule, live_count, max_n
    """Check whether cell i can possibly be part of a still life."""
    state = False
    if i >= 0 and i < len(pattern):
        state = pattern[i]
    
    min_neighbors = 0
    max_neighbors = len(neighbors)
    for delta in neighbors:
        j = i + delta
        if j < 0 or j >= len(pattern) or pattern[j] == False:
            max_neighbors -= 1
        elif pattern[j] == True:
            min_neighbors += 1
        elif final or live_count >= max_n:
            max_neighbors -= 1

    if state != True:  # false or none
        for n in range(min_neighbors, max_neighbors+1):
            if not rule[0][n]: return True
    if state != False:  # true or none
        for n in range(min_neighbors, max_neighbors+1):
            if rule[1][n]: return True
        
def merge_components(i):
    global neighbors, pattern, width, components, parents, comp_size, freedoms, merge_undo_list
    # find the adjacent connected components
    nearby = set()
    for delta in neighbors:
        j = i + delta
        if j < 0 or j >= len(pattern) or not pattern[j]:
            continue
        while j >= 0 and j != parents[j]:
            j = parents[j]
        if j < 0: raise "Cell %d (neighbor of %d) has invalid ancestor %d!" % (i+delta, i, j) 
        nearby.add(j)

    new_freedoms = set((i+1, i+width-1, i+width, i+width+1))
    
    if not nearby:
        # this is a new component!
        parents[i] = i
        comp_size[i] = 1
        freedoms[i] = new_freedoms
        components.add(i)
    else:
        # sort adjacent components by size, merge all into largest
        nearby = sorted(nearby, key=lambda x: comp_size[x])
        j = nearby[-1]
        old_freedoms = freedoms[j].copy()
        for k in nearby[:-1]:
            parents[k] = j
            comp_size[j] += comp_size[k]
            freedoms[j] |= freedoms[k]
            components.remove(k)
        # finally add this cell to the merged component
        parents[i] = j
        comp_size[i] = 1
        comp_size[j] += 1
        freedoms[j].remove(i)
        freedoms[j] |= new_freedoms
        # record undo information
        merge_undo_list[i] = (nearby, old_freedoms)

def undo_component_merge(i):
    global components, parents, comp_size, freedoms, merge_undo_list
    j = parents[i]
    if j >= 0 and parents[j] != j: raise "Parent %d of cell %d has other parent %d!" % (j, i, parent[j])

    if i in merge_undo_list:
        nearby, old_freedoms = merge_undo_list.pop(i)
        if nearby[-1] != j: raise "Cell %d has parent %d, expected %d!" % (i, j, nearby[-1])
        comp_size[j] -= 1
        for k in nearby[:-1]:
            if parents[k] != j: raise "Trying to split component %d from %d (while removing cell %d), but it has parent %d!" % (k, j, i, parent[k])
            parents[k] = k
            comp_size[j] -= comp_size[k]
            components.add(k)
        freedoms[j] = old_freedoms
    elif j >= 0:
        if i != j: raise "Cell %d has parent %d but no undo list!" % (i, j)
        if i not in components: raise "Cell %d is self-parented but not a component!" % (i)
        components.remove(i)
        freedoms.pop(i)
    else:
        return  # looks like an insta-reject

    # mark this cell as not being in a component 
    parents[i] = -1
    comp_size[i] = 0

def minimum_bridge_length():
    global components, freedoms, width
    """Return minimum number of cells needed to join all components together."""
    if len(components) < 2: return 0
    
    # FIXME: we really should store these pre-sorted
    ranges = sorted(sorted(i % width for i in freedoms[c]) for c in components)

    prev = ranges[0]
    stack = []
    parent = None
    gap_sum = gap_max = 0
    ranges.append([i + width for i in ranges[0]])
    for curr in ranges[1:]:
        if curr[0] < prev[-1]:
            # the new range is nested inside the previous one
            stack.append((prev, gap_max))
            parent = prev
            gap = curr[0] - max(i for i in parent if i <= curr[0])
            gap_max = gap
            gap_sum += gap
            continue

        while len(stack) and curr[0] >= parent[-1]:
            # the new range is outside the old parent
            gap = min(i for i in parent if i >= prev[-1]) - prev[-1]
            gap_max = max(gap, gap_max)
            gap_sum += gap - gap_max
            # designate the old parent as the previous component
            prev, gap_max = stack.pop()
            # restore grandparent as parent, if any
            if len(stack): parent = stack[-1][0]
            
        # now the new range is simply adjacent to the previous
        gap = curr[0] - prev[-1]
        gap_max = max(gap, gap_max)
        gap_sum += gap
        prev = curr

    gap_sum -= gap_max
    return gap_sum + len(components) - 1
        
def close_components(i):
    global close_undo_list, freedoms
    close_undo_list[i] = undo = []
    for c,f in freedoms.items():
        if i in f:
            undo.append(c)
            f.remove(i)
            if len(f) < 1: return False
    return True

def undo_component_close(i):
    global close_undo_list, freedoms
    for c in close_undo_list.pop(i, []):
        freedoms[c].add(i)

def print_pattern(i):
    global pattern, width
    left = right = start
    while left > 0 and True in pattern[left-1::width]:
        left -= 1
    while right <= left + width and True in pattern[right::width]:
        right += 1
    while True:
        row = pattern[left:right]
        if True not in row: break
        print("".join("#" if cell else "." for cell in row))
        left += width
        right += width
    print("")
    stdout.flush()
    
i = 0
while i >= 0:
    if pattern[i] == None:
        ok = set_pattern(i, False)
        if ok: i += 1
    elif pattern[i] == False:
        ok = set_pattern(i, True)
        if ok: i += 1
    elif pattern[i] == True:
        set_pattern(i, None)
        i -= 1
    else:
        raise "Unexpected value %s at index %d." % (repr(pattern[i]), i)
