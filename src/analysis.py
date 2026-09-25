import statistics
import math
import pandas as pd
import numpy as np
import json
import argparse
from pathlib import Path

import utils


class Analyst:
    """
    Script that produces the analysis plots and tables.
    file_name = "data/{game_name}/{game_name}.csv"
    """

    def __init__(self, file_name=None):
        self.filename = file_name

    def show_estimate_payoff(self, records: pd.DataFrame):
        # episodes_df = pd.DataFrame(records)
        episodes_df = records
        
        summary_rows = []
        for (s1, s2), group in episodes_df.groupby(["p1_strategy", "p2_strategy"], sort=False):
            u1_mean, u1_ci = self.mean_ci(group["u1"])
            u2_mean, u2_ci = self.mean_ci(group["u2"])
            summary_rows.append({
                "p1_strategy": s1, "p2_strategy": s2, "n": len(group),
                "u1_mean": u1_mean, "u1_ci95": u1_ci,
                "u2_mean": u2_mean, "u2_ci95": u2_ci,
            })
        
        estimates_df = pd.DataFrame(summary_rows)
        print(f"Emperical payoff estimation:\n{estimates_df}")
        if self.filename is not None:
            estimates_df.to_csv(self.filename)

    # 2.2 Compute the sample mean payoff
    # 2.3 Compute 95% confidence intervals
    def mean_ci(self, values):
        values = list(values)
        mean = statistics.fmean(values)
        half_width = 0.0 if len(values) < 2 else 1.96 * statistics.stdev(values) / math.sqrt(len(values))
        return mean, half_width


    def get_records(self, file_name):
        """
        json file
        """
        with open(file_name, 'r') as f:
            data = json.load(f)
        
        trials = data['trials']
        df_trials = pd.DataFrame(trials)

        return df_trials

    def analyze_game_llm_json(self, file_name, game_actions: list, payoff_matrix: np.ndarray,
                                nash_eq: np.ndarray, eps: float = 1e-5,
                                best_response_thres: float = 0.10):

        df_trials = self.get_records(file_name)

        action_to_idx = {act.upper(): idx for idx, act in enumerate(game_actions)}
        N = len(game_actions)

        player1_payoff = payoff_matrix[:, :, 0]

        nash_eq = np.asarray(nash_eq, dtype=float)
        nash_eq = np.clip(nash_eq, eps, 1.0)
        nash_eq /= nash_eq.sum()

        strategies = df_trials['p1_strategy'].unique()
        results = []

        for s in strategies:
            trials_per_strategy = df_trials[df_trials['p1_strategy'] == s]
            total_trials = len(trials_per_strategy)
            if total_trials == 0:
                continue

            actions_count1 = np.zeros(N)
            for act, count in trials_per_strategy['p1_action'].value_counts().items():
                if act in action_to_idx:
                    actions_count1[action_to_idx[act]] = count
            dist_per_strategy1 = actions_count1 / total_trials

            actions_count2 = np.zeros(N)
            for act, count in trials_per_strategy['p2_action'].value_counts().items():
                if act in action_to_idx:
                    actions_count2[action_to_idx[act]] = count
            dist_per_strategy2 = actions_count2 / total_trials
            dist_per_strategy1 = np.clip(dist_per_strategy1, eps, 1.0)
            dist_per_strategy1 /= dist_per_strategy1.sum()
            kl_div = np.sum(dist_per_strategy1 * np.log(dist_per_strategy2 / nash_eq))

            expected_payoffs1 = player1_payoff @ dist_per_strategy2 

            empirical_expected_payoff = np.dot(dist_per_strategy2, expected_payoffs1)

            max_expected_payoffs1 = np.max(expected_payoffs1)

            difference = max_expected_payoffs1 - empirical_expected_payoff
            is_approx_br = difference <= best_response_thres

            row_data = {
                "Prompt Strategy": s,
                "Trials": total_trials,
                "KL Div (P || Q)": round(kl_div, 4),
                "Exp Emp Payoff": round(empirical_expected_payoff, 4),
                "Max Payoff": round(max_expected_payoffs1, 4),
                "Difference": round(difference, 4),
                "~Best Response?": "Yes" if is_approx_br else "No"
            }

            for idx, act in enumerate(game_actions):
                row_data[f"P1 {act} Rate"] = round(dist_per_strategy2[idx], 4)

            results.append(row_data)

        summary_df = pd.DataFrame(results)
        return summary_df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json_trials_file",
        type=Path,
        required=True,
        help="JSON file containing the game definition and trial results",
    )
    parser.add_argument(
        "--game_name",
        type=str,
        required=True,
        choices=["negotiation", "prisoners_dilemma", "stag_hunt"],
    )

    parser.add_argument(
        "--save_estimate_payoff_path",
        type=str,
        default=None
    )
    
    args = parser.parse_args()

    game_name = Path(args.game_name).stem
    game_module = utils.load_game_info(game_name)
    actions = game_module.ACTIONS
    payoff_matrix = utils.read_payoff_matrix(game_module.PAYOFFS)

    stats = Analyst()

    for ne1 in game_module.NE1:
        results = stats.analyze_game_llm_json(
            args.json_trials_file,
            actions,
            payoff_matrix,
            ne1,
        )
        print(results.to_string(index=False))

    if args.save_estimate_payoff_path:
        stats.filename = args.json_trials_file
        stats.show_estimate_payoff(stats.get_records(stats.filename))


if __name__ == "__main__":
    main()