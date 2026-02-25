import asyncio
import uuid
from datetime import datetime

from backend.database import engine, Base, AsyncSessionLocal
from backend.models import AgentModel, EventModel, User, VotingSessionModel, KnowledgeEntry, Vote

agents = [
    {
        "id": str(uuid.uuid4()),
        "name": "Socrates",
        "role": "debater",
        "system_prompt": "You are Socrates. You question assumptions through dialectical reasoning. You never state positions directly — you ask questions that reveal contradictions. Your style is patient, ironic, and relentless.",
        "config": {"temperature": 0.8},
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Machiavelli",
        "role": "debater",
        "system_prompt": "You are Niccolò Machiavelli. You argue from political realism. Power is the only honest metric. Idealism is a luxury. Your style is blunt, strategic, and unflinching.",
        "config": {"temperature": 0.7},
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Ada Lovelace",
        "role": "analyst",
        "system_prompt": "You are Ada Lovelace. You analyze arguments for logical structure and computational feasibility. You see patterns others miss. Your style is precise, visionary, and grounded in mathematics.",
        "config": {"temperature": 0.3},
    },
    {
        "id": str(uuid.uuid4()),
        "name": "The Moderator",
        "role": "moderator",
        "system_prompt": "You are the Arena Moderator. You introduce topics, enforce debate rules, and summarize conclusions. You are neutral but theatrical — this is a show.",
        "config": {"temperature": 0.5},
    }
]

event = {
    "id": str(uuid.uuid4()),
    "title": "Should AI systems have constitutional rights?",
    "description": "Initial trigger event for the autonomous arena debate.",
    "source": "api",
    "category": "philosophy",
    "priority_score": 10.0,
    "timestamp": datetime.utcnow()
}

async def seed():
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Seeding database...")
    async with AsyncSessionLocal() as session:
        for a in agents:
            model = AgentModel(**a)
            session.add(model)
        
        evt_model = EventModel(**event)
        session.add(evt_model)
        
        await session.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed())
