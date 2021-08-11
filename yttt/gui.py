"""
GUI for yttt.
"""
import datetime
import json
import logging
import sys

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QPushButton, QPlainTextEdit, \
    QVBoxLayout, QMainWindow, QLabel, QLineEdit, QHBoxLayout

from yttt.cli import main, summarize_history_stats


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self, json_filename, csv_filename, date_from, date_to):
        super().__init__()
        self.json_filename = json_filename
        self.csv_filename = csv_filename
        self.date_from = date_from
        self.date_to = date_to

    def run(self):
        try:
            main(
                self.json_filename,
                self.csv_filename,
                date_from=self.date_from,
            )
        except Exception as exc:
            logging.error(str(exc))


class App(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.json_filename = None
        self.csv_filename = None

        self.title = 'Youtube Time Tracking'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        label = HyperlinkLabel(self)
        label.setText('Please refer to <a href="https://github.com/itsupera/youtube_time_tracking#usage">' \
                       'this documentation</a> to get the "watch-history.json" file.')

        buttonJSON = QPushButton('Select "watch-history.json" file to use', self)
        buttonJSON.setToolTip('Open dialog to select JSON file')
        buttonJSON.clicked.connect(self.on_click_select_input)

        self.label_date_from = QLabel(self)
        self.label_date_from.setText("Date from:")
        self.textbox_date_from = QLineEdit(self)
        self.label_date_to = QLabel(self)
        self.label_date_to.setText("Date to:")
        self.textbox_date_to = QLineEdit(self)

        self.buttonCSV = QPushButton('Select CSV file to write to', self)
        self.buttonCSV.setDisabled(True)
        self.buttonCSV.setToolTip('Open dialog to select CSV to write')
        self.buttonCSV.clicked.connect(self.on_click_select_output)

        self.buttonGenerate = QPushButton('Generate file', self)
        self.buttonGenerate.setDisabled(True)
        self.buttonGenerate.setToolTip('Compute the stats and write the selected CSV file')
        self.buttonGenerate.clicked.connect(self.on_click_generate)

        logTextBox = QTextEditLogger(self)
        # log_fmt = '%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s'
        log_fmt = '%(asctime)s %(levelname)s > %(message)s'
        logTextBox.setFormatter(logging.Formatter(log_fmt))
        logging.getLogger().addHandler(logTextBox)
        logging.getLogger().setLevel(logging.DEBUG)

        layout_dates = QHBoxLayout()
        layout_dates.addWidget(self.label_date_from)
        layout_dates.addWidget(self.textbox_date_from)
        layout_dates.addWidget(self.label_date_to)
        layout_dates.addWidget(self.textbox_date_to)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(buttonJSON)
        layout.addLayout(layout_dates)
        layout.addWidget(self.buttonCSV)
        layout.addWidget(self.buttonGenerate)
        layout.addWidget(logTextBox.widget)
        # layout.addStretch()

        centralWidget.setLayout(layout)

        self.show()

    @pyqtSlot()
    def on_click_select_input(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "JSON file (*.json)", options=options)
        if not filename:
            return

        self.json_filename = filename
        with open(self.json_filename) as fd:
            history = json.load(fd)
        nb_videos, oldest_day, newest_day = summarize_history_stats(history)
        logging.info(f"Found {nb_videos} entries from {oldest_day} to {newest_day}")

        self.buttonCSV.setDisabled(False)
        oldest_day_dt = datetime.datetime.strptime(oldest_day, "%Y-%m-%d")
        newest_day_dt = datetime.datetime.strptime(newest_day, "%Y-%m-%d")
        one_month_before_newest_day_dt = newest_day_dt - datetime.timedelta(days=30)
        date_from = max(oldest_day_dt, one_month_before_newest_day_dt).strftime("%Y-%m-%d")
        self.textbox_date_from.setText(date_from)
        self.textbox_date_from.setDisabled(False)
        self.textbox_date_to.setText(newest_day)
        self.textbox_date_to.setDisabled(False)

    @pyqtSlot()
    def on_click_select_output(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "CSV file (*.csv)", options=options)
        if not filename:
            return

        self.csv_filename = filename
        self.buttonGenerate.setDisabled(False)

    @pyqtSlot()
    def on_click_generate(self):
        date_from = self.textbox_date_from.text()
        date_to = self.textbox_date_to.text()

        self.thread = QThread()
        self.worker = Worker(self.json_filename, self.csv_filename, date_from, date_to)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()


class HyperlinkLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__()
        self.setOpenExternalLinks(True)
        self.setParent(parent)


class QTextEditLogger(logging.Handler, QObject):
    appendPlainText = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__()
        QObject.__init__(self)
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.appendPlainText.connect(self.widget.appendPlainText)

    def emit(self, record):
        msg = self.format(record)
        self.appendPlainText.emit(msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
