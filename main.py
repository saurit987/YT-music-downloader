import os
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import yt_dlp
import re # Already used, keep it

app = FastAPI()

# --- Configuration and Setup ---

# Directory where files will be saved on the Raspberry Pi
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Setup directories for web service
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=".")

# Semaphore to limit concurrency (optional, but good practice)
semaphore = asyncio.Semaphore(3)


# --- CORE DOWNLOAD FUNCTION (Local Save) ---

def run_yt_dlp(url: str, is_playlist: bool = False):
    """
    Synchronous function to run yt-dlp and save the file locally.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        # Save output to the downloads folder
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s', 
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }, {
            'key': 'EmbedThumbnail',
        }, {
            'key': 'FFmpegMetadata',
        }],
        'noplaylist': not is_playlist,
        'quiet': True,
        'no_warnings': True,
        # Option to bypass JS runtime error
        'extractor-args': 'youtube:player_client=web_public', 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return {"status": "success", "url": url}
    except Exception as e:
        # Check for specific format errors
        error_message = str(e)
        if "No video formats found" in error_message:
            error_message = "Download failed: Cannot find valid video/audio formats for this link."
        
        print(f"Error downloading {url}: {error_message}")
        return {"status": "error", "message": error_message}

async def download_task(url: str, is_playlist: bool):
    """
    Async wrapper that respects the semaphore limits and runs the download.
    """
    async with semaphore:
        # Run the blocking download in a separate thread so the server stays responsive
        result = await asyncio.to_thread(run_yt_dlp, url, is_playlist)
        print(f"Download Task Finished: {result}")


# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def start_download(background_tasks: BackgroundTasks, url: str = Form(...), type: str = Form(...)):
    """
    Receives the download request and adds it to background tasks.
    Returns immediate status to the user.
    """
    is_playlist = (type == "playlist")
    
    # 1. Reject empty/invalid URLs early
    if not url or not url.startswith(('http://', 'https://')):
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid URL provided."}
        )

    # 2. Add to background tasks
    background_tasks.add_task(download_task, url, is_playlist)
    
    download_type_str = "Playlist" if is_playlist else "Song"
    
    return JSONResponse({
        "status": "queued", 
        "message": f"{download_type_str} download queued! It will appear in the 'downloads' folder shortly."
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
