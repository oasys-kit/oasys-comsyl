
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QApplication, QSizePolicy
from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget import widget
from oasys.widgets import widget as oasyswidget, gui as oasysgui
import orangecanvas.resources as resources
import sys
import os
import numpy

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

class OWWavefront2DResample(oasyswidget.OWWidget):
    name = "Wavefront2DResample"
    id = "orange.widgets.dataWavefront2DResample"
    description = "Application to compute..."
    icon = "icons/Wavefront2DResample.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 40

    category = ""
    keywords = ["oasysaddontemplate", "Wavefront2DResample", "data", "file", "load", "read"]

    inputs  = [("GenericWavefront2D", GenericWavefront2D, "set_input")]
    outputs = [("GenericWavefront2D", GenericWavefront2D)]

    # outputs = [{"name": "oasysaddontemplate-data",
    #             "type": np.ndarray,
    #             "doc": "transfer numpy arrays"},
               # another possible output
               # {"name": "oasysaddontemplate-file",
               #  "type": str,
               #  "doc": "transfer a file"},
               #  ]

    # widget input (if needed)
    #inputs = [{"name": "Name",
    #           "type": type,
    #           "handler": None,
    #           "doc": ""}]

    want_main_area = False

    DIRECTION = Setting(2)
    TYPE_POINTS_X = Setting(0)
    RELATIVE_POINTS_X = Setting(1.0)
    ABSOLUTE_POINTS_X = Setting(1024)
    TYPE_POINTS_Y = Setting(0)
    RELATIVE_POINTS_Y = Setting(1.0)
    ABSOLUTE_POINTS_Y = Setting(1024)
    TYPE_INTERVAL_X = Setting(0)
    RELATIVE_INTERVAL_X = Setting(1.0)
    ABSOLUTE_INTERVAL_XMIN = Setting(-0.001)
    ABSOLUTE_INTERVAL_XMAX = Setting(0.001)
    TYPE_INTERVAL_Y = Setting(0)
    RELATIVE_INTERVAL_Y = Setting(1.0)
    ABSOLUTE_INTERVAL_YMIN = Setting(-0.001)
    ABSOLUTE_INTERVAL_YMAX = Setting(0.001)
    KEEP_INTENSITY = Setting(1)
    EXTRAPOLATION_TO_ZERO = Setting(1)

    wavefront2D = None

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Compute", self)
        self.runaction.triggered.connect(self.compute)
        self.addAction(self.runaction)

        box0 = gui.widgetBox(self.controlArea, " ",orientation="horizontal") 
        #widget buttons: compute, set defaults, help
        gui.button(box0, self, "Compute", callback=self.compute)
        gui.button(box0, self, "Defaults", callback=self.defaults)
        gui.button(box0, self, "Help", callback=self.get_doc)
        self.process_showers()
        box = gui.widgetBox(self.controlArea, " ",orientation="vertical") 
        
        
        idx = -1 
        
        #widget index 0 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "DIRECTION",
                     label=self.unitLabels()[idx], addSpace=True,
                    items=['Horizontal (X)', 'Vertical (Y)', 'Both', 'None'],
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 1 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "TYPE_POINTS_X",
                     label=self.unitLabels()[idx], addSpace=True,
                    items=['Expansion factor', 'Absolute value'],
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 2 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "RELATIVE_POINTS_X",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 3 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "ABSOLUTE_POINTS_X",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=int, validator=QIntValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 4 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "TYPE_POINTS_Y",
                     label=self.unitLabels()[idx], addSpace=True,
                    items=['Expansion factor', 'Absolute value'],
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 5 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "RELATIVE_POINTS_Y",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 6 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "ABSOLUTE_POINTS_Y",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=int, validator=QIntValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 7 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "TYPE_INTERVAL_X",
                     label=self.unitLabels()[idx], addSpace=True,
                    items=['Expansion factor', 'Absolute value'],
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 8 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "RELATIVE_INTERVAL_X",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 9 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "ABSOLUTE_INTERVAL_XMIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 10 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "ABSOLUTE_INTERVAL_XMAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 11 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "TYPE_INTERVAL_Y",
                     label=self.unitLabels()[idx], addSpace=True,
                    items=['Expansion factor', 'Absolute value'],
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 12 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "RELATIVE_INTERVAL_Y",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 13 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "ABSOLUTE_INTERVAL_YMIN",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 14 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "ABSOLUTE_INTERVAL_YMAX",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 15 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "KEEP_INTENSITY",
                     label=self.unitLabels()[idx], addSpace=True,
                    items=['No', 'Yes'],
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1) 
        
        #widget index 16 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.comboBox(box1, self, "EXTRAPOLATION_TO_ZERO",
                     label=self.unitLabels()[idx], addSpace=True,
                    items=['No', 'Yes'],
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1) 

        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Resampling direction ',\
                 'Resample number of pixels (Horizontal) by ','Scaling N factor (Horizontal) ','New number of pixels (Horizontal)',\
                 'Resample number of pixels (Vertical) by ',  'Scaling N factor (Vertical) ','New number of pixels (Vertical)',\
                 'Resample interval (Horizontal) by ','Scaling interval factor (Horizontal) ','New X min: ','New X max: ',\
                 'Resample interval (Vertical) by ',  'Scaling interval factor (Vertical) ','New Y min: ','New Y max: ',\
                 'Keep the same intensity','Set extrapolation to zero']


    def unitFlags(self):
         return ['True',\
                 '(self.DIRECTION == 0 or self.DIRECTION == 2)','(self.DIRECTION == 0 or self.DIRECTION == 2) and self.TYPE_POINTS_X == 0','(self.DIRECTION == 0 or self.DIRECTION == 2) and self.TYPE_POINTS_X == 1',\
                 '(self.DIRECTION == 1 or self.DIRECTION == 2)','(self.DIRECTION == 1 or self.DIRECTION == 2) and self.TYPE_POINTS_Y == 0','(self.DIRECTION == 1 or self.DIRECTION == 2) and self.TYPE_POINTS_Y == 1',\
                 '(self.DIRECTION == 0 or self.DIRECTION == 2)','(self.DIRECTION == 0 or self.DIRECTION == 2) and self.TYPE_INTERVAL_X == 0','(self.DIRECTION == 0 or self.DIRECTION == 2) and self.TYPE_INTERVAL_X == 1','(self.DIRECTION == 0 or self.DIRECTION == 2) and self.TYPE_INTERVAL_X == 1',\
                 '(self.DIRECTION == 1 or self.DIRECTION == 2)','(self.DIRECTION == 1 or self.DIRECTION == 2) and self.TYPE_INTERVAL_Y == 0','(self.DIRECTION == 1 or self.DIRECTION == 2) and self.TYPE_INTERVAL_Y == 1','(self.DIRECTION == 1 or self.DIRECTION == 2) and self.TYPE_INTERVAL_Y == 1',\
                 'self.DIRECTION < 3','self.DIRECTION < 3']


    def compute(self):

        if self.wavefront2D is None:
            print(">>>>>>>>>>>>> Nothing to send!")
        else:
            if self.DIRECTION == 3: # nothing to do
                print(">>>>>>> sending intact wavefront ")
                self.send("GenericWavefront2D", self.wavefront2D)
                return

            x0 = self.wavefront2D.get_coordinate_x()
            y0 = self.wavefront2D.get_coordinate_y()

            nx0 = x0.size
            ny0 = y0.size

            nx1 = nx0
            ny1 = ny0

            x1_min = x0[0]
            x1_max = x0[-1]
            y1_min = y0[0]
            y1_max = y0[-1]

            if self.DIRECTION == 0 or self.DIRECTION == 2:
                if self.TYPE_POINTS_X == 0:
                    nx1 = int(nx0 * self.RELATIVE_POINTS_X)
                elif self.TYPE_POINTS_X == 1:
                    nx1 = self.ABSOLUTE_POINTS_X
                else:
                    pass

                if self.TYPE_INTERVAL_X == 0:
                    x1_min = x0[0] * self.RELATIVE_INTERVAL_X
                    x1_max = x0[-1] * self.RELATIVE_INTERVAL_X
                else:
                    x1_min = self.ABSOLUTE_INTERVAL_XMIN
                    x1_max = self.ABSOLUTE_INTERVAL_XMAX


            if self.DIRECTION == 1 or self.DIRECTION == 2:
                if self.TYPE_POINTS_Y == 0:
                    ny1 = int(ny0 * self.RELATIVE_POINTS_Y)
                elif self.TYPE_POINTS_Y == 1:
                    ny1 = self.ABSOLUTE_POINTS_Y
                else:
                    pass

                if self.TYPE_INTERVAL_Y == 0:
                    y1_min = y0[0] * self.RELATIVE_INTERVAL_Y
                    y1_max = y0[-1] * self.RELATIVE_INTERVAL_Y
                else:
                    y1_min = self.ABSOLUTE_INTERVAL_YMIN
                    y1_max = self.ABSOLUTE_INTERVAL_YMAX


            print(">>>> X0min: %f,  X0max: %f, Nx0: %d"%(x0[0],x0[-1],nx0))
            print(">>>> Y0min: %f,  Y0max: %f, Ny0: %d"%(y0[0],y0[-1],ny0))
            print(">>>> Xmin: %f,  Xmax: %f, Nx: %d"%(x1_min,x1_max,nx1))
            print(">>>> Ymin: %f,  Ymax: %f, Ny: %d"%(y1_min,y1_max,ny1))

            x1 = numpy.linspace(x1_min,x1_max,nx1)
            y1 = numpy.linspace(y1_min,y1_max,ny1)

            X1 = numpy.outer(x1,numpy.ones_like(y1))
            Y1 = numpy.outer(numpy.ones_like(x1),y1)
            z1 = self.wavefront2D.get_interpolated_complex_amplitudes(X1,Y1)

            if self.EXTRAPOLATION_TO_ZERO:
                z1[numpy.where( X1 < x0[0])] = 0.0
                z1[numpy.where( X1 > x0[-1])] = 0.0
                z1[numpy.where( Y1 < y0[0])] = 0.0
                z1[numpy.where( Y1 > y0[-1])] = 0.0


            if self.KEEP_INTENSITY:
                z1 /= numpy.sqrt( (numpy.abs(z1)**2).sum() / self.wavefront2D.get_intensity().sum() )

            new_wf = GenericWavefront2D.initialize_wavefront_from_arrays(x1,y1,z1,wavelength=self.wavefront2D.get_wavelength())

            #dataArray = OWWavefront2DResample.calculate_external_Wavefront2DResample(DIRECTION=self.DIRECTION,TYPE_POINTS_X=self.TYPE_POINTS_X,RELATIVE_POINTS_X=self.RELATIVE_POINTS_X,ABSOLUTE_POINTS_X=self.ABSOLUTE_POINTS_X,TYPE_POINTS_Y=self.TYPE_POINTS_Y,RELATIVE_POINTS_Y=self.RELATIVE_POINTS_Y,ABSOLUTE_POINTS_Y=self.ABSOLUTE_POINTS_Y,TYPE_INTERVAL_X=self.TYPE_INTERVAL_X,RELATIVE_INTERVAL_X=self.RELATIVE_INTERVAL_X,ABSOLUTE_INTERVAL_XMIN=self.ABSOLUTE_INTERVAL_XMIN,ABSOLUTE_INTERVAL_XMAX=self.ABSOLUTE_INTERVAL_XMAX,TYPE_INTERVAL_Y=self.TYPE_INTERVAL_Y,RELATIVE_INTERVAL_Y=self.RELATIVE_INTERVAL_Y,ABSOLUTE_INTERVAL_YMIN=self.ABSOLUTE_INTERVAL_YMIN,ABSOLUTE_INTERVAL_YMAX=self.ABSOLUTE_INTERVAL_YMAX,KEEP_INTENSITY=self.KEEP_INTENSITY,EXTRAPOLATION_TO_ZERO=self.EXTRAPOLATION_TO_ZERO)



            # if fileName == None:
            #     print("No file to send")
            # else:
            #     self.send("oasysaddontemplate-file",fileName)
            print(">>>>>>> sending wavefront of shape: ",z1.shape)
            self.send("GenericWavefront2D", new_wf)


    def defaults(self):
         self.resetSettings()
         self.compute()
         return

    def get_doc(self):
        print("help pressed.")
        home_doc = resources.package_dirname("orangecontrib.oasysaddontemplate") + "/doc_files/"
        filename1 = os.path.join(home_doc,'Wavefront2DResample'+'.txt')
        print("Opening file %s"%filename1)
        if sys.platform == 'darwin':
            command = "open -a TextEdit "+filename1+" &"
        elif sys.platform == 'linux':
            command = "gedit "+filename1+" &"
        os.system(command)

    def set_input(self, wf):

        if not wf is None:
            self.wavefront2D = wf
        else:
            self.wavefront2D = None


    #
    # this is the calculation method to be implemented by the user
    # It is defined as static method to get all inputs from the arguments so it
    # can easily moved outside the class
    #
    @staticmethod
    def calculate_external_Wavefront2DResample(DIRECTION=2,TYPE_POINTS_X=0,RELATIVE_POINTS_X=1.0,ABSOLUTE_POINTS_X=1024,TYPE_POINTS_Y=0,RELATIVE_POINTS_Y=1.0,ABSOLUTE_POINTS_Y=1024,TYPE_INTERVAL_X=0,RELATIVE_INTERVAL_X=1.0,ABSOLUTE_INTERVAL_XMIN=-0.001,ABSOLUTE_INTERVAL_XMAX=0.001,TYPE_INTERVAL_Y=0,RELATIVE_INTERVAL_Y=1.0,ABSOLUTE_INTERVAL_YMIN=-0.001,ABSOLUTE_INTERVAL_YMAX=0.001,KEEP_INTENSITY=1,EXTRAPOLATION_TO_ZERO=1):
        print("Inside calculate_external_Wavefront2DResample. ")

        # # A MERE EXAMPLE
        # a = np.array([
        # [  8.47091837e+04,  8.57285714e+04,   8.67479592e+04, 8.77673469e+04,] ,
        # [  1.16210756e+12,  1.10833975e+12,   1.05700892e+12, 1.00800805e+12]
        # ])
        #
        # return a


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWWavefront2DResample()


    wf = GenericWavefront2D.initialize_wavefront_from_range(-1e-3,1e-3,-1e-3,1e-3,(200,200))
    wf.set_gaussian(1e-4,1e-4)

    w.set_input(wf)
    w.show()
    app.exec()
    w.saveSettings()
