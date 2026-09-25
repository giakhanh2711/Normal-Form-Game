import re
import importlib
import pandas as pd
import numpy as np
import math


def normalize_cf_cookie(raw):
    raw = raw.strip().strip('"').strip("'")
    match = re.search(r"CF_Authorization=([^;\n]+)", raw)
    return f"CF_Authorization={match.group(1)}" if match else (
        f"CF_Authorization={raw}" if raw.startswith("eyJ") else raw
    )


def load_game_info(game_name):
    """
    Load game's prompts and payoff
    """
    module_path = f"games.{game_name}"
    return importlib.import_module(module_path)


def read_prompt_strategies(strategy_prompts: dict):
    return list(strategy_prompts.keys())


def read_empirical_payoff_matrix(filename, strategies):
    """
    filename = "Normal-Form-Game/data/negotiation_game/negotiation_game.csv"
    strategies = ['Take risk', 'Avoid risk', 'Reasoning']
    """

    df = pd.read_csv(filename)

    player1 = df.pivot(index='p1_strategy', columns='p2_strategy', values='u1_mean').reindex(index=strategies, columns=strategies)
    player2 = df.pivot(index='p1_strategy', columns='p2_strategy', values='u2_mean').reindex(index=strategies, columns=strategies)

    payoff_matrix = np.stack([player1.values, player2.values], axis=-1)

    return payoff_matrix


def read_payoff_matrix(payoff: dict):
    payoff_matrix = []
    n_actions = int(math.log2(len(payoff)))

    print(n_actions)

    row = []
    i = 0
    for k, v in payoff.items():
        if i == n_actions:
            payoff_matrix.append(row.copy())
            row = []
            i = 0
        row.append(list(v))
        i += 1

    payoff_matrix.append(row.copy())
    return np.array(payoff_matrix)