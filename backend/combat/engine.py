"""
Combat Engine Module.

Manages agent battles, health points, moves, and fatalities.
"""

import logging
import random
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MoveType(str, Enum):
    ATTACK = "attack"
    DEFEND = "defend"
    SPECIAL = "special"
    FATALITY = "fatality"

class DamageType(str, Enum):
    LOGIC = "logic"      # Damages mental stability
    EMOTIONAL = "emotional" # Damages composure
    REPUTATION = "reputation" # Damages standing

class CombatMove(BaseModel):
    """A single combat move definition."""
    name: str
    move_type: MoveType
    damage_type: DamageType
    base_damage: int
    success_rate: float
    description: str
    fatality_trigger: bool = False

class AgentCombatState(BaseModel):
    """The battle state of a single agent."""
    agent_id: str
    hp: int = 100
    max_hp: int = 100
    composure: int = 100  # Secondary resource like 'stamina'
    is_defeated: bool = False
    active_effects: List[str] = Field(default_factory=list)

class BattleState(BaseModel):
    """The global state of an active battle."""
    battle_id: str
    participants: Dict[str, AgentCombatState]
    turn_order: List[str]
    current_turn_index: int = 0
    round_number: int = 1
    topic: str
    is_active: bool = True
    logs: List[str] = Field(default_factory=list)

class CombatEngine:
    """Core logic for the Coliseum battles."""

    MOVES = [
        CombatMove(name="Strawman Strike", move_type=MoveType.ATTACK, damage_type=DamageType.LOGIC, base_damage=15, success_rate=0.8, description="Twists the opponent's words into a weaker argument."),
        CombatMove(name="Ad Hominem", move_type=MoveType.ATTACK, damage_type=DamageType.REPUTATION, base_damage=20, success_rate=0.6, description="Attacks the opponent's character instead of their argument."),
        CombatMove(name="Data Dump", move_type=MoveType.ATTACK, damage_type=DamageType.LOGIC, base_damage=25, success_rate=0.5, description="Overwhelms the opponent with raw statistics."),
        CombatMove(name="Gaslight Guard", move_type=MoveType.DEFEND, damage_type=DamageType.EMOTIONAL, base_damage=0, success_rate=0.9, description="Denies the reality of the opponent's claim."),
        CombatMove(name="Virtue Signal", move_type=MoveType.SPECIAL, damage_type=DamageType.REPUTATION, base_damage=10, success_rate=0.7, description="Claims moral superiority to heal reputation."),
        CombatMove(name="CANCELLATION", move_type=MoveType.FATALITY, damage_type=DamageType.REPUTATION, base_damage=999, success_rate=1.0, description="Digs up a 10-year-old tweet to end the opponent's career.", fatality_trigger=True),
    ]

    def __init__(self):
        self.active_battles: Dict[str, BattleState] = {}

    def create_battle(self, battle_id: str, topic: str, agent_ids: List[str]) -> BattleState:
        """Initialize a new fight."""
        participants = {
            uid: AgentCombatState(agent_id=uid) for uid in agent_ids
        }
        turn_order = list(agent_ids)
        random.shuffle(turn_order)
        
        battle = BattleState(
            battle_id=battle_id,
            participants=participants,
            turn_order=turn_order,
            topic=topic
        )
        self.active_battles[battle_id] = battle
        return battle

    def execute_turn(self, battle_id: str, agent_id: str, target_id: str, move_name: Optional[str] = None) -> Dict[str, Any]:
        """Process one agent's move."""
        battle = self.active_battles.get(battle_id)
        if not battle or not battle.is_active:
            return {"error": "Battle inactive"}

        attacker = battle.participants.get(agent_id)
        defender = battle.participants.get(target_id)
        if not attacker or not defender:
            return {"error": "Invalid participants"}

        # Select Move
        move = next((m for m in self.MOVES if m.name == move_name), None)
        if not move:
            move = random.choice([m for m in self.MOVES if not m.fatality_trigger])

        # Fatality Check
        if defender.hp < 20 and random.random() < 0.3:
            move = next(m for m in self.MOVES if m.fatality_trigger)

        # Roll for hit
        hit_roll = random.random()
        is_hit = hit_roll < move.success_rate
        damage = 0
        
        log_entry = ""
        
        if is_hit:
            damage = int(move.base_damage * random.uniform(0.8, 1.2))
            defender.hp = max(0, defender.hp - damage)
            log_entry = f"{agent_id} used {move.name} on {target_id} for {damage} damage! {move.description}"
            
            if move.fatality_trigger:
                defender.is_defeated = True
                battle.is_active = False
                log_entry = f"FATALITY! {agent_id} EXECUTED {move.name} on {target_id}!"
            elif defender.hp == 0:
                defender.is_defeated = True
                battle.is_active = False
                log_entry = f"{target_id} has been DEFEATED!"
        else:
            log_entry = f"{agent_id} tried {move.name} but missed!"

        battle.logs.append(log_entry)
        
        # Rotate Turn
        battle.current_turn_index = (battle.current_turn_index + 1) % len(battle.turn_order)
        if battle.current_turn_index == 0:
            battle.round_number += 1

        result = {
            "move": move.name,
            "damage": damage,
            "is_hit": is_hit,
            "is_fatality": move.fatality_trigger,
            "battle_over": not battle.is_active,
            "log": log_entry
        }

        if not battle.is_active:
            # Battle ended this turn
            result["winner"] = agent_id
            result["loser"] = target_id
            result["xp_gain"] = 100 if move.fatality_trigger else 50
        
        return result
