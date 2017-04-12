

import numpy

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from PyQt4 import QtGui
from PyQt4.QtGui import QIntValidator, QDoubleValidator, QApplication
from PyQt4.QtCore import QRect

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import widget
from oasys.widgets import gui as oasysgui

from srxraylib.plot import gol
from silx.gui.plot import PlotWindow, Plot2D


class OWPlotTemplate(widget.OWWidget):
    name = "Plot Simple"
    id = "orange.widgets.data.widget_name"
    description = ""
    icon = "icons/plot_simple.png"
    author = ""
    maintainer_email = ""
    priority = 10
    category = ""
    keywords = ["list", "of", "keywords"]
    inputs = [{"name": "oasysaddontemplate-data",
                "type": numpy.ndarray,
                "doc": "",
                "handler": "do_plot" },
                ]

    TYPE_PRESENTATION = Setting(0) # 0=gol, 1=silx
    TAB_NUMBER = Setting(0)
    MACHINE_R_M = Setting(25.0)
    BFIELD_T = Setting(0.8)


    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    # TABS_AREA_HEIGHT = 560

    view_type=Setting(1)

    calculated_data = Setting(None)


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
        self.initializeTabs(titles=["TAB 0","TAB 1"])


    def initializeTabs(self,titles):

        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(titles)):
            self.tab.append(gui.createTabPage(self.tabs, titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)


    def set_calculated_data(self,data):
        self.calculated_data = data


    def build_left_panel(self):

        box = oasysgui.widgetBox(self.controlArea, " Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        idx = -1

        #widget index 0
        idx += 1
        box1 = gui.widgetBox(box)
        gui.comboBox(box1, self, "TYPE_PRESENTATION",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['matplotlib/gol', 'silx',],
                    valueType=int, orientation="horizontal", callback=self.change_TYPE_PRESENTATION)
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


    def change_TYPE_PRESENTATION(self):
        print("in change_TYPE_PRESENTAION")
        self.do_plot()


    def do_plot(self):

        print("self.TAB_NUMBER = ",self.TAB_NUMBER)
        self.tab[self.TAB_NUMBER].layout().removeItem(self.tab[self.TAB_NUMBER].layout().itemAt(0))



        if self.calculated_data is not None:
            x = self.calculated_data["x"]
            y = self.calculated_data["y"]
            x.shape = -1
            y.shape = -1
        else:
            print("Nothing to plot")
            return

        if self.TYPE_PRESENTATION == 0: # matplotlib
            figure = FigureCanvas(gol.plot(x,y,show=False,))
            self.plot_canvas[self.TAB_NUMBER] = figure
            self.tab[self.TAB_NUMBER].layout().addWidget(self.plot_canvas[self.TAB_NUMBER])
        elif self.TYPE_PRESENTATION == 1: # silx
            self.plot_canvas[self.TAB_NUMBER] = PlotWindow(parent=None,
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


            self.tab[self.TAB_NUMBER].layout().addWidget(self.plot_canvas[self.TAB_NUMBER])

            self.plot_canvas[self.TAB_NUMBER].setDefaultPlotLines(True)
            self.plot_canvas[self.TAB_NUMBER].setActiveCurveColor(color='darkblue')
            self.plot_canvas[self.TAB_NUMBER].setXAxisLogarithmic(False)
            self.plot_canvas[self.TAB_NUMBER].setYAxisLogarithmic(False)
            self.plot_canvas[self.TAB_NUMBER].setGraphXLabel("title")
            self.plot_canvas[self.TAB_NUMBER].setGraphYLabel("title")
            self.plot_canvas[self.TAB_NUMBER].addCurve(x, y, "TITLE", symbol='', color="darkblue", xlabel="X", ylabel="Y", replace=False) #'+', '^', ','
        #

if __name__ == '__main__':
    app = QtGui.QApplication([])
    ow = OWPlotTemplate()

    ow.set_calculated_data({"x":numpy.array([  8.47091837e+04,  8.57285714e+04,   8.67479592e+04, 8.77673469e+04]),
                            "y":numpy.array([  1.16210756e+12,  1.10833975e+12,   1.05700892e+12, 1.00800805e+12]) })
    ow.do_plot()
    ow.show()
    app.exec_()
    ow.saveSettings()
