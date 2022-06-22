import numpy
from oasys.util.oasys_util import get_fwhm

from srxraylib.plot.gol import plot, plot_image
import matplotlib.pylab as plt
import os, sys, time
import h5py
from srxraylib.util.h5_simple_writer import H5SimpleWriter

# def get_fwhm(histogram, bins):
#     quote = numpy.max(histogram)*0.5
#     cursor = numpy.where(histogram >= quote)
#
#     if histogram[cursor].size > 1:
#         bin_size    = bins[1]-bins[0]
#         fwhm        = bin_size*(cursor[0][-1]-cursor[0][0])
#         coordinates = (bins[cursor[0][0]], bins[cursor[0][-1]])
#     else:
#         fwhm = 0.0
#         coordinates = None
#
#     return fwhm, quote, coordinates

#
#
#
class Tally2D():
    def __init__(self,
                 scan_variable_name='x',
                 additional_stored_variable_names=None,
                 do_store_wavefronts=False):
        self.reset()
        self.scan_variable_name = scan_variable_name
        self.additional_stored_variable_names = additional_stored_variable_names
        self.do_store_wavefronts = do_store_wavefronts

    def reset(self):
        self.scan_variable_index = -1
        self.scan_variable_value = []
        self.fwhm_x = []
        self.fwhm_y = []
        self.intensity_at_center = []
        self.intensity_total = []
        self.intensity_peak = []
        self.intensity_accumulated = None
        self.coordinate_x = None
        self.coordinate_y = None
        self.additional_stored_values = []
        self.stored_wavefronts = []


    def append(self, wf, scan_variable_value=None, additional_stored_values=None):
        fwhm_x, fwhm_y, intensity_total, intensity_at_center, intensity_peak, intensity, x, y = self.process_wavefront_2d(wf)
        self.fwhm_x.append(fwhm_x)
        self.fwhm_y.append(fwhm_y)
        self.intensity_at_center.append(intensity_at_center)
        self.intensity_total.append(intensity_total)
        self.intensity_peak.append(intensity_peak)
        self.scan_variable_index += 1
        if scan_variable_value is None:
            self.scan_variable_value.append(self.scan_variable_index)
        else:
            self.scan_variable_value.append(scan_variable_value)

        self.additional_stored_values.append(additional_stored_values)

        if self.do_store_wavefronts:
            self.stored_wavefronts.append(wf.duplicate())

        if self.intensity_accumulated is None:
            self.intensity_accumulated = intensity
        else:
            self.intensity_accumulated += intensity

        self.coordinate_x = x
        self.coordinate_y = y

    def get_wavefronts(self):
        return self.stored_wavefronts

    def get_number_of_calls(self):
        return self.scan_variable_index + 1

    def get_additional_stored_values(self):
        return self.additional_stored_values

    def save_scan(self, filename="tmp.dat", add_header=True):
        raise Exception("Te be implemented")
        # f = open(filename, 'w')
        # if add_header:
        #     if self.additional_stored_variable_names is None:
        #         number_of_additional_parameters = 0
        #     else:
        #         number_of_additional_parameters = len(self.additional_stored_variable_names)
        #     header = "#S 1 scored data\n"
        #     header += "#N %d\n" % (number_of_additional_parameters + 5)
        #     header_titles = "#L  %s  %s  %s  %s  %s" % (self.scan_variable_name, "fwhm", "total_intensity", "on_axis_intensity", "peak_intensity")
        #     for i in range(number_of_additional_parameters):
        #         header_titles += "  %s" % self.additional_stored_variable_names[i]
        #     header_titles += "\n"
        #     header += header_titles
        #     f.write(header)
        # for i in range(len(self.fwhm)):
        #     f.write("%g %g %g %g %g" % (self.scan_variable_value[i],
        #                             1e6*self.fwhm[i],
        #                             self.intensity_total[i],
        #                             self.intensity_at_center[i],
        #                             self.intensity_peak[i]))
        #     for j in range(number_of_additional_parameters):
        #         f.write(" %g" % self.additional_stored_values[i][j])
        #     f.write("\n")
        # f.close()
        # print("File written to disk: %s" % filename)

    def get_fwhm_intensity_accumulated(self):

        nx = self.coordinate_x.size
        ny = self.coordinate_y.size

        fwhm_x, quote, coordinates = get_fwhm(self.intensity_accumulated[:, ny//2], self.coordinate_x)
        fwhm_y, quote, coordinates = get_fwhm(self.intensity_accumulated[nx // 2, :], self.coordinate_y)

        return fwhm_x, fwhm_y

    def get_histograms(self):
        hx = self.intensity_accumulated.sum(axis=1)
        hy = self.intensity_accumulated.sum(axis=0)
        return hx, hy

    def get_fwhm_histograms(self):
        hx, hy = self.get_histograms()
        fwhm_x, quote, coordinates = get_fwhm(hx, self.coordinate_x)
        fwhm_y, quote, coordinates = get_fwhm(hy, self.coordinate_y)
        return fwhm_x, fwhm_y

    def plot_intensity_accumulated(self, show=1, filename="", aspect=None,
                                   title="intensity accumulated", xtitle="x", ytitle="y",
                                   coordinates_factor=1.0):

        fwhm_x, fwhm_y = self.get_fwhm_intensity_accumulated()

        plot_image(self.intensity_accumulated,
                   coordinates_factor * self.coordinate_x,
                   coordinates_factor * self.coordinate_y,
                   title="%s fwhm of central profiles=%g x %g " % (title, coordinates_factor*fwhm_x, coordinates_factor * fwhm_y),
                   xtitle=xtitle, ytitle=ytitle, aspect=aspect, show=False)

        if filename != "":
            plt.savefig(filename)
            print("File written to disk: %s" % filename)

        if show:
            plt.show()
        else:
            plt.close()

    def save(self, filename=""):

        if filename == "": return

        fwhm_profile_x, fwhm_profile_y = self.get_fwhm_intensity_accumulated()
        fwhm_histo_x, fwhm_histo_y = self.get_fwhm_histograms()

        Z = self.intensity_accumulated
        hx, hy = self.get_histograms()
        x_coordinates = 1e3 * self.coordinate_x
        y_coordinates = 1e3 * self.coordinate_y

        #
        # initialize file
        #
        h5w = H5SimpleWriter.initialize_file(filename, creator="h5_basic_writer.py")

        # this is optional
        h5w.set_label_image("intensity_accumulated", b'x', b'y')
        h5w.set_label_dataset(b'abscissas', b'intensity')


        # create the entry for this iteration and set default plot to "Wintensity"
        h5w.create_entry("accumulated_intensity", nx_default="intensity")


        # add the images at this entry level
        h5w.add_image(Z, 1e3 * x_coordinates, 1e3 * y_coordinates,
                      entry_name="accumulated_intensity", image_name="intensity",
                      title_x="X [um]", title_y="Y [um]")


        h5w.add_dataset(1e3 * x_coordinates, Z[:, int(y_coordinates.size / 2)],
                        entry_name="accumulated_intensity", dataset_name="profileH",
                        title_x="X [um]", title_y="Profile along X")
        h5w.add_key("fwhm", 1e6*fwhm_profile_x, entry_name="accumulated_intensity/profileH")


        h5w.add_dataset(1e3 * y_coordinates, Z[int(x_coordinates.size / 2), :],
                        entry_name="accumulated_intensity", dataset_name="profileV",
                        title_x="Y [um]", title_y="Profile along Y")
        h5w.add_key("fwhm", 1e6 * fwhm_profile_y, entry_name="accumulated_intensity/profileV")


        h5w.add_dataset(1e3 * x_coordinates, hx,
                        entry_name="accumulated_intensity", dataset_name="histogramH",
                        title_x="X [um]", title_y="Histogram along X")
        h5w.add_key("fwhm", 1e6 * fwhm_histo_x, entry_name="accumulated_intensity/histogramH")


        h5w.add_dataset(1e3 * y_coordinates, hy,
                        entry_name="accumulated_intensity", dataset_name="histogramV",
                        title_x="Y [um]", title_y="Histogram along Y")
        h5w.add_key("fwhm", 1e6 * fwhm_histo_y, entry_name="accumulated_intensity/histogramV")

        print("File written to disk: %s" % filename)

    @classmethod
    def process_wavefront_2d(cls, wf):
        I = wf.get_intensity()
        x = wf.get_coordinate_x()
        y = wf.get_coordinate_y()

        nx = x.size
        ny = y.size

        fwhm_x, quote, coordinates = get_fwhm(I[:, ny//2], x)
        fwhm_y, quote, coordinates = get_fwhm(I[nx//2, :], y)

        intensity_at_center = I[nx//2, ny//2]
        intensity_total = I.sum() * (x[1] - x[0]) * (y[1] - y[0])
        intensity_peak = I.max()

        return fwhm_x, fwhm_y, intensity_total, intensity_at_center, intensity_peak, I, x, y



if __name__ == "__main__":
    from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

    sc = Tally2D(scan_variable_name='mode index', additional_stored_variable_names=['a', 'b'], do_store_wavefronts=False)
    for xmode in range(5):
        output_wavefront = GenericWavefront2D.initialize_wavefront_from_range(x_min=-0.00012, x_max=0.00012,
                                                                              y_min=-5e-05, y_max=5e-05,
                                                                              number_of_points=(400, 200))
        output_wavefront.set_photon_energy(7000)
        output_wavefront.set_gaussian_hermite_mode(sigma_x=3.00818e-05, sigma_y=6.99408e-06, amplitude=1, nx=xmode, ny=0,
                                                   betax=0.129748, betay=1.01172)


        sc.append(output_wavefront, scan_variable_value=xmode, additional_stored_values=[1,2.1])

    print(sc.fwhm_x, sc.fwhm_y)
    # plot_image(sc.intensity_accumulated, sc.coordinate_x, sc.coordinate_y)

    sc.plot_intensity_accumulated(coordinates_factor=1e6, aspect='auto')
    # sc.plot()
    sc.save("tmp.h5")

