
import h5py
import numpy

try:
    from comsyl.scripts.CompactAFReader import CompactAFReader
except:
    try:
        from CompactAFReader import CompactAFReader
    except:
        raise ImportError("Cannt find CompactAFReader")


def AF_to_h5(filename_without_extension,filename_out='comsyl_test.h5',max_number_of_modes=None,write_intensity=True):


    reader = CompactAFReader(filename_without_extension)

    print("File %s:" % filename_in)
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


    if max_number_of_modes == None:
        max_number_of_modes = reader.number_modes()

    eigenvalues = numpy.zeros(max_number_of_modes,dtype=complex)

    # TODO change the order - check with the viewer
    mystack = numpy.zeros((max_number_of_modes,y.size,x.size),dtype=complex)

    for i_mode in range(max_number_of_modes):
        eigenvalues[i_mode] = reader.occupation(i_mode)
        mode = reader.mode(i_mode)
        mystack[i_mode,:,:] = mode.T



    f = h5py.File(filename_out, 'w')

    f['converted_from_filename'] = filename_in
    f['number_of_modes'] = max_number_of_modes
    f['eigenvalues'] = eigenvalues
    f['x'] = x
    f['y'] = y
    f['modes'] = mystack

    if write_intensity:
        mystack_intensity = numpy.absolute(mystack)**2
        f['modes_intensity'] = mystack_intensity
        # delta = (x[1] - x[0]) *(y[1] - y[0])
        # for i in range(reader.number_modes()):
        #     print("mode: %d integral: %f"%(i,mystack_intensity[i,:,:].sum()*delta))

    f.close()
    print("File written to disk",filename_out)



if __name__ == "__main__":

    path_in = "/scisoft/users/srio/comsyl_srio/calculations/"
    path_out = path_in

    files = ['new_u18_2m_1h_s2.5.npy'] # ,'ph3_u18_3_17keV_s1.3.npy']

    for filename_in in files:
        print("Converting file: ",path_in+filename_in)
        filename_without_extension = ('.').join(filename_in.split('.')[:-1])
        AF_to_h5(path_in+filename_without_extension,
                 path_out+filename_without_extension+'_100modes.h5',
                 max_number_of_modes=100,write_intensity=True)

