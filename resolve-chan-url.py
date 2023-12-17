import yt_dlp

def resolve_url(url):
    ydl_opts = {
        'simulate': True,
        'quiet': True,
        'extract_flat': True,
        'dump_single_json': True,
        'playlist_items': '1',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        return info_dict['channel_url']

# Test the function
print(resolve_url('https://www.youtube.com/@skysports'))