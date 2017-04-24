import numpy
import sys
print('Hello world')
print(dir(in_object_1))
from comsyl.scripts.CompactAFReader import CompactAFReader


def plot_stack(mystack,what="intensity",title0="X",title1="Y",title2="Z"):

    from silx.gui.plot.StackView import StackViewMainWindow
    from silx.gui import qt


    app = qt.QApplication(sys.argv[1:])

    sv = StackViewMainWindow()
    sv.setColormap("jet", autoscale=True)
    if what == "intensity":
        sv.setStack(numpy.absolute(mystack))
    elif what == "real":
        sv.setStack(numpy.real(mystack))
    elif what == "imaginary":
        sv.setStack(numpy.imag(mystack))
    elif what == "phase":
        sv.setStack(numpy.angle(mystack))
    elif what == "phase_deg":
        sv.setStack(numpy.angle(mystack,deg=True))
    else:
        raise Exception("Undefined label "+what)

    sv.setLabels([title0,title1,title2])
    sv.show()

    app.exec_()


reader = in_object_1
print("contains")
print("%i modes" % reader.number_modes())
print("on the grid")
print("x: from %e to %e" % (reader.x_coordinates().min(), reader.x_coordinates().max()))
print("y: from %e to %e" % (reader.y_coordinates().min(), reader.y_coordinates().max()))
print("calculated at %f eV" % reader.photon_energy())
print("with total intensity in (maybe improper) normalization: %e" % reader.total_intensity().real.sum())


x = reader.x_coordinates()
y = reader.y_coordinates()
eigenvalues = numpy.zeros(reader.number_modes())

mystack = numpy.absolute(reader.modes())

plot_stack(mystack,what="intensity", title0="Mode index",
           title1="V from %3.2f to %3.2f um"%(1e3*x.min(),1e3*x.max()),
           title2="H from %3.2f to %3.2f um"%(1e3*y.min(),1e3*y.max()))