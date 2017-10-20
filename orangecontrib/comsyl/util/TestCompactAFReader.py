from CompactAFReader import CompactAFReader
import numpy as np

#
# auxiliary functions
#
def test_equal(af1,af2):
        np.testing.assert_almost_equal(af1.eigenvalue(5),af2.eigenvalue(5))
        np.testing.assert_almost_equal(af1.eigenvalue(5),af2.eigenvalue(5))
        np.testing.assert_almost_equal(af1.photon_energy(),af2.photon_energy())
        np.testing.assert_almost_equal(af1.total_intensity_from_spectral_density(),af2.total_intensity_from_spectral_density())
        np.testing.assert_almost_equal(af1.total_intensity(),af2.total_intensity())
        np.testing.assert_almost_equal(af1.number_modes(),af2.number_modes())
        np.testing.assert_almost_equal(af1.eigenvalues(), af2.eigenvalues())
        np.testing.assert_almost_equal(af1.x_coordinates(), af2.x_coordinates())
        np.testing.assert_almost_equal(af1.y_coordinates(), af2.y_coordinates())
        np.testing.assert_almost_equal(af1.spectral_density(), af2.spectral_density())
        np.testing.assert_almost_equal(af1.reference_electron_density(), af2.reference_electron_density())
        np.testing.assert_almost_equal(af1.reference_undulator_radiation(), af2.reference_undulator_radiation())
        np.testing.assert_almost_equal(af1.mode(25), af2.mode(25))
        np.testing.assert_almost_equal(af1.shape, af2.shape)

        np.testing.assert_almost_equal(af1.total_intensity_from_modes(),af2.total_intensity_from_modes()) #SLOW

def print_scattered_info(af1,af2=None):
        if af2 is None:
            af2 = af1

        print("File is: ",af1._filename,af2._filename)
        print("Eigenvalue 5: ",af1.eigenvalue(5),af2.eigenvalue(5))
        print("photon_energy : ",af1.photon_energy(),af2.photon_energy())
        print("total_intensity_from_spectral_density : ",af1.total_intensity_from_spectral_density(),af2.total_intensity_from_spectral_density())
        print("total_intensity : ",af1.total_intensity(),af2.total_intensity())
        print("number_modes : ",af1.number_modes(),af2.number_modes())

        print("Eigenvalues shape: ",                  af1.eigenvalues().shape, af2.eigenvalues().shape)
        print("x_coordinates shape: ",                af1.x_coordinates().shape, af2.x_coordinates().shape)
        print("y_coordinates shape: ",                af1.y_coordinates().shape, af2.y_coordinates().shape)
        print("spectral_density shape: ",             af1.spectral_density().shape, af2.spectral_density().shape)
        print("reference_electron_density shape: ",   af1.reference_electron_density().shape, af2.reference_electron_density().shape)
        print("reference_undulator_radiation shape: ",af1.reference_undulator_radiation().shape, af2.reference_undulator_radiation().shape)
        print("mode 25 shape: ",                      af1.mode(25).shape, af2.mode(25).shape)
        print("shape : ",                             af1.shape, af2.shape)

        print("keys : ",af1.keys(),af2.keys())
        print("total_intensity_from_modes [SLOW]: ",af1.total_intensity_from_modes(),af2.total_intensity_from_modes())

        af1.close_h5_file()
        af2.close_h5_file()
        # print("mode 25 shape: ",af2.mode(25).shape)  # should fail after closing

def tic():
    import time
    global startTime
    startTime = time.time()


def toc(text=""):
    import time
    print('')
    if 'startTime' in globals():
        deltaT = time.time() - startTime
        hours, minutes = divmod(deltaT, 3600)
        minutes, seconds =  divmod(minutes, 60)
        print("Elapsed time "+text+" : " + str(int(hours)) + "h " + str(int(minutes)) + "min " + str(seconds) + "s ")
    else:
        print("Warning: start time not set.")

if __name__ == "__main__":

    from srxraylib.plot.gol import plot_image

    from comsyl.autocorrelation.DegreeOfCoherence import DegreeOfCoherence

    filename_h5 = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.h5"
    filename_np = "/users/srio/COMSYLD/comsyl/comsyl/calculations/septest_cm_new_u18_2m_1h_s2.5.npz"


    # filename_h5 = "/users/srio/COMSYLD/comsyl/comsyl/calculations/alba_cm_u21_2m_1h_s1.0.h5"
    # filename_np = "/users/srio/COMSYLD/comsyl/comsyl/calculations/alba_cm_u21_2m_1h_s1.0.npz"

    af1  = CompactAFReader.initialize_from_file(filename_h5)
    tic()
    for i in range(af1.number_modes()):
        print(i,af1.mode(i).sum())
    toc()
    print(af1.info())
    #
    #
    af2  = CompactAFReader.initialize_from_file(filename_np)
    tic()
    for i in range(af2.number_modes()):
        print(i,af2.mode(i).sum())
    toc()




    # Cross spectral density

    Wx1x2,Wy1y2 = af2.CSD_in_one_dimension()

    print(Wx1x2.shape,Wx1x2[10,10])
    plot_image(np.abs(Wx1x2),1e6*af2.x_coordinates(),1e6*af2.x_coordinates(),show=False,title="Wx1x2")
    plot_image(np.abs(Wy1y2),1e6*af2.y_coordinates(),1e6*af2.y_coordinates(),show=True,title="Wy1y2")








