#
# TODO:
#      - Add progress bar


from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFont


from silx.gui.plot import PlotWindow, Plot2D
from silx.gui.plot.StackView import StackViewMainWindow

import numpy

from orangewidget import gui
from orangewidget.settings import Setting
from orangecontrib.wofry.widgets.gui.ow_wofry_widget import WofryWidget

from orangewidget import widget
from oasys.widgets import congruence
from oasys.widgets import gui as oasysgui

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D
from wofryimpl.beamline.beamline import WOBeamline

from comsyl.autocorrelation.CompactAFReader import CompactAFReader

from orangecontrib.wofry.util.wofry_objects import WofryData
from orangecontrib.comsyl.util.light_source import WOLightSourceCOMSYL

from oasys.util.oasys_util import TriggerIn, TriggerOut


class OWModesSelector(WofryWidget):

    name = "ModesSelector"
    id = "orangecontrib.comsyl.widgets.applications.comsyl_modes_viewer"
    description = ""
    icon = "icons/selector.png"
    author = ""
    maintainer_email = "srio@esrf.fr"
    priority = 45
    category = ""
    keywords = ["COMSYL", "coherent modes"]


    inputs = [("COMSYL modes" , CompactAFReader, "setCompactAFReader" ),
              ("Trigger", TriggerOut, "receive_trigger_signal")]

    outputs = [{"name":"WofryData",
                "type":WofryData,
                "doc":"WofryData",
                "id":"WofryData"},
               {"name":"Trigger",
                "type": TriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"},
               {"name":"COMSYL modes",
                "type":CompactAFReader,
                "doc":"COMSYL modes",
                "id":"COMSYL modes"},]


    NORMALIZATION = Setting(1) # 0=No, 1=With eigenvalues
    TYPE_PRESENTATION = Setting(0) # 0=intensity, 1=real, 2=phase
    INDIVIDUAL_MODES = Setting(False)
    MODE_INDEX = Setting(0)
    REFERENCE_SOURCE = Setting(0)

    # IS_DEVELOP = True
    _input_available = False

    def __init__(self):

        super().__init__(is_automatic=True, show_view_options=True, show_script_tab=True)

        self.runaction = widget.OWAction("Generate Wavefront", self)
        self.runaction.triggered.connect(self.do_plot_and_send_mode)
        self.addAction(self.runaction)

        gui.separator(self.controlArea)
        gui.separator(self.controlArea)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Plot and Send mode", callback=self.do_plot_and_send_mode)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT + 50)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_settings = oasysgui.createTabPage(tabs_setting, "Settings")


        #
        # Settings
        #

        gui.comboBox(self.tab_settings, self, "NORMALIZATION",
                    label="Renormalize modes ", addSpace=False,
                    items=["No (pure eigenvectors)", "Yes (to carry intensity from eigenvalues)"],
                    valueType=int, orientation="horizontal", callback=self.do_plot_and_send_mode)

        gui.comboBox(self.tab_settings, self, "TYPE_PRESENTATION",
                    label="Display coherent mode ", addSpace=False,
                    items=self.list_TYPE_PRESENTATION(),
                    valueType=int, orientation="horizontal", callback=self.do_plot_and_send_mode)


        gui.comboBox(self.tab_settings, self, "INDIVIDUAL_MODES",
                    label="Load all modes in memory ", addSpace=False,
                    items=['No [Fast, Recommended]','Yes [Slow, Memory hungry]',],
                    valueType=int, orientation="horizontal", callback=self.do_plot_and_send_mode)

        gui.comboBox(self.tab_settings, self, "REFERENCE_SOURCE",
                    label="Display reference source ", addSpace=False,
                    items=['No','Yes',],
                    valueType=int, orientation="horizontal", callback=self.do_plot_and_send_mode)


        mode_index_box = oasysgui.widgetBox(self.tab_settings, "", addSpace=True, orientation="horizontal")

        left_box_5 = oasysgui.widgetBox(mode_index_box, "", addSpace=True, orientation="horizontal", )
        oasysgui.lineEdit(left_box_5, self, "MODE_INDEX", "Send mode",
                        labelWidth=200, valueType=int, tooltip = "mode_index",
                        orientation="horizontal", callback=self.do_plot_and_send_mode)

        gui.button(left_box_5, self, "+1", callback=self.increase_mode_index, width=30)
        gui.button(left_box_5, self, "-1", callback=self.decrease_mode_index, width=30)
        gui.button(left_box_5, self,  "0", callback=self.reset_mode_index, width=30)


    def list_TYPE_PRESENTATION(self):
        return ['intensity','modulus','real part','imaginary part','angle [rad]']

    def get_light_source(self):
        return WOLightSourceCOMSYL(name=self.name,
                                   filename=self.af._filename,
                                   mode_index=self.MODE_INDEX,
                                   normalize_with_eigenvalue=self.NORMALIZATION)

    def initializeTabs(self):
        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        self.tab = []
        self.plot_canvas = []

        self.set_tab_titles()

        for index in range(0, len(self.tab_titles)):
            self.tab.append(gui.createTabPage(self.tabs, self.tab_titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

    def setCompactAFReader(self, data):
        if not data is None:
            self.af = data
            self._input_available = True
            self.wofry_output.setText(self.af.info(list_modes=False))
            self.main_tabs.setCurrentIndex(1)
            self.initializeTabs()
            self.do_plot_and_send_mode()

    def receive_trigger_signal(self, trigger):

        if trigger and trigger.new_object == True:
            if trigger.has_additional_parameter("variable_name"):
                variable_name = trigger.get_additional_parameter("variable_name").strip()
                variable_display_name = trigger.get_additional_parameter("variable_display_name").strip()
                variable_value = trigger.get_additional_parameter("variable_value")
                variable_um = trigger.get_additional_parameter("variable_um")

                if "," in variable_name:
                    variable_names = variable_name.split(",")

                    for variable_name in variable_names:
                        setattr(self, variable_name.strip(), variable_value)
                else:
                    setattr(self, variable_name, variable_value)

                self.do_plot_and_send_mode()
            else:
                self.increase_mode_index()

    def increase_mode_index(self):
        if self.MODE_INDEX+1 >= self.af.number_of_modes():
            pass
        else:
            self.MODE_INDEX += 1
            self.do_plot_and_send_mode()

    def decrease_mode_index(self):
        if self.MODE_INDEX-1 < 0:
            pass
        else:
            self.MODE_INDEX -= 1
            self.do_plot_and_send_mode()

    def reset_mode_index(self):
        self.MODE_INDEX = 0
        self.do_plot_and_send_mode()

    def _square_modulus(self,array1):
        return (numpy.absolute(array1))**2

    def _intensity_times_eigenvalue(self,array1):
        s = array1.shape
        if len(s) == 3: # stack
            for i in range(s[0]):
                array1[i] *= numpy.sqrt(self.af.eigenvalue(i).real)
        else:
            array1 *= numpy.sqrt(self.af.eigenvalue(self.MODE_INDEX).real)
        return (numpy.absolute(array1))**2


    def plot_data2D(self, data2D, dataX, dataY, plot_canvas_index, title="", xtitle="", ytitle=""):

        xmin = numpy.min(dataX)
        xmax = numpy.max(dataX)
        ymin = numpy.min(dataY)
        ymax = numpy.max(dataY)

        origin = (xmin, ymin)
        scale = (abs((xmax-xmin)/len(dataX)), abs((ymax-ymin)/len(dataY)))

        data_to_plot = data2D.T

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.plot_canvas[plot_canvas_index] = Plot2D()

        self.plot_canvas[plot_canvas_index].resetZoom()
        self.plot_canvas[plot_canvas_index].setXAxisAutoScale(True)
        self.plot_canvas[plot_canvas_index].setYAxisAutoScale(True)
        self.plot_canvas[plot_canvas_index].setGraphGrid(False)
        self.plot_canvas[plot_canvas_index].setKeepDataAspectRatio(True)
        self.plot_canvas[plot_canvas_index].yAxisInvertedAction.setVisible(False)

        self.plot_canvas[plot_canvas_index].setXAxisLogarithmic(False)
        self.plot_canvas[plot_canvas_index].setYAxisLogarithmic(False)
        #silx 0.4.0
        self.plot_canvas[plot_canvas_index].getMaskAction().setVisible(False)
        self.plot_canvas[plot_canvas_index].getRoiAction().setVisible(False)
        self.plot_canvas[plot_canvas_index].getColormapAction().setVisible(True)
        self.plot_canvas[plot_canvas_index].setKeepDataAspectRatio(False)

        self.plot_canvas[plot_canvas_index].addImage(numpy.array(data_to_plot),
                                                     legend="zio billy",
                                                     scale=scale,
                                                     origin=origin,
                                                     colormap=colormap,
                                                     replace=True)


        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].setGraphTitle(title)


        self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

    def set_tab_titles(self):
        if self.INDIVIDUAL_MODES:
            self.tab_titles = ["SPECTRUM","CUMULATED SPECTRUM","INDIVIDUAL MODES",]
            if self.REFERENCE_SOURCE:
                self.tab_titles += ["REFERENCE SPECTRAL DENSITY","SPECTRAL INTENSITY FROM MODES","REFERENCE ELECRON DENSITY","REFERENCE UNDULATOR WAVEFRONT"]
        else:
            self.tab_titles = ["SPECTRUM","CUMULATED SPECTRUM","MODE INDEX: %d"%self.MODE_INDEX,]
            if self.REFERENCE_SOURCE:
                self.tab_titles += ["REFERENCE SPECTRAL DENSITY","REFERENCE ELECRON DENSITY","REFERENCE UNDULATOR WAVEFRONT"]

    def do_plot_and_send_mode(self):
        self.do_plot_results()
        self.send_mode()

    def do_plot_results(self, progressBarValue=10):  # required by parent widget
        old_tab_index = self.tabs.currentIndex()

        try:
            for i in range(len(self.tab_titles)):
                self.tab[i].layout().removeItem(self.tab[i].layout().itemAt(0))
        except:
            pass

        if self.view_type != 0:

            self.set_tab_titles()
            # self.initialize_tabs()
            self.initializeTabs()

            if self.TYPE_PRESENTATION == 0:
                myprocess = self._square_modulus
                title0 = "Intensity of eigenvalues"
                title1 = "Intensity of eigenvector"
            if self.TYPE_PRESENTATION == 1:
                myprocess = numpy.absolute
                title0 = "Modulus of eigenvalues"
                title1 = "Modulus of eigenvector"
            elif self.TYPE_PRESENTATION == 2:
                myprocess = numpy.real
                title0 = "Real part of eigenvalues"
                title1 = "Real part of eigenvector"
            elif self.TYPE_PRESENTATION == 3:
                myprocess = numpy.imag
                title0 = "Imaginary part of eigenvalues"
                title1 = "Imaginary part of eigenvectos"
            elif self.TYPE_PRESENTATION == 4:
                myprocess = numpy.angle
                title0 = "Angle of eigenvalues [rad]"
                title1 = "Angle of eigenvector [rad]"


            if self._input_available:
                x_values = numpy.arange(self.af.number_modes())
                x_label = "Mode index"
                y_label = "Occupation"

                xx = self.af.x_coordinates()
                yy = self.af.y_coordinates()

                xmin = numpy.min(xx)
                xmax = numpy.max(xx)
                ymin = numpy.min(yy)
                ymax = numpy.max(yy)

            else:
                print("No input data")
                return

            #
            # plot spectrum
            #
            tab_index = 0
            self.plot_canvas[tab_index] = PlotWindow(parent=None,
                                                     backend=None,
                                                     resetzoom=True,
                                                     autoScale=False,
                                                     logScale=True,
                                                     grid=True,
                                                     curveStyle=True,
                                                     colormap=False,
                                                     aspectRatio=False,
                                                     yInverted=False,
                                                     copy=True,
                                                     save=True,
                                                     print_=True,
                                                     control=False,
                                                     position=True,
                                                     roi=False,
                                                     mask=False,
                                                     fit=False)

            self.tab[tab_index].layout().addWidget(self.plot_canvas[tab_index])

            self.plot_canvas[tab_index].setDefaultPlotLines(True)
            self.plot_canvas[tab_index].setXAxisLogarithmic(False)
            self.plot_canvas[tab_index].setYAxisLogarithmic(False)
            self.plot_canvas[tab_index].setGraphXLabel(x_label)
            self.plot_canvas[tab_index].setGraphYLabel(y_label)
            self.plot_canvas[tab_index].addCurve(x_values, numpy.abs(self.af.occupation_array()), title0, symbol='',
                                                 xlabel="X", ylabel="Y", replace=False)  # '+', '^', ','

            self.tab[tab_index].layout().addWidget(self.plot_canvas[tab_index])
            #
            # plot cumulated spectrum
            #
            tab_index += 1
            self.plot_canvas[tab_index] = PlotWindow(parent=None,
                                                     backend=None,
                                                     resetzoom=True,
                                                     autoScale=False,
                                                     logScale=True,
                                                     grid=True,
                                                     curveStyle=True,
                                                     colormap=False,
                                                     aspectRatio=False,
                                                     yInverted=False,
                                                     copy=True,
                                                     save=True,
                                                     print_=True,
                                                     control=False,
                                                     position=True,
                                                     roi=False,
                                                     mask=False,
                                                     fit=False)

            self.tab[tab_index].layout().addWidget(self.plot_canvas[tab_index])

            self.plot_canvas[tab_index].setDefaultPlotLines(True)
            self.plot_canvas[tab_index].setXAxisLogarithmic(False)
            self.plot_canvas[tab_index].setYAxisLogarithmic(False)
            self.plot_canvas[tab_index].setGraphXLabel(x_label)
            self.plot_canvas[tab_index].setGraphYLabel("Cumulated occupation")
            # self.plot_canvas[tab_index].addCurve(x_values, numpy.cumsum(numpy.abs(self.af.occupation_array())), "Cumulated occupation", symbol='', xlabel="X", ylabel="Y", replace=False) #'+', '^', ','
            self.plot_canvas[tab_index].addCurve(x_values, self.af.cumulated_occupation_array(), "Cumulated occupation",
                                                 symbol='', xlabel="X", ylabel="Y", replace=False)  # '+', '^', ','

            self.plot_canvas[tab_index].setGraphYLimits(0.0, 1.0)

            self.tab[tab_index].layout().addWidget(self.plot_canvas[tab_index])
            #
            # plot all modes
            #

            if self.INDIVIDUAL_MODES:
                tab_index += 1
                dim0_calib = (0, 1)
                dim1_calib = (1e6 * yy[0], 1e6 * (yy[1] - yy[0]))
                dim2_calib = (1e6 * xx[0], 1e6 * (xx[1] - xx[0]))

                colormap = {"name": "temperature", "normalization": "linear", "autoscale": True, "vmin": 0, "vmax": 0,
                            "colors": 256}

                self.plot_canvas[tab_index] = StackViewMainWindow()
                self.plot_canvas[tab_index].setGraphTitle(title1)
                self.plot_canvas[tab_index].setLabels(["Mode number",
                                                       "Y index from %4.2f to %4.2f um" % (1e6 * ymin, 1e6 * ymax),
                                                       "X index from %4.2f to %4.2f um" % (1e6 * xmin, 1e6 * xmax),
                                                       ])
                self.plot_canvas[tab_index].setColormap(colormap=colormap)

                self.plot_canvas[tab_index].setStack(myprocess(numpy.swapaxes(self.af.modes(), 2, 1)),
                                                     calibrations=[dim0_calib, dim1_calib, dim2_calib])

                self.tab[tab_index].layout().addWidget(self.plot_canvas[tab_index])
            else:
                tab_index += 1
                wf = self.af.get_wavefront(self.MODE_INDEX, normalize_with_eigenvalue=self.NORMALIZATION)
                image = myprocess(wf.get_complex_amplitude())

                self.plot_data2D(image,
                                 1e6 * self.af.x_coordinates(),
                                 1e6 * self.af.y_coordinates(),
                                 tab_index,
                                 title="%s; Mode %d" % (self.list_TYPE_PRESENTATION()[self.TYPE_PRESENTATION], self.MODE_INDEX),
                                 xtitle="X [um] (%d pixels)" % (image.shape[0]),
                                 ytitle="Y [um] (%d pixels)" % (image.shape[1]))

            #
            # plot spectral density
            #
            if self.REFERENCE_SOURCE:
                tab_index += 1
                image = myprocess((self.af.spectral_density()))
                # self.do_plot_image_in_tab(image,tab_index,title="Spectral Density (Intensity)")
                self.plot_data2D(image,
                                 1e6 * self.af.x_coordinates(),
                                 1e6 * self.af.y_coordinates(),
                                 tab_index,
                                 title="Spectral Density (Intensity)",
                                 xtitle="X [um] (%d pixels)" % (image.shape[0]),
                                 ytitle="Y [um] (%d pixels)" % (image.shape[1]))

            #
            # plot spectral density from modes
            #
            if self.REFERENCE_SOURCE:
                if self.INDIVIDUAL_MODES:
                    tab_index += 1
                    image = myprocess((self.af.intensity_from_modes()))
                    self.plot_data2D(image,
                                     1e6 * self.af.x_coordinates(),
                                     1e6 * self.af.y_coordinates(),
                                     tab_index,
                                     title="Spectral Density (Intensity)",
                                     xtitle="X [um] (%d pixels)" % (image.shape[0]),
                                     ytitle="Y [um] (%d pixels)" % (image.shape[1]))

            #
            # plot reference electron density
            #
            if self.REFERENCE_SOURCE:
                tab_index += 1
                image = numpy.abs(self.af.reference_electron_density()) ** 2  # TODO: Correct? it is complex...
                self.plot_data2D(image,
                                 1e6 * self.af.x_coordinates(),
                                 1e6 * self.af.y_coordinates(),
                                 tab_index,
                                 title="Reference electron density",
                                 xtitle="X [um] (%d pixels)" % (image.shape[0]),
                                 ytitle="Y [um] (%d pixels)" % (image.shape[1]))

            #
            # plot reference undulator radiation
            #
            if self.REFERENCE_SOURCE:
                tab_index += 1
                image = self.af.reference_undulator_radiation()[0, :, :, 0]  # TODO: Correct? is polarized?

                self.plot_data2D(image,
                                 1e6 * self.af.x_coordinates(),
                                 1e6 * self.af.y_coordinates(),
                                 tab_index,
                                 title="Reference undulator radiation",
                                 xtitle="X [um] (%d pixels)" % (image.shape[0]),
                                 ytitle="Y [um] (%d pixels)" % (image.shape[1]))

            try:
                self.tabs.setCurrentIndex(old_tab_index)
            except:
                pass


    def get_doc(self):
        pass

    def send_mode(self):

        wf = GenericWavefront2D.initialize_wavefront_from_arrays(
                self.af.x_coordinates(),self.af.y_coordinates(), self.af.mode(self.MODE_INDEX)  )
        wf.set_photon_energy(self.af.photon_energy())
        ampl = wf.get_complex_amplitude()

        if self.TYPE_PRESENTATION == 5:
            eigen = self.af.eigenvalues_old()
            wf.set_complex_amplitude(ampl * numpy.sqrt(eigen[self.MODE_INDEX]))
        else:
            wf.set_complex_amplitude(ampl)

        beamline = WOBeamline(light_source=self.get_light_source())
        print(">>> sending mode: ", int(self.MODE_INDEX))
        self.send("WofryData", WofryData(
            wavefront=wf,
            beamline=beamline))

        # script
        self.wofry_python_script.set_code(beamline.to_python_code())


if __name__ == '__main__':

    filename = "/scisoft/users/srio/COMSYL-SLURM/comsyl/comsyl-submit/calculations/id18_ebs_u18_2500mm_s6.0.npz"
    af = CompactAFReader.initialize_from_file(filename)



    app = QApplication([])
    ow = OWModesSelector()

    ow.setCompactAFReader(af)

    ow.show()
    app.exec_()
    ow.saveSettings()
