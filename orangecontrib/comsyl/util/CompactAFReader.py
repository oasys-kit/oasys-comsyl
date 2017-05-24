import numpy as np
import h5py

class CompactAFReader(object):
    def __init__(self,
                    eigenvalues  ,
                    modes        ,
                    x_coordinates,
                    y_coordinates,
                    spectral_density    ,
                    photon_energy,
                    info_dictionary=None,
                             ):

        self._eigenvalues   = eigenvalues
        self._modes         = modes
        self._x_coordinates = x_coordinates
        self._y_coordinates = y_coordinates
        self._spectral_density     = spectral_density
        self._photon_energy = photon_energy
        self._info_dictionary = info_dictionary


    @classmethod
    def initialize_from_file(cls,filename):
        filename_extension = filename.split('.')[-1]

        try:
            if filename_extension == "h5":
                return CompactAFReader.initialize_from_h5(filename)
            else:
                if filename_extension == "npy" or filename_extension == "npz":
                    filename_without_extension = ('.').join(filename.split('.')[:-1])
                    return CompactAFReader.initialize_from_af(filename_without_extension)
                else:
                    return CompactAFReader.initialize_from_af(filename)
        except:
            raise FileExistsError("Unknown file type")

    @classmethod
    def initialize_from_af(cls,filename):
        from comsyl.autocorrelation.AutocorrelationFunction import AutocorrelationFunction
        af = AutocorrelationFunction.load(filename+".npz")

        x_coordinates = af.xCoordinates()
        y_coordinates = af.yCoordinates()
        spectral_density = af.intensity()
        eigenvalues = af.Twoform().eigenvalues()
        photon_energy = af.photonEnergy()
        modes = af.Twoform().eigenvectors()
        info_dictionary = af.asDictionary()

        # a.) Spatial electron phase space density: af._static_electron_density
        # a.) Virtual source wavefront: af._wavefront
        # a.) they should be on the same grid sufficiently large because they are convolved
        # b.) Wavefront outside but close to the undulator: af._exit_slit_wavefront

        return CompactAFReader(
                    eigenvalues  ,
                    modes        ,
                    x_coordinates,
                    y_coordinates,
                    spectral_density    ,
                    photon_energy,
                    info_dictionary)


    @classmethod
    def initialize_from_numpy(cls,filename):
        file = np.load(filename+".npz")

        x_coordinates = file["np_twoform_0"]
        y_coordinates = file["np_twoform_1"]
        spectral_density = file["np_twoform_2"]
        eigenvalues = file["np_twoform_3"]
        photon_energy = file["np_energy"]

        vectors_shape = (eigenvalues.size,x_coordinates.size,y_coordinates.size)

        modes = np.memmap(filename+".npy", dtype=np.complex128, mode='c', shape=vectors_shape)

        return CompactAFReader(
                    eigenvalues  ,
                    modes        ,
                    x_coordinates,
                    y_coordinates,
                    spectral_density    ,
                    photon_energy,)

    @classmethod
    def initialize_from_h5(cls,filename):

        h5f = h5py.File(filename,'r')
        for key in h5f.keys():
            print(">>>>",key)


        eigenvalues      = h5f['eigenvalues'     ][:]
        modes            = h5f['modes'           ][:]
        x_coordinates    = h5f['x_coordinates'   ][:]
        y_coordinates    = h5f['y_coordinates'   ][:]
        spectral_density = h5f['spectral_density'][:]
        photon_energy    = h5f['photon_energy'   ][:]

        h5f.close()

        return CompactAFReader(
                    eigenvalues  ,
                    modes        ,
                    x_coordinates,
                    y_coordinates,
                    spectral_density    ,
                    photon_energy,)

    def write_h5(self,filename_out,max_occupacy_percent=None):

        f = h5py.File(filename_out, 'w')

        if max_occupacy_percent == None:
            f['eigenvalues'     ] = self.eigenvalues()
            f['modes'           ] = self.modes()
            f['x_coordinates'   ] = self.x_coordinates()
            f['y_coordinates'   ] = self.y_coordinates()
            f['spectral_density'] = self.spectral_density()
            f['photon_energy'   ] = self.photon_energy()
        else:
            nmax = 1 + self.mode_up_to_percent(max_occupacy_percent)
            f['eigenvalues'     ] = self.eigenvalues()[0:nmax]
            f['modes'           ] = self.modes()[0:nmax,:,:]
            f['x_coordinates'   ] = self.x_coordinates()
            f['y_coordinates'   ] = self.y_coordinates()
            f['spectral_density'] = self.spectral_density()
            f['photon_energy'   ] = self.photon_energy()


        # if self._info_dictionary is None:
        #     pass
        # else:
        #     for key in self._info_dictionary.keys():
        #         tmp = self._info_dictionary[key]
        #         if isinstance(tmp,str):
        #             f['dict '+key] = tmp
        #         elif isinstance(tmp,np.ndarray):
        #             f['dict '+key] = tmp


        f.close()
        print("File written to disk",filename_out)


    def spectral_density(self):
        return self._spectral_density


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

    def modes(self):
        return self._modes

    def eigenvalues(self):
        return self._eigenvalues

    def photon_energy(self):
        return self._photon_energy


    def total_intensity(self):
        return self._spectral_density

    def number_modes(self):
        return self._modes.shape[0]


    def mode(self, i_mode):
        return self._modes[i_mode,:,:]

    def occupation_number(self, i_mode):
        return self._eigenvalues[i_mode]/np.sum(self._eigenvalues)

    def occupation_number_array(self):
        return self._eigenvalues/np.sum(self._eigenvalues)

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
        print(">> Spectral density ",self.spectral_density().shape)

        print("Modes index to 90 percent occupancy:",self.mode_up_to_percent(90.0))
        print("Modes index to 95 percent occupancy:",self.mode_up_to_percent(95.0))
        print("Modes index to 99 percent occupancy:",self.mode_up_to_percent(99.0))

        if self._info_dictionary is None:
            pass
        else:
            for key in self._info_dictionary.keys():
                tmp = self._info_dictionary[key]
                if isinstance(tmp,str):
                    print(key,tmp)
                elif isinstance(tmp,np.ndarray):
                   print("Shape of ",key,tmp.shape)

    def mode_up_to_percent(self,up_to_percent):

        perunit = 0.0
        for i_mode in range(self.number_modes()):
            occupation = self.occupation_number(i_mode)
            perunit += occupation
            if 100*perunit >= up_to_percent:
                return i_mode
        raise Exception("The modes in the file contain %4.2f (less than %4.2f) occupancy"%(100*perunit,up_to_percent))

