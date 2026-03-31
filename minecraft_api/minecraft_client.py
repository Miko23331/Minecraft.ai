"""
Minecraft Integration Layer - Simulator
Минимальная симуляция Minecraft для обучения ИИ
"""
import random
from typing import Dict, List

class MinecraftSimulator:
    """Симпле симуляция Minecraft мира"""
    def __init__(self):
        self.world_blocks = {}
        self.mobs = []
        self.time_of_day = 0  # 0-24000
        self._generate_world()

    def _generate_world(self):
        """Создать простой мир вокруг спауна"""
        # Создаём квадрат 20x20 блоков вокруг спауна
        for x in range(-10, 10):
            for z in range(-10, 10):
                # Неровный ландшафт
                if abs(x) < 3 and abs(z) < 3:
                    self.world_blocks[(x, 63, z)] = "grass"
                    self.world_blocks[(x, 62, z)] = "dirt"
                else:
                    y = 63 if random.random() > 0.3 else 62
                    block_type = random.choice(["grass", "dirt", "stone"])
                    self.world_blocks[(x, y, z)] = block_type

                    # Деревья
                    if random.random() < 0.05:
                        self.world_blocks[(x, 64, z)] = "oak_log"
                        self.world_blocks[(x, 65, z)] = "oak_leaves"

    def get_block(self, x, y, z):
        """Получить блок из мира"""
        return self.world_blocks.get((x, y, z), "air")

    def place_block(self, x, y, z, block_type):
        """Поместить блок"""
        self.world_blocks[(x, y, z)] = block_type

    def break_block(self, x, y, z):
        """Сломать блок"""
        if (x, y, z) in self.world_blocks:
            del self.world_blocks[(x, y, z)]

class MinecraftAPI:
    def __init__(self, server_address: str = "localhost", port: int = 25565):
        self.server_address = server_address
        self.port = port
        self.connected = False
        self.simulator = MinecraftSimulator()

        # Состояние агента
        self.position = {"x": 0.0, "y": 64.0, "z": 0.0}
        self.rotation = {"pitch": 0.0, "yaw": 0.0}
        self.health = 20
        self.hunger = 20
        self.inventory = {}
        self.ticks = 0

    def connect(self) -> bool:
        """Подключиться к Minecraft (симулятор)"""
        print(f"[MINECRAFT] Starting simulator...")
        self.connected = True
        return True

    def get_game_state(self) -> dict:
        """Получить текущее состояние игры"""
        # Обновить время - ускорено 10x для быстрого дня/ночи
        self.ticks += 1
        # Каждые 15 тиков = полный день/ночь (240x ускорение)
        cycle_pos = (self.ticks // 1) % 240
        self.simulator.time_of_day = cycle_pos * 100

        # Кончается день, начинается ночь
        is_night = self.simulator.time_of_day > 12000

        # Ночь - ВЫСОКИЙ урон от мобов
        if is_night:
            if random.random() < 0.15:  # 15% урона ночью
                damage = random.randint(2, 5)
                self.health -= damage

        # Голод постепенно
        if self.ticks % 40 == 0:
            self.hunger = max(0, self.hunger - 1)

        # Мобы появляются ночью
        if is_night and random.random() < 0.15 and len(self.simulator.mobs) < 3:
            self.simulator.mobs.append({
                "type": random.choice(["zombie", "skeleton", "creeper"]),
                "distance": random.randint(2, 8)
            })

        # Убрать мобов если их много
        if len(self.simulator.mobs) > 5:
            self.simulator.mobs = self.simulator.mobs[:5]

        # Получить блоки вокруг
        blocks_around = []
        for x in range(-2, 3):
            for z in range(-2, 3):
                block = self.simulator.get_block(
                    int(self.position["x"]) + x,
                    int(self.position["y"]) - 1,
                    int(self.position["z"]) + z
                )
                if block != "air":
                    blocks_around.append(block)

        return {
            "position": self.position,
            "health": self.health,
            "hunger": self.hunger,
            "saturation": max(0, self.hunger),
            "inventory": self.inventory,
            "time_of_day": self.simulator.time_of_day,
            "is_night": is_night,
            "environment": {
                "blocks_around": blocks_around[:10],
                "mobs_nearby": self.simulator.mobs[:5],
                "weather": "clear"
            }
        }

    def send_action(self, action: str, params: dict = None) -> bool:
        """Отправить действие в Minecraft"""
        action = action.lower().strip()

        # Движение
        if action == "forward":
            self.position["x"] += 0.5
        elif action == "backward":
            self.position["x"] -= 0.5
        elif action == "left":
            self.position["z"] -= 0.5
        elif action == "right":
            self.position["z"] += 0.5
        elif action == "jump":
            self.position["y"] += 1

        # Активные действия
        elif action == "dig":
            # Сломать блок перед собой
            target_x = int(self.position["x"]) + 1
            target_y = int(self.position["y"])
            target_z = int(self.position["z"])
            block = self.simulator.get_block(target_x, target_y, target_z)
            if block != "air":
                self.simulator.break_block(target_x, target_y, target_z)
                self.inventory[block] = self.inventory.get(block, 0) + 1

        elif action == "eat":
            if "apple" in self.inventory and self.inventory["apple"] > 0:
                self.hunger = min(20, self.hunger + 4)
                self.inventory["apple"] -= 1
            elif "bread" in self.inventory and self.inventory["bread"] > 0:
                self.hunger = min(20, self.hunger + 5)
                self.inventory["bread"] -= 1

        elif action == "sleep":
            self.health = 20  # Полное исцеление
            self.simulator.time_of_day = 0  # Рассвет

        elif action == "wait":
            pass  # Просто подождать

        # Убить мобов если они близко
        if self.simulator.mobs and action == "attack":
            mob_dist = self.simulator.mobs[0].get("distance", 100)
            if mob_dist < 3:
                self.simulator.mobs.pop(0)

        # Атака мобами если они заметили
        if self.simulator.mobs:
            for mob in self.simulator.mobs:
                if mob.get("distance", 100) < 5:
                    self.health -= random.randint(0, 2)
                mob["distance"] -= 1

        # Гравитация
        if self.position["y"] > 64:
            self.position["y"] -= 0.5

        self.health = max(0, min(20, self.health))

        return True

    def disconnect(self):
        """Отключиться от сервера"""
        self.connected = False
        print("[MINECRAFT] Simulator stopped")
