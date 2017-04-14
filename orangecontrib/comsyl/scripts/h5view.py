__author__ = 'srio'

from silx.gui.data.DataViewer import DataViewer

import numpy

from PyQt4 import QtGui
import h5py


app = QtGui.QApplication([])

hfile = "/Users/srio/OASYS_VE/oasys-comsyl/orangecontrib/comsyl/scripts/ph3_u18_3_17keV_s1.3_100modes.h5"

h5f = h5py.File(hfile,'r')
for key in h5f.keys():
    print(">>>>",key)
data = h5f['modes'][:]
h5f.close()

print(">>>>>>>>>>",data.shape)


viewer = DataViewer()
viewer.setData(numpy.absolute(data)**2)
viewer.setVisible(True)

app.exec_()

