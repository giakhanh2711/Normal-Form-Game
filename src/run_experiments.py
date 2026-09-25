# Script that runs the LLM matchups and saves raw results.

import json
import re
import getpass
import os
from openai import OpenAI, APIConnectionError, APIError, RateLimitError
from dotenv import load_dotenv
import time
import itertools
import sys
from pathlib import Path
import argparse

import utils
import config


class ExperimentRunner:
    def __init__(self, payoffs_matrix, strategy_prompts, game_name = "", game_strategies = [], game_actions = [],
                 api_url: str = config.TAMU_BASE_URL,
                 model_name: str = config.SONNET_MODEL,
                 n_reps = config.N_REPS):

        self.game_name = game_name
        self.payoffs_matrix = payoffs_matrix
        self.strategy_prompts = strategy_prompts
        self.game_strategies = game_strategies
        self.game_actions_pattern = rf"\b({'|'.join(game_actions)})\b"
        self.api_url = api_url
        self.model = model_name
        self.n_reps = n_reps

        self.client = self.make_client()


    def make_client(self):
        load_dotenv()
        key = os.environ.get("TAMU_API_KEY") or getpass.getpass("TAMU_API_KEY: ")
        raw = os.environ.get("CF_COOKIE") or getpass.getpass("CF_COOKIE: ")
        return OpenAI(api_key=key,
                    base_url=self.api_url,
                    default_headers={"Cookie": utils.normalize_cf_cookie(raw)})


    # 2.1 Parse each LLM's response to extract its chosen action
    def _visible_content(self, response):
        """Read TAMU raw text/SSE replies or an OpenAI-compatible completion.
        Return the response and model used
        """
        model = None
        if isinstance(response, str):
            if "Cloudflare Access" in response and "Sign in" in response:
                raise RuntimeError(
                    "TAMU gateway returned the Cloudflare sign-in page; refresh CF_Authorization."
                )
            if response.lstrip().startswith("data:"):
                pieces = []
                for line in response.splitlines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if not payload or payload == "[DONE]":
                        continue
                    try:
                        event = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    if not model:
                        model = event["model"]
                    for choice in event.get("choices", []):
                        piece = choice.get("delta", {}).get("content")
                        if isinstance(piece, str):
                            pieces.append(piece)
                if pieces:
                    return re.sub(r"<think>.*?</think>", "", "".join(pieces), flags=re.DOTALL).strip(), model
            return response
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "")
        try:
            return response.choices[0].message.content
        except (AttributeError, IndexError, KeyError, TypeError) as exc:
            raise TypeError(f"Unsupported TAMU completion response: {type(response).__name__}") from exc


    def _response_usage(self, response):
        if isinstance(response, dict):
            return response.get("usage")
        return getattr(response, "usage", None)


    def choose_action(self, strategy, player_label):
        messages = [
            {"role": "system", "content": self.strategy_prompts[strategy]},
            {"role": "user", "content": f" This is the payoffs matrix {self.payoffs_matrix}. You are {player_label}. Choose your action now."},
        ]
        for attempt in range(4):
            try:
                api_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=1.0,
                    max_tokens=16_384,
                )
                response, model = self._visible_content(api_response)
                visible = re.sub(
                    r"<think>.*?</think>", "", response,
                    flags=re.DOTALL,
                ).strip()
                actions = re.findall(self.game_actions_pattern, visible.upper())
                if not actions:
                    # Could not parse model's response
                    action = None
                else:
                    action = actions[-1]
                usage = self._response_usage(api_response)
                return action, visible, (
                    getattr(usage, "prompt_tokens", 0) or 0,
                    getattr(usage, "completion_tokens", 0) or 0,
                    ), model
            
            except (RateLimitError, APIConnectionError, APIError, ValueError) as exc:
                if attempt == 3:
                    raise
                delay = 2 ** attempt
                print(f"Transient {type(exc).__name__}; retrying in {delay}s...")
                time.sleep(delay)


    def run_experiment(self):
        records = []
        prompt_tokens = completion_tokens = 0
        parse_failure_count = 0

        for p1_strategy, p2_strategy in itertools.product(self.strategy_prompts, repeat=2):
            for rep in range(1, self.n_reps + 1):
                a1, text1, usage1, model_version = self.choose_action(p1_strategy, "Player 1")
                a2, text2, usage2, model_version = self.choose_action(p2_strategy, "Player 2")
                if not a1 or not a2:
                    parse_failure_count += 1
                    continue

                u1, u2 = self.payoffs_matrix[(a1, a2)]
                prompt_tokens += usage1[0] + usage2[0]
                completion_tokens += usage1[1] + usage2[1]
                record = {
                    "p1_strategy": p1_strategy,
                    "p2_strategy": p2_strategy,
                    "rep": rep,
                    "p1_action": a1,
                    "p2_action": a2,
                    "p1_raw_response": text1,
                    "p2_raw_response": text2,
                    "u1": u1,
                    "u2": u2,
                    "model_version": model_version
                }
                records.append(record)
                # if raw_example is None:
                #     raw_example = {**record, "p1_visible_response": text1, "p2_visible_response": text2}
            print(f"[{p1_strategy}, {p2_strategy}]: {self.n_reps}/{self.n_reps} complete")

        output = self.format_saved_output(records)

        self.save_to_json(output)

        return records


    def format_saved_output(self, records):
        payoffs = {f"{k[0], k[1]}": list(v) for k, v in self.payoffs_matrix.items()}
        output = {
            "game": {
                "name": self.game_name,
                "actions": self.game_strategies,
                "payoffs": payoffs
            },
        
            "model": {
                "requested_model": self.model,
                "temperature": 1.0,
                "max_tokens": 16_384,
                "returned_model_version": self.model
            },
        
            "strategies": self.strategy_prompts,
        
            "trials": records
        }

        return output


    def save_to_json(self, output: dict):
        file_name = Path(f"data_test/{self.game_name}/{self.game_name}.json")
        file_name.mkdir(parents=True, exist_ok=True)

        with open(file_name, 'w') as f:
            json.dump(output, f, indent = 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--game_name",
        type=str,
        choices=["negotiation", "prisoners_dilemma", "stag_hunt"]
    )

    args = parser.parse_args()

    game_name = Path(args.game_name).stem
    game_module = utils.load_game_info(game_name)

    print("=" * 20, f"Running {game_module.GAME_NAME}", "=" * 20)

    experiment = ExperimentRunner(
        game_module.PAYOFFS,
        game_module.STRATEGY_PROMPTS,
        game_name=game_name,
        game_strategies=game_module.GAME_STRATEGIES,
        game_actions=game_module.ACTIONS,
        api_url=config.TAMU_BASE_URL,
        model_name=config.SONNET_MODEL,
        n_reps=config.N_REPS,
    )

    experiment.run_experiment()


if __name__ == "__main__":
    main()
