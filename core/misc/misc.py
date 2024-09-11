from io import BytesIO
from contextlib import redirect_stdout

import disnake
from wavelink import Playable
from yt_dlp import YoutubeDL


def download_track(track: Playable, output: BytesIO) -> int:
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


def create_ping_command_string(command_name: str, guild: disnake.Guild) -> str:
    """
    Create a string to ping a command in a message.
    :param command_name: The name of the command.
    :param guild: The guild to get the command from.
    :return: A string to ping the command.
    """
    command = guild.get_command_named(command_name)
    return "</{}:{}:>".format(command.name, command.id)


def shorten_text(text: str, max_length: int = 75) -> str:
    """
    Shorten a given text to a certain length.

    If the text is longer than the given length, it will be shortened
    to the given length and "..." will be appended to the end.

    Parameters:
    text (str): The text to shorten.
    max_length (int): The maximum length of the text.

    Returns:
    str: The shortened text.
    """
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text
