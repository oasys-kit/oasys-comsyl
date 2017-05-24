from PyQt4 import QtGui
from PyQt4.QtGui import QIntValidator, QDoubleValidator, QApplication
from PyQt4.QtCore import QRect

from silx.gui.plot import PlotWindow, Plot2D
from silx.gui.plot.StackView import StackViewMainWindow
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


import os
import sys
import numpy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import widget
from oasys.widgets import gui as oasysgui

from orangecontrib.comsyl.util.CompactAFReader import CompactAFReader

class OWAFViewer(widget.OWWidget):
    name = "AFViewer"
    id = "orangecontrib.comsyl.widgets.applications.AFViewer"
    description = ""
    icon = "icons/AFViewer.png"
    author = ""
    maintainer_email = "srio@esrf.fr"
    priority = 40
    category = ""
    keywords = ["AFViewer", "COMSYL", "EigenStates"]
    inputs = [{"name": "eigen-states",
                "type": CompactAFReader,
                "doc": "Coherent Modes Data",
                "id": "eigen-states",
                "handler": "_set_input_and_do_plot"},
              ]

    TYPE_PRESENTATION = Setting(0) # 0=abs, 1=real, 2=phase
    MODE_TO_PLOT = Setting(0)


    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    # TABS_AREA_HEIGHT = 560


    def unitLabels(self):
         return ['Type of presentation','Mode to plot:']
    def unitFlags(self):
         return ['True','True']

    def __init__(self):

        super().__init__()


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
        self.tab_titles = ["SPECTRUM","ALL MODES","MODE %d"%self.MODE_TO_PLOT]
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

        box = oasysgui.widgetBox(self.controlArea, "Plotting Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        idx = -1

        gui.button(box, self, "Replot", callback=self.do_plot)

        #widget index 0
        idx += 1
        box1 = gui.widgetBox(box)
        gui.comboBox(box1, self, "TYPE_PRESENTATION",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['intensity','modulus','real part','imaginary part','angle [rad]'],
                    valueType=int, orientation="horizontal", callback=self.do_plot)
        self.show_at(self.unitFlags()[idx], box1)



        #widget index 1
        idx += 1
        box1 = gui.widgetBox(box)
        oasysgui.lineEdit(box1, self, "MODE_TO_PLOT",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=int, validator=QIntValidator(), orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)


        #widget index 2
        idx += 1
        box1 = gui.widgetBox(box)
        self.info_energy = oasysgui.widgetLabel(box1, "Photon energy: ", labelWidth=250)
        self.info_nmodes = oasysgui.widgetLabel(box1, "Number of modes: ", labelWidth=250)
        # self.show_at(self.unitFlags()[idx], box1)



    def _set_input_and_do_plot(self, eigenstates):
        """This function is called when the widget receives an input."""
        self._set_input(eigenstates)
        self.do_plot()

    def _set_input(self, eigenstates):
        if eigenstates is not None:
            self._input_available = True  # The input is now available.
            print("AFViewer: The viewer has received the data.")
            print("AFViewer: %d modes received.\n"%(eigenstates.number_modes()))
            self.eigenstates = eigenstates
            self.info_energy.setText("Photon energy:   %5.3f eV"%eigenstates.photon_energy())
            self.info_nmodes.setText("Number of modes: %d"%eigenstates.number_modes())

    def _square_modulus(self,array1):
        return (numpy.absolute(array1))**2
    def do_plot(self):
        self.tab_titles = ["SPECTRUM","ALL MODES","MODE %d"%self.MODE_TO_PLOT]
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
            x_values = numpy.arange(self.eigenstates.number_modes())
            x_label = "Mode index"
            y_label =  "Occupation"


            xx = self.eigenstates.x_coordinates()
            yy = self.eigenstates.y_coordinates()

            xmin = numpy.min(xx)
            xmax = numpy.max(xx)
            ymin = numpy.min(yy)
            ymax = numpy.max(yy)

            integral1 = ((numpy.absolute(self.eigenstates.modes()[self.MODE_TO_PLOT,:,:]))**2).sum()*(xx[1]-xx[0])*(yy[1]-yy[0])
            integral1 = myprocess(self.eigenstates.modes()[self.MODE_TO_PLOT,:,:]).sum()
            integral1 *= (xx[1]-xx[0])*(yy[1]-yy[0])
            print("Integrated values for mode %d is %f"%(self.MODE_TO_PLOT,integral1))
        else:
            print("Nothing to plot")
            return

        #
        # plot spectrum
        #
        self.plot_canvas[0] = PlotWindow(parent=None,
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


        self.tab[0].layout().addWidget(self.plot_canvas[0])

        self.plot_canvas[0].setDefaultPlotLines(True)
        self.plot_canvas[0].setActiveCurveColor(color='darkblue')
        self.plot_canvas[0].setXAxisLogarithmic(False)
        self.plot_canvas[0].setYAxisLogarithmic(False)
        self.plot_canvas[0].setGraphXLabel(x_label)
        self.plot_canvas[0].setGraphYLabel(y_label)
        self.plot_canvas[0].addCurve(x_values, self.eigenstates.occupation_number_array(), title0, symbol='', xlabel="X", ylabel="Y", replace=False) #'+', '^', ','

        #
        # plot all modes
        #

        dim0_calib = (0, 1)
        dim1_calib = (1e6*yy[0], 1e6*(yy[1]-yy[0]))
        dim2_calib = (1e6*xx[0], 1e6*(xx[1]-xx[0]))


        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.plot_canvas[1] = StackViewMainWindow()
        self.plot_canvas[1].setGraphTitle(title1)
        self.plot_canvas[1].setLabels(["Mode number",
                                       "Y index from %4.2f to %4.2f um"%(1e6*ymin,1e6*ymax),
                                       "X index from %4.2f to %4.2f um"%(1e6*xmin,1e6*xmax)])
        self.plot_canvas[1].setColormap(colormap=colormap)
        self.plot_canvas[1].setStack( myprocess(numpy.swapaxes(self.eigenstates.modes(),2,1)),
                                      calibrations=[dim0_calib, dim1_calib, dim2_calib] )
        self.tab[1].layout().addWidget(self.plot_canvas[1])

        #
        # plot single mode
        #
        origin = (1e6*xmin, 1e6*ymin)
        scale = (1e6*abs((xmax-xmin)/self.eigenstates.x_coordinates().size),
                 1e6*abs((ymax-ymin)/self.eigenstates.y_coordinates().size))

        # origin = (0,0)
        # scale = (1,1)
        print("ZZ",self.eigenstates.modes().shape)
        print("XX",xx.size,1e6*xx.min(),1e6*xx[0],1e6*xx.max(),1e6*xx[-1])
        print("YY",yy.size,1e6*yy.min(),1e6*yy[0],1e6*yy.max(),1e6*yy[-1])

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}


        self.plot_canvas[2] = Plot2D()
        self.plot_canvas[2].resetZoom()
        self.plot_canvas[2].setXAxisAutoScale(True)
        self.plot_canvas[2].setYAxisAutoScale(True)
        self.plot_canvas[2].setGraphGrid(False)
        self.plot_canvas[2].setKeepDataAspectRatio(True)
        self.plot_canvas[2].yAxisInvertedAction.setVisible(False)
        self.plot_canvas[2].setXAxisLogarithmic(False)
        self.plot_canvas[2].setYAxisLogarithmic(False)
        self.plot_canvas[2].getMaskAction().setVisible(False)
        self.plot_canvas[2].getRoiAction().setVisible(False)
        self.plot_canvas[2].getColormapAction().setVisible(False)
        self.plot_canvas[2].setKeepDataAspectRatio(False)


        self.plot_canvas[2].addImage(myprocess( (self.eigenstates.modes()[self.MODE_TO_PLOT,:,:]).T ),
                                                     legend="zio billy",
                                                     colormap=colormap,
                                                     replace=True,
                                                     origin=origin,
                                                     scale=scale)

        self.plot_canvas[2].setActiveImage("zio billy")



        from matplotlib.image import AxesImage
        image = AxesImage(self.plot_canvas[2]._backend.ax)
        image.set_data(myprocess(self.eigenstates.modes()[self.MODE_TO_PLOT,:,:]))

        self.plot_canvas[2]._backend.fig.colorbar(image, ax=self.plot_canvas[2]._backend.ax)
        self.plot_canvas[2].setGraphXLabel("X [um]")
        self.plot_canvas[2].setGraphYLabel("Y [um]")
        self.plot_canvas[2].setGraphTitle(title1)

        self.tab[2].layout().addWidget(self.plot_canvas[2])



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



    app = QtGui.QApplication([])
    ow = OWAFViewer()

    filename = "/users/srio/OASYS_VE/oasys-comsyl/orangecontrib/comsyl/workspaces/tmp20.h5"
    filename = "/users/srio/OASYS1_VE/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.npz"
    # filename = "/users/srio/OASYS1_VE/oasys-comsyl/orangecontrib/comsyl/util/tmp20.h5"

    eigenstates = CompactAFReader.initialize_from_file(filename)

    ow._set_input(eigenstates)
    ow.do_plot()
    ow.show()

    app.exec_()
    ow.saveSettings()
