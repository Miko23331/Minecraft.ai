"""
Integration with llama.cpp for AI thinking
Supports both real llama.cpp and mock LLM for testing
"""
import requests
import json
import random

class MockLLM:
    """Mock LLM для тестирования (используется если реальная llama.cpp недоступна)"""
    def __init__(self):
        self.actions = ["forward", "dig", "eat", "sleep", "wait", "left", "right", "jump"]
        self.memories = {}

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """Генерировать простой ответ на основе промпта"""
        prompt_lower = prompt.lower()

        # Интеллектуальные ответы на основе состояния
        if "night" in prompt_lower or "dark" in prompt_lower:
            return "It's getting dark. I should find shelter or build a roof. I feel afraid of the darkness."
        elif "health" in prompt_lower and "low" in prompt_lower:
            return "I'm injured! I need to find food to recover. Let me look for apples or hunt animals."
        elif "hungry" in prompt_lower or "hunger" in prompt_lower:
            return "My stomach is rumbling. I need to find food. Maybe I can hunt or farm."
        elif "dig" in prompt_lower or "wood" in prompt_lower:
            return "I see trees around. Let me break the wood - it will be useful for crafting tools and shelter."
        elif "position" in prompt_lower or "location" in prompt_lower:
            return "I'm standing in a meadow. The area around me seems peaceful. Let me explore more."
        else:
            return "I should move forward and explore. There might be useful resources nearby."

    def parse_action_from_text(self, text: str) -> str:
        """Извлечь действие из текста"""
        text_lower = text.lower()

        actions_map = {
            "forward": ["forward", "move forward", "walk", "explore", "go ahead"],
            "dig": ["break", "dig", "wood", "cutting", "mine"],
            "eat": ["eat", "food", "hungry", "hunt", "farm"],
            "sleep": ["sleep", "rest", "night", "shelter", "roof"],
            "left": ["left", "turn left"],
            "right": ["right", "turn right"],
            "jump": ["jump", "climb"],
            "wait": ["wait", "think", "consider"],
            "attack": ["attack", "fight", "defend"]
        }

        for action, keywords in actions_map.items():
            if any(kw in text_lower for kw in keywords):
                return action

        return random.choice(self.actions)

class LlamaCppBridge:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.connected = False
        self.mock_llm = MockLLM()

    def connect(self) -> bool:
        """Проверить доступность llama.cpp сервера"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=2)
            self.connected = response.status_code == 200
            if self.connected:
                print("[LLAMA.CPP] [OK] Connected to real llama.cpp server")
            else:
                print("[LLAMA.CPP] [WARN] Will use mock LLM")
            return self.connected
        except:
            print("[LLAMA.CPP] [WARN] Server not available, using mock LLM")
            return False

    def think(self, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
        """
        Использовать llama.cpp для генерации мысли ИИ
        или mock LLM если реально не доступна
        """
        if self.connected:
            return self._think_real(system_prompt, user_prompt, max_tokens)
        else:
            return self._think_mock(user_prompt)

    def _think_real(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        """Запрос к реальному llama.cpp"""
        payload = {
            "prompt": f"{system_prompt}\n\nUser:\n{user_prompt}\n\nAssistant:",
            "n_predict": max_tokens,
            "temperature": 0.8,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "stop": ["\n\nUser:"]
        }

        try:
            response = requests.post(
                f"{self.api_url}/completion",
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("content", "I need to think about this...")
        except Exception as e:
            print(f"[LLAMA.CPP] Error: {e}, falling back to mock LLM")
            self.connected = False
            return self._think_mock(user_prompt)

        return "I need to think about this..."

    def _think_mock(self, user_prompt: str) -> str:
        """Mock LLM для симуляции"""
        return self.mock_llm.generate(user_prompt)

    def parse_action(self, thought: str) -> str:
        """
        Извлечь действие из рассуждения ИИ
        Примеры действий: forward, dig, craft, eat, sleep, attack
        """
        if self.connected:
            # Спросить у реального LLM какое действие
            pass

        # Использовать mock парсер
        return self.mock_llm.parse_action_from_text(thought)
