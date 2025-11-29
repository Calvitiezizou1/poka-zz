import numpy as np
import random
import json
class Node:
    def __init__(self, num_actions=2):
        self.info_set = ""

        # Regret Sum : On accumule les regrets ici pour décider de la stratégie courante
        self.regret_sum = np.zeros(num_actions)

        # Strategy Sum : On accumule la stratégie courante pour calculer la MOYENNE à la fin
        self.strategy_sum = np.zeros(num_actions)

        # La stratégie actuelle (probabilités)
        self.strategy = np.zeros(num_actions)

    def get_strategy(self, realization_weight):
        """
        Calcule la stratégie courante en utilisant le Regret Matching.
        Si j'ai beaucoup de regret positif sur une action, je vais augmenter sa probabilité.
        """

        # On ne garde que les regrets positifs (si regret < 0, on s'en fiche)
        strategy = np.maximum(0, self.regret_sum)
        normalizing_sum = np.sum(strategy)

        # Si tous les regrets sont négatifs ou nuls, on joue uniformément (50/50)
        if normalizing_sum > 0:
            strategy /= normalizing_sum
        else:
            strategy = np.ones_like(strategy) / len(strategy)

        self.strategy = strategy
        # On ajoute à la somme pour la moyenne finale (pondéré par la probabilité d'arriver ici)
        self.strategy_sum += strategy * realization_weight
        return strategy

    def get_average_strategy(self):
        """
        C'est la stratégie finale (Nash Equilibrium) qu'on utilisera pour jouer.
        Elle lisse les variations de l'apprentissage.
        """

        normalizing_sum = np.sum(self.strategy_sum)
        if normalizing_sum > 0:
            return self.strategy_sum / normalizing_sum
        return np.array([0.5, 0.5]) # Par défaut
    

    
class KuhnCFRTrainer:
    def __init__(self):
        self.node_map = {}  # Stocke tous les Nodes (Clé: "Carte + Historique")

    def get_node(self, info_set):
        """Récupère ou crée le noeud si c'est la première fois qu'on le voit"""
        if info_set not in self.node_map:
            self.node_map[info_set] = Node()
            self.node_map[info_set].info_set = info_set
        return self.node_map[info_set]
    
    def save_strategy(self, filename="strategy.json"):
        """Sauvegarde la stratégie finale dans un fichier JSON"""
        final_strategy = {}
        for info_set, node in self.node_map.items():
            # On convertit le numpy array en liste pour que JSON comprenne
            final_strategy[info_set] = node.get_average_strategy().tolist()
            
        with open(filename, 'w') as f:
            json.dump(final_strategy, f, indent=4)
        print(f"Stratégie sauvegardée dans '{filename}'")

    def cfr(self, cards, history, p0, p1):
        """
        L'algorithme récursif principal.
        cards: liste [card_p1, card_p2] (ex: [2, 0] pour Roi vs Valet)
        history: chaine 'pp', 'b', etc.
        p0: probabilité que le joueur 0 arrive ici (selon sa stratégie)
        p1: probabilité que le joueur 1 arrive ici
        """

        plays = len(history)
        player = plays % 2
        opponent = 1 - player

        # --- 1. Vérifier si c'est un état terminal (Fin de manche) ---
        if plays > 1:
            is_terminal = False
            payoff = 0
            
            # Cas Showdown (pp, bb, pbb)
            if history == "pp" or history == "bb" or history == "pbb":
                is_terminal = True
                pot = 2 if history == "pp" else 4
                winner = 1 if cards[player] > cards[opponent] else -1
                payoff = (pot / 2) * winner # Gain pour le joueur ACTUEL
            
            # Cas Fold (pbp, bp)
            elif history == "pbp" or history == "bp":
                is_terminal = True
                payoff = 1 # Le joueur actuel gagne car l'autre s'est couché avant
                            
            if is_terminal:
                return payoff

        # --- 2. Récupérer l'InfoSet et la Stratégie ---
        # L'infoSet est ce que voit le joueur : Sa Carte + L'Historique
        # Ex: "K" (Roi au début), "Jb" (Valet face à une mise)
        card_str = ["J", "Q", "K"][cards[player]]
        info_set = card_str + history
        
        node = self.get_node(info_set)
        
        # Pour mettre à jour la stratégie moyenne, on utilise la proba de l'adversaire
        # (C'est un détail mathématique important du CFR)
        realization_weight = p0 if player == 0 else p1
        strategy = node.get_strategy(realization_weight)
        
        # --- 3. Appel Récursif pour chaque action ---
        util = np.zeros(2) # Utilité de chaque action (0: Pass, 1: Bet)
        node_util = 0 # Ev
        
        actions = ['p', 'b']
        
        for a in range(2):
            next_history = history + actions[a]
            
            if player == 0:
                # Si P0 joue, on met à jour sa proba p0 * strategy[a]
                util[a] = -self.cfr(cards, next_history, p0 * strategy[a], p1)
            else:
                # Si P1 joue, on met à jour sa proba p1 * strategy[a]
                util[a] = -self.cfr(cards, next_history, p0, p1 * strategy[a])
                
            # Note le "-" devant self.cfr : C'est un jeu à somme nulle.
            # Ce que gagne le prochain joueur est ce que je perds.
            
            node_util += strategy[a] * util[a] 

        # --- 4. Calcul et Stockage des Regrets ---
        # Regret = (Ce que j'aurais gagné en jouant cette action) - (Ce que j'ai gagné en moyenne)
        
        for a in range(2):
            regret = util[a] - node_util
            # On pondère le regret par la probabilité que l'ADVERSAIRE nous laisse arriver ici
            # Si l'adversaire fold tout le temps avant, ce regret ne compte pas beaucoup
            opponent_proba = p1 if player == 0 else p0
            node.regret_sum[a] += opponent_proba * regret 
            
        return node_util

    def train(self, iterations):
        """Entraîne l'IA en jouant 'iterations' parties"""
        print(f"Training for {iterations} iterations...")
        cards = [0, 1, 2] # J, Q, K
        util = 0
        
        for i in range(iterations):
            # Mélange les cartes
            random.shuffle(cards)
            # Lance une partie récursive depuis la racine (history vide)
            # p0=1, p1=1 (probabilité initiale certaine)
            util += self.cfr(cards, "", 1, 1)
            
            if i % 1000 == 0 and i > 0:
                print(f"\rIteration {i}/{iterations}", end="")
                
        print(f"\nTraining complete. Average Game Value: {util / iterations:.4f}")

    def print_results(self):
        print("\nFinal Strategy (Nash Equilibrium):")
        # On trie pour afficher joliment
        for info_set in sorted(self.node_map.keys()):
            avg_strat = self.node_map[info_set].get_average_strategy()
            # 0 = Pass, 1 = Bet
            print(f"{info_set:3}: Pass {avg_strat[0]:.2f} | Bet {avg_strat[1]:.2f}")

# --- Execution ---
if __name__ == "__main__":
    trainer = KuhnCFRTrainer()
    # 50 000 itérations suffisent largement pour le Kuhn Poker
    trainer.train(50000)
    trainer.print_results()
    trainer.save_strategy() 