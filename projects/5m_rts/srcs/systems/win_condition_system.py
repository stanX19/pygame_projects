import esper
from srcs.config import *
from srcs.components import *

class WinConditionSystem(esper.Processor):
    def __init__(self, scene_manager):
        self.sm = scene_manager
        self.check_timer = 0.0
        self.check_interval = 2.0  # Check every 2 seconds

    def process(self):
        # Don't check if game is already over
        if self.sm.game_over:
            return

        dt = self.sm.dt
        self.check_timer += dt

        # Only check periodically to save performance
        if self.check_timer >= self.check_interval:
            self.check_timer = 0.0
            
            # Count entities per faction (excluding neutral and resource points)
            faction_counts = {}
            
            for ent, ident in self.world.get_component(Identity):
                # Only count units and castles for win condition
                # Resources don't count, and neutral faction doesn't participate
                if ident.faction != FACTION_NEUTRAL and ident.type in ['unit', 'castle']:
                    if ident.faction not in faction_counts:
                        faction_counts[ident.faction] = 0
                    faction_counts[ident.faction] += 1
            
            # Check if only one faction remains
            active_factions = [f for f, count in faction_counts.items() if count > 0]
            
            if len(active_factions) == 1:
                # We have a winner!
                winner = active_factions[0]
                self.sm.game_over = True
                self.sm.winner = winner
                winner_name = "PLAYER" if winner == self.sm.player_faction_id else f"AI FACTION {winner}"
                print(f"\n{'='*50}")
                print(f"GAME OVER! {winner_name} WINS!")
                print(f"Victory Faction ID: {winner}")
                print(f"{'='*50}\n")
            elif len(active_factions) == 0:
                # Edge case: everyone died (draw)
                self.sm.game_over = True
                self.sm.winner = None
                print(f"\n{'='*50}")
                print(f"GAME OVER! IT'S A DRAW!")
                print(f"{'='*50}\n")
