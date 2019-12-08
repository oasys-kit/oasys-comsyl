import os, sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QFileDialog

from PyQt5.QtGui import QIntValidator, QDoubleValidator

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from comsyl.autocorrelation.CompactAFReader import CompactAFReader

from orangecontrib.comsyl.widgets.gui.ow_comsyl_widget import OWComsylWidget
from orangecontrib.comsyl.util.preprocessor import ComsylPreprocessorData
from orangecontrib.comsyl.util.python_script import PythonConsole
from orangecontrib.comsyl.util.messages import showConfirmMessage


class OWComsylPropagateBeamline(OWComsylWidget):

    name = "Propagate Beamline Script"
    description = "COMSYL Propagate Beamline"
    icon = "icons/propagator.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 46
    category = ""
    keywords = ["COMSYL", "coherent modes"]

    inputs = [("COMSYL modes" , CompactAFReader, "setCompactAFReader" ),
              ("COMSYL preprocessor beamline" , ComsylPreprocessorData, "setPreprocessor" ),]

    outputs = [{"name":"COMSYL modes",
                "type":CompactAFReader,
                "doc":"COMSYL modes",
                "id":"COMSYL modes"} ]

    COMSYL_AF_FILE = ""
    BL_PICKLE_FILE = ""
    MODE_INDEX = Setting(2) # maxumim mode index
    REFERENCE_SOURCE = Setting(0)
    DIRECTORY_NAME = "tmp_comsyl_propagation"
    PYTHON_INTERPRETER = sys.executable


    IMAGE_WIDTH = 890
    IMAGE_HEIGHT = 680

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box=show_automatic_box)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Refresh Script", callback=self.refresh_script)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        gen_box = oasysgui.widgetBox(self.controlArea, "COMSYL Beamline Propagation", addSpace=False, orientation="vertical", height=530, width=self.CONTROL_AREA_WIDTH-5)


        figure_box0 = oasysgui.widgetBox(gen_box, "", addSpace=True, orientation="horizontal")
        self.id_comsyl_af_file = oasysgui.lineEdit(figure_box0, self, "COMSYL_AF_FILE", "Comsyl File with Modes:",
                                                    labelWidth=90, valueType=str, orientation="horizontal")
        gui.button(figure_box0, self, "...", callback=self.select_comsyl_af_file)


        figure_box = oasysgui.widgetBox(gen_box, "", addSpace=True, orientation="horizontal")
        self.id_bl_pickle_file = oasysgui.lineEdit(figure_box, self, "BL_PICKLE_FILE", "BL Pickle File:",
                                                    labelWidth=90, valueType=str, orientation="horizontal")
        gui.button(figure_box, self, "...", callback=self.select_bl_pickle_file)

        oasysgui.lineEdit(gen_box, self, "MODE_INDEX",
                    label="Maximum Mode index", addSpace=False,
                    valueType=int, validator=QIntValidator(), orientation="horizontal", labelWidth=150)

        oasysgui.lineEdit(gen_box, self, "DIRECTORY_NAME", "Temporal Directory", labelWidth=160, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(gen_box, self, "PYTHON_INTERPRETER", "Python interpreter", labelWidth=160, valueType=str, orientation="horizontal")


        tabs_setting = oasysgui.tabWidget(self.mainArea)
        tabs_setting.setFixedHeight(self.IMAGE_HEIGHT)
        tabs_setting.setFixedWidth(self.IMAGE_WIDTH)

        tab_scr = oasysgui.createTabPage(tabs_setting, "Python Script")
        tab_out = oasysgui.createTabPage(tabs_setting, "System Output")

        self.pythonScript = oasysgui.textArea(readOnly=False)
        self.pythonScript.setStyleSheet("background-color: white; font-family: Courier, monospace;")
        self.pythonScript.setMaximumHeight(self.IMAGE_HEIGHT - 250)

        script_box = oasysgui.widgetBox(tab_scr, "", addSpace=False, orientation="vertical", height=self.IMAGE_HEIGHT - 10, width=self.IMAGE_WIDTH - 10)
        script_box.layout().addWidget(self.pythonScript)

        console_box = oasysgui.widgetBox(script_box, "", addSpace=True, orientation="vertical",
                                          height=150, width=self.IMAGE_WIDTH - 10)

        self.console = PythonConsole(self.__dict__, self)
        console_box.layout().addWidget(self.console)

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.IMAGE_WIDTH - 45)
        out_box.layout().addWidget(self.shadow_output)


        button_box = oasysgui.widgetBox(tab_scr, "", addSpace=True, orientation="horizontal")

        gui.button(button_box, self, "Run Script", callback=self.execute_script, height=40)
        gui.button(button_box, self, "Save Script to File", callback=self.save_script, height=40)

        #############################

        # self.refresh_script()
    #

    def select_comsyl_af_file(self):
        self.id_comsyl_af_file.setText(oasysgui.selectFileFromDialog(self,
                        self.COMSYL_AF_FILE, "Select Input File",
                        file_extension_filter="COMSYL Files (*.npz)"))


    def select_bl_pickle_file(self):
        self.id_bl_pickle_file.setText(oasysgui.selectFileFromDialog(self,
                        self.BL_PICKLE_FILE, "Select Input File",
                        file_extension_filter="COMSYL Beamline Pickle Files (*.p)"))


    def setCompactAFReader(self, af):
        if not af is None:
            self.COMSYL_AF_FILE = af._af._io.fromFile()
            self.refresh_script()

    def setPreprocessor(self, data):
        try:
            self.BL_PICKLE_FILE = data.get_beamline_pickle_file()
            self.refresh_script()
        except:
            pass

    def execute_script(self):
        if showConfirmMessage(message = "Do you confirm launching a COMSYL propagation?",
                              informative_text="This is a long and resource-consuming process: launching it within the OASYS environment is highly discouraged." + \
                                               "The suggested solution is to save the script into a file and to launch it in a different environment."):
            self._script = str(self.pythonScript.toPlainText())
            self.console.write("\nRunning script:\n")
            self.console.push("exec(_script)")
            self.console.new_prompt(sys.ps1)

    def save_script(self):
        file_name = QFileDialog.getSaveFileName(self, "Save File to Disk", os.getcwd(), filter='*.py')[0]

        if not file_name is None:
            if not file_name.strip() == "":
                file = open(file_name, "w")
                file.write(str(self.pythonScript.toPlainText()))
                file.close()

                QtWidgets.QMessageBox.information(self, "QMessageBox.information()",
                                              "File " + file_name + " written to disk",
                                              QtWidgets.QMessageBox.Ok)

    def refresh_script(self):
        dd = {"COMSYL_AF_FILE": self.COMSYL_AF_FILE,
              "BL_PICKLE_FILE": self.BL_PICKLE_FILE,
              "DIRECTORY_NAME": self.DIRECTORY_NAME,
              "PYTHON_INTERPRETER": self.PYTHON_INTERPRETER,
              "MODE_INDEX": self.MODE_INDEX,
              }

        self.pythonScript.setText(self.script_template().format_map(dd))

    def script_template(self):
        return """import pickle
from comsyl.waveoptics.ComsylWofryBeamline import ComsylWofryBeamline
from comsyl.waveoptics.SRWAdapter import ComsylSRWBeamline
from comsyl.autocorrelation.CompactAFReader import CompactAFReader

comsyl_beamline  = pickle.load(open("{BL_PICKLE_FILE}","rb"))

filename = "{COMSYL_AF_FILE}"
af_oasys = CompactAFReader.initialize_from_file(filename)
af_comsyl = af_oasys.get_af()

# **source position correction**
source_position=af_comsyl.info().sourcePosition()
if source_position == "entrance":
    source_offset = af_comsyl._undulator.length() * 0.5
elif source_position == "center":
    source_offset = 0.0
else:
    raise Exception("Unhandled source position")
print("Using source position entrance z=%f" % source_offset)
comsyl_beamline.add_undulator_offset(source_offset)


af_propagated = comsyl_beamline.propagate_af(af_comsyl,
             directory_name="{DIRECTORY_NAME}",
             af_output_file_root="{DIRECTORY_NAME}/propagated_beamline",
             maximum_mode={MODE_INDEX},
             python_to_be_used="{PYTHON_INTERPRETER}")

#rediagonalization   **uncomment to proceed**
#af_propagated.diagonalizeModes({MODE_INDEX})
#af_propagated.save("{DIRECTORY_NAME}/rediagonalized")

"""


if __name__ == '__main__':

    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    ow = OWComsylPropagateBeamline()

    ow.COMSYL_AF_FILE = "/scisoft/users/glass/Documents/sources/Orange-SRW/comsyl/calculations/cs_new_u18_2m_1h_s2.5.npz"
    ow.BL_PICKLE_FILE = "/scisoft/xop2.4/extensions/shadowvui/shadow3-scripts/HIGHLIGHTS/bl.p"
    ow.refresh_script()

    ow.show()
    app.exec_()
    ow.saveSettings()