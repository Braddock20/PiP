import os
import tempfile
import yt_dlp
from flask import Flask, request, send_file, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret_key")

COOKIE_FILE = os.path.join(os.getcwd(), "cookies.txt")  # must exist in Netscape format

def get_ydl_opts(format_type, quality, output_template):
    opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }

    if os.path.exists(COOKIE_FILE):
        opts["cookiefile"] = COOKIE_FILE

    if format_type == "audio":
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        if quality == "1080":
            opts["format"] = "bestvideo[height<=1080]+bestaudio/best"
        elif quality == "720":
            opts["format"] = "bestvideo[height<=720]+bestaudio/best"
        else:
            opts["format"] = "bestvideo+bestaudio/best"
        opts["merge_output_format"] = "mp4"

    return opts

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        format_type = request.form.get("format_type", "video")
        quality = request.form.get("quality", "best")

        if not url:
            flash("Please provide a URL")
            return redirect(url_for("index"))

        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tmp_file.close()

            ydl_opts = get_ydl_opts(
                format_type,
                quality,
                tmp_file.name + ".%(ext)s"
            )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)

            if not os.path.exists(filepath):
                raise Exception("Downloaded file not found")

            return send_file(
                filepath,
                as_attachment=True,
                download_name=os.path.basename(filepath)
            )

        except Exception as e:
            flash(str(e))
            return redirect(url_for("index"))

    return render_template("index.html")


if __name__ == "__main__":
    # THIS MUST BE LAST — on its own line
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
