from __future__ import annotations
from coman.core.base_module import BaseModule
from coman.core.config import settings
from fastapi import HTTPException
import httpx, json
def _eval_expr(expr, ctx):
    if not isinstance(expr, dict): return False
    if "all" in expr: return all(_eval_expr(x, ctx) for x in expr["all"])
    if "any" in expr: return any(_eval_expr(x, ctx) for x in expr["any"])
    if "eq" in expr:
        k,v = expr["eq"]; return str(ctx.get(k)) == str(v)
    if "neq" in expr:
        k,v = expr["neq"]; return str(ctx.get(k)) != str(v)
    if "in" in expr:
        k, arr = expr["in"]; return str(ctx.get(k)) in [str(a) for a in arr]
    return False
class Module(BaseModule):
    name = "logic_app"; description = "Route by logic (JSON DSL) to integration callable"
    def __init__(self, core):
        super().__init__(core)
        @self.router.post("/rulesx/add")
        def rulesx_add(name: str, expr_json: str, action_json: str, priority: int = 0, enabled: int = 1):
            with httpx.Client(timeout=10) as c:
                r = c.post(f"{settings.api_base}/v1/logic/rulesx/add",
                           params={"name":name,"expr_json":expr_json,"action_json":action_json,"priority":priority,"enabled":enabled})
                return r.json()
        @self.router.post("/decide-and-call-advanced")
        def decide_and_call_advanced(context: dict):
            with httpx.Client(timeout=10) as c:
                rules = c.get(f"{settings.api_base}/v1/logic/rulesx/list").json()
            applied = []
            for r in rules:
                if not r["enabled"]: continue
                expr = json.loads(r["expr_json"])
                if _eval_expr(expr, context):
                    act = json.loads(r["action_json"])
                    applied.append({"id": r["id"], "name": r["name"], "priority": r["priority"], "action": act})
            if not applied: raise HTTPException(400, "no matching rule")
            applied.sort(key=lambda x: (-x["priority"], x["id"]))
            chosen = applied[0]; act = chosen["action"]
            integ = act.get("set",{}).get("use_integration"); call = act.get("set",{}).get("use_callable")
            if not (integ and call): raise HTTPException(400, "rule action missing use_integration/use_callable")
            with httpx.Client(timeout=15) as c:
                r = c.post(
                    f"{settings.api_base}/v1/integration/call",
                    params={"name": integ, "callable": call},
                    json={"kwargs": context},
                )
                return {"applied": applied, "chosen": chosen, "integration_result": r.json()}
