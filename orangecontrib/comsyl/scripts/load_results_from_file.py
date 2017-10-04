import numpy
from srxraylib.plot.gol import plot_image, plot
import sys

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

def load_stack(filename):
    # filename = "/users/srio/OASYS_VE/comsyl_srio/calculations/new_u18_2m_1h_s2.5"
    reader = CompactAFReader(filename)

    print("File %s:" % filename)
    print("contains")
    print("%i modes" % reader.number_modes())
    print("on the grid")
    print("x: from %e to %e" % (reader.x_coordinates().min(), reader.x_coordinates().max()))
    print("y: from %e to %e" % (reader.y_coordinates().min(), reader.y_coordinates().max()))
    print("calculated at %f eV" % reader.photon_energy())
    print("with total intensity in (maybe improper) normalization: %e" % reader.total_intensity().real.sum())



    print("Occupation and max abs value of the mode")

    x = reader.x_coordinates()
    y = reader.y_coordinates()

    eigenvalues = numpy.zeros(reader.number_modes())

    mystack = numpy.zeros((reader.number_modes(),y.size,x.size),dtype=complex)

    for i_mode in range(reader.number_modes()):
        eigenvalues[i_mode] = reader.occupation(i_mode)
        mode = reader.mode(i_mode)
        mystack[i_mode,:,:] = mode.T


    return x,y,mystack, eigenvalues

if __name__ == "__main__":

    h,v,mystack, occupation = load_stack("/users/srio/OASYS_VE/comsyl_srio/calculations/new_u18_2m_1h_s2.5")

    plot_stack(mystack,what="intensity", title0="Mode index",
               title1="V from %3.2f to %3.2f um"%(1e3*v.min(),1e3*v.max()),
               title2="H from %3.2f to %3.2f um"%(1e3*h.min(),1e3*h.max()))

    plot(numpy.arange(occupation.size),occupation)