from __future__ import annotations
from coman.core.base_module import BaseModule
from coman.core.config import settings
from fastapi import Body, Query
import os, json, httpx, re

TOOLS_PATH = os.path.join("coman","data","tools.json")

def load_tools():
    if not os.path.exists(TOOLS_PATH): return {"tools":[]}
    # utf-8-sig — на случай BOM в tools.json
    with open(TOOLS_PATH,"r",encoding="utf-8-sig") as f:
        return json.load(f)

def save_tools(d):
    os.makedirs(os.path.dirname(TOOLS_PATH), exist_ok=True)
    with open(TOOLS_PATH,"w",encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

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
            return load_tools()

        @self.router.post("/tools/register")
        def register_tool(name: str, method: str, path: str, params: str = "", desc: str = ""):
            d = load_tools()
            t = [x for x in d.get("tools", []) if x["name"] != name]
            t.append({"name":name,"method":method.upper(),"path":path,"params":[p for p in params.split(",") if p],"desc":desc})
            d["tools"] = t; save_tools(d)
            return {"ok": True}

        @self.router.post("/run")
        def run(payload: dict | None = Body(default=None), goal_q: str | None = Query(default=None)):
            goal = (payload or {}).get("goal") if isinstance(payload, dict) else None
            inputs = (payload or {}).get("inputs") if isinstance(payload, dict) else {}
            if not goal: goal = goal_q or ""

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

            if not tool_name:
                return {"goal": goal, "error":"no_tool","message":"No matching tool found", "known_tools": load_tools()}

            d = load_tools(); tools = {t["name"]: t for t in d.get("tools", [])}
            tool = tools.get(tool_name)
            if not tool: return {"error":"unknown_tool","name":tool_name}

            method, path, params = tool["method"], tool["path"], tool.get("params", [])
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

            return {"goal": goal, "tool": tool_name, "query": query, "result": res_body}
