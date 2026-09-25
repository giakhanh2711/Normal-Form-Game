import numpy as np
from itertools import combinations
import argparse
from pathlib import Path
import utils

class SupportEnumeration:
    def __init__(self, strategies):
        self.strategies = np.array(strategies)

    def solve_indifference(self, indv_matrix, idx_row, idx_col, size):
        if len(idx_col) != len(idx_row):
            return None
        
        sub_matrix = indv_matrix[np.ix_(idx_row, idx_col)].T
        Ax = np.block([
            [sub_matrix, -np.ones((len(idx_col), 1))],
            [np.ones((1, len(idx_row))), np.zeros((1, 1))]
        ])
        b = np.zeros(len(idx_col) + 1)
        b[-1] = 1

        try:
            probs = np.linalg.solve(Ax, b)
            probs = probs[:-1]
            if np.any(probs < -1e-8):
                return None

            mixed_strategy = np.zeros(size)
            mixed_strategy[list(idx_row)] = probs
            return mixed_strategy / np.sum(mixed_strategy)
        except np.linalg.LinAlgError:
            return None


    def is_valid_ne(self, player1_matrix, player2_matrix, mxs1, mxs2, supp1, supp2, tol=1e-7):
        expected_u1 = player1_matrix @ mxs2
        expected_u2 = mxs1 @ player2_matrix
        best_payoff1 = np.max(expected_u1)
        best_payoff2 = np.max(expected_u2)

        for s in supp1:
            if abs(expected_u1[s] - best_payoff1) > tol:
                return False
        for s in supp2:
            if abs(expected_u2[s] - best_payoff2) > tol:
                return False

        if np.any(expected_u1 > best_payoff1 + tol) or np.any (expected_u2 > best_payoff2 + tol):
            return False

        return True


    def support_enumeration(self, payoff_matrix, tol=1e-8):
        matrix1 = payoff_matrix[:, :, 0]
        matrix2 = payoff_matrix[:, :, 1]
        nrows, ncols = matrix1.shape

        nes = []
        # Consider all possible sizes of support of player 1
        max_size = min(nrows, ncols)
        for size1 in range(1, max_size + 1):
            # Consider all possible combinations for each size
            for supp1 in combinations(range(nrows), size1):
                    for supp2 in combinations(range(ncols), size1):
                        # Player 2 indifference, solve mixed strategy for player 1
                        p = self.solve_indifference(matrix2.T, supp1, supp2, nrows)
                        if p is None:
                            continue

                        # Player 1 indifference, solve mixed strategy for player 2
                        q = self.solve_indifference(matrix1, supp2, supp1, ncols)
                        if q is None:
                            continue

                        if self.is_valid_ne(matrix1, matrix2, p, q, supp1, supp2, tol):
                            is_duplicate = False
                            for x, y in nes:
                                if np.allclose(p, x, atol=tol) and np.allclose(q, y, atol=tol):
                                    is_duplicate = True
                                    break
                            if not is_duplicate:
                                nes.append((p, q))

        return nes


    def print_nes(self, nes):
        print(f"Strategies: {self.strategies}")
        print(f"There are {len(nes)} Nash equilibrium")
        for ne in nes:
            if sum(ne[0] == 1) == 1 and sum(ne[1] == 1):
                print(f"({self.strategies[ne[0] == 1]}, {self.strategies[ne[1] == 1]})")
            else:
                print(f"({ne[0]}, {ne[1]})")



