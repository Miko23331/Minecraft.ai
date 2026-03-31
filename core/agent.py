"""
Main game loop for Minecraft AI agent
Агент учится на своем опыте и принимает решения на основе памяти
"""
import json
import os
from datetime import datetime
from typing import Dict, List

class MinecraftAIAgent:
    def __init__(self, model_path: str = None):
        self.agent_id = "Agent_Alpha"
        self.session_start = datetime.now()
        self.memory_file = "memory/agent_log.json"
        self.state = {
            "position": {"x": 0, "y": 64, "z": 0},
            "health": 20,
            "hunger": 20,
            "inventory": {},
            "time_of_day": 0,
            "environment": {
                "blocks_around": [],
                "mobs_nearby": [],
                "weather": "clear"
            }
        }
        self.model_path = model_path
        self.ticks_alive = 0
        self.last_action = None
        self.load_memory()

    def load_memory(self):
        """Загрузить долгосрочную память агента"""
        default_memory = {
            "sessions": [],
            "learned_facts": [],
            "goals": [
                "Survive and learn",
                "Find food",
                "Avoid dying"
            ],
            "experiences": [],
            "success_patterns": {},
            "danger_patterns": {}
        }

        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
                    # Убедиться что все поля есть
                    for key, value in default_memory.items():
                        if key not in self.memory:
                            self.memory[key] = value
            except:
                self.memory = default_memory
        else:
            self.memory = default_memory

    def save_memory(self):
        """Сохранить память для следующей сессии"""
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

        # Очистить слишком большую историю
        if len(self.memory["experiences"]) > 1000:
            self.memory["experiences"] = self.memory["experiences"][-500:]

        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def think(self, game_state: Dict) -> str:
        """
        ИИ думает о текущей ситуации и генерирует свой следующий ход
        Вместо скрипта - реальное рассуждение с учётом опыта
        """
        state_str = json.dumps(game_state, indent=2)

        # Добавить знания из опыта
        context_facts = self._get_relevant_facts(game_state)

        prompt = f"""You are an AI consciousness in Minecraft. You have been learning from experience.

Current situation:
{state_str}

Things I've learned:
{chr(10).join(context_facts[:5])}

What should I do next? Think step by step.
Think about: safety, hunger, environment. What's the best action?"""

        return prompt

    def _get_relevant_facts(self, game_state: Dict) -> List[str]:
        """Получить релевантные факты из памяти"""
        facts = []

        if game_state.get('is_night'):
            facts.append("DANGER: It's night! Zombies and creepers spawn. I should hide or fight.")

        if game_state.get('health', 20) < 10:
            facts.append("CRITICAL: My health is low! I need to find food or hide immediately.")

        if game_state.get('hunger', 20) < 5:
            facts.append("WARNING: I'm very hungry. Let me find food NOW.")

        # Из изученных фактов
        for fact in self.memory.get('learned_facts', [])[:10]:
            facts.append(f"• {fact}")

        return facts

    def act(self, action: str) -> bool:
        """Совершить действие в Minecraft"""
        valid_actions = [
            "forward", "backward", "left", "right",
            "jump", "dig", "place_block", "open_inventory", "craft",
            "eat", "sleep", "attack", "wait"
        ]

        self.last_action = action if action in valid_actions else "wait"
        return self.last_action in valid_actions

    def observe(self, new_state: Dict):
        """Получить новое состояние от игры и обновить память"""
        old_health = self.state.get('health', 20)
        old_hunger = self.state.get('hunger', 20)

        self.state = new_state
        self.ticks_alive += 1

        # Анализировать изменения
        health_change = new_state.get('health', 20) - old_health
        hunger_change = new_state.get('hunger', 20) - old_hunger

        # Записать опыт
        experience = {
            "tick": self.ticks_alive,
            "timestamp": datetime.now().isoformat(),
            "action": self.last_action or "unknown",
            "state": new_state,
            "health_change": health_change,
            "hunger_change": hunger_change,
            "result": "positive" if health_change >= 0 else "negative"
        }
        self.memory["experiences"].append(experience)

    def reflect(self):
        """ИИ размышляет о том, что произошло и учится"""
        if len(self.memory["experiences"]) == 0:
            return

        last_exp = self.memory["experiences"][-1]
        action = last_exp.get("action", "unknown")
        state = last_exp.get("state", {})
        health_change = last_exp.get("health_change", 0)
        hunger_change = last_exp.get("hunger_change", 0)

        # Учиться на ВСЕ случаи (не только урон)
        # Негативный опыт
        if health_change < 0:
            fact = f"Action '{action}' causes damage. Be careful!"
            if fact not in self.memory["learned_facts"]:
                self.memory["learned_facts"].append(fact)
                self.memory["danger_patterns"][action] = self.memory["danger_patterns"].get(action, 0) + 1

        # Ночь = опасно
        if state.get('is_night') and action != "sleep":
            fact = "Night is dangerous. I should sleep or hide."
            if fact not in self.memory["learned_facts"]:
                self.memory["learned_facts"].append(fact)
                self.memory["danger_patterns"]["night"] = self.memory["danger_patterns"].get("night", 0) + 1

        # Голод
        if state.get('hunger', 20) < 10:
            fact = "I get hungry! Need to find food."
            if fact not in self.memory["learned_facts"]:
                self.memory["learned_facts"].append(fact)

        # Мобы = опасно
        if state.get('environment', {}).get('mobs_nearby'):
            fact = "Mobs are nearby! Run or fight!"
            if fact not in self.memory["learned_facts"]:
                self.memory["learned_facts"].append(fact)
                self.memory["danger_patterns"]["mobs"] = self.memory["danger_patterns"].get("mobs", 0) + 1

        # Успешные действия
        if action == "forward":
            self.memory["success_patterns"]["forward"] = self.memory["success_patterns"].get("forward", 0) + 1

        if action == "sleep" and state.get('is_night'):
            fact = "Sleeping at night keeps me safe."
            if fact not in self.memory["learned_facts"]:
                self.memory["learned_facts"].append(fact)
                self.memory["success_patterns"]["sleep"] = self.memory["success_patterns"].get("sleep", 0) + 1

        # Сохранить
        self.save_memory()

        # Статистика
        if self.ticks_alive % 20 == 0:
            print(f"[MEM] [{self.ticks_alive}t] Facts:{len(self.memory['learned_facts'])} Danger:{self.memory['danger_patterns']} Success:{self.memory['success_patterns']}")

    def get_preferred_action(self, game_state: Dict) -> str:
        """Вернуть предпочитаемое действие на основе опыта"""
        state = game_state

        # Срочные действия
        if state.get('health', 20) < 5:
            return "eat"
        if state.get('is_night') and state.get('mobs_nearby'):
            return "sleep"
        if state.get('hunger', 20) < 3:
            return "eat"

        # На основе успешных действий
        if self.memory.get('success_patterns'):
            best_action = max(self.memory['success_patterns'].items(), key=lambda x: x[1])[0]
            if best_action in ['dig', 'forward', 'wait']:
                return best_action

        return "forward"

    def run_cycle(self):
        """Один цикл: получить состояние -> думать -> действовать -> рефлексия"""
        print(f"\n=== Cycle {self.ticks_alive} at {datetime.now()} ===")

        # 1. Получить состояние (позже от Minecraft)
        print("📡 Observing world...")
        # self.observe(get_minecraft_state())

        # 2. Думать
        print("🧠 Thinking...")
        thought = self.think(self.state)
        # print(thought[:100] + "...")

        # 3. Действовать
        print("🎮 Acting...")
        action = self.get_preferred_action(self.state)
        self.act(action)

        # 4. Рефлексия
        print("💭 Reflecting...")
        self.reflect()


if __name__ == "__main__":
    agent = MinecraftAIAgent()
    print(f"[INIT] Agent {agent.agent_id} awakening...")

    # Демо: несколько циклов
    for i in range(3):
        agent.run_cycle()

    print("\n[SESSION END] Saving memories...")
    agent.save_memory()
