import os
import tempfile
from fastapi import FastAPI, Request, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import webex_utils
import audio_utils

app = FastAPI(title="Webex Voicemail Manager")

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/login")
async def login():
    """Redirect to Webex OAuth"""
    try:
        integration = webex_utils.get_integration()
        auth_url = integration.auth_url(state="my_state")
        return RedirectResponse(auth_url)
    except ValueError as e:
        return HTMLResponse(f"<h3>Configuration Error</h3><p>{str(e)}</p>", status_code=500)

@app.get("/oauth/callback")
async def oauth_callback(code: str, state: str = None):
    """Handle OAuth callback and set token cookie"""
    integration = webex_utils.get_integration()
    tokens = integration.tokens_from_code(code)
    access_token = tokens.access_token
    
    # Redirect to home and set cookie
    response = RedirectResponse(url="/")
    response.set_cookie(key="webex_token", value=access_token, httponly=True, max_age=3600)
    return response

@app.get("/me")
async def get_me(request: Request):
    """Get the currently authenticated user's details"""
    token = request.cookies.get("webex_token")
    if not token:
        config = webex_utils.load_config().get("webex", {})
        static_token = config.get("static_token")
        if static_token and static_token != "YOUR_STATIC_TEST_TOKEN":
            token = static_token
        else:
            raise HTTPException(status_code=401, detail="Not logged in")
    
    try:
        api = webex_utils.get_api(access_token=token)
        me = api.people.me()
        return {"name": me.display_name, "email": me.emails[0] if me.emails else ""}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload")
async def upload_audio(request: Request, audio_file: UploadFile = File(...)):
    """Handle audio upload, processing, and Webex integration"""
    # 1. Determine token
    token = request.cookies.get("webex_token")
    if not token:
        # Fallback to static token
        config = webex_utils.load_config().get("webex", {})
        static_token = config.get("static_token")
        if static_token and static_token != "YOUR_STATIC_TEST_TOKEN":
            token = static_token
        else:
            raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    
    # 2. Get API instance
    try:
        api = webex_utils.get_api(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_in:
        content = await audio_file.read()
        tmp_in.write(content)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(".webm", "_processed.wav")

    try:
        # 4. Process audio (append disclaimer, convert to 8kHz mono mu-law)
        audio_utils.process_voicemail_audio(tmp_in_path, tmp_out_path)
        
        # 5. Upload to Webex
        webex_utils.upload_voicemail_greetings(api, tmp_out_path)
        
        return JSONResponse(content={"status": "success", "message": "Voicemail greeting updated successfully!"})
    except Exception as e:
        import traceback
        app_config = webex_utils.load_config().get("app", {})
        if app_config.get("enable_file_logging", False):
            with open("app.log", "a") as log_file:
                log_file.write("=== Upload Error ===\n")
                traceback.print_exc(file=log_file)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process or upload: {str(e)}")
    finally:
        app_config = webex_utils.load_config().get("app", {})
        retain_files = app_config.get("retain_wav_files", False)
        
        # Cleanup temp files
        if not retain_files:
            if os.path.exists(tmp_in_path):
                os.remove(tmp_in_path)
            if os.path.exists(tmp_out_path):
                os.remove(tmp_out_path)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
