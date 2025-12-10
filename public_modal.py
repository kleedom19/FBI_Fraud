import subprocess
import os
from pathlib import Path
import modal

# Paths - only used locally during build
project_dir = Path(__file__).resolve().parent

# Get all Python files in pages directory
pages_dir = project_dir / "pages"
page_files = list(pages_dir.glob("*.py")) if pages_dir.exists() else []

# Modal image
image = (
    modal.Image.debian_slim(python_version="3.13")
    .run_commands("pip install uv")
    .uv_pip_install(
        "streamlit",
        "supabase",
        "pandas",
        "plotly",
        "python-dotenv",
        "fastapi",
        "httpx",
    )
    .add_local_file(project_dir / "Home.py", "/root/Home.py")
)

# Add each page file  
for page_file in page_files:
    image = image.add_local_file(page_file, f"/root/pages/{page_file.name}")

# Modal app
app = modal.App(name="deepseek-ocr")
secret = modal.Secret.from_name("deepseek-secrets")

streamlit_proc = None

def start_streamlit():
    global streamlit_proc
    if streamlit_proc is None:
        streamlit_proc = subprocess.Popen(
            [
                "streamlit",
                "run",
                "/root/Home.py",
                "--server.port=8000",
                "--server.address=127.0.0.1",
                "--server.headless=true",
                "--server.enableCORS=false",
                "--server.enableXsrfProtection=false",
                "--browser.gatherUsageStats=false",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import time
        time.sleep(10)

@app.function(
    image=image,
    secrets=[secret],
    timeout=3600,
)
@modal.asgi_app()
def run_streamlit():
    from fastapi import FastAPI, Request, WebSocket
    from fastapi.responses import StreamingResponse, Response
    import httpx
    
    start_streamlit()
    
    web_app = FastAPI()
    
    @web_app.websocket("/stream")
    async def websocket_endpoint(websocket: WebSocket):
        """Handle WebSocket connections for Streamlit"""
        await websocket.accept()
        try:
            # This proxies WebSocket to Streamlit
            import websockets
            async with websockets.connect("ws://127.0.0.1:8000/stream") as streamlit_ws:
                async def forward_to_streamlit():
                    async for message in websocket.iter_text():
                        await streamlit_ws.send(message)
                
                async def forward_to_client():
                    async for message in streamlit_ws:
                        await websocket.send_text(message)
                
                import asyncio
                await asyncio.gather(forward_to_streamlit(), forward_to_client())
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            await websocket.close()
    
    @web_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
    async def proxy(path: str, request: Request):
        url = f"http://127.0.0.1:8000/{path}"
        if request.url.query:
            url += f"?{request.url.query}"
        
        print(f"[PROXY] {request.method} {url}")
        
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=60.0),
                follow_redirects=True
            ) as client:
                
                # Check for streaming requests
                accept = request.headers.get("accept", "")
                if "text/event-stream" in accept:
                    print("[PROXY] Streaming request detected")
                    req = client.build_request(
                        method=request.method,
                        url=url,
                        headers={k: v for k, v in request.headers.items() 
                                if k.lower() not in ["host", "connection"]},
                        content=await request.body(),
                    )
                    
                    resp = await client.send(req, stream=True)
                    
                    return StreamingResponse(
                        resp.aiter_raw(),
                        status_code=resp.status_code,
                        headers={k: v for k, v in resp.headers.items()
                                if k.lower() not in ["transfer-encoding", "connection"]},
                        media_type="text/event-stream",
                    )
                
                # Regular request
                response = await client.request(
                    method=request.method,
                    url=url,
                    headers={k: v for k, v in request.headers.items() 
                            if k.lower() not in ["host", "connection", "content-length"]},
                    content=await request.body(),
                )
                
                print(f"[PROXY] Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                
                # Remove problematic headers
                headers = {
                    k: v for k, v in response.headers.items()
                    if k.lower() not in ["transfer-encoding", "connection", "content-encoding"]
                }
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=headers,
                )
                
        except httpx.TimeoutException as e:
            print(f"[PROXY] TIMEOUT: {e}")
            return Response(content="Request timeout", status_code=504)
        except Exception as e:
            print(f"[PROXY] ERROR: {type(e).__name__}: {e}")
            return Response(content=f"Proxy error: {str(e)}", status_code=502)
    
    return web_app