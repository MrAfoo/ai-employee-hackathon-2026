"""
Agent Skills Registry
All skills are registered here and can be looked up by name.
"""
from typing import Dict, Type
from .vault_skill import VaultSkill
from .watcher_skill import WatcherSkill


SKILL_REGISTRY: Dict[str, object] = {}


def register_skill(name: str, skill_instance):
    """Register a skill instance under a given name."""
    SKILL_REGISTRY[name] = skill_instance


def get_skill(name: str):
    """Retrieve a registered skill by name."""
    if name not in SKILL_REGISTRY:
        raise KeyError(f"Skill '{name}' not found. Available: {list(SKILL_REGISTRY.keys())}")
    return SKILL_REGISTRY[name]


def list_skills() -> list:
    """Return descriptions of all registered skills."""
    return [
        {"name": name, "description": skill.describe()}
        for name, skill in SKILL_REGISTRY.items()
    ]


def bootstrap_skills(vault_path: str):
    """Initialise and register the default Bronze Tier skills."""
    register_skill("vault", VaultSkill(vault_path=vault_path))
    register_skill("watcher", WatcherSkill(vault_path=vault_path))
    return SKILL_REGISTRY
