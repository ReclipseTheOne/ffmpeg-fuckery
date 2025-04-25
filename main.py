import pathlib
import ffmpeg
import yt_dlp
import re

from math import floor
from rites.rituals.printer import Printer

yt = yt_dlp.YoutubeDL()
p = Printer()
p.add_style("option", "OPT", 255, 218, 117)

dict_conversions = {
    1: "MP3",
    2: "MP4",
    3: "GIF",
    4: "Exit"
}


def getSecondsFromStream(file_choice: pathlib.WindowsPath, stream: int) -> int:
    duration = ffmpeg.probe(file_choice)['streams'][stream]['tags']['DURATION']
    (h, m, s) = duration.split(":")
    return int(h) * 3600 + int(m) * 60 + int(floor(float(s)))


def getIntInput(prompt: str, verifier) -> int:
    while True:
        try:
            value = int(input(prompt))
            if verifier(value):
                return value
            else:
                p.print_error("Invalid input. Please try again.")
        except ValueError:
            p.print_error("Invalid input. Please enter a number.")


def getStrInput(prompt: str, verifier) -> str:
    while True:
        try:
            value = input(prompt)
            if verifier(value):
                return value
            else:
                p.print_error("Invalid input. Please try again.")
        except ValueError:
            p.print_error("Invalid input. Please enter a number.")


linkRegex = r"(https?://)?(www\.)?youtube\.(com|org|net|co\.uk)"
shortLinkRegex = r"(https?://)?(www\.)?youtu\.be"


def getExtension(path: pathlib.WindowsPath) -> str:
    return path.suffix


def main():
    p.print_info("FFMPEG FUCKERY")

    # Search for all the files in the current directory
    current_directory = pathlib.Path(__file__).parent / "input"

    paths = [path for path in current_directory.glob("*")]

    # Create a dictionary with the index as keys
    dict_paths = {index: path for index, path in enumerate(paths)}


    # ==== PRINT OPTIONS ====
    for index, path in dict_paths.items():
        p.print_custom("option", f"{index}. {path}")
    p.print_custom("option", f"{int(len(dict_paths.keys())) + 1}. Download from YouTube")


    # ==== FILE CHOICE ====
    choice = getIntInput(">", lambda x: x in dict_paths.keys() or x == (int(len(dict_paths.keys())) + 1))

    if choice == (int(len(dict_paths.keys())) + 1):
        while True:
            returnStr = downloadFromYT()
            if returnStr == "":
                main()
                return
    else:
        file_choice = dict_paths[choice]

    ext = file_choice.suffix


    # ==== PRINT PROCESSES ====
    p.print_info(f"Selected file: {file_choice}")
    p.print_custom("option", "1. Conversion\n2. Remove Audio\n3. Extract Audio\n4. Extract Audio - Keep Ext\n5. Trim\n6. Exit")


    # ==== PROCESSING ====
    process_choice = getIntInput(">", lambda x: x in {1, 2, 3, 4, 5, 6})
    if process_choice == 6:
        return

    if process_choice == 1:
        p.print_info(f"Conversing {file_choice} to:")

        for index, conversion in dict_conversions.items():
            p.print_custom("option", f"{index}. {conversion}")

        conversion_choice = getIntInput(">", lambda x: dict_conversions.keys().__contains__(x))
        if dict_conversions[conversion_choice] == "Exit":
            return

        p.print_info(f"Converting {ext} to {dict_conversions[conversion_choice]}")
        output_path = pathlib.Path(__file__).parent / "output" / f"{file_choice.stem}.{dict_conversions[conversion_choice].lower()}"
        ffmpeg.input(file_choice).output(str(output_path)).run()

    elif process_choice == 2:
        output_path = pathlib.Path(__file__).parent / "output" / f"{file_choice.stem}_noaudio{ext}"
        ffmpeg.input(file_choice).output(str(output_path), **{"c:a": "copy", "c:v": "copy", "an": None}).run()

    elif process_choice == 3:
        output_path = pathlib.Path(__file__).parent / "output" / f"{file_choice.stem}_audio.mp3"
        ffmpeg.input(file_choice).output(str(output_path), **{"vn": None}).run()

    elif process_choice == 4:
        output_path = pathlib.Path(__file__).parent / "output" / f"{file_choice.stem}_audio.mp4"
        ffmpeg.input(file_choice).output(str(output_path), **{"vn": None, "c:v": "copy"}).run()

    elif process_choice == 5:
        s = getSecondsFromStream(file_choice, 0)
        duration = s

        m = s // 60
        h = m // 60
        if (duration >= 3600):
            m = m % 60
            s = s % 60
            p.print_info(f"Selected file has a play time of: {duration} seconds / {h}:{m}:{s}")
        elif (duration >= 60):
            s = s % 60
            p.print_info(f"Selected file has a play time of: {duration} seconds / {m}:{s}")
        elif (duration == 1):
            p.print_info(f"Selected file has a play time of: {duration} second")
        else:
            p.print_info(f"Selected file has a play time of: {duration} seconds")

        start_time = getIntInput("Start time (in seconds): ", lambda x: {
            duration > x >= 0
        })
        end_time = getIntInput("End time (in seconds): ", lambda x: {
            duration >= x > start_time
        })

        output_path = pathlib.Path(__file__).parent / "output" / f"{file_choice.stem}_trimmed{ext}"
        ffmpeg.input(file_choice, ss=start_time, to=end_time).output(str(output_path)).run()


def downloadFromYT() -> str:
    yt = yt_dlp.YoutubeDL()
    link = input("Enter the link (leave empty to close): ")
    if link == "":
        return ""
    if not (re.match(linkRegex, link) or re.match(shortLinkRegex, link)):
        p.print_error("Invalid link. Please try again.")
        return "Invalid Link"

    info = yt.extract_info(link, download=False)
    title = info["title"]
    p.print_info(f"Downloading {title} - Transfering to Input")

    output = pathlib.Path(__file__).parent / "input" / f"{title}.mp4"
    yt_opts = {
        'outtmpl': str(output)
    }
    yt = yt_dlp.YoutubeDL(yt_opts)

    yt.download([link])


if __name__ == "__main__":
    main()
