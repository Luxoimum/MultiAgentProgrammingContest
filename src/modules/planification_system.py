class PlanificaitonSystem:
    def __init__(self):
        internal_state = {}
        goal = {}
        """
        task --> (b1, b2, b3)
        1. is goal zone in state?
            yes --> next requirement
            no  --> find(goal)
        2. is b0 in state?
            yes --> next requirement
            no  --> find(b0)
        3. is b1 in state?
            yes --> next requirement
            no  --> find(b1)
        4. is b2 in state?
            yes --> next requirement
            no  --> find(b2)
        5. is task agent in goal?
            yes --> wait(agent), next requirement
            no  --> move_goal(agent), next requirement
        
        
        """


