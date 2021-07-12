import numpy
from oasys.util.oasys_util import get_fwhm

from srxraylib.plot.gol import plot, plot_image
import matplotlib.pylab as plt
import os

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

    def plot_intensity_accumulated(self, show=1, filename="",
                                   title="intensity accumulated", xtitle="x", ytitle="y",
                                   coordinates_factor=1.0):

        fwhm_x, fwhm_y = self.get_fwhm_intensity_accumulated()

        plot_image(self.intensity_accumulated,
                   coordinates_factor * self.coordinate_x,
                   coordinates_factor * self.coordinate_y,
                   title="%s fwhm=%g x %g " % (title, coordinates_factor*fwhm_x, coordinates_factor * fwhm_y),
                   xtitle=xtitle, ytitle=ytitle, show=False)

        if filename != "":
            plt.savefig(filename)
            print("File written to disk: %s" % filename)

        if show:
            plt.show()
        else:
            plt.close()

        # x = numpy.array(self.scan_variable_value)
        #
        #
        # y = numpy.array(self.intensity_at_center)
        # plot(x, y, yrange=[0,1.1*y.max()],
        #      title=title, ytitle="Intensity at center[a.u.]", xtitle=self.scan_variable_name,
        #      figsize=(15, 4), show=0)
        #
        # # y = numpy.array(self.intensity_total)
        # # plot(x, y, yrange=[0,1.1*y.max()],
        # #      title=title, ytitle="Beam intensity [a.u.]", xtitle=self.scan_variable_name,
        # #      figsize=(15, 4), show=0)
        #
        # y = numpy.array(self.fwhm)
        # plot(x, y, yrange=[0,1.1*y.max()],
        #      title=title, ytitle="FWHM [um]", xtitle=self.scan_variable_name,
        #      figsize=(15, 4), show=1)



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

    sc.plot_intensity_accumulated(coordinates_factor=1e6)
    # sc.plot()
    # sc.save_scan("tmp.dat")

