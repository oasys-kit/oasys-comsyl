
import os
import numpy

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence
from orangewidget import gui as orangegui

from comsyl.autocorrelation.CompactAFReader import CompactAFReader

class OWModesFileReader(widget.OWWidget):
    name = "Modes from COMSYL File"
    description = "Utility: COMSYL Modes File Reader"
    icon = "icons/file_reader.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 60
    category = "Utility"
    keywords = ["COMSYL", "coherent modes"]

    outputs = [{"name":"COMSYL modes",
                "type":CompactAFReader,
                "doc":"COMSYL modes",
                "id":"COMSYL modes"},]

    want_main_area = 0

    filename = Setting("")


    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Read COMSYL File", self)
        self.runaction.triggered.connect(self.read_file)
        self.addAction(self.runaction)

        self.setFixedWidth(590)
        self.setFixedHeight(150)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "COMSYL File Selection", addSpace=True, orientation="vertical",
                                         width=570, height=70)

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=35)

        self.le_beam_file_name = oasysgui.lineEdit(figure_box, self, "filename", "COMSYL File Name",
                                                    labelWidth=120, valueType=str, orientation="horizontal")
        self.le_beam_file_name.setFixedWidth(330)

        gui.button(figure_box, self, "...", callback=self.selectFile)

        #gui.separator(left_box_1, height=20)

        button = gui.button(self.controlArea, self, "Read COMSYL File", callback=self.read_file)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_beam_file_name.setText(oasysgui.selectFileFromDialog(self, self.filename, "Open COMSYL File"))

    def read_file(self):
        self.setStatusMessage("")
        filename = self.le_beam_file_name.text()
        if not os.path.exists(filename):
            raise Exception("File not found %s"%filename)

        try:
            if congruence.checkFileName(filename):

                try:
                    self.af = CompactAFReader.initialize_from_file(filename)
                except:
                    raise FileExistsError("Error loading COMSYL modes from file: %s"%filename)

        except:
            raise Exception("Failed to read file %s"%filename)

        self.send("COMSYL modes", self.af)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    a = QApplication(sys.argv)
    ow = OWModesFileReader()

    ow.filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.npy"

    ow.show()
    a.exec_()
