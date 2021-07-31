import csv
import datetime
import json
import os
import subprocess as sp
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional

import typer


def main(
    watch_history_json_filepath: str = typer.Argument(..., help="Path to the watch-history.json file"),
    output_filepath: str = typer.Argument(..., help="Path to write the CSV file to"),
    date_from: Optional[str] = typer.Option(None, help="YYYY-MM-DD formated date to filter history "
                                                       "from (must be before date_to)"),
    date_to: Optional[str] = typer.Option(None, help="YYYY-MM-DD formated date to filter history to "
                                                     "(default: today, must be after date_from)"),
):
    """
    Extract stats from your Youtube history and write a CSV file 
    with the total duration for each day and channel name.
    """
    if date_to:
        date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d")
    else:
        date_to = datetime.datetime.today()

    if date_from:
        date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d")
        if date_from > date_to:
            raise ValueError(f"date_from must be older than date_to ({date_to.strftime('%Y-%m-%d')}) !")
    else:
        confirm = input("No --date-from given, are you sure you want to compute stats for your entire Youtube history ? "
                        "(This may take a while) [Y/n]")
        if confirm.lower() != "y":
            sys.exit(0)

    with open(watch_history_json_filepath) as fd:
            history = json.load(fd)

    stats = defaultdict(lambda: Counter())
    stats_by_channel =  Counter()

    metadatas_fpath = "metadatas"
    Path(metadatas_fpath).mkdir(exist_ok=True, parents=True)

    for idx, entry in enumerate(history):
        dt = datetime.datetime.fromisoformat(entry['time'].rstrip("Z"))
        if date_from and dt < date_from:
            break
        elif dt > date_to:
            continue

        url_path = entry['titleUrl']
        prefix_fpath = os.path.join(metadatas_fpath, f"{str(idx + 1).zfill(5)}")
        download_video_metadata(url_path, prefix_fpath)
        metadata_fpath = prefix_fpath + ".info.json"

        with open(metadata_fpath) as fd:
            metadata = json.load(fd)

        channel_name = metadata['channel']
        duration_in_minutes = round(metadata['duration'] / 60)
        day = dt.strftime("%Y-%m-%d")
        stats[day][channel_name] += duration_in_minutes
        stats_by_channel[channel_name] += duration_in_minutes

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


def download_video_metadata(url_path, prefix_fpath):
    cmd = f'youtube-dl -o "{prefix_fpath}" --skip-download --write-info-json -i {url_path}'
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
    line = True
    while line:
        line = p.stdout.readline().decode("utf-8").strip()
        print(line)


if __name__ == "__main__":
    typer.run(main)
