# -*- coding: utf-8 -*-
import re
from textwrap import wrap
from traceback import format_exc

from natsort import natsorted
from PySide6 import QtCore, QtWidgets

from ..ui import resource_rc
from ..ui.multi_search_dialog import Ui_MultiSearchDialog


class MultiSearch(Ui_MultiSearchDialog, QtWidgets.QDialog):
    def __init__(self, channels_dbs, measurements, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowFlags(
            self.windowFlags()
            | QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowMinMaxButtonsHint
        )

        self.result = set()
        self.channels_dbs = channels_dbs
        self.measurements = measurements

        self.matches.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.apply_btn.clicked.connect(self._apply)
        self.add_btn.clicked.connect(self._add)
        self.cancel_btn.clicked.connect(self._cancel)
        self.show_measurement_list_btn.clicked.connect(self.show_measurement_list)

        self.search_box.editingFinished.connect(self.search_text_changed)
        self.match_kind.currentTextChanged.connect(self.search_box.textChanged.emit)

        self.setWindowTitle("Search & select channels")
        self.add_btn.setFocus()

    def search_text_changed(self):
        text = self.search_box.text().strip()
        if len(text) >= 2:
            if self.match_kind.currentText() == "Wildcard":
                pattern = text.replace("*", "_WILDCARD_")
                pattern = re.escape(pattern)
                pattern = pattern.replace("_WILDCARD_", ".*")
            else:
                pattern = text

            self.matches.clear()
            results = []

            try:
                pattern = re.compile(f"(?i){pattern}")
                for i, channels_db in enumerate(self.channels_dbs, 1):
                    match_results = [
                        f"{i:> 2}: {name}"
                        for name in channels_db
                        if pattern.fullmatch(name)
                    ]
                    results.extend(match_results)

            except Exception as err:
                self.status.setText(str(err))
            else:
                if results:
                    self.status.setText("")
                    self.matches.addItems(results)
                else:
                    self.status.setText("No match found")

        self.add_btn.setFocus()

    def _add(self, event):
        count = self.selection.count()
        names = set(self.selection.item(i).text() for i in range(count))

        to_add = set(item.text() for item in self.matches.selectedItems())

        names = names | to_add

        names = natsorted(names)

        self.selection.clear()
        self.selection.addItems(names)

        self.add_btn.setFocus()

    def _apply(self, event):
        count = self.selection.count()

        self.result = set()
        for i in range(count):
            text = self.selection.item(i).text()
            file_index, channel_name = [item.strip() for item in text.split(":")]
            file_index = int(file_index) - 1
            for entry in self.channels_dbs[file_index][channel_name]:
                self.result.add((file_index, entry))
        self.close()

    def _cancel(self, event):
        self.result = set()
        self.close()

    def show_measurement_list(self, event):
        info = []
        for i, name in enumerate(self.measurements, 1):
            info.extend(wrap(f"{i:> 2}: {name}", 120))

        QtWidgets.QMessageBox.information(
            self, "Measurement files used for comparison", "\n".join(info)
        )
