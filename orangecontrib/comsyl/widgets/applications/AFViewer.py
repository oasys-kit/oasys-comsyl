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

from comsyl.scripts.CompactAFReader import CompactAFReader


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
    TAB_NUMBER = Setting(0)
    MACHINE_R_M = Setting(25.0)
    BFIELD_T = Setting(0.8)


    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    # TABS_AREA_HEIGHT = 560


    def unitLabels(self):
         return ['Type of presentation','Tab number:','Parameter 1','Parameter 2']
    def unitFlags(self):
         return ['True','True','self.TYPE_PRESENTATION  ==  0','self.TAB_NUMBER  ==  1',]

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
        self.tab_titles = ["SPECTRUM","MODES"]
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

        box = oasysgui.widgetBox(self.controlArea, " Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        idx = -1

        #widget index 0
        idx += 1
        box1 = gui.widgetBox(box)
        gui.comboBox(box1, self, "TYPE_PRESENTATION",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['modulus','real part','imaginary part','angle [rad]'],
                    valueType=int, orientation="horizontal", callback=self.do_plot)
        self.show_at(self.unitFlags()[idx], box1)


        #widget index 2
        idx += 1
        box1 = gui.widgetBox(box)
        gui.comboBox(box1, self, "TAB_NUMBER",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['TAB 0', 'TAB 1'],
                    valueType=int, orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index 3
        idx += 1
        box1 = gui.widgetBox(box)
        oasysgui.lineEdit(box1, self, "MACHINE_R_M",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=float, validator=QDoubleValidator(), orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index 4
        idx += 1
        box1 = gui.widgetBox(box)
        oasysgui.lineEdit(box1, self, "BFIELD_T",
                     label=self.unitLabels()[idx], addSpace=False,
                    valueType=float, validator=QDoubleValidator(), orientation="horizontal", labelWidth=250)
        self.show_at(self.unitFlags()[idx], box1)


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

    def do_plot(self):
        self.initializeTabs()
        self.tab[0].layout().removeItem(self.tab[0].layout().itemAt(0))
        self.tab[1].layout().removeItem(self.tab[1].layout().itemAt(0))

        if self.TYPE_PRESENTATION == 0:
            myprocess = numpy.absolute
            title0 = "Modulus of eigenvalues"
            title1 = "Modulus of eigenvectors"
        elif self.TYPE_PRESENTATION == 1:
            myprocess = numpy.real
            title0 = "Real part of eigenvalues"
            title1 = "Real part of eigenvectors"
        elif self.TYPE_PRESENTATION == 2:
            myprocess = numpy.imag
            title0 = "Imaginary part of eigenvalues"
            title1 = "Imaginary part of eigenvectors"
        elif self.TYPE_PRESENTATION == 3:
            myprocess = numpy.angle

        if self._input_available:
            x_values = numpy.arange(self.eigenstates.number_modes())
            x_label = "Mode index"
            y_label =  "Occupation"
            y_values = numpy.zeros(self.eigenstates.number_modes())

            mystack = numpy.zeros((self.eigenstates.number_modes(),
                                self.eigenstates.y_coordinates().size,
                                self.eigenstates.x_coordinates().size),
                                dtype=complex)
            print("mystack shape: ",mystack.shape)

            for i_mode in range(self.eigenstates.number_modes()):
                y_values[i_mode] = myprocess(self.eigenstates.occupation_number(i_mode))
                mode = myprocess(self.eigenstates.mode(i_mode))
                mystack[i_mode,:,:] = mode.T
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
        self.plot_canvas[0].addCurve(x_values, y_values, "TITLE", symbol='', color="darkblue", xlabel="X", ylabel="Y", replace=False) #'+', '^', ','

        #
        # plot modes
        #
        xmin = numpy.min(self.eigenstates.x_coordinates())
        xmax = numpy.max(self.eigenstates.x_coordinates())
        ymin = numpy.min(self.eigenstates.y_coordinates())
        ymax = numpy.max(self.eigenstates.y_coordinates())

        origin = (xmin, ymin)
        scale = (abs((xmax-xmin)/len(self.eigenstates.x_coordinates())), abs((ymax-ymin)/len(self.eigenstates.y_coordinates())))

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.plot_canvas[1] = StackViewMainWindow()
        self.plot_canvas[1].setGraphTitle("Eigenvectors")
        self.plot_canvas[1].setLabels(["Mode number","Y","X"])
        self.plot_canvas[1].setColormap(colormap=colormap)
        self.plot_canvas[1].setStack(numpy.absolute(mystack)) # , origin=origin, scale=scale,  )
        self.tab[1].layout().addWidget(self.plot_canvas[1])


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

    filename = "/users/srio/OASYS_VE/comsyl_srio/calculations/new_u18_2m_1h_s2.5"
    eigenstates = CompactAFReader(filename)

    ow._set_input(eigenstates)
    ow.do_plot()
    ow.show()

    app.exec_()
    ow.saveSettings()
