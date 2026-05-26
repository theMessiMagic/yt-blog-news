import os
import json
import datetime
from dotenv import load_dotenv
import googleapiclient.discovery
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = "UCIgnGlGkVRhd4qNFcEwLL4A"

youtube = googleapiclient.discovery.build(
    "youtube",
    "v3",
    developerKey=YOUTUBE_API_KEY
)

STATE_FILE = "state.json"
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)


def get_last_video():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as f:
        return json.load(f).get("last_video")


def save_last_video(video_id):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_video": video_id}, f)


def get_latest_video():

    response = youtube.search().list(
        part="snippet",
        channelId=CHANNEL_ID,
        order="date",
        maxResults=1,
        type="video"
    ).execute()

    item = response["items"][0]

    return item["id"]["videoId"]

def get_video_details(video_id):

    response = youtube.videos().list(
        part="snippet",
        id=video_id
    ).execute()

    item = response["items"][0]

    snippet = item["snippet"]

    title = snippet["title"]

    thumbnail = (
        snippet["thumbnails"]
        .get("high", {})
        .get("url", "")
    )

    return {
        "title": title,
        "thumbnail": thumbnail
    }

def get_transcript(video_id):

    try:
        transcript = YouTubeTranscriptApi().fetch(
            video_id,
            languages=['en', 'en-IN']
        )

        return " ".join(
            item["text"]
            for item in transcript.to_raw_data()
        )

    except Exception as e:
        print("Transcript Error:", e)
        return None
    
def generate_article(transcript):

    prompt = f"""
You are a professional AI news journalist.

Convert this transcript into a professional AI news article.

Return EXACTLY in this format:

TITLE:
<seo headline>

SUMMARY:
<3-5 sentence summary>

ARTICLE:
<600-1000 word article>

TAGS:
<tag1, tag2, tag3, tag4, tag5>

TRANSCRIPT:

{transcript[:25000]}
"""

    result = model.invoke(prompt)

    return result.content

def save_article(video_id, article):

    details = get_video_details(video_id)

    os.makedirs("articles", exist_ok=True)

    data = {
        "video_id": video_id,
        "title": details["title"],
        "thumbnail": details["thumbnail"],
        "article": article,
        "created_at": datetime.datetime.now().isoformat()
    }

    filename = f"articles/{video_id}.json"

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"Saved article: {filename}")


latest_video = get_latest_video()
last_video = get_last_video()

print("Latest:", latest_video)
print("Saved:", last_video)

if latest_video != last_video:

    print("NEW VIDEO FOUND")

    transcript = get_transcript(latest_video)

    if transcript:

        print("Transcript Length:", len(transcript))

        print("Generating article...")

        article = generate_article(transcript)

        save_article(
            latest_video,
            article
        )

        print("\n====================\n")
        print(article[:1500])
        print("\n====================\n")

    save_last_video(latest_video)

else:
    print("No new upload")
    
    
