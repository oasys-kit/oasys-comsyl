from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

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

from orangecontrib.comsyl.util.CompactAFReader import CompactAFReader

from matplotlib.image import AxesImage

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D


class OWAFViewer(widget.OWWidget):
    name = "AFViewer"
    id = "orangecontrib.comsyl.widgets.applications.AFViewer"
    description = ""
    icon = "icons/AFViewer.png"
    author = ""
    maintainer_email = "srio@esrf.fr"
    priority = 40
    category = ""
    keywords = ["AFViewer", "COMSYL", "EigenStates","AutocorrelationFunction"]
    # inputs = [{"name": "eigen-states",
    #             "type": CompactAFReader,
    #             "doc": "Coherent Modes Data",
    #             "id": "eigen-states",
    #             "handler": "_set_input_and_do_plot"},
    #           ]

    outputs = [{"name":"GenericWavefront2D",
                "type":GenericWavefront2D,
                "doc":"GenericWavefront2D",
                "id":"GenericWavefront2D"}]

    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    # TABS_AREA_HEIGHT = 560

    beam_file_name = Setting("/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.h5")

    TYPE_PRESENTATION = Setting(0) # 0=abs, 1=real, 2=phase

    INDIVIDUAL_MODES = Setting(False)

    MODE_INDEX = Setting(0)

    def unitLabels(self):
         return ['Type of presentation','Mode to plot:']
    def unitFlags(self):
         return ['True','True']

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

        self.tab = []
        self.tabs = gui.tabWidget(plot_tab)
        self.tab_titles = [] #["SPECTRUM","ALL MODES","MODE XX"]
        self.initializeTabs()


    def initializeTabs(self):

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

    def build_left_panel(self):

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Files Selection", addSpace=True, orientation="vertical",)
                                         # width=570, height=60)


        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", ) #width=550, height=50)
        self.le_beam_file_name = oasysgui.lineEdit(figure_box, self, "beam_file_name", "COMSYL File:",
                                                    labelWidth=90, valueType=str, orientation="horizontal")
        self.le_beam_file_name.setFixedWidth(330)
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

        oasysgui.lineEdit(self.controlArea, self, "MODE_INDEX",
                    label="Load/Plot/Send mode ", addSpace=False,
                    valueType=int, validator=QIntValidator(), orientation="horizontal", labelWidth=150,
                    callback=self.do_plot)

        #widget index 2
        # idx += 1
        # box1 = gui.widgetBox(self.controlArea)
        # self.info_energy = oasysgui.widgetLabel(box1, "Photon energy: ", labelWidth=250)
        # self.info_nmodes = oasysgui.widgetLabel(box1, "Number of modes: ", labelWidth=250)
        # self.show_at(self.unitFlags()[idx], box1)


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
        print(">>>>>> Loading file",filename)

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
                except:
                    raise FileExistsError("Error loading COMSYL modes from file: %s"%filename)

                print(">>>> File %s:" % filename)
                print(">>>> contains")
                print(">>>> %i modes" % self.af.number_modes())
                print(">>>> on the grid")
                print(">>>> x: from %e to %e" % (self.af.x_coordinates().min(), self.af.x_coordinates().max()))
                print(">>>> y: from %e to %e" % (self.af.y_coordinates().min(), self.af.y_coordinates().max()))

        except:
            raise Exception("Failed to read file %s"%filename)


    def send_mode(self,mode_index=None):
        if mode_index is None:
            mode_index = self.MODE_INDEX
        if mode_index >= self.af.number_of_modes():
            raise Exception("Mode index out of range")

        print(">>> Sending generic wavefront for mode index %d"%mode_index)

        wf = GenericWavefront2D.initialize_wavefront_from_arrays(
                self.af.x_coordinates(),self.af.y_coordinates(), self.af.mode(mode_index)  )
        wf.set_photon_energy(self.af.photon_energy())
        self.send("GenericWavefront2D", wf)


    def _square_modulus(self,array1):
        return (numpy.absolute(array1))**2

    def do_plot_image_in_tab(self,input_data,tab_index,title=""):

        xx = self.af.x_coordinates()
        yy = self.af.y_coordinates()

        xmin = numpy.min(xx)
        xmax = numpy.max(xx)
        ymin = numpy.min(yy)
        ymax = numpy.max(yy)

        origin = (1e6*xmin, 1e6*ymin)
        scale = (1e6*abs((xmax-xmin)/self.af.x_coordinates().size),
                 1e6*abs((ymax-ymin)/self.af.y_coordinates().size))

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.plot_canvas[tab_index] = Plot2D()
        self.plot_canvas[tab_index].resetZoom()
        self.plot_canvas[tab_index].setXAxisAutoScale(True)
        self.plot_canvas[tab_index].setYAxisAutoScale(True)
        self.plot_canvas[tab_index].setGraphGrid(False)
        self.plot_canvas[tab_index].setKeepDataAspectRatio(True)
        self.plot_canvas[tab_index].yAxisInvertedAction.setVisible(False)
        self.plot_canvas[tab_index].setXAxisLogarithmic(False)
        self.plot_canvas[tab_index].setYAxisLogarithmic(False)
        self.plot_canvas[tab_index].getMaskAction().setVisible(False)
        self.plot_canvas[tab_index].getRoiAction().setVisible(False)
        self.plot_canvas[tab_index].getColormapAction().setVisible(False)
        self.plot_canvas[tab_index].setKeepDataAspectRatio(False)

        self.plot_canvas[tab_index].addImage( input_data,
                                                     legend="zio billy",
                                                     colormap=colormap,
                                                     replace=True,
                                                     origin=origin,
                                                     scale=scale)

        self.plot_canvas[tab_index].setActiveImage("zio billy")

        image = AxesImage(self.plot_canvas[tab_index]._backend.ax)
        image.set_data( input_data )

        self.plot_canvas[tab_index]._backend.fig.colorbar(image, ax=self.plot_canvas[tab_index]._backend.ax)
        self.plot_canvas[tab_index].setGraphXLabel("X [um]")
        self.plot_canvas[tab_index].setGraphYLabel("Y [um]")
        self.plot_canvas[tab_index].setGraphTitle(title)

        self.tab[tab_index].layout().addWidget(self.plot_canvas[tab_index])

    def do_plot(self):


        old_tab_index = self.tabs.currentIndex()

        if self.INDIVIDUAL_MODES:
            self.tab_titles = ["SPECTRUM","INDIVIDUAL MODES",              "SPECTRAL DENSITY (INTENSITY)","SPECTRAL INTENSITY FROM MODES","REFERENCE ELECRON DENSITY","REFERENCE UNDULATOR WAVEFRONT"]
        else:
            self.tab_titles = ["SPECTRUM","MODE INDEX: %d"%self.MODE_INDEX,"SPECTRAL DENSITY (INTENSITY)",                                "REFERENCE ELECRON DENSITY","REFERENCE UNDULATOR WAVEFRONT"]

        self.initializeTabs()


        for i in range(len(self.tab_titles)):
            self.tab[i].layout().removeItem(self.tab[i].layout().itemAt(0))

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

            # integral1 = myprocess(self.af.mode(0)).sum()
            # integral1 *= (xx[1]-xx[0])*(yy[1]-yy[0])
            # print(">>>> Integrated values for mode %d is %f"%(0,integral1))
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


        self.tab[tab_index].layout().addWidget(self.plot_canvas[0])

        self.plot_canvas[tab_index].setDefaultPlotLines(True)
        self.plot_canvas[tab_index].setActiveCurveColor(color='darkblue')
        self.plot_canvas[tab_index].setXAxisLogarithmic(False)
        self.plot_canvas[tab_index].setYAxisLogarithmic(False)
        self.plot_canvas[tab_index].setGraphXLabel(x_label)
        self.plot_canvas[tab_index].setGraphYLabel(y_label)
        self.plot_canvas[tab_index].addCurve(x_values, self.af.occupation_array(), title0, symbol='', xlabel="X", ylabel="Y", replace=False) #'+', '^', ','

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

            self.tab[tab_index].layout().addWidget(self.plot_canvas[1])
        else:
            tab_index += 1
            image = myprocess( (self.af.mode(self.MODE_INDEX)).T)
            self.do_plot_image_in_tab(image,tab_index,title="Mode %d"%self.MODE_INDEX)

        #
        # plot spectral density
        #
        tab_index += 1
        image = myprocess( (self.af.spectral_density()).T)
        self.do_plot_image_in_tab(image,tab_index,title="Spectral Density (Intensity)")

        #
        # plot spectral density
        #
        if self.INDIVIDUAL_MODES:
            tab_index += 1
            image = myprocess( (self.af.intensity_from_modes()).T)
            self.do_plot_image_in_tab(image,tab_index,title="Spectral Density (Intensity)")


        #
        # plot reference electron density
        #
        tab_index += 1
        image = numpy.abs( self.af.reference_electron_density().T )**2  #TODO: Correct? it is complex...
        self.do_plot_image_in_tab(image,tab_index,title="Reference electron density")


        #
        # plot reference undulator radiation
        #
        tab_index += 1
        image = self.af.reference_undulator_radiation()[0,:,:,0]   #TODO: Correct? is polarized?
        self.do_plot_image_in_tab(image,tab_index,title="Reference undulator radiation")

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
    ow = OWAFViewer()


    # filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.h5"
    # filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.npz"
    # filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/alba_cm_u21_2m_1h_s2.5.h5"
    filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/id16s_ebs_u18_1400mm_1h_s1.0.npz"
    # CompactAFReader.convert_to_h5(filename,maximum_number_of_modes=100)
    filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/id16s_ebs_u18_1400mm_1h_s1.0.h5"


    ow.set_selected_file(filename)
    ow.read_file()
    ow.do_plot()

    ow.show()

    app.exec_()
    ow.saveSettings()
