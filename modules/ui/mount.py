from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from coman.core.config import settings
import httpx
templates = Jinja2Templates(directory="coman/modules/ui/templates")
def mount_ui(app):
    router = APIRouter()
    @router.get("/ui", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    @router.get("/ui/tools", response_class=HTMLResponse)
    def tools_view(request: Request):
        with httpx.Client(timeout=10) as c:
            tools = c.get(f"{settings.api_base}/manager/tools").json()
        return templates.TemplateResponse("tools.html", {"request": request, "tools": tools})
    @router.post("/ui/tools/register")
    def tools_register(request: Request, name: str, method: str, path: str, params: str = "", desc: str = ""):
        with httpx.Client(timeout=10) as c:
            c.post(f"{settings.api_base}/manager/tools/register",
                   params={"name":name,"method":method,"path":path,"params":params,"desc":desc})
        return RedirectResponse(url="/ui/tools", status_code=303)
    @router.get("/ui/integrations", response_class=HTMLResponse)
    def integ_view(request: Request):
        with httpx.Client(timeout=10) as c:
            lst = c.get(f"{settings.api_base}/integration/list").json()
        return templates.TemplateResponse("integrations.html", {"request": request, "lst": lst})
    @router.post("/ui/integrations/register")
    def integ_register(request: Request, name: str, path: str, module: str, callable: str):
        with httpx.Client(timeout=10) as c:
            c.post(f"{settings.api_base}/integration/register",
                   params={"name":name,"path":path,"module":module,"callable":callable})
        return RedirectResponse(url="/ui/integrations", status_code=303)
    @router.get("/ui/rules", response_class=HTMLResponse)
    def rules_view(request: Request):
        with httpx.Client(timeout=10) as c:
            rules = c.get(f"{settings.api_base}/logic/rulesx/list").json()
        return templates.TemplateResponse("rules.html", {"request": request, "rules": rules})
    @router.post("/ui/rules/add")
    def rules_add(request: Request, name: str, expr_json: str, action_json: str, priority: int = 0):
        with httpx.Client(timeout=10) as c:
            c.post(f"{settings.api_base}/logic/rulesx/add",
                   params={"name":name,"expr_json":expr_json,"action_json":action_json,"priority":priority,"enabled":1})
        return RedirectResponse(url="/ui/rules", status_code=303)
    app.include_router(router)
