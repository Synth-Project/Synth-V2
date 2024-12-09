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
    with redirect_stdout(output), YoutubeDL(  # type: ignore
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


def mention_slash(guild: disnake.Guild, command_name: str) -> str | None:
    """
    Create a string in the format of a mention of a command
    that can be used to ping the command.

    :param guild: The guild that the command is in.
    :type guild: disnake.Guild
    :param command_name: The name of the command to ping.
    :type command_name: str
    :return: The string in the format of a mention of the command.
    :rtype: str | None
    """
    command_parts = command_name.split()
    command = guild.get_command_named(command_parts[0])
    if not command:
        return None

    command_name = " ".join(command_parts) if len(command_parts) > 1 else command_name

    return f"</{command_name}:{command.id}>"


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
