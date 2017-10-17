__author__ = 'labx'

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QMessageBox
from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from wofry.propagator.wavefront1D.generic_wavefront import GenericWavefront1D
from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

from orangecontrib.wofry.widgets.gui.ow_wofry_widget import WofryWidget

class ComsylWavefrontViewer2D(WofryWidget):

    name = "Wavefront Viewer 2D"
    id = "WavefrontViewer2D"
    description = "Wavefront Viewer 2D"
    icon = "icons/accumulation.png"
    priority = 40

    category = ""
    keywords = ["data", "file", "load", "read"]

    inputs = [("GenericWavefront2D", GenericWavefront2D, "set_input")]

    wavefront2D = None

    def __init__(self):
        super().__init__(is_automatic=False, show_view_options=False)

        self.accumulated_data = None

        gui.separator(self.controlArea)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")




        button = gui.button(button_box, self, "Refresh", callback=self.refresh)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")
        button = gui.button(button_box, self, "Reset Accumulated Wavefronts", callback=self.reset_accumumation)
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
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT+50)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_sou = oasysgui.createTabPage(tabs_setting, "Wavefront Viewer Settings")

    def initializeTabs(self):
        size = len(self.tab)
        indexes = range(0, size)

        for index in indexes:
            self.tabs.removeTab(size-1-index)

        titles = ["Wavefront 2D Intensity"]
        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(titles)):
            self.tab.append(gui.createTabPage(self.tabs, titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)


    def set_input(self, wavefront2D):
        if not wavefront2D is None:
            self.wavefront2D = wavefront2D

            self.do_plot_results(0) #refresh()

    def refresh(self):
        self.progressBarInit()

        self.plot_data2D(data2D=self.accumulated_data["intensity"],
                         dataX=self.accumulated_data["x"],
                         dataY=self.accumulated_data["y"],
                         progressBarValue=10,
                         tabs_canvas_index=0,
                         plot_canvas_index=0,
                         title="Wavefront 2D Intensity",
                         xtitle="Horizontal Coordinate",
                         ytitle="Vertical Coordinate")

        self.progressBarFinished()


    def do_plot_results(self, progressBarValue):
        if not self.wavefront2D is None:

            self.progressBarSet(progressBarValue)

            titles = ["Wavefront 2D Intensity"] #, "Wavefront 2D Phase"]


            if self.accumulated_data is None:
                self.accumulated_data = {}
                self.accumulated_data["intensity"] = self.wavefront2D.get_intensity()
                self.accumulated_data["x"] = self.wavefront2D.get_coordinate_x()
                self.accumulated_data["y"] = self.wavefront2D.get_coordinate_y()
            else:
                self.accumulated_data["intensity"] += self.wavefront2D.get_intensity()




            self.plot_data2D(data2D=self.accumulated_data["intensity"],
                             dataX=self.accumulated_data["x"],
                             dataY=self.accumulated_data["y"],
                             progressBarValue=progressBarValue+10,
                             tabs_canvas_index=0,
                             plot_canvas_index=0,
                             title="Wavefront 2D Intensity",
                             xtitle="Horizontal Coordinate",
                             ytitle="Vertical Coordinate")


            self.progressBarFinished()

    def reset_accumumation(self):
        try:
            self.progressBarInit()

            self.set_input(GenericWavefront2D.initialize_wavefront_from_range(-1e-3,1e-3,-1e-3,1e-3,(200,200)))

            self.accumulated_data = None

            self.progressBarFinished()
        except:
            pass

if __name__ == '__main__':

    from PyQt5.QtWidgets import QApplication

    app = QApplication([])
    ow = ComsylWavefrontViewer2D()

    ow.set_input(GenericWavefront2D.initialize_wavefront_from_range(-1e-3,1e-3,-1e-3,1e-3,(200,200)))

    ow.show()

    app.exec_()
    ow.saveSettings()