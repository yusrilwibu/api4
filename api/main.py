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
    """Get direct audio stream URL — mencoba 6 client YouTube berurutan untuk bypass bot detection"""
    url = f"https://music.youtube.com/watch?v={video_id}"
    
    # Urutan client yang dicoba: mediaconnect → ios → tv_html5 → web_safari → mweb → ios+mediaconnect
    clients_to_try = [
        ["mediaconnect"],
        ["ios"],
        ["tv_html5"],
        ["web_safari"],
        ["mweb"],
        ["ios", "mediaconnect"],
    ]
    
    last_error = ""
    for clients in clients_to_try:
        try:
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'extractor_args': {
                    'youtube': {
                        'player_client': clients
                    }
                }
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info.get('url', '')
                if stream_url:
                    return {
                        "status": "success",
                        "data": {
                            "url": stream_url,
                            "duration": info.get('duration', 0),
                            "title": info.get('title', ''),
                            "thumbnail": info.get('thumbnail', ''),
                        }
                    }
        except Exception as e:
            last_error = str(e)
            continue  # coba client berikutnya
    
    raise HTTPException(status_code=500, detail=f"All YouTube clients failed: {last_error}")

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
