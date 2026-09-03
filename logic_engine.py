# logic_engine.py
# IT3012 - Intelligent Agents | Practical 05
# Part 1: The Knowledge Base (KB) — Declarative Fact & Rule Store

class KnowledgeBase:
    """
    A propositional Knowledge Base that stores Facts and Horn Clause Rules.

    Attributes:
        facts (set):  A set of unique string facts representing current percepts.
                      Example: {'TargetVisible', 'HasDust'}
        rules (list): A list of Tuples, each in the form:
                      ([premise_1, premise_2, ...], 'ConclusionString')
                      Example: (['TargetVisible', 'HasDust'], 'SafeToEngage')
    """

    def __init__(self):
        # DECLARE facts AS Set — stores unique string percepts
        self.facts = set()

        # DECLARE rules AS List — stores (premise_list, conclusion) tuples
        self.rules = []

    def tell_fact(self, fact_string: str):
        """
        Assert a new fact into the Knowledge Base.

        Args:
            fact_string (str): A percept label e.g. 'TargetVisible', 'HasDust'
        """
        # ADD fact_string TO facts
        self.facts.add(fact_string)

    def tell_rule(self, premise_list: list, conclusion_string: str):
        """
        Add a Horn Clause rule to the Knowledge Base.

        A Horn Clause has the form: P1 ∧ P2 ∧ ... → Conclusion
        Stored internally as: ([P1, P2, ...], 'Conclusion')

        Args:
            premise_list (list):       List of strings that are the antecedents.
            conclusion_string (str):   The string fact to derive if all premises hold.
        """
        # APPEND Tuple(premise_list, conclusion_string) TO rules
        self.rules.append((premise_list, conclusion_string))

    def clear_facts(self):
        """
        Remove all facts from the Knowledge Base.
        Rules are PRESERVED — only percepts (facts) are cleared.
        This is called before evaluating each new tile in A*.
        """
        # EMPTY the facts Set
        self.facts = set()

    def forward_chain(self):
        """
        Data-Driven Forward Chaining Inference Engine.

        Iterates over all rules repeatedly until no new facts are deduced
        in a complete pass (fixed-point / saturation).

        Algorithm (Modus Ponens):
            WHILE new facts were added in the last pass:
                FOR EACH (premises, conclusion) in rules:
                    IF conclusion NOT already known:
                        IF ALL premises ARE known facts:
                            ADD conclusion to facts
                            mark that new facts were added
        """
        # DECLARE new_facts_added = TRUE  →  enter the while loop at least once
        new_facts_added = True

        # Keep iterating until a full pass adds nothing new (fixed-point)
        while new_facts_added:
            new_facts_added = False          # reset flag at the start of each pass

            # Scan every rule in the knowledge base
            for premises, conclusion in self.rules:

                # Only consider rules whose conclusion is NOT yet known
                if conclusion not in self.facts:

                    # Modus Ponens Check:
                    # ALL premises must be present in the current fact set
                    if all(p in self.facts for p in premises):
                        # Fire the rule — derive the new fact
                        self.facts.add(conclusion)
                        new_facts_added = True   # signal: need another pass

if __name__ == '__main__':
    kb = KnowledgeBase()

    # Add a rule
    kb.tell_rule(['A', 'B'], 'C')
    assert len(kb.rules) == 1
    assert kb.rules[0] == (['A', 'B'], 'C')

    # Add facts
    kb.tell_fact('A')
    kb.tell_fact('A')   # duplicate — should not add twice
    assert kb.facts == {'A'}

    # Clear facts — rules must survive
    kb.clear_facts()
    assert kb.facts == set()
    assert len(kb.rules) == 1   # rule still exists!

    print("Part 1 smoke test PASSED")
