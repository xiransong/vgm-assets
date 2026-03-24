from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .object_semantics_explorer import (
    ObjectSemanticsExplorerConfig,
    default_object_semantics_explorer_config,
    get_object_semantics_asset_detail,
    list_object_semantics_assets,
    load_object_semantics_schema,
    save_reviewed_object_semantics_asset,
    source_file_path_for_asset,
)


def create_app(config: ObjectSemanticsExplorerConfig | None = None) -> FastAPI:
    explorer_config = config or default_object_semantics_explorer_config()
    app = FastAPI(title="vgm-assets Object Semantics Explorer v0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/object-semantics/assets")
    def list_assets() -> dict[str, Any]:
        return {"assets": list_object_semantics_assets(explorer_config)}

    @app.get("/api/object-semantics/assets/{asset_id}")
    def get_asset(asset_id: str) -> dict[str, Any]:
        try:
            return get_object_semantics_asset_detail(explorer_config, asset_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (ValueError, FileNotFoundError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/object-semantics/assets/{asset_id}")
    def save_asset(asset_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return save_reviewed_object_semantics_asset(explorer_config, asset_id, payload)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/object-semantics/assets/{asset_id}/source-file/{kind}")
    def get_source_file(asset_id: str, kind: str) -> FileResponse:
        try:
            path = source_file_path_for_asset(explorer_config, asset_id, kind)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        media_type, _ = mimetypes.guess_type(str(path))
        return FileResponse(path, media_type=media_type or "application/octet-stream")

    @app.get("/api/object-semantics/schema")
    def get_schema() -> dict[str, Any]:
        return load_object_semantics_schema()

    static_dir = explorer_config.frontend_dist_path
    if static_dir.exists():
        app.mount(
            "/object-semantics-explorer-v0",
            StaticFiles(directory=static_dir, html=True),
            name="object-semantics-explorer-v0",
        )

        @app.get("/")
        def root() -> RedirectResponse:
            return RedirectResponse(url="/object-semantics-explorer-v0/")

    return app


app = create_app()
