from __future__ import annotations
from coman.core.base_module import BaseModule
from .db import get_conn
class Module(BaseModule):
    name = "logic"; description = "Facts & rules storage (sqlite) + extended rules"
    def __init__(self, core):
        super().__init__(core)
        @self.router.post("/facts")
        def add_fact(label: str, value: str):
            with get_conn() as c:
                c.execute("INSERT OR REPLACE INTO facts(label, value) VALUES (?, ?)", (label, value)); c.commit()
            return {"ok": True}
        @self.router.get("/facts")
        def list_facts():
            with get_conn() as c:
                rows = c.execute("SELECT label, value FROM facts").fetchall()
            return [{"label": r[0], "value": r[1]} for r in rows]
        @self.router.post("/rules")
        def add_rule(name: str, if_label: str, if_value: str, then_label: str, then_value: str):
            with get_conn() as c:
                c.execute("INSERT INTO rules(name, if_label, if_value, then_label, then_value) VALUES (?,?,?,?,?)",
                          (name, if_label, if_value, then_label, then_value)); c.commit()
            return {"ok": True}
        @self.router.post("/infer")
        def infer():
            applied = 0
            with get_conn() as c:
                facts = {label: value for (label, value) in c.execute("SELECT label, value FROM facts")}
                rules = c.execute("SELECT name, if_label, if_value, then_label, then_value FROM rules").fetchall()
                for name, if_l, if_v, then_l, then_v in rules:
                    if facts.get(if_l) == if_v:
                        c.execute("INSERT OR REPLACE INTO facts(label, value) VALUES (?, ?)", (then_l, then_v)); applied += 1
                c.commit()
            return {"applied_rules": applied}
        @self.router.post("/rulesx/add")
        def rulesx_add(name: str, expr_json: str, action_json: str, priority: int = 0, enabled: int = 1):
            with get_conn() as c:
                c.execute("INSERT INTO rules_ext(name, expr_json, action_json, priority, enabled) VALUES (?,?,?,?,?)",
                          (name, expr_json, action_json, priority, enabled)); c.commit()
            return {"ok": True}
        @self.router.get("/rulesx/list")
        def rulesx_list():
            with get_conn() as c:
                rows = c.execute("SELECT id,name,expr_json,action_json,priority,enabled FROM rules_ext ORDER BY priority DESC,id ASC").fetchall()
            return [{"id":r[0],"name":r[1],"expr_json":r[2],"action_json":r[3],"priority":r[4],"enabled":bool(r[5])} for r in rows]
        @self.router.post("/rulesx/clear")
        def rulesx_clear():
            with get_conn() as c:
                c.execute("DELETE FROM rules_ext"); c.commit()
            return {"ok": True}
