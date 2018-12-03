
class ComsylPreprocessorData(object):
    def __init__(self,beamline_pickle_file=""):
        self._beamline_pickle_file=beamline_pickle_file

    def get_beamline_pickle_file(self,filename):
        self._beamline_pickle_file = filename

    def get_beamline_pickle_file(self):
        return self._beamline_pickle_file


if __name__=="__main__":
    pass