import sys
import requests
import yt_dlp
import argparse
import subprocess
import re
import scrapetube

def find_youtube_urls(text):
    url_pattern = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    urls = re.findall(url_pattern, text)
    youtube_urls = ['https://www.youtube.com/watch?v=' + url[5] for url in urls]
    return youtube_urls

def resolve_url(url):
    print(f"Resolving non-canonical url {url}:")
    ydl_opts = {
        'simulate': True,
        'quiet': True,
        'extract_flat': True,
        'dump_single_json': True,
        'playlist_items': '1',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        print(info_dict['channel_url'])
        return info_dict['channel_url']

def request_transcription(video_url):
    url = "http://localhost:8080/requestYoutubeTranscription"
    data = {
        'username': 'your_username',  # replace with your username
        'apiKey': 'your_api_key',  # replace with your api key
        'requestedModel': 'large-v3',
        'jobType': 'public-youtube-video',
        'audioUrl': video_url
    }
    response = requests.post(url, json=data)
    print(response.json())

def process_file(file_path, skip_prompt): # TODO: clean up this function
    video_urls = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                if line.find("youtube.com/@"): # new-style URL; resolve
                    line = resolve_url(line)
                if line.find("/channel/"):
                    channel_id = line.split("/channel/")[1]
                    videos = scrapetube.get_channel(channel_id)
                    for video in videos:
                        individual_video_link = f"https://www.youtube.com/watch?v={video['videoId']}"
                        video_urls.append(individual_video_link)
                        print(individual_video_link)
                elif line.find("youtube.com/watch?v="):
                    print(line)
                    video_urls.append(line)
                elif line.find("youtube.com/playlist?list="):
                    playlist_id = line.split("youtube.com/playlist?list=")[1]
                    videos = scrapetube.get_playlist(playlist_id)
                    for video in videos:
                        individual_video_link = f"https://www.youtube.com/watch?v={video['videoId']}"
                        video_urls.append(individual_video_link)
                        print(individual_video_link)

    if not skip_prompt:
        prompt = input(f"Do you want to transcribe {len(video_urls)} videos for -1 kudos? [Y/n] ")
        if prompt.lower() != 'y':
            return
    for video_url in video_urls:
        request_transcription(video_url)

def convert_and_request_transcription(file_path):
    output_file = file_path.rsplit('.', 1)[0] + '.wav'
    subprocess.run(['ffmpeg', '-i', file_path, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', output_file])
    url = "http://localhost:8080/requestFileTranscription"
    with open(output_file, 'rb') as f:
        files = {'file': f}
        data = {
            'username': 'your_username',  # replace with your username
            'apiKey': 'your_api_key',  # replace with your api key
            'requestedModel': 'large-v3',
            'jobType': 'file'
        }
        response = requests.post(url, files=files, data=data)
        print(response.json())
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--video-list', '-l', help='file containing YouTube video links')
    group.add_argument('--video', '-v', help='YouTube video link')
    group.add_argument('--file', '-f', help='file to convert to WAV and transcribe')
    parser.add_argument('--skip-prompt', action='store_true', help='skip the prompt when using --video-list')
    args = parser.parse_args()

    if args.video_list:
        process_file(args.video_list, args.skip_prompt)
    elif args.video:
        request_transcription(args.video)
    elif args.file:
        convert_and_request_transcription(args.file)