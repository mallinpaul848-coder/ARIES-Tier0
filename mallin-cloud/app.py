from __future__ import annotations
import hmac, json, os, re, shutil, subprocess, threading, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(os.getenv("MALLIN_DATA_DIR", "/data")).resolve()
PUBLISHED = BASE / "published"
WORK = BASE / "work"
STATE = BASE / "deployments.json"
for p in (PUBLISHED, WORK):
    p.mkdir(parents=True, exist_ok=True)
TOKEN = os.getenv("MALLIN_ADMIN_TOKEN", "")
app = FastAPI(title="MALLIN Cloud", version="0.1.0")
lock = threading.Lock()
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,47}$")
REPO = re.compile(r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?$")

class DeployRequest(BaseModel):
    repo: str = Field(min_length=10, max_length=300)
    branch: str = Field(default="main", min_length=1, max_length=120)
    project: str = Field(min_length=1, max_length=48)

def read_rows():
    try: return json.loads(STATE.read_text("utf-8"))
    except (OSError, ValueError): return []

def write_rows(rows):
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    tmp.replace(STATE)

def authorize(value: Optional[str]):
    if not TOKEN:
        raise HTTPException(503, "Deployments disabled: set MALLIN_ADMIN_TOKEN on the server.")
    if not value or not hmac.compare_digest(value, "Bearer " + TOKEN):
        raise HTTPException(401, "Admin bearer token required.")

def git(cmd, cwd=None, timeout=90):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    if p.returncode:
        raise RuntimeError((p.stdout or "Command failed")[-5000:])
    return p.stdout[-5000:]

@app.get("/health")
def health():
    return {"ok": True, "service": "MALLIN Cloud", "version": app.version, "deployments": len(read_rows())}

@app.get("/api/deployments")
def deployments():
    return {"deployments": read_rows()[:100]}

@app.post("/api/deploy")
def deploy(payload: DeployRequest, authorization: Optional[str] = Header(default=None)):
    authorize(authorization)
    if not SLUG.fullmatch(payload.project):
        raise HTTPException(400, "Project slug must use lowercase letters, numbers, and hyphens.")
    if not REPO.fullmatch(payload.repo):
        raise HTTPException(400, "Only public HTTPS GitHub repositories are supported.")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", payload.branch) or payload.branch.startswith("-"):
        raise HTTPException(400, "Invalid branch name.")
    ident = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    temp = WORK / ident
    out = PUBLISHED / payload.project / ident
    record = {"id": ident, "project": payload.project, "repo": payload.repo, "branch": payload.branch,
              "status": "building", "created_at": datetime.now(timezone.utc).isoformat()}
    with lock:
        rows = read_rows(); rows.insert(0, record); write_rows(rows)
    try:
        # Safety boundary: this MVP does not run package scripts from untrusted repositories.
        git(["git", "clone", "--depth", "1", "--branch", payload.branch, "--", payload.repo, str(temp)])
        source = next((p for p in (temp / "dist", temp / "build", temp / "out") if (p / "index.html").is_file()), temp)
        if not (source / "index.html").is_file():
            raise RuntimeError("No ready-to-serve index.html found. Build the site in a trusted environment and commit the output to the repository root, dist/, build/, or out/. MALLIN Cloud does not execute untrusted npm build scripts.")
        out.mkdir(parents=True, exist_ok=False)
        for child in source.iterdir():
            dest = out / child.name
            if child.is_dir(): shutil.copytree(child, dest)
            else: shutil.copy2(child, dest)
        current = PUBLISHED / payload.project / "current"
        next_link = PUBLISHED / payload.project / "current-next"
        if next_link.exists() or next_link.is_symlink(): next_link.unlink()
        next_link.symlink_to(out, target_is_directory=True)
        if current.exists() or current.is_symlink(): current.unlink()
        next_link.replace(current)
        record.update(status="ready", url=f"/sites/{payload.project}/", finished_at=datetime.now(timezone.utc).isoformat())
    except Exception as e:
        record.update(status="failed", error=str(e)[-5000:], finished_at=datetime.now(timezone.utc).isoformat())
    finally:
        shutil.rmtree(temp, ignore_errors=True)
        with lock:
            rows = read_rows()
            for row in rows:
                if row.get("id") == ident: row.update(record); break
            write_rows(rows)
    return record

@app.get("/sites/{project}/{asset_path:path}")
def site_asset(project: str, asset_path: str):
    if not SLUG.fullmatch(project):
        raise HTTPException(404, "Site not found")
    root = PUBLISHED / project / "current"
    target = (root / (asset_path or "index.html")).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise HTTPException(404, "Asset not found")
    return FileResponse(target)

@app.get("/sites/{project}")
def site_root(project: str):
    if not SLUG.fullmatch(project): raise HTTPException(404, "Site not found")
    target = PUBLISHED / project / "current" / "index.html"
    if not target.is_file(): raise HTTPException(404, "Site not deployed")
    return FileResponse(target)

@app.get("/", response_class=HTMLResponse)
def dashboard():
    index = Path(__file__).with_name("index.html")
    if not index.exists(): return "<h1>MALLIN Cloud</h1><p>Dashboard asset missing.</p>"
    return HTMLResponse(index.read_text("utf-8"))
