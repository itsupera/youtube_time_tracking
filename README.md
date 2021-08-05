Youtube Time Tracking
======================

Script to compute stats on how much time you watched Youtube, aggregated by day and channel name.

The output is a CSV file, which will look like this:
```
Day,TOTAL,YUYUの日本語Podcast,マコなり社長,Teppei,Nihongo SWiTCH
2021-07-29,36,20,,16,
2021-07-30,52,20,18,,14
2021-07-31,0,,,,
```

Setup
------

Tested on Ubuntu Linux, should work on other platforms supporting Python

```bash
sudo apt install python3-virtualenv
virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

(Optional) To build a standalone executable for the application:
```bash
pip3 install nuitka
python3 -m nuitka --plugin-enable=pyqt5 --onefile yttt_qt.py
./yttt_qt.bin
```

Usage
------

Run `python3 yttt_q3.py`

**IMPORTANT**: To use this, you first need go to https://takeout.google.com to extract "YouTube and YouTube Music" for your account.

Make sure you click "Multiple formats" and choose JSON instead of HTML for the "History" entry.

Extract the zip file, it should contain the file `takeout/YouTube and YouTube Music/history/watch-history.json`
which you will give to the script.