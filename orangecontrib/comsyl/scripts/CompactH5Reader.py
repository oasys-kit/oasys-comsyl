import numpy as np
import h5py

class CompactH5Reader(object):
    def __init__(self, filename):

        h5f = h5py.File(filename,'r')
        for key in h5f.keys():
            print(">>>>",key)

        self._x_coordinates = h5f["x"][:]
        self._y_coordinates = h5f["y"][:]
        self._eigenvalues = h5f["eigenvalues"][:]
        self._modes = h5f["modes"][:]
        # TODO
        # self._intensity = file["np_twoform_2"]
        # self._photon_energy = file["np_energy"]

        print(">>>>>>>",self._x_coordinates.shape,self._y_coordinates.shape,self._modes.shape)
        h5f.close()

    def total_intensity(self):
        return self._intensity

    def number_modes(self):
        return self._modes.shape[0]

    def x_coordinates(self):
        """
        Horizontal dimension.
        """
        return self._x_coordinates

    def y_coordinates(self):
        """
        Vertical dimension.
        """
        return self._y_coordinates

    def mode(self, i_mode):
        return self._modes[i_mode,:,:]

    def occupation_number(self, i_mode):
        return self._eigenvalues[i_mode]/np.sum(self._eigenvalues)

    def photon_energy(self):
        return self._photon_energy

if __name__ == "__main__":
    # import sys
    # filename = sys.argv[1]
    filename = "/Users/srio/OASYS_VE/oasys-comsyl/orangecontrib/comsyl/scripts/ph3_u18_3_17keV_s1.3_100modes.h5"

    reader = CompactH5Reader(filename)

    print("File %s:" % filename)
    print("contains")
    print("%i modes" % reader.number_modes())
    print("on the grid")
    print("x: from %e to %e" % (reader.x_coordinates().min(), reader.x_coordinates().max()))
    print("y: from %e to %e" % (reader.y_coordinates().min(), reader.y_coordinates().max()))
    #TODO
    # print("calculated at %f eV" % reader.photon_energy())
    # print("with total intensity in (maybe improper) normalization: %e" % reader.total_intensity().real.sum())

    print("Occupation and max abs value of the mode")
    for i_mode in range(reader.number_modes()):
        occupation = reader.occupation_number(i_mode)
        mode = reader.mode(i_mode)
        max_abs_value = np.abs(mode).max()
        print("%i is %e %e" % (i_mode, occupation, max_abs_value))

