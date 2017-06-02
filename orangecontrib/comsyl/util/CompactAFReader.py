import numpy as np
import h5py
from comsyl.autocorrelation.AutocorrelationFunction import AutocorrelationFunction

class CompactAFReader(object):
    def __init__(self,af):

        self._af   = af

    @classmethod
    def initialize_from_file(cls,filename):
        filename_extension = filename.split('.')[-1]

        try:
            if filename_extension == "h5":
                return CompactAFReader(AutocorrelationFunction.loadh5(filename))
            elif filename_extension == "npz":
                return CompactAFReader(AutocorrelationFunction.load(filename))
            elif filename_extension == "npy":
                filename_without_extension = ('.').join(filename.split('.')[:-1])
                return CompactAFReader(AutocorrelationFunction.load(filename_without_extension+".npz"))
            else:
                raise FileExistsError("Please enter a file with .npy, .npz or .h5 extension")
        except:
            raise FileExistsError("Error reading file")


    def spectral_density(self):
        return self._af.intensity()

    def x_coordinates(self):
        """
        Horizontal dimension.
        """
        return self._af.xCoordinates()

    def y_coordinates(self):
        """
        Vertical dimension.
        """
        return self._af.yCoordinates()

    def modes(self):
        return self._af.Twoform().allVectors()

    def eigenvalues(self):
        return self._af.eigenvalues()

    def eigenvalue(self,mode):
        return self._af.eigenvalue(mode)

    def photon_energy(self):
        return self._af.photonEnergy()

    def total_intensity(self):
        return self.spectral_density()

    def number_modes(self):
        return self._af.numberModes()

    def mode(self, i_mode):
        return self.modes[i_mode,:,:]

    def occupation_number(self, i_mode):
        return self.eigenvalue(i_mode)/np.sum(self.eigenvalues())

    def occupation_number_array(self):
        return self.eigenvalues()/np.sum(self.eigenvalues())


    def info(self,list_modes=True):
        # print("File %s:" % filename)
        print("contains")
        print("%i modes" % self.number_modes())
        print("on the grid")
        print("x: from %e to %e" % (self.x_coordinates().min(), self.x_coordinates().max()))
        print("y: from %e to %e" % (self.y_coordinates().min(), self.y_coordinates().max()))
        print("calculated at %f eV" % self.photon_energy())
        print("with total intensity in (maybe improper) normalization: %e" % self.total_intensity().real.sum())

        print("Occupation and max abs value of the mode")
        percent = 0.0
        if list_modes:
            for i_mode in range(self.number_modes()):
                occupation = self.occupation_number(i_mode)
                # mode = self.mode(i_mode)
                # max_abs_value = np.abs(mode).max()
                percent += occupation
                print("%i occupation: %e, accumulated percent: %12.10f" % (i_mode, occupation, 100*percent))

        print(">> Shape x,y,",self.x_coordinates().shape,self.y_coordinates().shape)
        print(">> Shape modes",self.modes().shape)
        print(">> Shape Spectral density ",self.spectral_density().shape)
        print(">> Shape Photon Energy ",self.photon_energy().shape)

        print("Modes index to 90 percent occupancy:",self.mode_up_to_percent(90.0))
        print("Modes index to 95 percent occupancy:",self.mode_up_to_percent(95.0))
        print("Modes index to 99 percent occupancy:",self.mode_up_to_percent(99.0))


    def mode_up_to_percent(self,up_to_percent):

        perunit = 0.0
        for i_mode in range(self.number_modes()):
            occupation = self.occupation_number(i_mode)
            perunit += occupation
            if 100*perunit >= up_to_percent:
                return i_mode
        raise Exception("The modes in the file contain %4.2f (less than %4.2f) occupancy"%(100*perunit,up_to_percent))

def main():
    print(">> reading npz file...")
    af = AutocorrelationFunction.load("/scisoft/users/srio/Working/COMSYL/calculations/septest_cm_new_u18_2m_1h_s2.5.npz")
    print(">> writing npz file...")
    af.save("tmp.npz")
    print(">> writing h5 file...")
    af.saveh5("tmp.h5")


    dd = af.asDictionary()
    for key in dd.keys():
        print(">> ",key,type(dd[key]))

    print(">> reading tmp.npz file...")
    af = AutocorrelationFunction.load("tmp.npz")
    print(">>shape: ",af.Twoform().allVectors().shape)
    print(">> reading tmp.h5 file...")
    af = AutocorrelationFunction.loadh5("tmp.h5")

    print(">>shape: ",af.Twoform().allVectors().shape)


    # af.showMode(1)

if __name__ == "__main__":
    # main()
    af = CompactAFReader.initialize_from_file("tmp.h5")
    print(">>shape: ",af._af.Twoform().allVectors().shape)
    print(af.info())
    pass








