# visual_grid_game.py
import random
import tkinter as tk


class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, custom_walls=None):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.agent_facing = 'Right'  # Facing direction: 'Up', 'Down', 'Left', 'Right'

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            # Dynamically generate random scattered walls (~10% of total grid cells)
            self.walls = set()
            num_walls = int(self.width * self.height * 0.10)
            while len(self.walls) < num_walls:
                wx = random.randint(0, self.width - 1)
                wy = random.randint(0, self.height - 1)
                if (wx, wy) != (0, 0):  # Avoid agent starting position
                    self.walls.add((wx, wy))

        # Dynamically generate random food positions avoiding walls and agent start
        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        # Generate adversarial opponents
        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    def get_percept(self) -> dict:
        """
        Step 1.1 — Partial Observability:
        Instead of returning exact global coordinates (agent_pos), this method
        now returns only LOCAL boolean percepts based on the agent's current
        facing direction, simulating a partially observable environment.
        """
        # Compute the cell directly ahead in the agent's facing direction
        ax, ay = self.agent_pos
        direction_deltas = {
            'Up':    (0,  1),
            'Down':  (0, -1),
            'Left':  (-1, 0),
            'Right': (1,  0),
        }
        dx, dy = direction_deltas[self.agent_facing]
        ahead_x, ahead_y = ax + dx, ay + dy

        # wall_ahead: True if the cell in front is a wall OR out of bounds
        out_of_bounds = not (
            0 <= ahead_x < self.width and 0 <= ahead_y < self.height)
        wall_ahead = out_of_bounds or (ahead_x, ahead_y) in self.walls

        # food_here: True if there is food on the agent's CURRENT cell
        food_here = tuple(self.agent_pos) in self.food_positions

        return {
            'wall_ahead': wall_ahead,
            'food_here':  food_here,
            'facing':     self.agent_facing,
            'score':      self.score,
            'remaining_food': len(self.food_positions),
            # ── Step 1.1: Expose the global world model so search agents ────
            # can plan paths offline before taking any physical action.
            'grid_size': (self.width, self.height),
            'walls':     list(self.walls),
            'all_food':  list(self.food_positions),
            # Current agent position is also exposed for search planning
            'agent_pos': list(self.agent_pos),
        }

    def execute_action(self, action: str):
        """
        Supported actions:
          - 'move_forward' : move one cell in the current facing direction
          - 'turn_left'    : rotate facing 90° counter-clockwise (no movement)
          - 'turn_right'   : rotate facing 90° clockwise (no movement)
          - 'suck'         : collect food on the current cell
          Legacy directional actions ('Up','Down','Left','Right') are still
          accepted for backwards compatibility with the random baseline.
        """
        self.steps += 1
        new_pos = list(self.agent_pos)

        # --- Turning actions (change facing, no movement) ---
        turn_left_map = {'Up': 'Left',  'Left': 'Down',
                         'Down': 'Right', 'Right': 'Up'}
        turn_right_map = {'Up': 'Right', 'Right': 'Down',
                          'Down': 'Left',  'Left': 'Up'}

        if action == 'turn_left':
            self.agent_facing = turn_left_map[self.agent_facing]
            return  # pure rotation, no position change

        if action == 'turn_right':
            self.agent_facing = turn_right_map[self.agent_facing]
            return  # pure rotation, no position change

        if action == 'suck':
            # Collect food at current position (handled below)
            pass

        elif action == 'move_forward':
            direction_deltas = {
                'Up':    (0,  1),
                'Down':  (0, -1),
                'Left':  (-1, 0),
                'Right': (1,  0),
            }
            dx, dy = direction_deltas[self.agent_facing]
            new_pos[0] += dx
            new_pos[1] += dy
            # Clamp to grid boundaries
            new_pos[0] = max(0, min(self.width - 1, new_pos[0]))
            new_pos[1] = max(0, min(self.height - 1, new_pos[1]))

        # --- Legacy directional actions (backward compatibility) ---
        elif action == 'Up':
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)
            self.agent_facing = 'Up'
        elif action == 'Down':
            new_pos[1] = max(0, new_pos[1] - 1)
            self.agent_facing = 'Down'
        elif action == 'Left':
            new_pos[0] = max(0, new_pos[0] - 1)
            self.agent_facing = 'Left'
        elif action == 'Right':
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)
            self.agent_facing = 'Right'

        if tuple(new_pos) in self.walls:
            self.score -= 5
        else:
            self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.food_positions:
            self.food_positions.remove(tuple_pos)
            self.score += 20

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1

            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 120 or self.collision


