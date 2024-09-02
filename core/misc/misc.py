from io import BytesIO
from contextlib import redirect_stdout

from wavelink import Playable
from yt_dlp import YoutubeDL


def download_track(track: Playable, output: BytesIO) -> None:
    """
    Download a track.
    :param track: The track to download.
    :param output: The output stream.
    :return: None
    """
    with redirect_stdout(output), YoutubeDL(
        {
            "extract_audio": True,
            "format": "bestaudio",
            "outtmpl": f"-",
            "logtostderr": True,
            "postprocessors": [],
        }
    ) as ydl:
        ydl.download([track.uri])

        return output.seek(0)
