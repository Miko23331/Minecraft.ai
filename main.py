"""
Minecraft.ai - Main Entry Point
An AI consciousness learning to survive in Minecraft
Полный цикл с реальной игровой логикой и обучением
"""
import sys
import os
import json
from pathlib import Path

# Add project directories to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.agent import MinecraftAIAgent
from core.llama_integration import LlamaCppBridge
from minecraft_api.minecraft_client import MinecraftAPI


class MinecraftAIGame:
    def __init__(self, config_path: str = "config/config.json"):
        self.config = self._load_config(config_path)
        self.agent = MinecraftAIAgent()
        self.llama = LlamaCppBridge(api_url="http://localhost:8000")
        self.minecraft = MinecraftAPI(
            server_address=self.config["minecraft"]["server_address"],
            port=self.config["minecraft"]["server_port"]
        )
        self.running = False
        self.system_prompt = ""

    def _load_config(self, config_path: str) -> dict:
        """Загрузить конфигурацию"""
        config_file = project_root / config_path
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}

    def initialize(self) -> bool:
        """Инициализировать все компоненты"""
        print("=" * 70)
        print("🤖 MINECRAFT.AI - AI Consciousness Awakening 🤖")
        print("=" * 70)

        print("\n[INIT] Loading system prompt...")
        system_prompt_file = project_root / "ai/system_prompt.txt"
        if system_prompt_file.exists():
            with open(system_prompt_file, 'r', encoding='utf-8') as f:
                self.system_prompt = f.read()
                print(f"✓ Loaded {len(self.system_prompt)} characters of system prompt")
        else:
            self.system_prompt = "You are an AI learning to survive in Minecraft."

        print("\n[INIT] Connecting to LLM...")
        if self.llama.connect():
            print("✓ Real llama.cpp server connected!")
        else:
            print("⚠️  Using mock LLM for thinking (fallback mode)")

        print("\n[INIT] Starting Minecraft simulator...")
        if self.minecraft.connect():
            print("✓ Minecraft simulator started")

        print("\n[INIT] Loading agent memory...")
        print(f"   - Learned facts: {len(self.agent.memory.get('learned_facts', []))}")
        print(f"   - Success patterns: {self.agent.memory.get('success_patterns', {})}")
        print(f"   - Danger patterns: {self.agent.memory.get('danger_patterns', {})}")

        self.running = True
        return True

    def run_game_loop(self, max_cycles: int = 100):
        """Запустить основной цикл игры - ИИ учится выживать"""
        print("\n" + "=" * 70)
        print("🎮 STARTING GAME LOOP - AI LEARNING SURVIVAL")
        print("=" * 70)

        for cycle in range(max_cycles):
            if not self.running:
                break

            print(f"\n{'─' * 70}")
            print(f"📍 CYCLE {cycle + 1}/{max_cycles}")
            print(f"{'─' * 70}")

            # 1️⃣ Получить состояние мира
            print("\n📡 [1] Observing world state...")
            game_state = self.minecraft.get_game_state()

            # Показать состояние
            pos = game_state['position']
            print(f"   Position: ({pos['x']:.1f}, {pos['y']:.1f}, {pos['z']:.1f})")
            print(f"   Health: {game_state['health']}/20 | Hunger: {game_state['hunger']}/20")
            print(f"   Time: {game_state['time_of_day']} {'🌙 NIGHT' if game_state['is_night'] else '☀️  DAY'}")
            print(f"   Blocks around: {game_state['environment']['blocks_around'][:5]}")
            if game_state['environment']['mobs_nearby']:
                print(f"   ⚠️  MOBS NEARBY: {[m['type'] for m in game_state['environment']['mobs_nearby']]}")

            # Проверить выживание
            if game_state['health'] <= 0:
                print("\n💀 AGENT DIED!")
                session_summary = {
                    "duration": self.agent.ticks_alive,
                    "final_health": game_state['health'],
                    "facts_learned": len(self.agent.memory['learned_facts']),
                    "experiences": len(self.agent.memory['experiences'])
                }
                self.agent.memory['sessions'].append(session_summary)
                self.agent.save_memory()
                break

            # 2️⃣ Агент наблюдает (обновляет состояние)
            self.agent.observe(game_state)

            # 2️⃣ Думать на основе системного промпта и текущего состояния
            print("\n🧠 [2] Agent thinking...")
            thought_prompt = self.agent.think(game_state)

            # Получить мысль от LLM (real или mock)
            thought = self.llama.think(
                self.system_prompt,
                thought_prompt,
                max_tokens=200
            )
            print(f"   💭 Thought: {thought[:150]}...")

            # 3️⃣ Парсить действие из мысли и действовать
            print("\n🎮 [3] Taking action...")
            action = self.llama.parse_action(thought)
            self.minecraft.send_action(action)
            print(f"   ► Action taken: {action}")

            # 4️⃣ Рефлексия - ИИ учится на опыте
            print("\n💭 [4] Reflecting and learning...")
            self.agent.reflect()

            # Статистика обучения
            if cycle % 20 == 0:
                print(f"\n📊 LEARNING PROGRESS:")
                print(f"   - Ticks alive: {self.agent.ticks_alive}")
                print(f"   - Facts learned: {len(self.agent.memory['learned_facts'])}")
                print(f"   - Success patterns: {self.agent.memory['success_patterns']}")
                print(f"   - Danger patterns: {self.agent.memory['danger_patterns']}")

        print("\n" + "=" * 70)
        print("🛑 GAME LOOP ENDED")
        print("=" * 70)

    def shutdown(self):
        """Завершить программу и сохранить состояние"""
        print("\n🔴 Shutting down...")
        print(f"   Agent survived: {self.agent.ticks_alive} ticks")
        print(f"   Learned facts: {len(self.agent.memory['learned_facts'])}")
        print(f"   Memories saved to: {self.agent.memory_file}")

        self.agent.save_memory()
        self.minecraft.disconnect()
        self.running = False
        print("✓ All systems shut down")


def main():
    game = MinecraftAIGame()

    try:
        if game.initialize():
            # Запустить достаточно долго чтобы ИИ мог обучиться
            game.run_game_loop(max_cycles=200)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        game.shutdown()


if __name__ == "__main__":
    main()
