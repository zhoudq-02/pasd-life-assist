"""Optional MCP server exposing the skill library to Claude Code (stdio JSON-RPC 2.0).

Tools: observe_failure / verify_gate2 / retrieve_repair / snapshot.

This speaks the MCP JSON-RPC-over-stdio protocol. Before enabling it, verify the Claude Code
MCP registration config on your host (docs/08 section 7); do not guess the config format.
"""
from __future__ import annotations

import json
import sys

from src.pasd_life.executor import MockSimRunner
from src.pasd_life.gates import gate1_observe_failure, gate2_verify
from src.pasd_life.pasd_core import Extractor, OnlineClusterer, SkillLibrary
from src.pasd_life.schema import PiPERError, SceneContext, Trace

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {"name": "snapshot",
     "description": "Return the current skill-library snapshot (size, verified).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "retrieve_repair",
     "description": "Retrieve VERIFIED/SAFE repairs matching the given features.",
     "inputSchema": {"type": "object",
                     "properties": {"instruction": {"type": "string"},
                                    "features": {"type": "object"}},
                     "required": ["instruction", "features"]}},
    {"name": "observe_failure",
     "description": "Record a failure trace through Gate1.",
     "inputSchema": {"type": "object",
                     "properties": {"task": {"type": "string"},
                                    "error_code": {"type": "string"},
                                    "features": {"type": "object"}},
                     "required": ["task", "error_code", "features"]}},
    {"name": "verify_gate2",
     "description": "Verify a CANDIDATE skill through Gate2 simulation.",
     "inputSchema": {"type": "object",
                     "properties": {"error_code": {"type": "string"}},
                     "required": ["error_code"]}},
]


class _Server:
    def __init__(self) -> None:
        self.extractor = Extractor()
        self.clusterer = OnlineClusterer()
        self.library = SkillLibrary()

    def call_tool(self, name: str, args: dict) -> dict:
        if name == "snapshot":
            return {"library_size": self.library.size, "verified": self.library.verified_count}
        if name == "retrieve_repair":
            ctx = SceneContext(args.get("instruction", ""), "", "dev", args.get("features", {}))
            skills = self.library.retrieve(ctx)
            return {"hints": [{"text": s.repair.get("text", ""),
                               "error_code": s.sigma.error_code} for s in skills]}
        if name == "observe_failure":
            task = args.get("task", "")
            features = args.get("features", {})
            trace = Trace.from_error(task, PiPERError(args.get("error_code", ""), features),
                                     SceneContext(task, "", "dev", features))
            skill = gate1_observe_failure(trace, self.extractor, self.clusterer, self.library)
            return {"admitted": skill is not None}
        if name == "verify_gate2":
            sim = MockSimRunner({"aspect_ratio": 1.0})
            for skill in self.library.all():
                if skill.sigma.error_code == args.get("error_code") and skill.state == "CANDIDATE":
                    ok = gate2_verify(skill, sim)
                    if ok:
                        skill.state = "VERIFIED"
                    return {"verified": ok}
            return {"verified": False, "reason": "no CANDIDATE skill for that error_code"}
        raise ValueError(f"unknown tool: {name}")


def _handle(server: _Server, req: dict) -> dict | None:
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}},
            "serverInfo": {"name": "pasd-life-assist", "version": "0.1.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        try:
            name = req["params"]["name"]
            args = req["params"].get("arguments", {})
            result = server.call_tool(name, args)
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
        except Exception as e:  # noqa: BLE001
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32000, "message": str(e)}}
    if method and method.startswith("notifications/"):
        return None  # notifications get no response
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> None:
    server = _Server()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(server, req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
