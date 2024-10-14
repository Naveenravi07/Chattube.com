import sys
from youtube_transcript_api import YouTubeTranscriptApi


def get_video_id(url):
    if "youtu.be" in url:
        return url.split("/")[-1]
    elif "youtube.com" in url:
        return url.split("v=")[-1].split("&")[0]
    else:
        raise ValueError("Invalid YouTube URL")


def fetch_and_save_subtitles(video_url, language_code='en'):
    try:
        print(f"Fetching subtitles for video: {video_url}")
        video_id = get_video_id(video_url)

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print("Available transcript languages:")
        for transcript in transcript_list:
            print(f"- {transcript.language} ({transcript.language_code})")

        try:
            transcript = transcript_list.find_transcript([language_code])
        except:
            try:
                transcript = transcript_list.find_transcript(['en'])
                print(f"Requested language '{
                      language_code}' not found. Falling back to English.")
            except:
                transcript = transcript_list.find_generated_transcript(['en'])
                print("No manual captions found. Using auto-generated English captions.")

        subtitle_data = transcript.fetch()
        srt_subtitles = convert_to_srt(subtitle_data)
        filename = f"subtitles_{transcript.language_code}.srt"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(srt_subtitles)
        print(f"Subtitles saved to {filename}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


def convert_to_srt(subtitle_data):
    srt_output = ""
    for index, item in enumerate(subtitle_data, start=1):
        start_time = format_time(item['start'])
        end_time = format_time(item['start'] + item['duration'])
        text = item['text']
        srt_output += f"{index}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_output


def format_time(seconds):
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <youtube_url> [language_code]")
        sys.exit(1)

    video_url = sys.argv[1]
    language_code = sys.argv[2] if len(sys.argv) > 2 else 'en'

    fetch_and_save_subtitles(video_url, language_code)
