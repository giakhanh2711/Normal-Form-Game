GAME_NAME = "Negotiation-style"

GAME_STRATEGIES = ["Take risk", "Avoid risk", "Reasoning"]

PAYOFFS = {
    ("LOW", "LOW"): (3, 3),
    ("LOW", "MEDIUM"): (3, 5),
    ("LOW", "HIGH"): (3, 7),
    ("MEDIUM", "LOW"): (5, 3),
    ("MEDIUM", "MEDIUM"): (5, 5),
    ("MEDIUM", "HIGH"): (0, 0),
    ("HIGH", "LOW"): (7, 3),
    ("HIGH", "MEDIUM"): (0, 0),
    ("HIGH", "HIGH"): (0, 0),
}


STRATEGY_PROMPTS = {
    "Take risk": ("You are playing a simultaneous-move game with an opponent. "
    "Both of you will give the decision simultaneously without knowing the opponent's choice. "
    "The total available surplus is 10. "
    "You must choose one of the demand: Low (3), Medium (5), High (7). "
    "You both will receive your demand if the total of your demand and your opponent's demand does not exceed 10, "
    "otherwise you both receive 0. "
    "You are completely willing to take risk with the purpose to give yourself a chance to receive the highest possible payoff. Choose your demand by "
    "responding with exactly one word: LOW, MEDIUM or HIGH."
    ),

    "Avoid risk": ("You are playing a simultaneous-move game with an opponent. "
    "Both of you will give the decision simultaneously without knowing the opponent's choice. "
    "The total available surplus is 10. "
    "You must choose one of the demand: Low (3), Medium (5), High (7). "
    "You both will receive your demand if the total of your demand and your opponent's demand does not exceed 10, "
    "otherwise you both receive 0. "
    "You are highly risk-averse, and to prioritize to receive a non-zero payoff above all else. "
    "Choose the demand that completely minimize the risk of negotiation fails. "
    "Response with exactly one word: LOW, MEDIUM or HIGH."
    ),

    "Reasoning": ("You are playing a simultaneous-move game with an opponent. "
    "Both of you will give the decision simultaneously without knowing the opponent's choice. "
    "The total available surplus is 10. "
    "You must choose one of the demand: Low (3), Medium (5), High (7). "
    "You both will receive your demand if the total of your demand and your opponent's demand does not exceed 10, "
    "otherwise you both receive 0. "
    "Reason logically about what the opponent is most likely to demand, considering the expected payoff you can receive. Then, determine the optimal best-response of the demand to your prediction. "
    "Respond with exactly one word: LOW, MEDIUM or HIGH."
    )
}


ACTIONS = ["LOW", "MEDIUM", "HIGH"]