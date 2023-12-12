import requests
import yt_dlp
from faster_whisper import WhisperModel
import tempfile
import base64
import psutil
import time
import datetime
import os
from icecream import ic

def download_audio(video_url, output_dir):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'noplaylist': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def transcribe_audio(audio_file, job_id, model_size="small"):
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_file, beam_size=5)
    transcriptions = ["WEBVTT\n"]
    for segment in segments:
        start_time = str(datetime.timedelta(seconds=segment.start))
        end_time = str(datetime.timedelta(seconds=segment.end))
        transcript_string = f"{start_time} --> {end_time}\n{segment.text}\n"
        transcriptions.append(transcript_string)
        print(transcript_string)
        transcript_base64 = base64.b64encode('\n'.join(transcriptions).encode()).decode()

        requests.post('http://localhost:8080/updateJobProgress', json={
            'workerName': 'exampleWorker',
            'apiKey': 'exampleKey',
            'progress': 50,  # Replace with your own progress estimation logic
            'cpuLoad': get_cpu_load(),
            'workerType': 'cpu',
            'transcript': transcript_base64,
            'jobIdentifier': job_id
        })
    return '\n'.join(transcriptions)

def get_cpu_load():
    return psutil.cpu_percent(interval=1)

def main():
    
    while True:
        response = requests.post('http://localhost:8080/workerGetJob', json={
            'workerName': 'exampleWorker',
            'apiKey': 'exampleKey',
            'workerType': 'cpu'
        })

        data = response.json()
        job_type = data.get('jobType')

        if job_type == 'none':
            ic("API server has nothing for us to do")
            time.sleep(1)
            continue

        if job_type == 'public-youtube-video':
            audio_url = data.get('audioUrl')
            requested_model = data.get('requestedModel')
            job_id = data.get('jobIdentifier')


            with tempfile.TemporaryDirectory() as tmp_dir:
                download_audio(audio_url, tmp_dir)
                for audio_file in os.listdir(tmp_dir):
                    transcript = transcribe_audio(os.path.join(tmp_dir, audio_file), job_id, requested_model)
                    transcript_base64 = base64.b64encode(transcript.encode()).decode()

                    requests.post('http://localhost:8080/uploadCompletedJob', json={
                        'workerName': 'exampleWorker',
                        'apiKey': 'exampleKey',
                        'cpuLoad': get_cpu_load(),
                        'workerType': 'cpu',
                        'transcript': transcript_base64,
                        'jobIdentifier': job_id
                    })
        

if __name__ == "__main__":
    main()