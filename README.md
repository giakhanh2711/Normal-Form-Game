# Normal-Form-Game

You can create a .env file to include API key and CF_Authorization in this format
TAMU_API_KEY=
CF_COOKIE=

To run run_experiment.py
python .\src\run_experiments.py --game_name <game_name>
game_name = {prisoners_dilemma, "stag_hunt", "negotiation"}

To run compute equilibria
python Normal-form-game\src\compute_equilibria.py <algorithm name>  <filename of empirical payoff estimate>.csv --game_name <game_name>

For my current data folder and games' information folder, choices are:

algorithm_name = {"lemke-howson", "support-enumeration"}
filename of empirical payoff estimate = {"negotiation_game.csv", "prisoners_dilemma.csv", "coordination_game.csv"}
game_name = {"negotiation", "prisoners_dilemma", "stag_hunt"}

There are command to run for 3 games' estimated payoff matrix with recorded data
1. python .\src\compute_equilibria.py support-enumeration prisoners_dilemma.csv --game_name prisoners_dilemma
   
   python .\src\compute_equilibria.py lemke-howson prisoners_dilemma.csv --game_name prisoners_dilemma

2. python .\src\compute_equilibria.py support-enumeration coordination_game.csv --game_name stag_hunt
   
   python .\src\compute_equilibria.py lemke-howson coordination_game.csv --game_name stag_hunt

3. python .\src\compute_equilibria.py support-enumeration negotiation_game.csv --game_name negotiation

    python .\src\compute_equilibria.py lemke-howson negotiation_game.csv --game_name negotiation 