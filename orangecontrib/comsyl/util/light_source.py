import numpy
from syned.storage_ring.light_source import LightSource
# from syned.storage_ring.electron_beam import ElectronBeam
from syned.storage_ring.empty_light_source import EmptyLightSource
from syned.storage_ring.magnetic_structures.undulator import Undulator

from wofry.beamline.decorators import LightSourceDecorator
# from wofryimpl.propagator.util.undulator_coherent_mode_decomposition_1d import UndulatorCoherentModeDecomposition1D
#
# from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

from comsyl.autocorrelation.CompactAFReader import CompactAFReader

class WOLightSourceCOMSYL(LightSource, LightSourceDecorator):
    def __init__(self,
                 name                = "Undefined",
                 filename="",  # comsyl result filename
                 # electron_beam       = None,
                 # magnetic_structure  = None,
                 # undulator_coherent_mode_decomposition_1d = None,
                 # dimension           = 2,
                 mode_index=None, # for wavefront retrieving
                 normalize_with_eigenvalue=1, # for wavefront retrieving (integer)
                 ):

        electron_beam = EmptyLightSource(name=name)
        magnetic_structure = None # Undulator(K_vertical=undulator_coherent_mode_decomposition_1d.K,
                                       # period_length=undulator_coherent_mode_decomposition_1d.undulator_period,
                                       # number_of_periods=undulator_coherent_mode_decomposition_1d.undulator_nperiods)

        LightSource.__init__(self, name=name,
                             electron_beam=electron_beam,
                             magnetic_structure=magnetic_structure)

        self.filename = filename
        self.af_oasys = None
        self._dimension =  2
        self.dimension = 2
        self.mode_index = mode_index
        self.normalize_with_eigenvalue = normalize_with_eigenvalue
        self._set_support_text([
                    # ("name"      ,           "to define ", "" ),
                    ("dimension"      , "dimension ", "" ),
                    ("filename", "filename ", ""),
            ] )

    def set_mode_index(self, mode_index):
        self.mode_index = mode_index

    def get_mode_index(self):
        return self.mode_index

    def get_filename(self):
        return self.filename

    def get_dimension(self):
        return self._dimension

    def load_comsyl_file(self):
        self.af_oasys = CompactAFReader.initialize_from_file(self.filename)

    # from Wofry Decorator
    def get_wavefront(self):
        if self.af_oasys is None: self.load_comsyl_file()
        return self.af_oasys.get_wavefront(mode_index=self.mode_index,
                                           normalize_with_eigenvalue=self.normalize_with_eigenvalue)

    def to_python_code(self, do_plot=True, add_import_section=False):

        txt = ""

        txt += "#"
        txt += "\n# create output_wavefront\n#"
        txt += "\n#"

        if self._dimension == 2:
            txt += "\nfrom comsyl.autocorrelation.CompactAFReader import CompactAFReader"
        else:
            raise Exception("Not implemented")

        txt += '\nfilename = "%s"' % self.filename
        txt += "\naf_oasys = CompactAFReader.initialize_from_file(filename)"
        txt += "\n\nmode_index = %d"  % self.mode_index
        txt += "\noutput_wavefront = af_oasys.get_wavefront(mode_index,normalize_with_eigenvalue=%d)" % self.normalize_with_eigenvalue

        return txt


if __name__ == "__main__":
    filename = "/users/srio/Oasys/id18_ebs_u18_2500mm_s3.0.npz"
    pp = WOLightSourceCOMSYL(name="tmp", filename=filename, mode_index=3)

    print(">>>>> Dimension: ", pp.get_dimension())
    print(">>>>> filename: ", pp.get_filename())
    print(">>>>> code: \n", pp.to_python_code())

    wf = pp.get_wavefront()
    from srxraylib.plot.gol import plot_image
    plot_image(wf.get_intensity(), wf.get_coordinate_x(), wf.get_coordinate_y())