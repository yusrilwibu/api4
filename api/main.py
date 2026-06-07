from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp
import traceback

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
    """Get direct audio stream URL for a YouTube video ID.
    Tries multiple player clients to bypass YouTube bot protection."""
    
    errors = []
    
    # Try multiple player client combinations
    client_combos = [
        ['mediaconnect'],
        ['ios'],
        ['tv_html5'],
        ['web_safari'],
        ['mweb'],
        ['ios', 'mediaconnect'],
    ]
    
    for clients in client_combos:
        try:
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'extractor_args': {'youtube': {'player_client': clients}}
            }
            url = f"https://music.youtube.com/watch?v={video_id}"
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
                            "source": "youtube",
                            "client": ','.join(clients),
                        }
                    }
        except Exception as e:
            errors.append(f"{','.join(clients)}: {str(e)[:100]}")
            continue
    
    # All methods failed
    raise HTTPException(
        status_code=500,
        detail=f"All YouTube clients failed: {'; '.join(errors)}"
    )

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

@app.get("/api/home")
async def get_home():
    try:
        home = yt.get_home(limit=6)
        result = {}
        for section in home:
            title = section.get('title', 'Unknown')
            items = []
            for item in section.get('contents', []):
                if item.get('videoId'):
                    items.append({
                        'videoId': item.get('videoId', ''),
                        'title': item.get('title', 'Unknown'),
                        'artist': ', '.join([a['name'] for a in item.get('artists', [])]) if item.get('artists') else 'Unknown',
                        'thumbnail': item.get('thumbnails', [{}])[-1].get('url', '') if item.get('thumbnails') else '',
                    })
            if items:
                result[title] = items
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
