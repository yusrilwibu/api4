from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from ytmusicapi import YTMusic
import yt_dlp
import concurrent.futures

app = FastAPI(title="SANN404 FORUM Music API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yt = YTMusic()

# Global memory cache to store the last working client config
last_successful_client = ["mediaconnect"]

def try_client(clients, url):
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
                "url": stream_url,
                "duration": info.get('duration', 0),
                "title": info.get('title', ''),
                "thumbnail": info.get('thumbnail', ''),
                "client": clients
            }
    raise ValueError("No stream URL returned")

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
    """Get direct audio stream URL — paralel & caching client untuk load super cepat"""
    url = f"https://music.youtube.com/watch?v={video_id}"
    global last_successful_client
    
    # 1. Coba last successful client dulu secara sinkron (karena kemungkinan besar masih bekerja & sangat cepat)
    if last_successful_client:
        try:
            res = try_client(last_successful_client, url)
            return {"status": "success", "data": res}
        except Exception:
            pass
            
    # List client yang akan dicoba jika default/last sukses gagal
    clients_to_try = [
        ["mediaconnect"],
        ["android_vr"],
        ["ios"],
        ["tv_html5"],
        ["web_safari"],
        ["mweb"],
        ["android"],
        ["tv"],
        ["ios", "mediaconnect"]
    ]
    
    # Saring agar client yang sudah dicoba dan gagal tidak dicoba lagi di pool
    other_clients = [c for c in clients_to_try if c != last_successful_client]
    
    # 2. Jalankan sisa client secara paralel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(other_clients)) as executor:
        # Submit task untuk setiap client
        futures = {executor.submit(try_client, client, url): client for client in other_clients}
        
        # Tunggu sampai salah satu selesai dengan sukses
        done, not_done = concurrent.futures.wait(
            futures.keys(),
            return_when=concurrent.futures.FIRST_COMPLETED
        )
        
        # Cek mana yang sukses pertama kali
        for future in done:
            try:
                res = future.result()
                # Simpan client yang sukses ini ke global cache
                last_successful_client = res["client"]
                # Batalkan future lain yang belum berjalan/selesai
                for f in not_done:
                    f.cancel()
                return {"status": "success", "data": res}
            except Exception:
                pass
                
        # Jika task FIRST_COMPLETED ternyata gagal, tunggu task lainnya secara as_completed
        for future in concurrent.futures.as_completed(not_done):
            try:
                res = future.result()
                last_successful_client = res["client"]
                return {"status": "success", "data": res}
            except Exception:
                pass

    raise HTTPException(status_code=500, detail="All YouTube clients failed to extract stream URL.")

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
