import os
import tempfile
import yt_dlp
from flask import Flask, request, send_file, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret_key")


def get_ydl_opts(format_type, quality, output_template):
    opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }

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
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()

            ydl_opts = get_ydl_opts(
                format_type,
                quality,
                tmp.name + ".%(ext)s"
            )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if "requested_downloads" in info:
                    filepath = info["requested_downloads"][0]["filepath"]
                else:
                    filepath = ydl.prepare_filename(info)

            if not os.path.exists(filepath):
                raise Exception("File not found after download")

            return send_file(
                filepath,
                as_attachment=True,
                download_name=os.path.basename(filepath)
            )

        except Exception as e:
            print("ERROR:", e)
            flash(str(e))
            return redirect(url_for("index"))

    return render_template("index.html")


# 🚨 DO NOT ADD ANYTHING AFTER THIS
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
