import sys

from orangewidget import gui,widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence
from oasys.widgets import widget as oasyswidget

from orangecontrib.comsyl.util.CompactAFReader import CompactAFReader

class OWCompactAFReader(oasyswidget.OWWidget):
    name = "CompactAFReader"
    description = "Utility: COMSYL mode reader"
    icon = "icons/CompactAFReader.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 9
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 0

    beam_file_name = Setting("../../workspaces/tmp20.h5")

    outputs = [{"name": "eigen-states",
                "type": CompactAFReader,
                "doc": "Coherent Modes Data",
                "id": "eigen-states"}, ]



    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Read COMSYL Results from Files", self)
        self.runaction.triggered.connect(self.read_file)
        self.addAction(self.runaction)

        self.setFixedWidth(590)
        self.setFixedHeight(150)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Files Selection", addSpace=True, orientation="vertical",
                                         width=570, height=60)

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=50)
        self.le_beam_file_name = oasysgui.lineEdit(figure_box, self, "beam_file_name", "COMSYL File Name Root",
                                                    labelWidth=120, valueType=str, orientation="horizontal")
        self.le_beam_file_name.setFixedWidth(330)
        gui.button(figure_box, self, "...", callback=self.selectFile)


        gui.separator(left_box_1, height=20)

        button = gui.button(self.controlArea, self, "Read COMSYL File", callback=self.read_file)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def selectFile(self):

        filename = oasysgui.selectFileFromDialog(self,
                previous_file_path=self.beam_file_name, message="Open COMSYL File [*.npy or *.npz or *.h5]",
                start_directory=".", file_extension_filter="*.*")

        self.le_beam_file_name.setText(filename)



    def read_file(self):
        self.setStatusMessage("")

        try:
            if congruence.checkFileName(self.beam_file_name):

                try:
                    reader = CompactAFReader.initialize_from_file(self.beam_file_name)
                except:
                    raise FileExistsError("Error loading COMSYL modes from file: %s"%self.beam_file_name)

                print("File %s:" % self.beam_file_name)
                print("contains")
                print("%i modes" % reader.number_modes())
                print("on the grid")
                print("x: from %e to %e" % (reader.x_coordinates().min(), reader.x_coordinates().max()))
                print("y: from %e to %e" % (reader.y_coordinates().min(), reader.y_coordinates().max()))
                print("Sending eigen-states")
                self.send("eigen-states", reader)
        except:
            raise Exception("Failed to read file %s"%self.beam_file_name)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication


    app = QApplication(sys.argv)
    w = OWCompactAFReader()
    w.beam_file_name = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.h5"
    w.show()
    app.exec()
    w.saveSettings()

