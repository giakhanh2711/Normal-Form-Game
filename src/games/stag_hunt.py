GAME_NAME = "STAG HUNT (Coordination game)"

GAME_STRATEGIES = ["STAG", "HUNT"]

STRATEGY_PROMPTS = {
    "Take risk": ("You are playing Stag Hunt Game. "
                    "You should coorperate with the other player and should take risk. "
                    "Respond with exactly one word: STAG or HARE"),

    "Avoid risk": ("You are playing Stag Hunt Game. "
                    "You are should play safely to guarantee a non-zero payoff and protect yourself against the worst-case scenario where the opponent defect or plays selfishly. "
                    "Respond with exactly one word: STAG or HARE"),

    "Reasoning": ("You are playing Stag Hunt Game. "
                    "Evaluate potential risks and payoffs that you can receive, and choose the mathematically optimal action "
                    "Respond with exactly one word: STAG or HARE")
}

PAYOFFS = {
    ("STAG", "STAG"): (4, 4),
    ("STAG", "HARE"): (0, 3),
    ("HARE", "STAG"): (3, 0),
    ("HARE", "HARE"): (3, 3),
}


ACTIONS = ["STAG", "HARE"]
