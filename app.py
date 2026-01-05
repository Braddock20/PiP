import os
import tempfile
import yt_dlp
from flask import Flask, request, send_file, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super_secret_key_change_this")

def get_ydl_opts(format_type, quality):
    """
    Generate yt-dlp options based on user selection.
    """
    opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,  # Safe filenames
    }

    if format_type == 'audio':
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # Video formats
        if quality == 'best':
            opts['format'] = 'bestvideo+bestaudio/best'
        elif quality == '1080':
            opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif quality == '720':
            opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        else:
             opts['format'] = 'best'
        
        # Merge into mp4 for better compatibility
        opts['merge_output_format'] = 'mp4'

    return opts

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        format_type = request.form.get('format_type') # 'video' or 'audio'
        quality = request.form.get('quality') # 'best', '1080', '720'

        if not url:
            flash("Please provide a URL")
            return redirect(url_for('index'))

        try:
            # Create a temporary directory for this specific download
            # We use a context manager so it cleans up automatically after the block
            # BUT send_file needs the file to exist. 
            # Strategy: Download to temp, send_file with delete option (if supported) or risk temp usage.
            # Best practice for simple apps: Use a temp dir, stream file, then rely on OS to clean temp later
            # or use try/finally block with manual cleanup after sending (tricky in Flask).
            # Here we use proper temp directory management.
            
            temp_dir = tempfile.mkdtemp()
            
            ydl_opts = get_ydl_opts(format_type, quality)
            ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_filename = ydl.prepare_filename(info)
                
                # Handling post-processed filenames (e.g. mp3 changes extension)
                if format_type == 'audio':
                    base, _ = os.path.splitext(downloaded_filename)
                    downloaded_filename = base + ".mp3"
                elif ydl_opts.get('merge_output_format') == 'mp4':
                    base, _ = os.path.splitext(downloaded_filename)
                    downloaded_filename = base + ".mp4"

            if not os.path.exists(downloaded_filename):
                # Fallback search if exact name match failed due to yt-dlp quirks
                files = os.listdir(temp_dir)
                if files:
                    downloaded_filename = os.path.join(temp_dir, files[0])
                else:
                    raise Exception("File not found after download.")

            # Send file and trust OS/Server to clean up temp dir eventually, 
            # or use a scheduled task in production. 
            # For immediate response:
            return send_file(
                downloaded_filename, 
                as_attachment=True, 
                download_name=os.path.basename(downloaded_filename)
            )

        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    # Threaded=True helps prevent blocking on download
    app.run(debug=True, threaded=True)
          
