__author__ = 'srio'

import numpy

from PyQt5.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

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
    accumulated_data = None

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

        titles = titles = ["Wavefront 2D Intensity","W(x1,0,x2,0)","W(0,y1,0,y2)"] #, "Wavefront 2D Phase"]
        self.tab = []
        self.plot_canvas = []

        for index in range(0, len(titles)):
            self.tab.append(gui.createTabPage(self.tabs, titles[index]))
            self.plot_canvas.append(None)

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)


    def crossSpectralDensityHV(self):

        WF = self.wavefront2D.get_complex_amplitude()
        imodeX = WF[:,int(0.5*WF.shape[1])]
        imodeY = WF[int(0.5*WF.shape[0]),:]

        Wx1x2 =  numpy.outer( numpy.conj(imodeX) , imodeX ) #* self.eigenvalue(i)
        Wy1y2 =  numpy.outer( numpy.conj(imodeY) , imodeY ) #* self.eigenvalue(i)


        return Wx1x2,Wy1y2

    def set_input(self, wf):

        if not wf is None:

            self.wavefront2D = wf

            Wx1x2,Wy1y2  = self.crossSpectralDensityHV()

            if self.accumulated_data is None:
                self.accumulated_data = {}
                self.accumulated_data["intensity"] = self.wavefront2D.get_intensity()


                self.accumulated_data["W_x1_0_x2_0"] = Wx1x2
                self.accumulated_data["W_0_y1_0_y2"] = Wy1y2
                self.accumulated_data["x"] = self.wavefront2D.get_coordinate_x()
                self.accumulated_data["y"] = self.wavefront2D.get_coordinate_y()

            else:
                self.accumulated_data["intensity"] += self.wavefront2D.get_intensity()
                self.accumulated_data["W_x1_0_x2_0"] += Wx1x2
                self.accumulated_data["W_0_y1_0_y2"] += Wy1y2

            self.progressBarInit()
            self.do_plot_results(10) #refresh()

    def refresh(self):


        self.do_plot_results(10)  # TODO: check progressBar...




    def do_plot_results(self, progressBarValue):

        if self.accumulated_data is None:
            return
        else:
            self.progressBarInit()
            self.progressBarSet(progressBarValue)

            # titles = ["Wavefront 2D Intensity","W(x1,0,x2,0)","W(0,y1,0,y2)"] #, "Wavefront 2D Phase"]

            self.plot_data2D(data2D=self.accumulated_data["intensity"],
                             dataX=1e6*self.accumulated_data["x"],
                             dataY=1e6*self.accumulated_data["y"],
                             progressBarValue=progressBarValue+10,
                             tabs_canvas_index=0,
                             plot_canvas_index=0,
                             title="Wavefront 2D Intensity",
                             xtitle="Horizontal Coordinate [$\mu$m]",
                             ytitle="Vertical Coordinate [$\mu$m]")

            self.plot_data2D(data2D=numpy.abs(self.accumulated_data["W_x1_0_x2_0"]),
                             dataX=1e6*self.accumulated_data["x"],
                             dataY=1e6*self.accumulated_data["y"],
                             progressBarValue=progressBarValue+10,
                             tabs_canvas_index=1,
                             plot_canvas_index=0,
                             title="Cross spectral density (horizontal, at y=0)",
                             xtitle="Horizontal Coordinate x1 [$\mu$m]",
                             ytitle="Horizontal Coordinate x2 [$\mu$m]")

            self.plot_data2D(data2D=numpy.abs(self.accumulated_data["W_0_y1_0_y2"]),
                             dataX=1e6*self.accumulated_data["x"],
                             dataY=1e6*self.accumulated_data["y"],
                             progressBarValue=progressBarValue+10,
                             tabs_canvas_index=2,
                             plot_canvas_index=0,
                             title="Cross spectral density (vertical, at x=0)",
                             xtitle="Vertical Coordinate y1 [$\mu$m]",
                             ytitle="Vertical Coordinate y2 [$\mu$m]")

            self.progressBarFinished()

    def reset_accumumation(self):

        self.initializeTabs()
        self.accumulated_data = None
        self.wavefront2D = None

        # try:
        #     if self.accumulated_data is not None:
        #         self.progressBarInit()
        #         self.accumulated_data["intensity"] *= 0.0
        #         self.accumulated_data["W_x1_0_x2_0"] *= 0.0
        #         self.accumulated_data["W_0_y1_0_y2"] *= 0.0
        #         self.progressBarInit()
        #         self.set_input(None) # GenericWavefront2D.initialize_wavefront_from_range(-1e-3,1e-3,-1e-3,1e-3,(200,200)))
        #         self.do_plot_results(10)
        #         self.progressBarFinished()
        # except:
        #     pass

if __name__ == '__main__':

    from PyQt5.QtWidgets import QApplication
    from orangecontrib.comsyl.util.CompactAFReader import CompactAFReader

    app = QApplication([])
    ow = ComsylWavefrontViewer2D()


    filename_np = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.npz"
    af = CompactAFReader.initialize_from_file(filename_np)
    wf = GenericWavefront2D.initialize_wavefront_from_arrays(af.x_coordinates(),
                                                             af.y_coordinates(),
                                                             af.mode(0))
    wf.set_photon_energy(af.photon_energy())


    # wf = GenericWavefront2D.initialize_wavefront_from_range(-1e-3,1e-3,-1e-3,1e-3,(200,200))
    # wf.set_gaussian(1e-4,1e-4)

    ow.set_input(wf)
    ow.show()
    app.exec_()
    ow.saveSettings()