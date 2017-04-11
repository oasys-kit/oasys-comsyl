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

    TYPE_CALC = Setting(0)
    MACHINE_NAME = Setting("ESRF bending magnet")
    RB_CHOICE = Setting(0)
    MACHINE_R_M = Setting(25.0)
    BFIELD_T = Setting(0.8)


    IMAGE_WIDTH = 760
    IMAGE_HEIGHT = 545
    MAX_WIDTH = 1320
    MAX_HEIGHT = 700
    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 560

    view_type=Setting(1)

    calculated_data = None

    want_main_area = 1


    def unitLabels(self):
         return ['Type of calculation','Machine name','B from:','Machine Radius [m]','Magnetic Field [T]']
    def unitFlags(self):
         return ['True','True','True','self.RB_CHOICE  ==  0','self.RB_CHOICE  ==  1',]

    def __init__(self):
        # super().__init__()
        # self.figure_canvas = None
        # self.build_gui()
        super().__init__()

        self.runaction = OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        box0 = gui.widgetBox(self.controlArea, "", orientation="horizontal")
        #widget buttons: compute, set defaults, help
        gui.button(box0, self, "Compute", callback=self.compute)
        gui.button(box0, self, "Defaults", callback=self.defaults)
        gui.button(box0, self, "Help", callback=self.help1)

        gui.separator(self.controlArea, height=10)

        self.build_gui()

        self.process_showers()

        gui.rubber(self.controlArea)

        self.main_tabs = gui.tabWidget(self.mainArea)
        plot_tab = gui.createTabPage(self.main_tabs, "Results")
        out_tab = gui.createTabPage(self.main_tabs, "Output")

        view_box = oasysgui.widgetBox(plot_tab, "Results Options", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="View Results",
                                            labelWidth=220,
                                            items=["No", "Yes"],
                                            callback=self.set_ViewType, sendSelectedValue=False, orientation="horizontal")

        self.tab = []
        self.tabs = gui.tabWidget(plot_tab)

        self.initializeTabs()

        self.xoppy_output = QtGui.QTextEdit()
        self.xoppy_output.setReadOnly(True)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.xoppy_output)

        self.xoppy_output.setFixedHeight(600)
        self.xoppy_output.setFixedWidth(600)

        gui.rubber(self.mainArea)

    def compute(self):
        pass

    def defaults(self):
        pass

    def help1(self):
        pass

    def set_ViewType(self):
        pass

    def initializeTabs(self):
        pass

    def figure_canvas(self):
        pass

    def build_gui(self):

        box = oasysgui.widgetBox(self.controlArea, " Input Parameters", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5)

        idx = -1

        #widget index 0
        idx += 1
        box1 = gui.widgetBox(box)
        gui.comboBox(box1, self, "TYPE_CALC",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['Energy or Power spectra', 'Angular distribution (all wavelengths)', 'Angular distribution (one wavelength)', '2D flux and power (angular,energy) distribution'],
                    valueType=int, orientation="horizontal", callback=self.set_TYPE_CALC)
        self.show_at(self.unitFlags()[idx], box1)

        #widget index 1
        idx += 1
        box1 = gui.widgetBox(box)
        oasysgui.lineEdit(box1, self, "MACHINE_NAME",
                     label=self.unitLabels()[idx], addSpace=False, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1)

        #widget index 2
        idx += 1
        box1 = gui.widgetBox(box)
        gui.comboBox(box1, self, "RB_CHOICE",
                     label=self.unitLabels()[idx], addSpace=False,
                    items=['Magnetic Radius', 'Magnetic Field'],
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

        self.initializeTabs()
        if self.TYPE_CALC == 3:
                self.VER_DIV = 2

    def do_plot(self,custom_data):
        x = custom_data[0,:]
        y = custom_data[-1,:]
        x.shape = -1
        y.shape = -1
        # fig = plt.figure()
        # plt.plot(x,y,linewidth=1.0, figure=fig)
        # plt.grid(True)
        # if self.figure_canvas is not None:
        #     self.mainArea.layout().removeWidget(self.figure_canvas)
        # self.figure_canvas = FigureCanvas(fig) #plt.figure())
        # self.mainArea.layout().addWidget(self.figure_canvas)

        if not self.view_type == 0:
            if not calculated_data is None:
                self.view_type_combo.setEnabled(False)

                xoppy_data = calculated_data.get_content("xoppy_data")

                titles = self.getTitles()
                xtitles = self.getXTitles()
                ytitles = self.getYTitles()

                progress_bar_step = (100-progressBarValue)/len(titles)

                for index in range(0, len(titles)):
                    x_index, y_index = self.getVariablesToPlot()[index]
                    log_x, log_y = self.getLogPlot()[index]

                    try:
                        self.plot_histo(xoppy_data[:, x_index],
                                        xoppy_data[:, y_index],
                                        progressBarValue + ((index+1)*progress_bar_step),
                                        tabs_canvas_index=index,
                                        plot_canvas_index=index,
                                        title=titles[index],
                                        xtitle=xtitles[index],
                                        ytitle=ytitles[index],
                                        log_x=log_x,
                                        log_y=log_y)

                        self.tabs.setCurrentIndex(index)
                    except Exception as e:
                        self.view_type_combo.setEnabled(True)

                        raise Exception("Data not plottable: bad content\n" + str(e))

                self.view_type_combo.setEnabled(True)
            else:
                raise Exception("Empty Data")

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