# =============================================================================
# Step 1.2 — Simple Reflex Agent
# =============================================================================
class SimpleReflexAgent:
    """
    A Simple Reflex Agent that acts on ONLY the current percept.
    It has NO __init__ and stores NO history — pure Condition-Action rules.

    Fatal flaw: in a partially observable environment it cannot detect loops,
    so it gets trapped in corners / U-shaped walls and cycles forever.

    Condition-Action rules (in priority order):
      1. IF food_here  → suck
      2. IF wall_ahead → turn_left
      3. ELSE          → move_forward
    """

    def sense_and_act(self, percept: dict) -> str:
        # Rule 1 — highest priority: eat food when standing on it
        if percept['food_here']:
            return 'suck'

        # Rule 2 — obstacle avoidance: wall or boundary directly ahead
        if percept['wall_ahead']:
            return 'turn_left'

        # Rule 3 — default: keep moving forward
        return 'move_forward'


# =============================================================================
# Step 1.3 — Model-Based Agent (Memory & State)
# =============================================================================
class ModelBasedAgent:
    """
    A Model-Based Reflex Agent that maintains an internal memory state.

    Unlike SimpleReflexAgent, this agent:
      - Has an __init__ that initialises memory (visited cells, position tracker)
      - Updates its internal model BEFORE choosing an action (Transition Model)
      - Queries memory in its IF-THEN rules to break out of loops

    Internal state (all relative — the agent has NO access to global coords):
      - self.rel_pos     : [dx, dy] relative position from start
      - self.visited     : set of visited relative positions
      - self.last_action : the action returned on the previous step
    """

    # ── Step 1.3 (2) ── initialise memory state ──────────────────────────────
    def __init__(self):
        self.rel_pos = (0, 0)              # relative position from start
        self.visited = {(0, 0)}            # cells we have been on
        self.last_action = None            # most recent action taken
        self.facing = 'Right'              # mirror of environment facing

    # ── helpers for relative-position bookkeeping ────────────────────────────
    _DIRECTION_DELTA = {
        'Up':    (0,  1),
        'Down':  (0, -1),
        'Left':  (-1, 0),
        'Right': (1,  0),
    }
    _TURN_LEFT = {'Up': 'Left',  'Left': 'Down',
                  'Down': 'Right', 'Right': 'Up'}
    _TURN_RIGHT = {'Up': 'Right', 'Right': 'Down',
                   'Down': 'Left',  'Left': 'Up'}

    def _cell_in_direction(self, direction):
        """Return the relative cell that is one step in `direction`."""
        dx, dy = self._DIRECTION_DELTA[direction]
        return (self.rel_pos[0] + dx, self.rel_pos[1] + dy)

    # ── Step 1.3 (3 & 4) ── sense, update model, then act ────────────────────
    def sense_and_act(self, percept: dict) -> str:
        # ── Transition & Sensor Model: update internal state ────────────────
        #    Record what happened as a result of the PREVIOUS action.
        if self.last_action == 'move_forward' and not percept['wall_ahead']:
            # The move succeeded on the previous tick — update rel_pos
            # (If wall_ahead is True RIGHT NOW, the move may have been blocked;
            #  we only advance the tracker when we actually moved.)
            pass  # position already updated below after choosing action
        self.facing = percept['facing']  # sync with environment

        # ── Condition-Action rules that QUERY memory ────────────────────────

        # Rule 1 — eat food if standing on it
        if percept['food_here']:
            self.last_action = 'suck'
            return 'suck'

        # Rule 2 — wall ahead: decide turn direction using memory
        if percept['wall_ahead']:
            left_dir = self._TURN_LEFT[self.facing]
            right_dir = self._TURN_RIGHT[self.facing]
            left_cell = self._cell_in_direction(left_dir)
            right_cell = self._cell_in_direction(right_dir)

            left_is_visited = left_cell in self.visited
            right_is_visited = right_cell in self.visited

            # Step 1.3 (4) example rule:
            #   IF wall_ahead AND left_is_visited THEN turn_right
            if left_is_visited and not right_is_visited:
                self.last_action = 'turn_right'
                return 'turn_right'
            elif right_is_visited and not left_is_visited:
                self.last_action = 'turn_left'
                return 'turn_left'
            elif left_is_visited and right_is_visited:
                # Both visited — try turning right to break the cycle
                self.last_action = 'turn_right'
                return 'turn_right'
            else:
                # Neither visited — default to turning left
                self.last_action = 'turn_left'
                return 'turn_left'

        # Rule 3 — no wall: check if moving forward leads to an unvisited cell
        ahead_cell = self._cell_in_direction(self.facing)
        if ahead_cell in self.visited:
            # Already been there — try turning to find unexplored territory
            right_dir = self._TURN_RIGHT[self.facing]
            right_cell = self._cell_in_direction(right_dir)
            if right_cell not in self.visited:
                self.last_action = 'turn_right'
                return 'turn_right'
            left_dir = self._TURN_LEFT[self.facing]
            left_cell = self._cell_in_direction(left_dir)
            if left_cell not in self.visited:
                self.last_action = 'turn_left'
                return 'turn_left'
            # All neighbours visited — move forward anyway to avoid deadlock

        # Default — move forward and record the new cell
        new_cell = self._cell_in_direction(self.facing)
        self.rel_pos = new_cell
        self.visited.add(new_cell)
        self.last_action = 'move_forward'
        return 'move_forward'


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=2, walls=None,
                 agent_class=None):
        self.root = root
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents,
                                      custom_walls=walls)
        # Instantiate the agent (SimpleReflexAgent has no __init__ args needed)
        self.agent = agent_class() if agent_class is not None else None

        # Dynamically calculate cell size so the total canvas fits nicely within a 600x600 window ceiling
        max_canvas_dim = 600
        self.cell_size = max(
            20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w,
                                height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(
            root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12), bg="#000066",
                             fg="white")
        self.btn.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#f1f5f9" if (
                    x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                # Only draw text if cell is large enough
                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                         outline="#7a0000")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066",
                                outline="#1e3a8a")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()

                if self.agent is not None:
                    # Use the plugged-in agent (e.g. SimpleReflexAgent)
                    action = self.agent.sense_and_act(percept)
                else:
                    # Fallback: random baseline
                    action = random.choice(['Up', 'Down', 'Left', 'Right'])

                self.env.execute_action(action)

                self.draw_grid()
                facing_arrow = {'Up': '↑', 'Down': '↓', 'Left': '←', 'Right': '→'}.get(
                    self.env.agent_facing, '?')
                self.label.config(
                    text=(
                        f"Score: {self.env.score} | Steps: {self.env.steps} | "
                        f"Action: {action} | Facing: {facing_arrow} | "
                        f"Food left: {percept['remaining_food']}"
                    )
                )
                self.root.after(300, step)
            else:
                end_text = (
                    f"Collision! Game Over! Final Score: {self.env.score}"
                    if self.env.collision
                    else f"Done! Final Score: {self.env.score}"
                )
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    # ── Step 1.2/1.3: import SearchAgent from agent.py ──────────────────────
    from agent import SearchAgent

    root = tk.Tk()
    root.withdraw()  # hide main window until choice is made

    # ── Let the user pick which agent to watch ──────────────────────────────
    import tkinter.simpledialog as sd
    choice = sd.askstring(
        "IT3012 — Agent Selection",
        "Which agent?\n\n"
        "  1 = SimpleReflexAgent  (will get trapped)\n"
        "  2 = ModelBasedAgent    (uses memory to escape)\n"
        "  3 = SearchAgent — BFS  (Practical 03, optimal)\n"
        "  4 = SearchAgent — DFS  (Practical 03, suboptimal)\n"
        "  5 = SearchAgent — UCS  (Practical 03, optimal)\n"
        "  6 = SearchAgent — A*   (Practical 04, optimal)\n\n"
        "Enter 1, 2, 3, 4, 5, or 6:",
        parent=root,
    )

    if choice == '2':
        agent_cls = ModelBasedAgent
        title_suffix = "Model-Based Agent (Practical 02)"
    elif choice == '3':
        # BFS Search Agent
        def make_bfs():
            a = SearchAgent(); a.active_algo = 'BFS'; return a
        agent_cls = make_bfs
        title_suffix = "Search Agent — BFS (Practical 03)"
    elif choice == '4':
        # DFS Search Agent
        def make_dfs():
            a = SearchAgent(); a.active_algo = 'DFS'; return a
        agent_cls = make_dfs
        title_suffix = "Search Agent — DFS (Practical 03)"
    elif choice == '5':
        # UCS Search Agent
        def make_ucs():
            a = SearchAgent(); a.active_algo = 'UCS'; return a
        agent_cls = make_ucs
        title_suffix = "Search Agent — UCS (Practical 03)"
    elif choice == '6':
        # A* Search Agent
        def make_astar():
            a = SearchAgent(); a.active_algo = 'AStar'; return a
        agent_cls = make_astar
        title_suffix = "Search Agent — A* (Practical 04)"
    else:
        agent_cls = SimpleReflexAgent
        title_suffix = "Simple Reflex Agent (Practical 02)"

    root.deiconify()

    # Fixed set of 15 manually placed walls (same map on every run)
    custom_fixed_walls = [
        # Wall 1: Vertical barrier on the left (5 blocks)
        (5, 4), (5, 5), (5, 6), (5, 7), (5, 8),
        # Wall 2: Horizontal barrier in the middle (5 blocks)
        (12, 12), (13, 12), (14, 12), (15, 12), (16, 12),
        # Wall 3: L-shaped barrier on the right (5 blocks)
        (22, 6), (22, 7), (22, 8), (23, 8), (24, 8)
    ]

    app = GridGameGUI(
        root,
        width=30, height=20,
        num_food=10,
        num_opponents=0,
        walls=custom_fixed_walls,   # <--- Fixed 15 manually placed walls
        agent_class=agent_cls,
    )
    root.title(f"IT3012 — {title_suffix}")
    root.mainloop()
