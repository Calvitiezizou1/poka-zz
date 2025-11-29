import json
import random
import numpy as np
from kuhn import KuhnPoker

def load_strategy(filename="strategy.json"):
    with open(filename, 'r') as f:
        return json.load(f)

def get_ai_action(strategy, card, history):
    # 1. Construire l'InfoSet (ex: "K" ou "Jpb")
    card_str = {0: 'J', 1: 'Q', 2: 'K'}[card]
    info_set = card_str + history
    
    # 2. Récupérer les probas du fichier JSON
    if info_set in strategy:
        probs = strategy[info_set]
    else:
        # Fallback si situation inconnue (ne devrait pas arriver)
        probs = [0.5, 0.5]
        
    # 3. Choisir une action selon les probas
    # 0 = Pass ('p'), 1 = Bet ('b')
    action_idx = np.random.choice([0, 1], p=probs)
    return 'p' if action_idx == 0 else 'b'

# --- Le Jeu ---
if __name__ == "__main__":
    game = KuhnPoker()
    strategy = load_strategy()
    print("--- CHARGEMENT DE L'IA TERMINÉ ---")
    print("L'IA joue selon l'Equilibre de Nash.")

    while True:
        state = game.reset()
        done = False
        print("\n" + "="*40)
        print("--- NOUVELLE MAIN ---")
        
        while not done:
            current_player = state['turn']
            history = state['history']
            
            # TOUR DU JOUEUR (Toi)
            if current_player == 0:
                print(f"\nTa carte : [{game.card_str[state['p1_card']]}]")
                print(f"Historique : {history}")
                print(f"Pot : {2 + history.count('b')}")
                
                valid = False
                while not valid:
                    action = input("Ton action (p/b) : ").strip().lower()
                    if action in ['p', 'b']: valid = True
            
            # TOUR DE L'IA (Adversaire)
            else:
                # L'IA regarde SA carte (p2_card) et l'historique
                print("L'AI reflechit...")
                ai_action = get_ai_action(strategy, state['p2_card'], history)
                print(f"Et joue : {ai_action.upper()}")
                action = ai_action
            
            state, reward, done = game.step(action)

        # Fin de manche
        print("\n--- RÉSULTAT ---")
        print(f"Historique Final : {state['history']}")
        print(f"Ta carte : {game.card_str[state['p1_card']]}")
        print(f"Carte IA : {game.card_str[state['p2_card']]}")
        
        if reward > 0:
            print(f"VICTOIRE ! Tu gagnes {reward} jeton(s).")
        elif reward < 0:
            print(f"DÉFAITE. Tu perds {abs(reward)} jeton(s).")
        else:
            print("ÉGALITÉ (Tie).")
            
        if input("\nRejouer ? (Entrée pour oui, 'n' pour quitter) : ") == 'n':
            break