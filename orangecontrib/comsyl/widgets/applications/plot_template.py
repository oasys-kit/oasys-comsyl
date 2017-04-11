from PyQt4 import QtGui
# from orangewidget import widget, gui
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


from PyQt4.QtGui import QIntValidator, QDoubleValidator, QApplication
from PyQt4.QtCore import QRect

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import OWAction
from oasys.widgets import widget
from oasys.widgets import gui as oasysgui
from oasys.widgets.exchange import DataExchangeObject

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
                "type": np.ndarray,
                "doc": "",
                "handler": "do_plot" },
                ]

    TYPE_PRESENTATION = Setting(0)
    TAB_NUMBER = Setting(0)
    MACHINE_R_M = Setting(25.0)
    BFIELD_T = Setting(0.8)


    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 560

    view_type=Setting(1)

    calculated_data = Setting(None)

    want_main_area = 1


    def unitLabels(self):
         return ['Type of presentation','Tab number:','Parameter 1','Parameter 2']
    def unitFlags(self):
         return ['True','True','self.TYPE_PRESENTATION  ==  0','self.TAB_NUMBER  ==  1',]

    def __init__(self):
        # super().__init__()
        # self.figure_canvas = None
        # self.build_gui()
        super().__init__()

        # self.runaction = OWAction("Compute", self)
        # self.runaction.triggered.connect(self.compute)
        # self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        # box0 = gui.widgetBox(self.controlArea, "", orientation="horizontal")
        #widget buttons: compute, set defaults, help
        # gui.button(box0, self, "Compute", callback=self.compute)
        # gui.button(box0, self, "Defaults", callback=self.defaults)
        # gui.button(box0, self, "Help", callback=self.help1)

        gui.separator(self.controlArea, height=10)

        self.build_gui()

        self.process_showers()

        gui.rubber(self.controlArea)

        self.main_tabs = gui.tabWidget(self.mainArea)
        plot_tab = gui.createTabPage(self.main_tabs, "Results")
        # out_tab = gui.createTabPage(self.main_tabs, "Output")



        # view_box = oasysgui.widgetBox(plot_tab, "Results Options", addSpace=False, orientation="horizontal")
        # view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)
        #
        # self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="View Results",
        #                                     labelWidth=220,
        #                                     items=["No", "Yes"],
        #                                     callback=self.set_ViewType, sendSelectedValue=False, orientation="horizontal")

        self.tab = []
        self.tabs = gui.tabWidget(plot_tab)

        self.initializeTabs()

        # self.xoppy_output = QtGui.QTextEdit()
        # self.xoppy_output.setReadOnly(True)
        #
        # out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        # out_box.layout().addWidget(self.xoppy_output)
        #
        # self.xoppy_output.setFixedHeight(600)
        # self.xoppy_output.setFixedWidth(600)
        #
        # gui.rubber(self.mainArea)

    # def compute(self):
    #     pass
    #
    # def defaults(self):
    #     pass
    #
    # def help1(self):
    #     pass

    def set_ViewType(self):
        self.progressBarInit()

        if not self.calculated_data==None:
            try:
                self.initializeTabs()

                self.plot_results(self.calculated_data)
            except Exception as exception:
                QtGui.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtGui.QMessageBox.Ok)

        self.progressBarFinished()

    def initializeTabs(self):
        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = ["TAB 1","TAB 2"]

        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(titles)):
            self.tab.append(gui.createTabPage(self.tabs, titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

    def figure_canvas(self):
        pass

    def build_gui(self):

        box = oasysgui.widgetBox(self.controlArea, " Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        idx = -1

        #widget index 0
        idx += 1
        box1 = gui.widgetBox(box)
        gui.comboBox(box1, self, "TYPE_PRESENTATION",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['matplotlib/gol', 'silx',],
                    valueType=int, orientation="horizontal", callback=self.set_TYPE_CALC)
        self.show_at(self.unitFlags()[idx], box1)


        #widget index 2
        idx += 1
        box1 = gui.widgetBox(box)
        gui.comboBox(box1, self, "TAB_NUMBER",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['TAB 1', 'TAB 2'],
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


    def set_TYPE_CALC(self):
        pass
        # self.initializeTabs()
        # if self.TYPE_PRESENTATION == 3:
        #         self.VER_DIV = 2

    def do_plot(self,custom_data=None,kind="silx"):

        if custom_data is not None:
            x = custom_data[0,:]
            y = custom_data[-1,:]
            x.shape = -1
            y.shape = -1
            print(">>>>",x.shape,y.shape)
        else:
            print("Nothing to plot")
            return

        if kind == "gol":
            figure = FigureCanvas(gol.plot(x,y,show=False,))
            self.plot_canvas[0] = figure
            # self.figure_canvas = figure
            self.tab[0].layout().addWidget(self.plot_canvas[0])
        elif kind == "silx":
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
            self.plot_canvas[0].setGraphXLabel("title")
            self.plot_canvas[0].setGraphYLabel("title")

            self.plot_canvas[0].addCurve(x, y, "TITLE", symbol='', color="darkblue", xlabel="X", ylabel="Y", replace=False) #'+', '^', ','
            # self.plot_canvas[0].setDrawModeEnabled(True, 'rectangle')
            # self.plot_canvas[0].setZoomModeEnabled(True)
            # self.plot_canvas[0].resetZoom()
            # self.plot_canvas[0].replot()



        return

if __name__ == '__main__':
    app = QtGui.QApplication([])
    ow = OWPlotTemplate()
    a = np.array([
        [  8.47091837e+04,  8.57285714e+04,   8.67479592e+04, 8.77673469e+04,] ,
        [  1.16210756e+12,  1.10833975e+12,   1.05700892e+12, 1.00800805e+12]
        ])
    ow.do_plot(a)
    ow.show()
    app.exec_()
    ow.saveSettings()
