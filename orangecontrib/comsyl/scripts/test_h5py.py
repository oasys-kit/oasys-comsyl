__author__ = 'srio'


import h5py
import numpy
f = h5py.File('dset.h5', 'w')
x = numpy.linspace(-10.,10,200)
y = numpy.linspace(-10,10,100)
z = numpy.zeros((10,x.size,y.size), dtype=numpy.float)
X = numpy.outer(x,numpy.ones_like(y))
Y = numpy.outer(numpy.ones_like(x),y)
print(X.shape,Y.shape)

for i in range(z.shape[0]):
    z[i,:,:] = numpy.exp( - (X*X + Y*Y) / (2 * (5/(i+1))**2 ))
    print(i)

print(Y,Y.shape)

f['dset'] = z
f.close()
