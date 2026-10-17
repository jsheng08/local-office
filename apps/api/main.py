"""Local Office FastAPI app."""
import importlib
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from services.inference.client import InferenceError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("local_office")

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "apps" / "web" / ".output" / "public"

app = FastAPI(title="Local Office")

ROUTER_MODULES = ["system", "requirements", "onboarding", "finance", "executive"]
LOADED_ROUTERS = []
for _name in ROUTER_MODULES:
    try:
        _mod = importlib.import_module("apps.api.routers.%s" % _name)
        app.include_router(_mod.router)
        LOADED_ROUTERS.append(_name)
        log.info("router loaded: %s", _name)
    except Exception:
        log.exception("router failed to load: %s", _name)


@app.exception_handler(InferenceError)
async def _inference_error(request: Request, exc: InferenceError) -> JSONResponse:
    log.error("local inference failed: %s", exc)
    return JSONResponse(status_code=502, content={
        "error": "local_inference_failed", "detail": exc.reason,
        "use_case": exc.use_case, "model": exc.model,
    })


# Serve only the built Nuxt SPA (`npm run generate` in apps/web), never its source tree.
# During development the Nuxt dev server on :3000 proxies /api to this app instead.
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
