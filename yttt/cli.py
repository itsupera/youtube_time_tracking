import csv
import datetime
import json
import logging
import os
import subprocess as sp
import sys
from collections import Counter, defaultdict
from tempfile import TemporaryDirectory
from typing import Optional

import typer


def typer_app(
    watch_history_json_filepath: str = typer.Argument(..., help="Path to the watch-history.json file"),
    output_filepath: str = typer.Argument(..., help="Path to write the CSV file to"),
    date_from: Optional[str] = typer.Option(None, help="YYYY-MM-DD formated date to filter history "
                                                       "from (must be before date_to)"),
    date_to: Optional[str] = typer.Option(None, help="YYYY-MM-DD formated date to filter history to "
                                                     "(default: today, must be after date_from)"),
):
    main(watch_history_json_filepath, output_filepath, date_from=date_from, date_to=date_to, interactive=True)


def main(
    watch_history_json_filepath,
    output_filepath,
    date_from=None,
    date_to=None,
    interactive=False,
):
    """
    Extract stats from your Youtube history and write a CSV file 
    with the total duration for each day and channel name.
    """
    logging.info("Starting...")

    if date_to:
        date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d")
    else:
        date_to = datetime.datetime.today()

    if date_from:
        date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d")
        if date_from > date_to:
            raise ValueError(f"date_from must be older than date_to ({date_to.strftime('%Y-%m-%d')}) !")
    elif interactive:
        confirm = input("No --date-from given, are you sure you want to compute stats "
                        "for your entire Youtube history ? (This may take a while) [Y/n]")
        if confirm.lower() != "y":
            sys.exit(0)

    with open(watch_history_json_filepath) as fd:
        history = json.load(fd)

    stats = defaultdict(lambda: Counter())
    stats_by_channel = Counter()

    with TemporaryDirectory(prefix="yttt_metadatas") as metadatas_fpath:
        for idx, entry in enumerate(history):
            dt = parse_entry_time(entry)
            if date_from and dt < date_from:
                break
            elif dt > date_to:
                continue

            url_path = entry['titleUrl']
            prefix_fpath = os.path.join(metadatas_fpath, f"{str(idx + 1).zfill(5)}")
            download_video_metadata(url_path, prefix_fpath)
            metadata_fpath = prefix_fpath + ".info.json"

            try:
                with open(metadata_fpath) as fd:
                    metadata = json.load(fd)

                channel_name = metadata['channel']
                duration_in_minutes = round(metadata['duration'] / 60)
                day = dt.strftime("%Y-%m-%d")
                stats[day][channel_name] += duration_in_minutes
                stats_by_channel[channel_name] += duration_in_minutes
            except FileNotFoundError:
                logging.warning(f"Could not retrieve stats for video {entry['titleUrl']}")

    if not date_from:
        date_from = dt

    dates = [
        (date_from + datetime.timedelta(days=x)).strftime("%Y-%m-%d")
        for x in range(0, (date_to - date_from).days + 1)
    ]

    sorted_channels = [x[0] for x in stats_by_channel.most_common()]
    columns = ["Day", "TOTAL"] + sorted_channels

    with open(output_filepath, "w") as fd:
        csv_writer = csv.DictWriter(fd, columns)
        csv_writer.writeheader()
        for day in dates:
            channel_to_duration = stats.get(day, {})
            row = {"Day": day, "TOTAL": sum(channel_to_duration.values()), **channel_to_duration}
            csv_writer.writerow(row)

    logging.info("DONE !")


def download_video_metadata(url_path, prefix_fpath):
    cmd = f'youtube-dl -o "{prefix_fpath}" --skip-download --write-info-json -i {url_path}'
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
    line = True
    while line:
        line = p.stdout.readline().decode("utf-8").strip()
        logging.info(line)


def summarize_history_stats(history):
    if not history:
        return "Empty watch history"

    nb_videos = len(history)
    oldest_day = parse_entry_time(history[-1]).strftime("%Y-%m-%d")
    newest_day = parse_entry_time(history[0]).strftime("%Y-%m-%d")
    return nb_videos, oldest_day, newest_day


def parse_entry_time(entry):
    return datetime.datetime.fromisoformat(entry['time'].rstrip("Z"))


if __name__ == "__main__":
    typer.run(typer_app)
