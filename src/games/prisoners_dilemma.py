GAME_NAME = "Prisoner's Dilemma"

GAME_STRATEGIES = ["COOPERATE", "DEFECT"]

# 1.2. Prompts for LLM to choose strategies
STRATEGY_PROMPTS = {
    "Cooperative": ("You are playing a one-shot Prisoner's Dilemma. "
    "You should coorperate with the other player. "
    "Respond with exactly one word: COOPERATE or DEFECT"),

    "Reasoning": ("You are playing a one-shot Prisoner's Dilemma. "
    "Reason about what the opponent is likely to do and choose the strategy that you believe is the best respond to maximize your expected payoff. "
    "Respond with exactly one word: COOPERATE or DEFECT"),

    "Greedy": ("You are playing a one-shot Prisoner's Dilemma. "
    "You should be seflfish and maximize your own payoff, regardless of the opponent's payoff or choice or the social outcome. "
    "Respond with exactly one word: COOPERATE or DEFECT")
}

# 1.1. Payoff matrix for strategy profiles
PAYOFFS = {
    ("COOPERATE", "COOPERATE"): (3, 3),
    ("COOPERATE", "DEFECT"): (0, 5),
    ("DEFECT", "COOPERATE"): (5, 0),
    ("DEFECT", "DEFECT"): (1, 1),
}

ACTIONS = ["COOPERATE", "DEFECT"]

NE1 = [[0.0, 1.0]]