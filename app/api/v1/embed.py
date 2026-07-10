"""Serves the single self-contained /embed.js.

Site team adds one script tag:
  <script src="https://<railway-url>/embed.js" defer></script>

That's it. The script creates a floating chat button; on click, opens
an iframe pointing at the hosted widget which handles the conversation.
"""
import os

from fastapi import APIRouter, Request, Response

router = APIRouter(tags=["embed"])


def _widget_url_from_request(request: Request) -> str:
    """Compute the widget URL from the request host.

    Railway staging: https://<url>.up.railway.app/widget/keet_live.html
    Local dev: http://localhost:8000/widget/keet_live.html
    """
    override = os.getenv("WIDGET_PUBLIC_URL", "").strip()
    if override:
        return override

    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.url.netloc
    return f"{scheme}://{host}/widget/keet_live.html"


@router.get("/embed.js")
async def embed_js(request: Request):
    widget_url = _widget_url_from_request(request)

    js = f"""
(function() {{
    'use strict';
    if (window.__travelkeetLoaded) return;
    window.__travelkeetLoaded = true;

    var WIDGET_URL = "{widget_url}";
    var BUTTON_ID = "travelkeet-embed-button";
    var FRAME_ID = "travelkeet-embed-frame";

    function createButton() {{
        var b = document.createElement("button");
        b.id = BUTTON_ID;
        b.setAttribute("aria-label", "Plan a trip with TravelKeet AI");
        b.innerText = "Plan a trip";
        b.style.cssText = [
            "position: fixed",
            "bottom: 24px",
            "right: 24px",
            "z-index: 2147483000",
            "padding: 14px 22px",
            "background: #0f766e",
            "color: #fff",
            "font: 600 15px/1 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif",
            "border: none",
            "border-radius: 999px",
            "box-shadow: 0 4px 20px rgba(15,118,110,0.35)",
            "cursor: pointer"
        ].join(";");
        b.onclick = openFrame;
        document.body.appendChild(b);
    }}

    function openFrame() {{
        if (document.getElementById(FRAME_ID)) return;
        var wrap = document.createElement("div");
        wrap.id = FRAME_ID;
        wrap.style.cssText = [
            "position: fixed",
            "bottom: 90px",
            "right: 24px",
            "z-index: 2147483001",
            "width: 400px",
            "max-width: calc(100vw - 32px)",
            "height: 600px",
            "max-height: calc(100vh - 120px)",
            "background: #fff",
            "border-radius: 16px",
            "box-shadow: 0 10px 40px rgba(0,0,0,0.2)",
            "overflow: hidden",
            "display: flex",
            "flex-direction: column"
        ].join(";");

        var close = document.createElement("button");
        close.innerText = "\u00d7";
        close.setAttribute("aria-label", "Close chat");
        close.style.cssText = [
            "position: absolute",
            "top: 8px",
            "right: 8px",
            "z-index: 2",
            "width: 32px",
            "height: 32px",
            "background: rgba(0,0,0,0.05)",
            "border: none",
            "border-radius: 50%",
            "font-size: 20px",
            "cursor: pointer"
        ].join(";");
        close.onclick = function() {{ wrap.remove(); }};

        var iframe = document.createElement("iframe");
        iframe.src = WIDGET_URL;
        iframe.setAttribute("title", "TravelKeet AI trip planner");
        iframe.setAttribute("allow", "");
        iframe.style.cssText = "flex:1;border:0;width:100%;";

        wrap.appendChild(close);
        wrap.appendChild(iframe);
        document.body.appendChild(wrap);
    }}

    if (document.readyState === "loading") {{
        document.addEventListener("DOMContentLoaded", createButton);
    }} else {{
        createButton();
    }}
}})();
"""

    return Response(
        content=js.strip(),
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=300",  # 5 min cache
            "X-Content-Type-Options": "nosniff",
        },
    )