if __name__ == "__main__":
    import sys, os
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "/users/srio/OASYS_VE/comsyl_srio/calculations/new_u18_2m_1h_s2.5"
        filename = "/users/srio/OASYS_VE/comsyl_srio/calculations/new_u18_2m_1h_s2.5.h5"
        filename = "/scisoft/users/glass/Documents/sources/Orange-SRW/comsyl/calculations/ph3_u18_3_17keV_s1.3"
        filename = "/scisoft/users/glass/Documents/sources/Orange-SRW/comsyl/calculations/cs_new_u18_2m_1h_s2.5"
        # filename = "/users/srio/OASYS_VE/oasys-comsyl/orangecontrib/comsyl/scripts/cs_new_u18_2m_1h_s2.5.h5"
        filename = "/users/srio/OASYS1_VE/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.npz"

    reader = CompactAFReader.initialize_from_file(filename)
    reader.info(list_modes=False)

    # reader.write_h5("tmp.h5")
    reader.write_h5("tmp20.h5",max_occupacy_percent=20.0)

    # file_in_path = "/scisoft/users/glass/Documents/sources/Orange-SRW/comsyl/calculations/"
    # file_out_path = "/scisoft/data/srio/COMSYL/CALCULATIONS/"
    # file_out_path95 = "/scisoft/data/srio/COMSYL/CALCULATIONS95/"
    #
    # f = open("tmp",'r')
    # file_list = f.readlines()
    # f.close()
    # for file in file_list:
    #
    #     full_file = (file_in_path+file).rstrip()
    #     print(">>>processing file: ",full_file)
    #     filename_without_extension = ('.').join(file.rstrip().split('.')[:-1])
    #     reader = CompactAFReader.initialize_from_file(full_file)
    #     reader.write_h5(file_out_path+filename_without_extension+".h5")
    #     reader.write_h5(file_out_path95+filename_without_extension+".h5",max_occupacy_percent=95.0)


