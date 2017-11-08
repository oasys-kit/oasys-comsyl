
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

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

class OWWavefront2DPadding(oasyswidget.OWWidget):
    name = "Wavefront2DPadding"
    id = "orange.widgets.dataWavefront2DPadding"
    description = "Application to compute..."
    icon = "icons/Wavefront2DPadding.png"
    author = "create_widget.py"
    maintainer_email = "srio@esrf.eu"
    priority = 40

    category = ""
    keywords = ["oasysaddontemplate", "Wavefront2DPadding", "data", "file", "load", "read"]

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
    RELATIVE_POINTS_X = Setting(1.0)
    RELATIVE_POINTS_Y = Setting(1.0)
    ABSOLUTE_POINTS_X = Setting(1024)
    ABSOLUTE_POINTS_Y = Setting(1024)

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
                    items=['No padding', 'Relative scaling number of pixels', 'Absolute Number of pixels'],
                    valueType=int, orientation="horizontal")
        self.show_at(self.unitFlags()[idx], box1) 
        

        
        #widget index 2 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "RELATIVE_POINTS_X",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=float, validator=QDoubleValidator())
        self.show_at(self.unitFlags()[idx], box1) 

        #widget index 5
        idx += 1
        box1 = gui.widgetBox(box)
        gui.lineEdit(box1, self, "RELATIVE_POINTS_Y",
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

        #widget index 6 
        idx += 1 
        box1 = gui.widgetBox(box) 
        gui.lineEdit(box1, self, "ABSOLUTE_POINTS_Y",
                     label=self.unitLabels()[idx], addSpace=True,
                    valueType=int, validator=QIntValidator())
        self.show_at(self.unitFlags()[idx], box1) 


        gui.rubber(self.controlArea)

    def unitLabels(self):
         return ['Padding ',\
                 'Scaling N factor (Horizontal) ','Scaling N factor (Vertical) ',\
                 'New number of pixels (Horizontal)','New number of pixels (Vertical)']

    def unitFlags(self):
         return ['True',\
                 '(self.DIRECTION == 1) ','(self.DIRECTION == 1 )',\
                 '(self.DIRECTION == 2) ','(self.DIRECTION == 2 )' ]


    def compute(self):

        if self.DIRECTION == 2:
            raise Exception(NotImplemented)


        if self.wavefront2D is None:
            print(">>>>>>>>>>>>> Nothing to send!")
        else:


            wf = self.wavefront2D
            print(dir(wf))
            A = wf.get_complex_amplitude()

            Nx,Ny = A.shape
            Fx = int( 0.5 * (Nx * self.RELATIVE_POINTS_X - Nx))
            Fy = int( 0.5 * (Ny * self.RELATIVE_POINTS_Y - Ny))

            print(">>>>>>>>>>>>>>>>    Original pixels in X, Y: ",Nx,Ny)
            print(">>>>>>>>>>>>>>>>    Adding pixels (both directions) in X, Y: ",Fx,Fy)

            x = wf.get_coordinate_x()
            y = wf.get_coordinate_y()


            x1 = numpy.arange(Nx+2*Fx) * (x[1]-x[0])
            y1 = numpy.arange(Ny+2*Fy) * (y[1]-y[0])

            # TODO: check if there is subpixel shift
            x1 -= x1[int(0.5*(Nx+Fx))]
            y1 -= y1[int(0.5*(Ny+Fy))]

            A1 = numpy.lib.pad(A,((Fx,Fx),(Fy,Fy)), 'constant'  )

            print("padded: ",A1.shape,x1.shape,y1.shape)

            print(">>>>>>>>>>>>>>>>>>> limits before: X,Y ",x[0],x[-1],y[0],y[-1])
            print(">>>>>>>>>>>>>>>>>>> limits after: X,Y ",x1[0],x1[-1],y1[0],y1[-1])

            new_wf = GenericWavefront2D.initialize_wavefront_from_arrays(x1,y1,A1,wavelength=self.wavefront2D.get_wavelength())

            self.send("GenericWavefront2D", new_wf)



    def defaults(self):
         self.resetSettings()
         self.compute()
         return

    def get_doc(self):
        print("help pressed.")
        home_doc = resources.package_dirname("orangecontrib.oasysaddontemplate") + "/doc_files/"
        filename1 = os.path.join(home_doc,'Wavefront2DPadding'+'.txt')
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
    def calculate_external_Wavefront2DPadding(DIRECTION=2,TYPE_POINTS_X=0,RELATIVE_POINTS_X=1.0,ABSOLUTE_POINTS_X=1024,TYPE_POINTS_Y=0,RELATIVE_POINTS_Y=1.0,ABSOLUTE_POINTS_Y=1024,TYPE_INTERVAL_X=0,RELATIVE_INTERVAL_X=1.0,ABSOLUTE_INTERVAL_XMIN=-0.001,ABSOLUTE_INTERVAL_XMAX=0.001,TYPE_INTERVAL_Y=0,RELATIVE_INTERVAL_Y=1.0,ABSOLUTE_INTERVAL_YMIN=-0.001,ABSOLUTE_INTERVAL_YMAX=0.001,KEEP_INTENSITY=1,EXTRAPOLATION_TO_ZERO=1):
        print("Inside calculate_external_Wavefront2DPadding. ")

        # # A MERE EXAMPLE
        # a = np.array([
        # [  8.47091837e+04,  8.57285714e+04,   8.67479592e+04, 8.77673469e+04,] ,
        # [  1.16210756e+12,  1.10833975e+12,   1.05700892e+12, 1.00800805e+12]
        # ])
        #
        # return a


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWWavefront2DPadding()


    wf = GenericWavefront2D.initialize_wavefront_from_range(-1e-3,1e-3,-1e-3,1e-3,(200,200))
    wf.set_gaussian(1e-4,1e-4)

    w.set_input(wf)
    w.show()
    app.exec()
    w.saveSettings()
