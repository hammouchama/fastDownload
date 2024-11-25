from flask import Flask, request, Response, jsonify, render_template
from yt_dlp import YoutubeDL
import io
import requests

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


def stream_youtube_video(video_url):
    try:
        # Use an in-memory buffer to avoid saving the file
        buffer = io.BytesIO()

        # Configure youtube_dl to write to the buffer
        ydl_opts = {
            "format": "best",  # Best quality
            "outtmpl": "-",  # Prevent saving to disk
            "noplaylist": True,  # Do not download playlists
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_stream_url = info["url"]

            return video_stream_url, info["title"]

    except Exception as e:
        raise ValueError(f"Failed to retrieve video: {e}")


@app.route("/download", methods=["POST"])
def download():
    data = request.json
    video_url = data.get("video_url")

    if not video_url:
        return jsonify({"error": "video_url is required"}), 400

    try:
        video_stream_url, title = stream_youtube_video(video_url)

        # Stream video content directly
        def generate_video_stream():
            with requests.get(video_stream_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=8192):
                    yield chunk

        response = Response(
            generate_video_stream(),
            content_type="video/mp4",
        )
        response.headers["Content-Disposition"] = f"attachment; filename={title}.mp4"
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
