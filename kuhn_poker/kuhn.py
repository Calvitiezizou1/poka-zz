import random

class KuhnPoker:
    def __init__(self):
        # 0=Jack, 1=Queen, 2=King
        self.deck = [0, 1, 2]
        self.card_str = {0: 'J', 1: 'Q', 2: 'K'}
        self.reset()

    def reset(self):
        """Resets the game state for a new hand."""
        random.shuffle(self.deck)
        self.p1_card = self.deck[0]
        self.p2_card = self.deck[1]
        self.history = "" # Tracks actions: 'p' (pass/check), 'b' (bet)
        self.turn = 0     # 0 for Player 1, 1 for Player 2
        return self.get_state()

    def get_state(self):
        """Returns the minimal info needed for the AI or UI."""
        return {
            'p1_card': self.p1_card,
            'p2_card': self.p2_card,
            'history': self.history,
            'turn': self.turn
        }

    def is_terminal(self):
        """Checks if the hand is over."""
        h = self.history
        # Terminal states: 
        # pp (showdown), pbp (fold), pbb (showdown), bp (fold), bb (showdown)
        if h == 'pp' or h == 'pbb' or h == 'bb':
            return True, 'showdown'
        if h == 'pbp' or h == 'bp':
            return True, 'fold'
        return False, None

    def step(self, action):
        """
        Applies an action ('p' or 'b').
        Returns: (state, reward_for_active_player, done)
        """
        if action not in ['p', 'b']:
            raise ValueError("Action must be 'p' (pass/check) or 'b' (bet).")
        
        self.history += action
        self.turn = 1 - self.turn # Switch turn
        
        done, result = self.is_terminal()
        reward = 0
        
        if done:
            reward = self.calc_payoff(result)
            
        return self.get_state(), reward, done

    def calc_payoff(self, result):
        """
        Calculates payoff relative to PLAYER 1.
        (If P1 wins +1, return +1. If P1 loses 1, return -1).
        """
        h = self.history
        p1 = self.p1_card
        p2 = self.p2_card
        
        # Pot calculation
        # Ante is 1 each (Total 2)
        # Bet adds 1.
        
        if result == 'fold':
            # Who folded? The last person to act lost.
            # If history is 'bp', P1 bet, P2 passed (folded). P1 wins 1.
            if h == 'bp': return 1
            # If history is 'pbp', P1 checked, P2 bet, P1 folded. P1 loses 1.
            if h == 'pbp': return -1
            
        if result == 'showdown':
            pot = 2 # Antes
            if 'b' in h: pot = 4 # If there were bets/calls
            
            winner = 1 if p1 > p2 else -1
            return (pot / 2) * winner
            
        return 0

    # --- UI Section ---
    def render(self):
        print("\n" + "="*30)
        print(f"Player 1 Card: [{self.card_str[self.p1_card]}]")
        # In a real game, you wouldn't see P2's card, but useful for debug
        print(f"Player 2 Card: [?]") 
        print(f"History: {self.history}")
        print(f"Pot: {2 + self.history.count('b')}")
        print("="*30)

# --- The Game Loop ---
if __name__ == "__main__":
    game = KuhnPoker()
    
    while True:
        state = game.reset()
        done = False
        print("\n--- NEW HAND ---")
        print(f"Your Card: {game.card_str[state['p1_card']]}")
        
        while not done:
            current_player = state['turn']
            
            # Simple UI logic
            if current_player == 0:
                print(f"\nYour turn (History: {state['history']})")
                action = input("Enter action (p = check/fold, b = bet/call): ").strip().lower()
            else:
                # Stupid AI for now (Random)
                print(f"\nOpponent turn (History: {state['history']})")
                action = random.choice(['p', 'b'])
                print(f"Opponent chose: {action}")
            
            if action not in ['p', 'b']: continue
            
            state, reward, done = game.step(action)
            
        # End of hand
        print(f"\nHand Over! History: {state['history']}")
        print(f"P1 Card: {game.card_str[state['p1_card']]}")
        print(f"P2 Card: {game.card_str[state['p2_card']]}")
        print(f"Result for P1: {reward}")
        
        if input("Play again? (y/n): ") != 'y': break