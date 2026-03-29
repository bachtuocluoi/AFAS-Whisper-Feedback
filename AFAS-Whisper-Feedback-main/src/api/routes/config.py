from fastapi import APIRouter
from fastapi.responses import Response
from config.settings import settings

router = APIRouter(tags=["config"])


@router.get("/view-config.js")
def get_view_config():
    content = f"""
window.APP_CONFIG = {{
  BACKEND_BASE_URL: "{settings.backend_base_url}"
}};
"""
    return Response(content=content, media_type="application/javascript")