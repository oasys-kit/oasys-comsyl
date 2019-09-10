import os
import numpy

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence


from comsyl.autocorrelation.CompactAFReader import CompactAFReader
from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D


class OWModesFileWriter(widget.OWWidget):
    name = "Modes to File"
    description = "Utility: COMSYL Modes File Writer"
    icon = "icons/file_writer.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 61
    category = "Utility"
    keywords = ["COMSYL", "coherent modes"]

    want_main_area = 0

    file_name = Setting("tmp.h5")
    index_format = Setting("%04d")
    is_automatic_run= Setting(1)
    TYPE_OF_OUTPUT = Setting(1) # 'COMSYL hdf5 with multi-mode','WOFRY hdf5 with multi-mode','WOFRY multiple files'
    ALL_MODES = Setting(0)
    MODE_TO = Setting(10)

    inputs = [("COMSYL modes" , CompactAFReader, "setCompactAFReader" )]


    af = None

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Write HDF5 File", self)
        self.runaction.triggered.connect(self.write_file)
        self.addAction(self.runaction)

        self.setFixedWidth(590)
        self.setFixedHeight(500)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "HDF5 File Selection", addSpace=True, orientation="vertical",
                                         width=570, height=400)

        gui.checkBox(left_box_1, self, 'is_automatic_run', 'Automatic Execution')

        gui.separator(left_box_1, height=10)

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=50)


        #
        #
        #
        self.le_file_name = oasysgui.lineEdit(figure_box, self, "file_name", "Output File Name",
                                                    labelWidth=120, valueType=str, orientation="horizontal")
        self.le_file_name.setFixedWidth(330)


        gui.button(figure_box, self, "...", callback=self.selectFile)

        gui.separator(left_box_1, height=10)


        #
        #
        #

        gui.comboBox(left_box_1, self, "TYPE_OF_OUTPUT", label=" Type of output file", labelWidth=260,
                     items=['COMSYL hdf5 with multi-mode','WOFRY hdf5 with multi-mode','WOFRY multiple files'],
                     #callback=self.set_Propagator,
                     sendSelectedValue=False, orientation="horizontal")

        self.le_index_format = oasysgui.lineEdit(left_box_1, self, "index_format", "index format [for individual files]",
                                                    labelWidth=200, valueType=str, orientation="horizontal")
        gui.separator(left_box_1, height=10)



        #
        #
        #
        gui.comboBox(left_box_1, self, "ALL_MODES", label=" Modes to write", labelWidth=260,
                     items=['Selected modes','All modes'],
                     #callback=self.set_Propagator,
                     sendSelectedValue=False, orientation="horizontal")


        oasysgui.lineEdit(left_box_1, self, "MODE_TO", "To mode index:",
                                                    labelWidth=200, valueType=int, orientation="horizontal")

        gui.separator(left_box_1, height=10)
        #
        #
        #
        button = gui.button(self.controlArea, self, "Write File", callback=self.write_file)
        button.setFixedHeight(45)
        self.le_index_format.setFixedWidth(330)

        gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_file_name.setText(oasysgui.selectFileFromDialog(self, self.file_name, "Open HDF5 File"))

    def setCompactAFReader(self, data):
        if not data is None:
            self.af = data

            if self.is_automatic_run:
                self.write_file()


    def write_file(self):
        self.setStatusMessage("")

        try:
            if not self.af is None:
                congruence.checkDir(self.file_name)


                if self.TYPE_OF_OUTPUT == 0: # ['COMSYL hdf5 with multi-mode','WOFRY hdf5 with multi-mode','WOFRY multiple files'
                    if self.ALL_MODES:
                        self.af.write_h5(self.file_name,maximum_number_of_modes=None)
                    else:
                        self.af.write_h5(self.file_name,maximum_number_of_modes=self.MODE_TO)
                        path, file_name = os.path.split(self.file_name)
                        self.setStatusMessage("File Out: " + file_name)
                else: # WOFRY
                    if self.ALL_MODES == 0 and (self.MODE_TO < self.af.number_of_modes()):
                        nmax = self.MODE_TO
                    else:
                        nmax = self.af.number_of_modes()

                    for i in range(nmax+1):
                        eigenvalue = numpy.real(self.af.eigenvalue(i),)
                        eigenfunction = self.af.mode(i)
                        w = GenericWavefront2D.initialize_wavefront_from_arrays(
                            self.af.x_coordinates(), self.af.y_coordinates(),
                            eigenfunction*numpy.sqrt(eigenvalue))
                        w.set_photon_energy(self.af.photon_energy() )


                        if self.TYPE_OF_OUTPUT == 1: #
                            file_name = self.file_name
                            subgroupname = "mode"+self.index_format%(i)
                            overwrite = False
                        elif self.TYPE_OF_OUTPUT == 2:
                            subgroupname = "mode"+self.index_format%(i)
                            file_name = self.file_name.split(".")[0]+"_"+(self.index_format%i)+".h5"
                            overwrite = True

                        if i==0:
                            w.save_h5_file(file_name,subgroupname=subgroupname,intensity=True,phase=True,overwrite=True)
                        else:
                            w.save_h5_file(file_name,subgroupname=subgroupname,intensity=True,phase=True,overwrite=overwrite)
                        path, file_name = os.path.split(file_name)
                        self.setStatusMessage("File Out: " + file_name)



                # path, file_name = os.path.split(self.file_name)

                # self.setStatusMessage("File Out: " + file_name)

            else:
                QMessageBox.critical(self, "Error",
                                     "COMSYL modes not present",
                                     QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    a = QApplication(sys.argv)
    ow = OWModesFileWriter()
    ow.file_name = "tmp.h5"

    filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.npy"
    af = CompactAFReader.initialize_from_file(filename)
    ow.af = af

    ow.show()
    a.exec_()