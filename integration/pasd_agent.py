"""Claude Code agent glue (PLUGIN POINT).

Wires a policy generator + memory through the shared EpisodeRunner. The retrieve() hints
are injected into the prompt by the policy generator (the only read point); the runner is
the only write point (docs/01 section 8).
"""
from __future__ import annotations

from src.pasd_life.policy_gen import StubPolicyGenerator


def run_agent_episode(memory, env, task: str, seed: int = 0, policy_gen=None):
    """Run one episode: policy generator + memory through the shared EpisodeRunner."""
    from .runner import run_episode

    policy = policy_gen or StubPolicyGenerator()
    return run_episode(policy, memory, env, task, seed)
