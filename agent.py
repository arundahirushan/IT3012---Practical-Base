# agent.py
import random
from collections import deque
import heapq
import math
from logic_engine import KnowledgeBase


# =============================================================================
# Original Greedy/Random Agent (baseline)
# =============================================================================
class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)


# =============================================================================
# Step 1.2 & 1.3 — Search Agent (Goal-Based / Planning Agent)
# =============================================================================
class SearchAgent:
    """
    A Goal-Based Planning Agent that uses uninformed search (BFS / DFS / UCS)
    to compute a full action plan BEFORE moving, then executes it step-by-step.

    Step 1.2 — implements bfs_search(), dfs_search(), ucs_search()
    Step 1.3 — sense_and_act() builds a plan when empty and pops one action per tick
    """

    def __init__(self):
        self.plan = []                 # Step 1.3: the offline action sequence
        self.active_algo = 'BFS'      # Switch to 'DFS' or 'UCS' to compare

        # ── Step 3.1: Instantiate the Knowledge Base ─────────────────────────────
        self.kb = KnowledgeBase()

        # ── Step 3.1: Define game safety rules (Horn Clauses) ────────────────────
        # Rule 1: TargetVisible ∧ HasDust → SafeToEngage
        self.kb.tell_rule(['TargetVisible', 'HasDust'], 'SafeToEngage')

        # Rule 2: SafeToEngage ∧ BloodseekerMissing → Retreat
        self.kb.tell_rule(['SafeToEngage', 'BloodseekerMissing'], 'Retreat')

    def manhattan_distance(self, pos, goal):
        """h(n) = |x1 - x2| + |y1 - y2|"""
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def euclidean_distance(self, pos, goal):
        """h(n) = sqrt((x1-x2)^2 + (y1-y2)^2)"""
        return math.sqrt((pos[0] - goal[0])**2 + (pos[1] - goal[1])**2)

    # ──────────────────────────────────────────────────────────────────────────
    # Step 1.2 (3) — BFS: FIFO queue → shallowest (shortest) path first
    # ──────────────────────────────────────────────────────────────────────────
    def bfs_search(self, start, goal, walls, grid_size):
        """
        Breadth-First Search.
        Returns a list of directional actions (e.g. ['Right', 'Up', 'Up', ...])
        that form the shortest path from start to goal, or [] if unreachable.

        Uses a FIFO deque — deque.popleft() expands the shallowest node first.
        Maintains a `reached` set (Graph Search) to prevent revisiting states.
        """
        width, height = grid_size
        wall_set = set(map(tuple, walls))

        # Each node in the frontier: (position, path_so_far)
        frontier = deque()
        frontier.append((tuple(start), []))
        reached = {tuple(start)}          # Step 1.2 (6): visited set

        while frontier:
            pos, path = frontier.popleft()   # FIFO — shallowest node first

            if pos == tuple(goal):
                return path                  # Found! Return the action sequence

            for action, (dx, dy) in [('Up',    (0, 1)),
                                      ('Down',  (0, -1)),
                                      ('Left',  (-1, 0)),
                                      ('Right', (1, 0))]:
                nx, ny = pos[0] + dx, pos[1] + dy
                neighbour = (nx, ny)

                # Check bounds, walls, and already-visited
                if (0 <= nx < width and 0 <= ny < height
                        and neighbour not in wall_set
                        and neighbour not in reached):
                    reached.add(neighbour)
                    frontier.append((neighbour, path + [action]))

        return []   # No path found

    # ──────────────────────────────────────────────────────────────────────────
    # Step 1.2 (4) — DFS: LIFO stack → deepest path first (suboptimal)
    # ──────────────────────────────────────────────────────────────────────────
    def dfs_search(self, start, goal, walls, grid_size):
        """
        Depth-First Search.
        Returns a list of actions from start to goal, or [] if unreachable.

        Uses a LIFO list — list.pop() expands the deepest node first.
        This finds A path, but NOT necessarily the shortest one.
        Maintains a `reached` set to prevent infinite loops (Graph Search).
        """
        width, height = grid_size
        wall_set = set(map(tuple, walls))

        frontier = [(tuple(start), [])]      # LIFO stack
        reached = {tuple(start)}

        while frontier:
            pos, path = frontier.pop()       # LIFO — deepest node first

            if pos == tuple(goal):
                return path

            for action, (dx, dy) in [('Up',    (0, 1)),
                                      ('Down',  (0, -1)),
                                      ('Left',  (-1, 0)),
                                      ('Right', (1, 0))]:
                nx, ny = pos[0] + dx, pos[1] + dy
                neighbour = (nx, ny)

                if (0 <= nx < width and 0 <= ny < height
                        and neighbour not in wall_set
                        and neighbour not in reached):
                    reached.add(neighbour)
                    frontier.append((neighbour, path + [action]))

        return []

    # ──────────────────────────────────────────────────────────────────────────
    # Step 1.2 (5) — UCS: Priority Queue ordered by total path cost g(n)
    # ──────────────────────────────────────────────────────────────────────────
    def ucs_search(self, start, goal, walls, grid_size):
        """
        Uniform-Cost Search.
        Returns the LOWEST-COST path from start to goal, or [] if unreachable.

        Uses a min-heap (heapq) — heapq.heappop() always expands the node with
        the lowest accumulated cost g(n) so far. With uniform step cost = 1,
        UCS is equivalent to BFS and also finds the optimal (shortest) path.
        Maintains a `reached` set for Graph Search.
        """
        width, height = grid_size
        wall_set = set(map(tuple, walls))

        # Heap entries: (cost, tie_breaker, position, path)
        counter = 0
        frontier = [(0, counter, tuple(start), [])]
        reached = {tuple(start)}

        while frontier:
            cost, _, pos, path = heapq.heappop(frontier)  # lowest cost first

            if pos == tuple(goal):
                return path

            for action, (dx, dy) in [('Up',    (0, 1)),
                                      ('Down',  (0, -1)),
                                      ('Left',  (-1, 0)),
                                      ('Right', (1, 0))]:
                nx, ny = pos[0] + dx, pos[1] + dy
                neighbour = (nx, ny)

                if (0 <= nx < width and 0 <= ny < height
                        and neighbour not in wall_set
                        and neighbour not in reached):
                    reached.add(neighbour)
                    counter += 1
                    step_cost = 1          # uniform cost grid
                    heapq.heappush(frontier,
                                   (cost + step_cost, counter,
                                    neighbour, path + [action]))

        return []

    # ──────────────────────────────────────────────────────────────────────────
    # Step 1.2: A* Search
    # ──────────────────────────────────────────────────────────────────────────
    def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan', percept=None):
        width, height = grid_size
        wall_set = set(map(tuple, walls))

        # Select heuristic
        h = self.manhattan_distance if heuristic_type == 'manhattan' else self.euclidean_distance

        g_start = 0
        h_start = h(start_pos, goal_pos)
        f_start = g_start + h_start

        counter = 0
        frontier = [(f_start, g_start, counter, tuple(start_pos), [])]
        reached_states = set()

        while frontier:
            f_cost, g_cost, _, current_pos, path_taken = heapq.heappop(frontier)

            if current_pos == tuple(goal_pos):
                return path_taken

            if current_pos in reached_states:
                continue
            reached_states.add(current_pos)

            for action, (dx, dy) in [('Up',    (0, 1)),
                                      ('Down',  (0, -1)),
                                      ('Left',  (-1, 0)),
                                      ('Right', (1, 0))]:
                nx, ny = current_pos[0] + dx, current_pos[1] + dy
                neighbour = (nx, ny)

                if (0 <= nx < width and 0 <= ny < height
                        and neighbour not in wall_set
                        and neighbour not in reached_states):

                    # ── Step 3.2: KB Feasibility Check ───────────────────────────────────────
                    # 1. Clear old percepts (facts only, rules are preserved)
                    self.kb.clear_facts()

                    # 2. Feed current tile's percepts into the KB
                    if percept:
                        food_list = percept.get('all_food', [])
                        target_visible = any(
                            abs(neighbour[0] - f[0]) + abs(neighbour[1] - f[1]) <= 2
                            for f in food_list
                        )
                        if target_visible:
                            self.kb.tell_fact('TargetVisible')

                        if list(neighbour) in food_list or tuple(neighbour) in [tuple(f) for f in food_list]:
                            self.kb.tell_fact('HasDust')

                        opponents = percept.get('opponents', [])
                        bloodseeker_present = any(
                            abs(neighbour[0] - op[0]) + abs(neighbour[1] - op[1]) <= 1
                            for op in opponents
                        )
                        if not bloodseeker_present:
                            self.kb.tell_fact('BloodseekerMissing')

                    # 3. Run inference
                    self.kb.forward_chain()

                    # 4. Feasibility gate: if Retreat was deduced, skip this tile
                    if 'Retreat' in self.kb.facts:
                        continue   # tile is LOGICALLY INFEASIBLE — do not add to open list

                    # ── Normal A* expansion ──────────────────────────────────────
                    g_new = g_cost + 1
                    h_new = h(neighbour, goal_pos)
                    f_new = g_new + h_new
                    counter += 1
                    heapq.heappush(frontier,
                                   (f_new, g_new, counter, neighbour, path_taken + [action]))

        return []

    # ──────────────────────────────────────────────────────────────────────────
    # Step 1.3 — sense_and_act: plan offline, execute one action per tick
    # ──────────────────────────────────────────────────────────────────────────
    def sense_and_act(self, percept: dict) -> str:
        """
        Goal-Based Planning Agent:
          1. If self.plan is empty, find the closest food pellet and run the
             selected search algorithm to build a complete action sequence.
          2. Pop and return the FIRST action from the plan each tick.
        """
        # Step 1.3 (2): check if plan is empty
        if not self.plan:
            start     = tuple(percept['agent_pos'])
            all_food  = percept['all_food']
            walls     = percept['walls']
            grid_size = percept['grid_size']

            if not all_food:
                # No food left — stay still
                return 'move_forward'

            # Step 1.3 (3): find the closest food pellet (Manhattan distance)
            goal = min(all_food,
                       key=lambda f: abs(f[0] - start[0]) + abs(f[1] - start[1]))
            goal = tuple(goal)

            # Run the chosen search algorithm
            if self.active_algo == 'DFS':
                path = self.dfs_search(start, goal, walls, grid_size)
            elif self.active_algo == 'UCS':
                path = self.ucs_search(start, goal, walls, grid_size)
            elif self.active_algo == 'AStar':
                path = self.astar_search(start, goal, walls, grid_size, heuristic_type='manhattan', percept=percept)
            else:
                path = self.bfs_search(start, goal, walls, grid_size)

            # Store the plan (reverse it so we can use .pop(0) efficiently)
            self.plan = path if path else ['move_forward']

        # Step 1.3 (4): return the next action from the plan
        return self.plan.pop(0)
