import os, sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QFileDialog

from PyQt5.QtGui import QIntValidator, QDoubleValidator

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence


from orangecontrib.comsyl.widgets.gui.ow_comsyl_widget import OWComsylWidget
from orangecontrib.comsyl.util.CompactAFReader import CompactAFReader

from orangecontrib.comsyl.util.python_script import PythonConsole
# from orangecontrib.srw.util.srw_objects import SRWData
from orangecontrib.comsyl.util.messages import showConfirmMessage
# from orangecontrib.srw.widgets.gui.ow_srw_widget import SRWWidget
#
# from wofrysrw.storage_ring.light_sources.srw_bending_magnet_light_source import SRWBendingMagnetLightSource
# from wofrysrw.storage_ring.light_sources.srw_undulator_light_source import SRWUndulatorLightSource

class OWComsylPropagateBeamline(OWComsylWidget):

    name = "COMSYL Propagate Beamline"
    description = "COMSYL Propagate Beamline"
    icon = "icons/selector.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 2
    category = ""
    keywords = ["COMSYL", "coherent modes"]

    inputs = [("COMSYL modes" , CompactAFReader, "setCompactAFReader" ),]

    outputs = [{"name":"COMSYL modes",
                "type":CompactAFReader,
                "doc":"COMSYL modes",
                "id":"COMSYL modes"} ]

    BL_PROPAGATOR = Setting(0) # 0=wofry, 1=srw
    BL_FROM = Setting(1) # 0=Beamline history, 1=pickle file
    BL_PICKLE_FILE = "/scisoft/xop2.4/extensions/shadowvui/shadow3-scripts/HIGHLIGHTS/bl.p"
    MODE_INDEX = Setting(2) # maxumim mode index
    REFERENCE_SOURCE = Setting(0)
    UNDULATOR_POSITION = 0 # 0=entyrance, 1=center
    DIRECTORY_NAME = "tmp_comsyl_propagation"
    PYTHON_INTERPRETER = "python3"


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

        gui.comboBox(gen_box, self, "BL_PROPAGATOR", label="Propagation package",
                     items=["WOFRY", "SRW"], labelWidth=300,
                     valueType=int, orientation="horizontal")

        gui.comboBox(gen_box, self, "BL_FROM", label="Beamline from",
                     items=["COMSYL BL Preprocessor", "Pickle file"], labelWidth=300,
                     valueType=int, orientation="horizontal")


        figure_box = oasysgui.widgetBox(gen_box, "", addSpace=True, orientation="horizontal")
        self.id_bl_pickle_file = oasysgui.lineEdit(figure_box, self, "BL_PICKLE_FILE", "BL Pickle File:",
                                                    labelWidth=90, valueType=str, orientation="horizontal")
        # self.le_beam_file_name.setFixedWidth(330)
        gui.button(figure_box, self, "...", callback=self.select_pickle_file)
        # gui.separator(left_box_1, height=20)

        # mode_index_box = oasysgui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal", ) #width=550, height=50)
        oasysgui.lineEdit(gen_box, self, "MODE_INDEX",
                    label="Maximum Mode index", addSpace=False,
                    valueType=int, validator=QIntValidator(), orientation="horizontal", labelWidth=150)

        gui.comboBox(gen_box, self, "UNDULATOR_POSITION", label="Undulator Position",
                     items=["Entrance", "Origin"], labelWidth=300,
                     valueType=int, orientation="horizontal")


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

        #############################

        button_box = oasysgui.widgetBox(tab_scr, "", addSpace=True, orientation="horizontal")

        gui.button(button_box, self, "Run Script", callback=self.execute_script, height=40)
        gui.button(button_box, self, "Save Script to File", callback=self.save_script, height=40)


    def select_pickle_file(self):
        pass


    def setCompactAFReader(self, data):
        if not data is None:
            self.af = data
            self._input_available = True
            self.write_std_out(self.af.info(list_modes=False))
            self.main_tabs.setCurrentIndex(1)
            self.initialize_tabs()


    def execute_script(self):
        if showConfirmMessage(message = "Do you confirm launching a ME propagation?",
                              informative_text="This is a very long and resource-consuming process: launching it within the OASYS environment is highly discouraged." + \
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

    # def set_input(self, srw_data=SRWData()):
    #     if not srw_data is None:
    #         self.input_srw_data = srw_data
    #
    #         if self.is_automatic_run:
    #             self.refresh_script()
    #     else:
    #         QtWidgets.QMessageBox.critical(self, "Error", str(e), QtWidgets.QMessageBox.Ok)

    def refresh_script(self):

        script = """
import pickle
from comsyl.waveoptics.WOFRYAdapter import CWBeamline
from comsyl.waveoptics.SRWAdapter import CSRWBeamline
from comsyl.autocorrelation.AutocorrelationFunction import AutocorrelationFunction

comsyl_beamline  = pickle.load(open("/scisoft/xop2.4/extensions/shadowvui/shadow3-scripts/HIGHLIGHTS/bl.p","rb"))

filename = "/scisoft/users/glass/Documents/sources/Orange-SRW/comsyl/calculations/cs_new_u18_2m_1h_s2.5.npz" # OK EBS
autocorrelation_function = AutocorrelationFunction.load(filename)

directory_name = "propagation_EBS_25x25"

af_propagated = comsyl_beamline.propagate_af(autocorrelation_function,
             directory_name=directory_name,
             af_output_file_root="%s/propagated_beamline"%(directory_name),
             maximum_mode=2,python_to_be_used="/users/srio/OASYS1.1d/miniconda3/bin/python")

print(">>>>>>>>>>>>>>>>>",comsyl_beamline.propagation_code())
"""
        self.pythonScript.setText(script)

        # if not self.input_srw_data is None:
        #     self.pythonScript.setText("# srio@esrf.eu")
        #
            # try:
            #     received_light_source = self.input_srw_data.get_srw_beamline().get_light_source()
            #
            #     if not (isinstance(received_light_source, SRWBendingMagnetLightSource) or isinstance(received_light_source, SRWUndulatorLightSource)):
            #         raise ValueError("ME Script is not available with this source")
            #
            #     _char = 0 if self._char == 0 else 4
            #
            #     parameters = [self.sampFactNxNyForProp,
            #                   self.nMacroElec,
            #                   self.nMacroElecAvgOneProc,
            #                   self.nMacroElecSavePer,
            #                   self.srCalcMeth,
            #                   self.srCalcPrec,
            #                   self.strIntPropME_OutFileName,
            #                   _char]
            #
            #     self.pythonScript.setText(self.input_srw_data.get_srw_beamline().to_python_code([self.input_srw_data.get_srw_wavefront(), True, parameters]))
            # except Exception as e:
            #     self.pythonScript.setText("Problem in writing python script:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))
            #
            #     if self.IS_DEVELOP: raise e



if __name__ == '__main__':

    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    ow = OWComsylPropagateBeamline()


    ow.show()
    app.exec_()
    ow.saveSettings()