"""API Routers Package"""

from .agents import router as agents_router
from .events import router as events_router
from .voting import router as voting_router
from .blockchain import router as blockchain_router
from .achievements import router as achievements_router
from .users import router as users_router
from .demo import router as demo_router
from .state import router as state_router

__all__ = [
    'agents_router',
    'events_router',
    'voting_router',
    'blockchain_router',
    'achievements_router',
    'users_router',
    'demo_router',
    'state_router',
]
