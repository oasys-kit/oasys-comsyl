#
# TODO:
#      - Add progress bar



from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

from PyQt5 import  QtGui, QtWidgets

from silx.gui.plot import PlotWindow, Plot2D
from silx.gui.plot.StackView import StackViewMainWindow

import os
import sys
import numpy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import widget
from oasys.widgets import congruence
from oasys.widgets import gui as oasysgui

from comsyl.autocorrelation.CompactAFReader import CompactAFReader

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

class OWModesLoader(widget.OWWidget):
    name = "Modes loader"
    id = "orangecontrib.comsyl.widgets.applications.AFViewer"
    description = ""
    icon = "icons/loader.png"
    author = ""
    maintainer_email = "srio@esrf.fr"
    priority = 40
    category = ""
    keywords = ["COMSYL", "coherent modes"]

    outputs = [{"name":"GenericWavefront2D",
                "type":GenericWavefront2D,
                "doc":"GenericWavefront2D",
                "id":"GenericWavefront2D"},
               {"name":"COMSYL modes",
                "type":CompactAFReader,
                "doc":"COMSYL modes",
                "id":"COMSYL modes"},]

    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    # TABS_AREA_HEIGHT = 560

    beam_file_name = Setting("/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.h5")

    TYPE_PRESENTATION = Setting(0) # 0=intensity, 1=real, 2=phase

    INDIVIDUAL_MODES = Setting(False)

    MODE_INDEX = Setting(0)

    def __init__(self):

        super().__init__()

        self._input_available = False
        self.af = None

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())


        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        self.build_left_panel()

        self.process_showers()

        gui.rubber(self.controlArea)

        self.main_tabs = gui.tabWidget(self.mainArea)
        plot_tab = gui.createTabPage(self.main_tabs, "Results")
        info_tab = gui.createTabPage(self.main_tabs, "Info")

        self.tab = []
        self.tabs = gui.tabWidget(plot_tab)
        self.info = gui.tabWidget(info_tab)
        self.tab_titles = [] #["SPECTRUM","ALL MODES","MODE XX"]
        self.initialize_tabs()

        # info tab
        self.comsyl_output = QtWidgets.QTextEdit()
        self.comsyl_output.setReadOnly(True)

        out_box = gui.widgetBox(self.info, "COMSYL file info", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.comsyl_output)

        self.comsyl_output.setFixedHeight(self.IMAGE_HEIGHT)
        self.comsyl_output.setFixedWidth(self.IMAGE_WIDTH)



    def initialize_tabs(self):

        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(self.tab_titles)):
            self.tab.append(gui.createTabPage(self.tabs, self.tab_titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

    def write_std_out(self, text):
        cursor = self.comsyl_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.comsyl_output.setTextCursor(cursor)
        self.comsyl_output.ensureCursorVisible()

    def build_left_panel(self):

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Files Selection", addSpace=True, orientation="vertical")
                                         # width=570, height=60)


        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal") #width=550, height=50)
        self.le_beam_file_name = oasysgui.lineEdit(figure_box, self, "beam_file_name", "COMSYL File:",
                                                    labelWidth=90, valueType=str, orientation="horizontal")
        # self.le_beam_file_name.setFixedWidth(330)
        gui.button(figure_box, self, "...", callback=self.selectFile)
        gui.separator(left_box_1, height=20)


        button = gui.button(self.controlArea, self, "Read COMSYL File", callback=self.read_file)
        button.setFixedHeight(45)
        gui.separator(left_box_1, height=20)


        button = gui.button(self.controlArea, self, "PLOT COMSYL data", callback=self.do_plot)
        button.setFixedHeight(45)

        gui.comboBox(self.controlArea, self, "TYPE_PRESENTATION",
                    label="Display magnitude ", addSpace=False,
                    items=['intensity','modulus','real part','imaginary part','angle [rad]'],
                    valueType=int, orientation="horizontal", callback=self.do_plot)
        gui.separator(left_box_1, height=20)


        gui.comboBox(self.controlArea, self, "INDIVIDUAL_MODES",
                    label="Access individual modes ", addSpace=False,
                    items=['No [Fast]','Yes [Slow, memory hungry]',],
                    valueType=int, orientation="horizontal", callback=self.do_plot)
        gui.separator(left_box_1, height=20)



        mode_index_box = oasysgui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal", ) #width=550, height=50)
        oasysgui.lineEdit(mode_index_box, self, "MODE_INDEX",
                    label="Load/Plot/Send mode ", addSpace=False,
                    valueType=int, validator=QIntValidator(), orientation="horizontal", labelWidth=150,
                    callback=self.do_plot)
        gui.button(mode_index_box, self, "+1", callback=self.increase_mode_index)
        gui.separator(left_box_1, height=20)



    def increase_mode_index(self):
        if self.MODE_INDEX+1 >= self.af.number_of_modes():
            raise Exception("Mode index %d not available"%(self.MODE_INDEX+1))
        self.MODE_INDEX += 1
        self.do_plot()


    def set_selected_file(self,filename):
        self.le_beam_file_name.setText(filename)

    def selectFile(self):
        filename = oasysgui.selectFileFromDialog(self,
                previous_file_path=self.beam_file_name, message="Open COMSYL File [*.npy or *.npz or *.h5]",
                start_directory=".", file_extension_filter="*.*")

        self.le_beam_file_name.setText(filename)


    def read_file(self):
        self.setStatusMessage("")
        filename = self.le_beam_file_name.text()
        try:
            if congruence.checkFileName(filename):

                # just in case old file is open
                try:
                    self.af.close_h5_file()
                except:
                    pass

                try:
                    self.af = CompactAFReader.initialize_from_file(filename)
                    self._input_available = True
                    self.write_std_out(self.af.info(list_modes=False))
                    self.main_tabs.setCurrentIndex(1)
                    self.initialize_tabs()

                    self.send("COMSYL modes", self.af)
                except:
                    raise FileExistsError("Error loading COMSYL modes from file: %s"%filename)

        except:
            raise Exception("Failed to read file %s"%filename)


    def send_mode(self,mode_index=None):
        if mode_index is None:
            mode_index = self.MODE_INDEX
        if mode_index >= self.af.number_of_modes():
            raise Exception("Mode index out of range")


        wf = GenericWavefront2D.initialize_wavefront_from_arrays(
                self.af.x_coordinates(),self.af.y_coordinates(), self.af.mode(mode_index)  )
        wf.set_photon_energy(self.af.photon_energy())
        ampl = wf.get_complex_amplitude()
        eigen = self.af.eigenvalues()
        wf.set_complex_amplitude(ampl * eigen[self.MODE_INDEX])
        self.send("GenericWavefront2D", wf)


    def _square_modulus(self,array1):
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
                                                     legend="",
                                                     scale=scale,
                                                     origin=origin,
                                                     colormap=colormap,
                                                     replace=True)


        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].setGraphTitle(title)


        self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])


    def do_plot(self):

        old_tab_index = self.tabs.currentIndex()

        try:
            for i in range(len(self.tab_titles)):
                self.tab[i].layout().removeItem(self.tab[i].layout().itemAt(0))
        except:
            pass

        if self.INDIVIDUAL_MODES:
            self.tab_titles = ["SPECTRUM","CUMULATED SPECTRUM","INDIVIDUAL MODES",              "SPECTRAL DENSITY (INTENSITY)","SPECTRAL INTENSITY FROM MODES","REFERENCE ELECRON DENSITY","REFERENCE UNDULATOR WAVEFRONT"]
        else:
            self.tab_titles = ["SPECTRUM","CUMULATED SPECTRUM","MODE INDEX: %d"%self.MODE_INDEX,"SPECTRAL DENSITY (INTENSITY)",                                "REFERENCE ELECRON DENSITY","REFERENCE UNDULATOR WAVEFRONT"]

        self.initialize_tabs()

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
            y_label =  "Occupation"


            xx = self.af.x_coordinates()
            yy = self.af.y_coordinates()

            xmin = numpy.min(xx)
            xmax = numpy.max(xx)
            ymin = numpy.min(yy)
            ymax = numpy.max(yy)

        else:
            raise Exception("Nothing to plot")

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
        self.plot_canvas[tab_index].addCurve(x_values, numpy.abs(self.af.occupation_array()), title0, symbol='', xlabel="X", ylabel="Y", replace=False) #'+', '^', ','

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
        self.plot_canvas[tab_index].addCurve(x_values, self.af.cumulated_occupation_array(), "Cumulated occupation", symbol='', xlabel="X", ylabel="Y", replace=False) #'+', '^', ','

        self.plot_canvas[tab_index].setGraphYLimits(0.0,1.0)

        self.tab[tab_index].layout().addWidget(self.plot_canvas[tab_index])
        #
        # plot all modes
        #

        if self.INDIVIDUAL_MODES:
            tab_index += 1
            dim0_calib = (0, 1)
            dim1_calib = (1e6*yy[0], 1e6*(yy[1]-yy[0]))
            dim2_calib = (1e6*xx[0], 1e6*(xx[1]-xx[0]))


            colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

            self.plot_canvas[tab_index] = StackViewMainWindow()
            self.plot_canvas[tab_index].setGraphTitle(title1)
            self.plot_canvas[tab_index].setLabels(["Mode number",
                                           "Y index from %4.2f to %4.2f um"%(1e6*ymin,1e6*ymax),
                                           "X index from %4.2f to %4.2f um"%(1e6*xmin,1e6*xmax),
                                           ])
            self.plot_canvas[tab_index].setColormap(colormap=colormap)

            self.plot_canvas[tab_index].setStack( myprocess(numpy.swapaxes(self.af.modes(),2,1)),
                                          calibrations=[dim0_calib, dim1_calib, dim2_calib] )

            # self.plot_canvas[1].setStack( self.af.modes(),
            #                               calibrations=[dim0_calib, dim1_calib, dim2_calib] )

            self.tab[tab_index].layout().addWidget(self.plot_canvas[tab_index])
        else:
            tab_index += 1
            image = myprocess( (self.af.mode(self.MODE_INDEX)))
            self.plot_data2D( image,
                    1e6*self.af.x_coordinates(),
                    1e6*self.af.y_coordinates(),
                    tab_index,
                    title="Mode %d"%self.MODE_INDEX,
                    xtitle="X [um] (%d pixels)"%(image.shape[0]),
                    ytitle="Y [um] (%d pixels)"%(image.shape[1]))



        #

        # plot spectral density
        #
        tab_index += 1
        image = myprocess( (self.af.spectral_density()))
        # self.do_plot_image_in_tab(image,tab_index,title="Spectral Density (Intensity)")
        self.plot_data2D( image,
                1e6*self.af.x_coordinates(),
                1e6*self.af.y_coordinates(),
                tab_index,
                title="Spectral Density (Intensity)",
                xtitle="X [um] (%d pixels)"%(image.shape[0]),
                ytitle="Y [um] (%d pixels)"%(image.shape[1]))


        #
        # plot spectral density from modes
        #
        if self.INDIVIDUAL_MODES:
            tab_index += 1
            image = myprocess( (self.af.intensity_from_modes()))
            self.plot_data2D( image,
                    1e6*self.af.x_coordinates(),
                    1e6*self.af.y_coordinates(),
                    tab_index,
                    title="Spectral Density (Intensity)",
                    xtitle="X [um] (%d pixels)"%(image.shape[0]),
                    ytitle="Y [um] (%d pixels)"%(image.shape[1]))


        #
        # plot reference electron density
        #
        tab_index += 1
        image = numpy.abs( self.af.reference_electron_density() )**2  #TODO: Correct? it is complex...
        # self.do_plot_image_in_tab(image,tab_index,title="Reference electron density")
        self.plot_data2D( image,
                1e6*self.af.x_coordinates(),
                1e6*self.af.y_coordinates(),
                tab_index,
                title="Reference electron density",
                xtitle="X [um] (%d pixels)"%(image.shape[0]),
                ytitle="Y [um] (%d pixels)"%(image.shape[1]))

        #
        # plot reference undulator radiation
        #
        tab_index += 1
        image = self.af.reference_undulator_radiation()[0,:,:,0]   #TODO: Correct? is polarized?
        self.plot_data2D( image,
                1e6*self.af.x_coordinates(),
                1e6*self.af.y_coordinates(),
                tab_index,
                title="Reference undulator radiation",
                xtitle="X [um] (%d pixels)"%(image.shape[0]),
                ytitle="Y [um] (%d pixels)"%(image.shape[1]))

        try:
            self.tabs.setCurrentIndex(old_tab_index)
        except:
            pass

        self.send_mode()


    def get_doc(self):
        print("PhotonViewer: help pressed.\n")
        home_doc = resources.package_dirname("orangecontrib.oasyscrystalpy") + "/doc_files/"
        filename1 = os.path.join(home_doc, 'CrystalViewer'+'.txt')
        print("PhotonViewer: Opening file %s\n" % filename1)
        if sys.platform == 'darwin':
            command = "open -a TextEdit "+filename1+" &"
        elif sys.platform == 'linux':
            command = "gedit "+filename1+" &"
        else:
            raise Exception("PhotonViewer: sys.platform did not yield an acceptable value!\n")
        os.system(command)

if __name__ == '__main__':

    app = QApplication([])
    ow = OWModesLoader()

    # filename = "/scisoft/data/srio/COMSYL/ID16/id16s_hb_u18_1400mm_1h_s1.0.h5"
    # filename = "/scisoft/data/srio/COMSYL/ID16/id16s_hb_u18_1400mm_1h_s1.0.npz"

    # filename = "/scisoft/data/srio/COMSYL/ID16/id16s_ebs_u18_1400mm_1h_s1.0.npz"
    # filename = "/scisoft/data/srio/COMSYL/ID16/id16s_ebs_u18_1400mm_1h_sampling2p5_s2.5.npz"
    # filename = "/scisoft/data/srio/COMSYL/ID16/id16s_ebs_u18_1400mm_1h_s1.5.npz"
    # filename = "/scisoft/data/srio/COMSYL/ID16/id16s_ebs_u18_1400mm_1h_new_s1.0.npz"

    filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.h5"
    ow.set_selected_file(filename)
    ow.read_file()
    ow.do_plot()

    ow.show()
    app.exec_()
    ow.saveSettings()
