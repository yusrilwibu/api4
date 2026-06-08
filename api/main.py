from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from ytmusicapi import YTMusic
import yt_dlp
import re

app = FastAPI(title="SANN404 FORUM Music API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yt = YTMusic()

@app.get("/api/search")
async def search_music(query: str):
    try:
        results = yt.search(query, filter="songs")
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/charts")
async def get_charts():
    try:
        results = yt.get_charts()
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream")
async def get_stream_url(video_id: str):
    """Get direct audio stream URL for a YouTube video ID"""
    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # android_vr TERBUKTI bypass blokir YouTube bot detection
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'android', 'web']
                }
            }
        }
        url = f"https://music.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url', '')
            duration = info.get('duration', 0)
            title = info.get('title', '')
            thumbnail = info.get('thumbnail', '')
            
            if not stream_url:
                raise HTTPException(status_code=404, detail="Stream URL not found")
            
            return {
                "status": "success",
                "data": {
                    "url": stream_url,
                    "duration": duration,
                    "title": title,
                    "thumbnail": thumbnail,
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lyrics")
async def get_lyrics(video_id: str):
    try:
        watch_playlist = yt.get_watch_playlist(videoId=video_id)
        lyrics_id = watch_playlist.get("lyrics")
        if not lyrics_id:
            return {"status": "error", "message": "Lirik tidak ditemukan"}
        
        lyrics = yt.get_lyrics(lyrics_id)
        return {"status": "success", "data": lyrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/album")
async def get_album_info(browse_id: str):
    try:
        results = yt.get_album(browse_id)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
