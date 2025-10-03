from __future__ import annotations
from pathlib import Path

from coman.core.base_module import BaseModule
from fastapi import HTTPException
import json, subprocess, shlex
from coman.core.config import settings


def _data_file() -> Path:
    return Path(settings.data_dir) / "vulnerabilities.json"
class Module(BaseModule):
    name = "defense_system"; description = "Security scans, nmap, report"
    def __init__(self, core):
        super().__init__(core)
        @self.router.get("/vuln/min-safe")
        def min_safe(package: str):
            path = _data_file()
            with path.open("r", encoding="utf-8") as f: data = json.load(f)
            pkg = data.get("packages", {}).get(package)
            if not pkg: raise HTTPException(404, f"No data for {package}")
            return {"package": package, "min_safe_version": pkg["min_safe_version"]}
        @self.router.get("/nmap")
        def nmap_scan(target: str = "127.0.0.1"):
            try: res = subprocess.run(shlex.split(f"nmap -F {target}"), capture_output=True, text=True, timeout=20)
            except FileNotFoundError: return {"error": "nmap not installed"}
            return {"stdout": res.stdout, "stderr": res.stderr, "code": res.returncode}
        @self.router.get("/report")
        def report():
            path = _data_file()
            with path.open("r", encoding="utf-8") as f: data = json.load(f)
            return {"cves": data.get("cves", [])}
