import numpy as np
import os
from astropy.table import Table
import scipy.interpolate as inter
import glob
import matplotlib.pyplot as plt
import math

#Reads in spectra file names
spectra_files = glob.glob("../../../data/cfa/*/*.flm")

spectra_arrays=[]
bad_files = []
file_name =[]

num=40	#number of spectra to analyse, eventually will be len(spectra_files)

for i in range(num):
	try:
		spectra_arrays.append(Table.read(spectra_files[i],format='ascii'))
		file_name.append(spectra_files[i])
	except ValueError:
		bad_files.append(spectra_files[i])

#deredshift data
parameters = Table.read('../../../data/cfa/cfasnIa_param.dat',format='ascii')
sn_name = parameters["col1"]
sn_z = parameters["col2"]
for i in range(len(file_name)):
	old_spectrum=spectra_arrays[i]
	z=0
	for j in range(len(sn_name)):
		if sn_name[j] in file_name[i]:
			z=sn_z[j]
	lambda_obs=old_spectrum["col1"]
	lambda_emit= lambda_obs/(1+z)
	spectra_arrays[i]=Table([lambda_emit,old_spectrum["col2"]],names=('col1','col2'))

	
#scale spectra		
wave_min=0  #arbitrary minimum of wavelength range
wave_max=1000000   #arbitrary maximum of wavelength range

for i in range(len(spectra_arrays)):
	spectra = spectra_arrays[i]
	if (min(spectra["col1"]) > wave_min): #changes minimum wavelength if larger than previous
		wave_min=min(spectra["col1"])
	if (max(spectra["col1"]) < wave_max):  #changes maximum wavelength if smaller than previous
		wave_max=max(spectra["col1"])

wavelength = np.linspace(wave_min,wave_max,wave_max-wave_min)  #creates 100 equally spaced wavelength values between the smallest range

#generates composite spectrum
fitted_flux=[]	#new interpolated flux values over wavelength range
for i in range(len(spectra_arrays)):
	new_spectrum=spectra_arrays[i]	#declares new spectrum from list
	new_wave=new_spectrum["col1"]	#wavelengths
	new_flux=new_spectrum["col2"]	#fluxes
	lines=np.where((new_wave>wave_min) & (new_wave<wave_max))	#creates an array of wavelength values between minimum and maximum wavelengths from new spectrum
	sm1=inter.splrep(new_wave[lines],new_flux[lines])	#creates b-spline from new spectrum
	y1=inter.splev(wavelength,sm1)	#fits b-spline over wavelength range
	y1 /= np.median(y1)
	fitted_flux.append(y1)

avg_flux = np.mean(fitted_flux,axis=0)	#finds average flux at each wavelength

avg_spectrum=Table([wavelength,avg_flux],names=('col1','col2'))	#puts together the average spectrum

#RMS Spectrum, Residual
delta=[]
scatter=[]
for i in range(len(fitted_flux)):
	delta.append(avg_flux-fitted_flux[i])

rms_flux = np.sqrt(np.mean(np.square(delta),axis=0))	#creates RMS value of flux at each wavelength

for i in range(len(rms_flux)):
	scatter.append(rms_flux[i]/avg_flux[i]*100)	#creates residual values

#RMS Residual
plt.figure(1)
plt.subplot(211)
plot1,=plt.plot(wavelength,avg_flux+rms_flux,label= 'rms+', color='k')
plot2,=plt.plot(wavelength,avg_flux-rms_flux, label= 'rms-')
plot3,=plt.plot(wavelength,avg_flux,label='comp')
legend=plt.legend(loc='upper right', shadow=True)
plt.xlim(wave_min,wave_max)
plt.ylabel('Flux')
plt.subplot(212)
plot1,=plt.plot(wavelength,scatter,label='rms residual')
plt.xlim(wave_min,wave_max)
plt.ylim(0,100)
plt.xlabel('Wavelength')
plt.ylabel('RMS Flux/ Average Flux')
plt.savefig('rmsplot.png')
plt.show()

