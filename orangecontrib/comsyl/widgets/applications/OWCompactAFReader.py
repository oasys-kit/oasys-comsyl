import os
import numpy
import sys

from PyQt4 import QtGui
from orangewidget import gui,widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence
from oasys.widgets import widget as oasyswidget

# import numpy
# from srxraylib.plot.gol import plot_image, plot
# import sys

from comsyl.scripts.CompactAFReader import CompactAFReader
from orangecontrib.comsyl.scripts.CompactH5Reader import CompactH5Reader


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

    beam_file_name = Setting("/Users/srio/OASYS_VE/oasys-comsyl/orangecontrib/comsyl/scripts/ph3_u18_3_17keV_s1.3_100modes.h5")

    outputs = [{"name": "eigen-states",
                "type": CompactAFReader,
                "doc": "Coherent Modes Data",
                "id": "eigen-states"}, ]



    def __init__(self):
        super().__init__()

        self.CompactReader = CompactH5Reader

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
                previous_file_path=self.beam_file_name, message="Open COMSYL File [*.npy or *.npz or h5]",
                start_directory=".", file_extension_filter="*.*")

        filename_witout_extension = ('.').join(filename.split('.')[:-1])
        file_extension = filename.split('.')[-1]

        print("File extension is: ",file_extension)

        if file_extension == "h5":
            self.CompactReader = CompactH5Reader
            self.le_beam_file_name.setText(filename)
        elif file_extension == "npy":
            self.CompactReader = CompactAFReader
            self.le_beam_file_name.setText(filename_witout_extension)
        elif file_extension == "npz":
            self.CompactReader = CompactAFReader
            self.le_beam_file_name.setText(filename_witout_extension)
        else:
            raise FileExistsError("Unknown file")



    def read_file(self):
        self.setStatusMessage("")

        try:
            if congruence.checkFileName(self.beam_file_name):

                try:
                    reader = self.CompactReader(self.beam_file_name)
                except:
                    raise FileExistsError("Error loading COMSYL modes from file: %s.npy .npz"%self.beam_file_name)

                print("File %s:" % self.beam_file_name)
                print("contains")
                print("%i modes" % reader.number_modes())
                print("on the grid")
                print("x: from %e to %e" % (reader.x_coordinates().min(), reader.x_coordinates().max()))
                print("y: from %e to %e" % (reader.y_coordinates().min(), reader.y_coordinates().max()))
                # print("calculated at %f eV" % reader.photon_energy())
                # print("with total intensity in (maybe improper) normalization: %e" % reader.total_intensity().real.sum())

                #
                #
                #
                # print("Occupation and max abs value of the mode")
                #
                # x = reader.x_coordinates()
                # y = reader.y_coordinates()
                #
                # eigenvalues = numpy.zeros(reader.number_modes())
                #
                # mystack = numpy.zeros((reader.number_modes(),y.size,x.size),dtype=complex)
                #
                # for i_mode in range(reader.number_modes()):
                #     eigenvalues[i_mode] = reader.occupation_number(i_mode)
                #     mode = reader.mode(i_mode)
                #     mystack[i_mode,:,:] = mode.T
                #
                #
                # return x,y,mystack, eigenvalues


                # reader.loadFromFile(self.beam_file_name)
                # reader.history.append(ShadowOEHistoryItem()) # fake Source
                # reader._oe_number = 0
                #
                # # just to create a safe history for possible re-tracing
                # reader.traceFromOE(reader, self.create_dummy_oe(), history=True)
                #
                # path, file_name = os.path.split(self.beam_file_name)
                #
                # self.setStatusMessage("Current: " + file_name)

                print("Sending eigen-states")
                self.send("eigen-states", reader)
        except Exception as exception:
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception), QtGui.QMessageBox.Ok)


if __name__ == "__main__":

    from PyQt4.QtGui import QApplication

    app = QApplication(sys.argv)
    w = OWCompactAFReader()
    w.show()
    app.exec()
    w.saveSettings()

