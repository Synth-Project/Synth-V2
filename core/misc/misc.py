from io import BytesIO

from wavelink import Playable
from yt_dlp import YoutubeDL


def download_track(track: Playable, output: BytesIO) -> None:
    with YoutubeDL(
        {
            "extract_audio": True,
            "format": "bestaudio",
            "outtmpl": f"{track.title}.mp3",
            "postprocessors": [],
        }
    ) as ydl:
        info = ydl.extract_info(track.uri, download=True)
        filename = ydl.prepare_filename(info)

        with open(filename, "rb") as f:
            output.write(f.read())

        output.seek(0)
        return
