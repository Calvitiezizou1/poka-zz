import random

class LeducGame:
    def __init__(self):
        # 0,1,2 = J,Q,K (x2)
        self.deck = [0, 0, 1, 1, 2, 2]
        self.rank_map = {0: 'J', 1: 'Q', 2: 'K'}

    def reset(self):
        random.shuffle(self.deck)
        self.cards = [self.deck[0], self.deck[1]]
        self.board = self.deck[2]
        self.pot = 2.0 # Ante 1 each
        self.history = "" 
        
        # Structure interne pour tracker les mises : [Mise P1, Mise P2]
        self.bets = [1.0, 1.0] 
        self.round = 1
        self.active_player = 0
        self.finished = False
        return self.get_state()

    def get_state(self):
        board_visible = self.board if self.round == 2 else -1
        return {
            'info_set': f"{self.cards[self.active_player]}|{board_visible}|{self.history}",
            'history': self.history,
            'round': self.round,
            'active_player': self.active_player
        }

    def get_valid_actions(self):
        # Actions: k=Check, r=Raise(Bet), c=Call, f=Fold
        
        # Analyse du round actuel pour savoir ce qui est permis
        # On regarde juste les actions depuis le dernier '/'
        current_round_hist = self.history.split('/')[-1]
        
        if self.finished: return []
        
        # Si personne n'a misé (ou checké) -> Check ou Bet
        if not current_round_hist or current_round_hist == 'k':
            return ['k', 'r']
            
        # Si face à un Bet ('r') -> Fold, Call, (Raise? Limitons à 1 raise par round pour simplifier l'IA)
        if current_round_hist.endswith('r'):
             # Simplification: Pas de sur-relance (Re-raise) pour l'instant
            return ['f', 'c'] 
            
        # Si face à un Check-Bet ('kr') -> Fold, Call
        if 'r' in current_round_hist:
            return ['f', 'c']

        return ['k', 'r']

    def step(self, action):
        if self.finished: return 0

        self.history += action
        
        # Gestion du Pot
        if action == 'r':
            self.bets[self.active_player] += 1
            self.pot += 1
        elif action == 'c':
            diff = self.bets[1-self.active_player] - self.bets[self.active_player]
            self.bets[self.active_player] += diff
            self.pot += diff
            
        # Gestion Fin de Manche (Fold)
        if action == 'f':
            self.finished = True
            # Le joueur qui fold perd, l'autre gagne le pot
            # Payoff pour P1 : Si P1 fold (-pot/2), Si P2 fold (+pot/2)
            amount = self.pot / 2
            return -amount if self.active_player == 0 else amount

        # Gestion Fin de Round ou Jeu
        # Round fini si : kk, rc, krc, crc (toutes les séquences où les mises sont égales)
        current_round_hist = self.history.split('/')[-1]
        
        round_over = False
        if len(current_round_hist) >= 2:
            if current_round_hist == 'kk': round_over = True # Check Check
            if current_round_hist.endswith('c'): round_over = True # Bet Call
            
        if round_over:
            if self.round == 1:
                # Passage au Round 2
                self.round = 2
                self.history += "/"
                self.active_player = 0 # P1 commence toujours le round
            else:
                # Fin du jeu (Showdown)
                self.finished = True
                return self.get_showdown_payoff()
        else:
            # On change de joueur
            self.active_player = 1 - self.active_player
            
        return 0 # Pas de payoff immédiat tant que pas fini

    def get_showdown_payoff(self):
        # Force : Paire (Score 3+) > Haute Carte (Score 0-2)
        def get_score(card, board):
            if card == board: return 3 + card
            return card
            
        s1 = get_score(self.cards[0], self.board)
        s2 = get_score(self.cards[1], self.board)
        
        winner = 0
        if s1 > s2: winner = 1
        elif s2 > s1: winner = -1
        
        return (self.pot / 2) * winner
        
    def render(self):
        b_str = self.rank_map[self.board] if self.round == 2 else "?"
        p1_str = self.rank_map[self.cards[0]]
        p2_str = self.rank_map[self.cards[1]]
        print(f"Board: [{b_str}] | Pot: {self.pot} | Hist: {self.history}")
        print(f"P1: {p1_str} (Bet {self.bets[0]}) | P2: {p2_str} (Bet {self.bets[1]})")

# Test rapide
if __name__ == "__main__":
    game = LeducGame()
    game.reset()
    game.render()
    # Simu Check - Bet - Call (Round 1) -> Check - Check (Round 2)
    moves = ['k', 'r', 'c', 'k', 'k']
    for m in moves:
        payoff = game.step(m)
        game.render()
        if game.finished:
            print(f"Game Over. Payoff P1: {payoff}")
            break