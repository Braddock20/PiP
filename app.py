import os
import tempfile
import yt_dlp
from flask import Flask, request, send_file, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret_key")

# ===========================
# Paste your full cookies string here
COOKIES_STRING = """
GPS=1;__Secure-ROLLOUT_TOKEN=COei_smPx76MHBD3tLG84PSRAxjqyLPW4PSRAw%3D%3D;__Secure-1PSIDTS=sidts-CjUBflaCdb5WSKRbZp8XobRys1NHF1_x714gstAYsM6N_UrrpWSQgsnupcBzb9wEUjporkn4JBAA;__Secure-3PSIDTS=sidts-CjUBflaCdb5WSKRbZp8XobRys1NHF1_x714gstAYsM6N_UrrpWSQgsnupcBzb9wEUjporkn4JBAA;HSID=Aw0LkvpGUkVN04MGY;SSID=As1wBIMR5iPLlUVGY;APISID=HzcZ7aFjIMkkSzsD/ABmyDjUEBbxjG5PUV;SAPISID=uz6BMzl8f2yKL_9A/A-wkPFVcRmZLZ-LcG;__Secure-1PAPISID=uz6BMzl8f2yKL_9A/A-wkPFVcRmZLZ-LcG;__Secure-3PAPISID=uz6BMzl8f2yKL_9A/A-wkPFVcRmZLZ-LcG;SID=g.a0005QgTcXFGyUBZG6Nakpoa0VOUaBOrl3X9aBOlWHEqzAALgrJrFkuWoRVIoeqHsNaGl8DxhgACgYKAYwSARcSFQHGX2MiELxLUsNRKDcvZPDhnYpaBBoVAUF8yKpoMO7OeyGGuLzYcR6Jd_Mq0076;__Secure-1PSID=g.a0005QgTcXFGyUBZG6Nakpoa0VOUaBOrl3X9aBOlWHEqzAALgrJrT_BAbY__PrqjL7jgihsT2wACgYKAdUSARcSFQHGX2MimdSDm8BN_GL4rOAHYwlO_RoVAUF8yKoHOl29zzLl_uRZMz1Qo_5o0076;__Secure-3PSID=g.a0005QgTcXFGyUBZG6Nakpoa0VOUaBOrl3X9aBOlWHEqzAALgrJr-7ZPHQYsIA3IPXpjLUL97AACgYKAYcSARcSFQHGX2MibmvqIVYyMwYn3TazRtAVJRoVAUF8yKpxoRsgbnVDoLlNYRmnhxIc0076;LOGIN_INFO=AFmmF2swRgIhAKLll54KwMemgCCD6NpZWFvwylqdutaTwx_HwEavOzqpAiEAgC_5vh_7vlM3luUuLDw7GUpwj6glhxvDHAEBaJeReKE:QUQ3MjNmek1xZTJtNzg4UERsTjYtUVB6OXNRQVVmT1RmMVlnblhBRG4wT2RCTFVNa2ZkdTB6NXVuWXVuUnp4Z3V0Q3NWdXRVNkRpQThzVlZtWGNoamlQQXppSE02cVFFRkQtby0yRjVxNk9EdHoxNnBkZFdNTE5DcDZwTFVsZndDZWZNeWpHQTRfZDExTnZHSTNWWjFmQ25OM2NzZXdFUDZn;ST-30qypu=csn=8htoHZG5EptJ0nSe&itct=CIUBEIf2BBgBIhMI3_Cy3OH0kQMVzEP-BR0KNQaWWg9GRXdoYXRfdG9fd2F0Y2iaAQUIJBCOHsoBBF5fIt8%3D;ST-u9c8ui=csn=8htoHZG5EptJ0nSe&itct=CFwQ_FoiEwjf8LLc4fSRAxXMQ_4FHQo1BpYyCmctaGlnaC1yZWNaD0ZFd2hhdF90b193YXRjaJoBBhCOHhieAcoBBF5fIt8%3D;YSC=ZPrtAa2jnIw;VISITOR_INFO1_LIVE=UwQnf06xPE4;VISITOR_PRIVACY_METADATA=CgJLRRIEGgAgGg%3D%3D;PREF=f6=40000000&tz=Africa.Nairobi;SIDCC=AKEyXzUFZEKl9r2Sl3UYowr1_Z6zcH_7WlJ00f187IQ5aW7gXvmWmE7ke6-iFDYodwsebT3NrA;__Secure-1PSIDCC=AKEyXzVPBV2mqVl6_Z66kl1CW2tDneiE4AmjwRkZa8HZS7jnbTFmUDby1QpgMvzHEEs-M5HbdQ;__Secure-3PSIDCC=AKEyXzWp0YXNVHEW7shtm01kxaIfhCm6ElDNGzhzG5gH_1q5mdVQTBR1ilzAq2W7bl6c72d8;
"""
# ===========================

COOKIE_FILE_PATH = os.path.join(os.getcwd(), "cookies.txt")
with open(COOKIE_FILE_PATH, "w") as f:
    # Convert semicolon-separated cookies into line-separated for yt-dlp
    for cookie in COOKIES_STRING.strip().split(";"):
        cookie = cookie.strip()
        if cookie:
            f.write(cookie + "\n")


def get_ydl_opts(format_type, quality, output_template):
    opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
    }

    if os.path.exists(COOKIE_FILE_PATH):
        opts["cookiefile"] = COOKIE_FILE_PATH

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
                if "requested_downloads" in info:
                    filepath = info["requested_downloads"][0]["filepath"]
                else:
                    filepath = ydl.prepare_filename(info)

            if not os.path.exists(filepath):
                raise Exception("Downloaded file not found")

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
