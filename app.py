from flask import Flask, request, Response, jsonify, render_template, make_response
from yt_dlp import YoutubeDL
import io
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
)


@app.route("/")
@limiter.limit("10 per minute")
def index():
    return render_template("index.html")


def stream_media(video_url, media_type):
    """
    Extracts the direct URL for video or audio based on user choice.
    """
    try:
        # Choose the format based on media_type
        format_choice = "best" if media_type == "video" else "bestaudio/best"

        ydl_opts = {
            "format": format_choice,
            "noplaylist": True,
            "quiet": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            stream_url = info.get("url")
            title = info.get("title", "media")

            if not stream_url:
                raise ValueError("Failed to retrieve a valid stream URL.")

            return stream_url, title

    except Exception as e:
        raise ValueError(f"Failed to retrieve media: {e}")


@app.route("/download", methods=["POST"])
@limiter.limit("5 per minute")
def download():
    data = request.json
    video_url = data.get("video_url")
    media_type = data.get("media_type")

    if not video_url or not media_type:
        return jsonify({"error": "video_url and media_type are required"}), 400

    try:
        stream_url, title = stream_media(video_url, media_type)

        # Stream video/audio content directly
        def generate_stream():
            with requests.get(stream_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=8192):
                    yield chunk

        response = Response(
            generate_stream(),
            content_type="video/mp4" if media_type == "video" else "audio/mpeg",
        )
        file_extension = "mp4" if media_type == "video" else "mp3"
        response.headers["Content-Disposition"] = (
            f"attachment; filename={title}.{file_extension}"
        )
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