class LemkeHowson:
    def __init__(self, strategies):
        self.strategies = np.array(strategies)

        
    def setup_equations(self, payoff_matrix1, payoff_matrix2):
        m, n = payoff_matrix1.shape
        equation_player1 = np.hstack([payoff_matrix2.T, np.eye(n), np.ones((n, 1))])
        equation_player2 = np.hstack([np.eye(m), payoff_matrix1, np.ones((m, 1))])
        return equation_player1, equation_player2

    
    def normalize_positive(self, payoff_matrix):
        A = payoff_matrix[:, :, 0]
        shiftA = abs(A.min()) + 1 if A.min() <= 0 else 0
        B = payoff_matrix[:, :, 1]
        shiftB = abs(B.min()) + 1 if B.min() <= 0 else 0
        normalized = payoff_matrix.astype(float).copy()
        normalized[:, :, 0] += shiftA
        normalized[:, :, 1] += shiftB

        return normalized


    def pivot(self, equations, not_zero_labels, dropped_label):
        """
        Returns picked up label (to have prob = 0)
        """
        m, n = equations.shape
        free_term_idx = n - 1
        dropped_label_idx = dropped_label - 1

        increase_amounts = []
        for i in range(m):
            coeff = equations[i, dropped_label_idx]
            if coeff > 1e-12:
                increase_amounts.append((equations[i, free_term_idx] / coeff, i))
            else:
                increase_amounts.append((np.inf, i))

        min_increase_amount, picked_up_idx = min(increase_amounts, key=lambda x: x[0])

        if np.isinf(min_increase_amount):
            return None, None

        picked_up_label = not_zero_labels[picked_up_idx]

        equations[picked_up_idx, :] = equations[picked_up_idx, :] / equations[picked_up_idx, dropped_label_idx]

        for i in range(m):
            if i != picked_up_idx:
                equations[i, :] -= equations[i, dropped_label_idx] * equations[picked_up_idx, :]

        return picked_up_idx, picked_up_label


    def find_ne(self, payoff_matrix, initial_dropped_label):
        normalized_payoff_matrix = self.normalize_positive(payoff_matrix)
        payoff_matrix1 = normalized_payoff_matrix[:, :, 0]
        payoff_matrix2 = normalized_payoff_matrix[:, :, 1]

        m, n, _ = payoff_matrix.shape

        equations1, equations2 = self.setup_equations(payoff_matrix1, payoff_matrix2)

        # Start at artificial ne pair
        # => Only slack variables are non-zeros
        not_zero_labels1 = list(range(m + 1, m + n + 1)) # labeled by player's 2 strategies
        not_zero_labels2 = list(range(1, m + 1))         # labeled by player's 1 strategies

        # Start to drop label from the artificial NE
        dropped_label = initial_dropped_label

        # Traverse along paths to find dropped label again
        while True:
            # If dropped_label belong to player 1's strategies
            if dropped_label <= m:
                picked_up_idx, picked_up_label = self.pivot(equations1, not_zero_labels1, dropped_label)
                not_zero_labels1[picked_up_idx] = dropped_label
            # If dropped_label belong to player 2's strategies
            else:
                picked_up_idx, picked_up_label = self.pivot(equations2, not_zero_labels2, dropped_label)
                not_zero_labels2[picked_up_idx] = dropped_label

            if picked_up_label == initial_dropped_label:
                break

            dropped_label = picked_up_label

        p1, p2 = self.normalize_probs(m, n, equations1, equations2, not_zero_labels1, not_zero_labels2)
        return p1, p2


    def normalize_probs(self,m, n, equations1, equations2, not_zero_labels1, not_zero_labels2):
        p1_over_v1 = np.zeros(m)
        p2_over_v2 = np.zeros(n)

        for i, label in enumerate(not_zero_labels1):
            if 1 <= label <= m:
                p1_over_v1[label - 1] = equations1[i, -1]

        for i, label in enumerate(not_zero_labels2):
            if m + 1 <= label <= m + n:
                p2_over_v2[label - m - 1] = equations2[i, -1]

        if p1_over_v1.sum() == 0 or p2_over_v2.sum() == 0:
            return None, None
        
        p1 = p1_over_v1 / p1_over_v1.sum()
        p2 = p2_over_v2 / p2_over_v2.sum()

        return p1, p2


    def find_all_lemke_howson(self, payoff_matrix):
        m, n, _ = payoff_matrix.shape
        
        nes = []
        for dropped_label in range(1, m + n + 1):
            p, q = self.find_ne(payoff_matrix, dropped_label)
            if p is None or q is None:
                continue
            is_duplicate = False
            for ne in nes:
                if np.allclose(p, ne[0]) and np.allclose(q, ne[1]):
                    is_duplicate = True
                    break

            if not is_duplicate:
                nes.append((p, q))

        return nes


    def print_nes(self, nes):
        print(f"Strategies: {self.strategies}")
        print(f"There are {len(nes)} Nash equilibrium")
        for ne in nes:
            if np.sum(ne[0] == 1) == 1 and np.sum(ne[1] == 1) == 1:
                print(f"({self.strategies[np.argmax(ne[0])]}, {self.strategies[np.argmax(ne[1])]})")
            else:
                print(f"Mixed Strategy: ({np.round(ne[0])}, {np.round(ne[1])})")


def main():
    parser = argparse.ArgumentParser(description="Compute Nash equilibria.")
    parser.add_argument(
        "algorithm",
        choices=["support-enumeration", "lemke-howson"],
    )
    parser.add_argument(
        "filename",
        type=str,
        help="CSV game filename contains empirical payoff, such as negotiation_game.csv",
    )
    parser.add_argument(
        "--data-dir",
        default=Path(__file__).resolve().parents[1] / "data",
    )

    parser.add_argument(
        "--game_name",
        type=str,
        choices=["negotiation", "prisoners_dilemma", "stag_hunt"]
    )

    args = parser.parse_args()

    filename = Path(args.filename)
    game_name = args.game_name

    game_info = utils.load_game_info(game_name)

    strategies = utils.read_prompt_strategies(game_info.STRATEGY_PROMPTS)

    payoff_path = filename
    if not payoff_path.exists():
        payoff_path = Path(args.data_dir) / filename.stem / filename.name

    payoff_matrix = utils.read_empirical_payoff_matrix(
        payoff_path,
        strategies,
    )

    if args.algorithm == "support-enumeration":
        solver = SupportEnumeration(strategies)
        equilibria = solver.support_enumeration(payoff_matrix)
    else:
        solver = LemkeHowson(strategies)
        equilibria = solver.find_all_lemke_howson(payoff_matrix)

    solver.print_nes(equilibria)


if __name__ == "__main__":
    main()