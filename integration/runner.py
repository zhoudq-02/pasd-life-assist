"""Shared EpisodeRunner. Contract: docs/01 section 8 / docs/03 section 1."""
from __future__ import annotations

from src.pasd_life.executor import Executor
from src.pasd_life.schema import PiPERError, Trace
from .judge import judge
from .baselines.base import check_snapshot


def run_episode(policy_gen, memory, env, task: str, seed: int):
    ctx = env.reset(task, seed)
    hints = memory.retrieve(ctx)                                  # (1) only read point
    policy = policy_gen.generate(task, ctx, hints)
    try:
        obs = Executor(env.api).run(policy, step_cb=memory.on_step_end)
        env.state = dict(obs.state)
        trace = Trace.from_success(task, obs, ctx)
    except PiPERError as e:
        trace = Trace.from_error(task, e, ctx)                     # (2) only failure input
    success = judge(task, env.state)
    if ctx.split == "dev":                                        # (3) anti-contamination
        memory.on_episode_end(trace)                              # (4) only write point
    check_snapshot(memory.snapshot())
    return success, trace
