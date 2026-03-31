"""
AI Learning Visualizer - Real-time monitoring dashboard
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.agent import MinecraftAIAgent
from core.llama_integration import LlamaCppBridge
from minecraft_api.minecraft_client import MinecraftAPI
import time

class LearningVisualizer:
    def __init__(self):
        self.agent = MinecraftAIAgent()
        self.llama = LlamaCppBridge()
        self.minecraft = MinecraftAPI()
        self.stats = {
            "deaths": 0,
            "nights": 0,
            "day_distance": 0,
            "night_distance": 0,
            "max_health_lost": 0
        }

    def draw_bar(self, value, max_val, width=30, char="="):
        """Draw ASCII progress bar"""
        filled = int((value / max_val) * width)
        return "[" + char * filled + " " * (width - filled) + "]"

    def run_training(self, max_cycles=2500):
        print("\033[2J\033[H")  # Clear screen
        print("=" * 100)
        print("MINECRAFT.AI - LIVE LEARNING DASHBOARD")
        print("=" * 100)

        self.minecraft.connect()
        self.llama.connect()

        last_night = False
        start_time = time.time()

        for cycle in range(max_cycles):
            game_state = self.minecraft.get_game_state()
            is_night = game_state['is_night']
            health = game_state['health']
            hunger = game_state['hunger']
            time_of_day = game_state['time_of_day']
            mobs = len(game_state['environment']['mobs_nearby'])

            # Track night
            if is_night and not last_night:
                self.stats["nights"] += 1
            last_night = is_night

            # Track health loss
            if 20 - health > self.stats["max_health_lost"]:
                self.stats["max_health_lost"] = 20 - health

            # Death check
            if health <= 0:
                self.stats["deaths"] += 1
                break

            # Main cycle
            self.agent.observe(game_state)
            thought = self.llama.think("Survive.", self.agent.think(game_state), max_tokens=25)
            action = self.llama.parse_action(thought)
            self.minecraft.send_action(action)
            self.agent.reflect()

            # Every 25 cycles update screen
            if cycle % 25 == 0:
                elapsed = time.time() - start_time

                # Clear and redraw
                print("\033[2J\033[H")
                print("=" * 100)
                print("MINECRAFT.AI - LIVE LEARNING DASHBOARD")
                print("=" * 100)

                # Current status
                print(f"\n[REAL-TIME STATUS]")
                print(f"  Cycle: {cycle:4d}/{max_cycles} | Elapsed: {elapsed:6.1f}s | Health: {health:2d}/20 | Hunger: {hunger:2d}/20 | Mobs: {mobs}")
                print(f"  Time of day: {time_of_day:5d} | Status: {'NIGHT [DANGER]' if is_night else 'DAY [SAFE]'}")

                # Health bar
                health_bar = self.draw_bar(health, 20, 40, "H")
                print(f"\n  Health:  {health_bar} {health}/20")

                # Hunger bar
                hunger_bar = self.draw_bar(hunger, 20, 40, "F")
                print(f"  Hunger:  {hunger_bar} {hunger}/20")

                # Learning progress
                facts = len(self.agent.memory['learned_facts'])
                fact_bar = self.draw_bar(facts, 20, 40, "*")
                print(f"\n[LEARNING]")
                print(f"  Facts:   {fact_bar} {facts} learned")
                print(f"  Danger:  {self.agent.memory['danger_patterns']}")
                print(f"  Success: {self.agent.memory['success_patterns']}")

                # Statistics
                print(f"\n[STATISTICS]")
                print(f"  Nights survived: {self.stats['nights']}")
                print(f"  Deaths: {self.stats['deaths']}")
                print(f"  Max damage taken: {self.stats['max_health_lost']}")
                print(f"  Total experiences: {len(self.agent.memory['experiences'])}")

                # Knowledge
                if self.agent.memory['learned_facts']:
                    print(f"\n[AI KNOWLEDGE BASE]")
                    for i, fact in enumerate(self.agent.memory['learned_facts'], 1):
                        print(f"  {i}. {fact}")

                print("\n" + "-" * 100)

        self.agent.save_memory()
        self._final_report()

    def _final_report(self):
        print("\n" + "=" * 100)
        print("TRAINING COMPLETE - FINAL REPORT")
        print("=" * 100)

        agent = self.agent
        print(f"\nAgent: {agent.agent_id}")
        print(f"Total ticks alive: {agent.ticks_alive}")
        print(f"Deaths: {self.stats['deaths']}")
        print(f"Nights survived: {self.stats['nights']}")
        print(f"Max health lost: {self.stats['max_health_lost']}")

        print(f"\n[MEMORY STATISTICS]")
        print(f"  Experiences recorded: {len(agent.memory['experiences'])}")
        print(f"  Facts learned: {len(agent.memory['learned_facts'])}")
        print(f"  Danger patterns: {agent.memory['danger_patterns']}")
        print(f"  Success patterns: {agent.memory['success_patterns']}")

        if agent.memory['learned_facts']:
            print(f"\n[COMPLETE KNOWLEDGE]")
            for i, fact in enumerate(agent.memory['learned_facts'], 1):
                print(f"  {i}. {fact}")

        print(f"\nMemory saved to: {agent.memory_file}")
        print("=" * 100)

if __name__ == "__main__":
    viz = LearningVisualizer()
    viz.run_training(max_cycles=2500)
