# test_logic.py
# IT3012 - Intelligent Agents | Practical 05
# Part 4: Self-Evaluation Test Cases for the Forward Chaining Logic Engine

from logic_engine import KnowledgeBase


def test_forward_chaining():
    """
    Automated validation of the KnowledgeBase and forward_chain() method.
    Runs 2 test cases that mirror the lab specification exactly.
    """
    kb = KnowledgeBase()

    # ── Add Domain Rules (Horn Clauses) ──────────────────────────────────────
    # These are the global game constraints defined in Step 3.1.
    # Rule 1: TargetVisible ∧ HasDust → SafeToEngage
    kb.tell_rule(['TargetVisible', 'HasDust'], 'SafeToEngage')
    # Rule 2: SafeToEngage ∧ BloodseekerMissing → Retreat
    kb.tell_rule(['SafeToEngage', 'BloodseekerMissing'], 'Retreat')

    # ─────────────────────────────────────────────────────────────────────────
    # Test Case 1: Safe Engagement (NO Retreat expected)
    # Scenario: The agent sees a target with dust, but the Bloodseeker is present.
    # Expected: SafeToEngage is deduced. Retreat is NOT deduced.
    # ─────────────────────────────────────────────────────────────────────────
    kb.clear_facts()                        # fresh start
    kb.tell_fact('TargetVisible')           # sensor: target spotted
    kb.tell_fact('HasDust')                 # sensor: dust confirmed
    # NOTE: 'BloodseekerMissing' is NOT asserted → Bloodseeker IS present
    kb.forward_chain()

    assert 'SafeToEngage' in kb.facts, \
        "Test 1 FAILED: Should have deduced SafeToEngage (TargetVisible ∧ HasDust → SafeToEngage)"
    assert 'Retreat' not in kb.facts, \
        "Test 1 FAILED: Should NOT have deduced Retreat (BloodseekerMissing was never told)"

    print("Test 1 Passed - Safe Engagement")

    # ─────────────────────────────────────────────────────────────────────────
    # Test Case 2: Unsafe Engagement (Retreat expected)
    # Scenario: Target visible, dust present, AND the Bloodseeker is missing.
    # Expected: Both SafeToEngage AND Retreat are deduced (chain: Rule1 → Rule2).
    # ─────────────────────────────────────────────────────────────────────────
    kb.clear_facts()                        # fresh start (rules still intact)
    kb.tell_fact('TargetVisible')           # sensor: target spotted
    kb.tell_fact('HasDust')                 # sensor: dust confirmed
    kb.tell_fact('BloodseekerMissing')      # sensor: Bloodseeker nowhere in sight
    kb.forward_chain()

    assert 'SafeToEngage' in kb.facts, \
        "Test 2 FAILED: Should have deduced SafeToEngage as intermediate step"
    assert 'Retreat' in kb.facts, \
        "Test 2 FAILED: Should have deduced Retreat (SafeToEngage ∧ BloodseekerMissing → Retreat)"

    print("Test 2 Passed - Unsafe Engagement")

    # ─────────────────────────────────────────────────────────────────────────
    # Final confirmation
    # ─────────────────────────────────────────────────────────────────────────
    print("\nAll Logic Engine Test Cases Passed!")

# ==============================================================================
# THEORY_ANSWERS
# ==============================================================================
"""
Question 1 - Reachability vs. Feasibility (Apply)
Reachability is a physical constraint - it asks "Can the agent physically enter this tile?" This is checked by verifying if the coordinates are in bounds, not a wall, and not already visited.
Feasibility is a logical constraint - it asks "Even if the agent can physically enter this tile, should it?" This is checked by clearing facts, inputting new percepts for the tile, running forward chaining on the KnowledgeBase, and skipping the tile if 'Retreat' is deduced.

Question 2 - Declarative vs. Procedural Paradigms (Analyze)
Procedural logic requires hardcoding an explicitly nested sequence of `if-else` blocks for each condition (e.g. `if TargetVisible and HasDust: ...`). With 50 rules, this results in O(50) explicitly written nested `if-else` statements.
Declarative logic with a KnowledgeBase lets the developer store rules as data instead of code, making it decoupled and robust. Adding 50 rules just means 50 `kb.tell_rule()` statements while the `forward_chain()` mechanism remains unchanged. Rule chaining also occurs seamlessly without having to manually order rules.

Question 3 - Modus Ponens & Horn Clauses (Understand)
Modus Ponens dictates: if P -> Q is true, and P is true, then Q must be true.
The `for premises, conclusion in self.rules` iterates the Horn Clauses (the rules / P -> Q).
The `all(p in self.facts for p in premises)` checks if the premise is true (if P is true).
The `self.facts.add(conclusion)` realizes the Modus Ponens logic by executing the logical conclusion (Q is true).
"""

if __name__ == "__main__":
    test_forward_chaining()
