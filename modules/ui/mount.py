from fastapi import APIRouter, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from coman.core.config import settings
import json
import httpx


templates = Jinja2Templates(directory="coman/modules/ui/templates")


def mount_ui(app):
    router = APIRouter()

    @router.get("/ui", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @router.get("/ui/analysis", response_class=HTMLResponse)
    def analysis_view(request: Request):
        context = {"request": request, "text": "", "result_json": None, "error": None}
        return templates.TemplateResponse("analysis.html", context)

    @router.post("/ui/analysis/run", response_class=HTMLResponse)
    def analysis_run(request: Request, text: str = Form(...)):
        error = None
        result_json = None
        with httpx.Client(timeout=10) as c:
            try:
                resp = c.post(f"{settings.api_base}/analysis/frequency", params={"text": text})
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                error = f"Request failed: {exc}"
            else:
                try:
                    payload = resp.json()
                except ValueError:
                    payload = resp.text
                try:
                    result_json = json.dumps(payload, ensure_ascii=False, indent=2)
                except TypeError:
                    result_json = str(payload)
        context = {"request": request, "text": text, "result_json": result_json, "error": error}
        return templates.TemplateResponse("analysis.html", context)

    @router.get("/ui/tools", response_class=HTMLResponse)
    def tools_view(request: Request):
        with httpx.Client(timeout=10) as c:
            tools = c.get(f"{settings.api_base}/manager/tools").json()
        return templates.TemplateResponse("tools.html", {"request": request, "tools": tools})

    @router.post("/ui/tools/register")
    def tools_register(request: Request, name: str, method: str, path: str, params: str = "", desc: str = ""):
        with httpx.Client(timeout=10) as c:
            c.post(
                f"{settings.api_base}/manager/tools/register",
                params={"name": name, "method": method, "path": path, "params": params, "desc": desc},
            )
        return RedirectResponse(url="/ui/tools", status_code=303)

    @router.get("/ui/integrations", response_class=HTMLResponse)
    def integ_view(request: Request):
        with httpx.Client(timeout=10) as c:
            lst = c.get(f"{settings.api_base}/integration/list").json()
        return templates.TemplateResponse("integrations.html", {"request": request, "lst": lst})

    @router.post("/ui/integrations/register")
    def integ_register(request: Request, name: str, path: str, module: str, callable: str):
        with httpx.Client(timeout=10) as c:
            c.post(
                f"{settings.api_base}/integration/register",
                params={"name": name, "path": path, "module": module, "callable": callable},
            )
        return RedirectResponse(url="/ui/integrations", status_code=303)


    @router.get("/ui/telegram", response_class=HTMLResponse)
    def telegram_view(request: Request):
        status = {}
        error = None
        with httpx.Client(timeout=10) as c:
            try:
                resp = c.get(f"{settings.api_base}/telegram/status")
                resp.raise_for_status()
                try:
                    status = resp.json()
                except ValueError:
                    status = {}
                    error = "Unexpected response from API"
            except httpx.HTTPError as exc:
                error = f"Request failed: {exc}"
        context = {"request": request, "status": status, "message": None, "error": error}
        return templates.TemplateResponse("telegram.html", context)

    @router.post("/ui/telegram/save", response_class=HTMLResponse)
    def telegram_save(request: Request, token: str = Form(""), action: str = Form("save")):
        status = {}
        error = None
        message = None
        payload_token = "" if action == "clear" else token.strip()

        with httpx.Client(timeout=10) as c:
            try:
                resp = c.post(f"{settings.api_base}/telegram/token", json={"token": payload_token})
                resp.raise_for_status()
                message = "Token saved" if payload_token.strip() else "Token cleared"
                try:
                    status = resp.json()
                except ValueError:
                    status = {}
                    error = "Unexpected response from API"
            except httpx.HTTPError as exc:
                error = f"Request failed: {exc}"

            if not status:
                try:
                    status_resp = c.get(f"{settings.api_base}/telegram/status")
                    status_resp.raise_for_status()
                    status = status_resp.json()
                except httpx.HTTPError as exc:
                    if not error:
                        error = f"Failed to fetch status: {exc}"
                except ValueError:
                    if not error:
                        error = "Failed to parse status response"

        context = {"request": request, "status": status, "message": message, "error": error}
        return templates.TemplateResponse("telegram.html", context)


    @router.get("/ui/rules", response_class=HTMLResponse)
    def rules_view(request: Request):
        with httpx.Client(timeout=10) as c:
            rules = c.get(f"{settings.api_base}/logic/rulesx/list").json()
        return templates.TemplateResponse("rules.html", {"request": request, "rules": rules})

    @router.post("/ui/rules/add")
    def rules_add(request: Request, name: str, expr_json: str, action_json: str, priority: int = 0):
        with httpx.Client(timeout=10) as c:
            c.post(
                f"{settings.api_base}/logic/rulesx/add",
                params={
                    "name": name,
                    "expr_json": expr_json,
                    "action_json": action_json,
                    "priority": priority,
                    "enabled": 1,
                },
            )
        return RedirectResponse(url="/ui/rules", status_code=303)

    app.include_router(router)
