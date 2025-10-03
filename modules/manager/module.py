from __future__ import annotations
from pathlib import Path

from coman.core.base_module import BaseModule
from coman.core.config import settings
from coman.core.messages import (
    ManagerRunRequest,
    ManagerRunResult,
    ToolDefinition,
    ToolRegistry,
)
from fastapi import Body, HTTPException, Query
import os, json, httpx, re


def _tools_path() -> Path:
    return Path(settings.data_dir) / "tools.json"


def load_tools() -> ToolRegistry:
    path = _tools_path()
    if not path.exists():
        return ToolRegistry()
    # utf-8-sig — на случай BOM в tools.json
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return ToolRegistry.from_payload(data)


def save_tools(registry: ToolRegistry) -> None:
    path = _tools_path()
    os.makedirs(path.parent, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(registry.to_payload(), f, ensure_ascii=False, indent=2)

URL_RX = re.compile(r'(https?://[^\s\]\)\}\,;"]+)', re.I)

# порядок важен: url/title -> uppercase -> ресурсы
HEURISTICS = [
    (re.compile(r"\btitle\b|\burl\b", re.I), "webscraper.title"),
    (re.compile(r"\bupper(case)?\b", re.I), "text.uppercase"),
    (re.compile(r"\b(cpu|memory|ram)\b", re.I), "resources.snapshot"),
]

class Module(BaseModule):
    name = "manager"; description = "Minimal AI manager: plan → select tool → execute"

    def __init__(self, core):
        super().__init__(core)

        @self.router.get("/tools")
        def tools():
            return load_tools().to_payload()

        @self.router.post("/tools/register")
        def register_tool(
            payload: ToolDefinition | None = Body(default=None),
            name: str | None = Query(default=None),
            method: str | None = Query(default=None),
            path: str | None = Query(default=None),
            params: str = Query(default=""),
            desc: str = Query(default=""),
        ):
            if payload is not None:
                tool = ToolDefinition.from_payload(payload)
            else:
                if not name or not path:
                    raise HTTPException(400, "name and path are required")
                tool = ToolDefinition(
                    name=name,
                    method=(method or "GET"),
                    path=path,
                    params=params,
                    desc=desc,
                )
            registry = load_tools()
            registry.upsert(tool)
            save_tools(registry)
            resp = {"ok": True, "tool": tool.to_payload()}
            return resp

        @self.router.post("/run")
        def run(payload: ManagerRunRequest | dict | None = Body(default=None), goal_q: str | None = Query(default=None)):
            req = ManagerRunRequest.from_payload(payload)
            if goal_q and not req.goal:
                req = req.clone(goal=goal_q)
            goal = req.goal
            inputs = req.inputs

            # 1) если есть URL — принудительно webscraper.title
            url_in_text = None
            m = URL_RX.search(goal or "")
            if m:
                url_in_text = m.group(1)
                tool_name = "webscraper.title"
            else:
                tool_name = None
                for rx, name in HEURISTICS:
                    if goal and rx.search(goal):
                        tool_name = name
                        break

            registry = load_tools()
            if not tool_name:
                result = ManagerRunResult(goal=goal, error="no_tool", message="No matching tool found")
                result.set_known_tools(registry)
                return result.to_payload()

            tool = registry.find(tool_name)
            if not tool:
                result = ManagerRunResult(goal=goal, tool=tool_name, error="unknown_tool", message="Tool is not registered")
                payload = result.to_payload()
                payload.setdefault("name", tool_name)
                return payload

            method, path, params = tool.method, tool.path, tool.params
            query = {}
            for p in params:
                if p in (inputs or {}):
                    query[p] = inputs[p]
                elif p == "s":
                    query[p] = goal
                elif p == "url" and url_in_text:
                    query["url"] = url_in_text

            with httpx.Client(timeout=20) as c:
                r = c.get(f"{settings.api_base}{path}", params=query) if method == "GET" else c.post(f"{settings.api_base}{path}", params=query, json={})

            # 2) НОРМАЛИЗАЦИЯ ОТВЕТА: декодируем мягко, разворачиваем строковый JSON, приводим к объекту
            try:
                res_body = r.json()
            except Exception:
                res_body = r.text

            if isinstance(res_body, str):
                s = res_body.strip()
                if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
                    try:
                        res_body = json.loads(s)
                    except Exception:
                        pass

            # если всё ещё строка — оборачиваем как {"text": "..."}
            if isinstance(res_body, str):
                res_body = {"text": res_body}

            result = ManagerRunResult(goal=goal, tool=tool_name, query=query, result=res_body)
            return result.to_payload()
