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

    @classmethod
    def convert_to_h5(cls,filename):
        af = AutocorrelationFunction.load(filename)


        filename_extension = filename.split('.')[-1]

        if filename_extension == "h5":
            print("File is already h5: nothing to convert")
            return None

        filename_without_extension = ('.').join(filename.split('.')[:-1])

        af.saveh5(filename_without_extension+".h5")

        return CompactAFReader(af)

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
        print("total intensity:", (np.absolute(self._af.intensity())**2).sum() )
        print("total intensity from modes:" , (np.absolute(self._af.intensityFromModes())**2).sum() )

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

    def get_dictionary(self):
        return self._af.asDictionary()

    def keys(self):
        return self.get_dictionary().keys()

    def shape(self):
        return self._af.Twoform().allVectors().shape


if __name__ == "__main__":
    filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.npz"
    filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/alba_cm_u21_2m_1h_s2.5.npz"
    filename = "/users/srio/COMSYLD/comsyl/comsyl/calculations/alba_cm_u21_2m_1h_s2.5.h5"

    af = CompactAFReader.initialize_from_file(filename)

    # af = CompactAFReader.convert_to_h5(filename)

    print(af.info())

    # d1 = af.get_dictionary()
    # for key in af.keys():
    #     print(key, d1[key])







