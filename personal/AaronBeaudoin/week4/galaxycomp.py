import numpy as np
import os
from astropy.table import Table
import scipy.interpolate as inter
import glob
import matplotlib.pyplot as plt
import math

#Reads in spectra file names
spectra_files=Table.read('MaxSpectra.dat',format='ascii')
spectra_arrays=[]
spectra_names=[]
bad_files=[]

num=len(spectra_files)	#number of spectra to analyse, eventually will be len(spectra_files)

for i in range(num):
	spectrum_file=spectra_files[i]
	try:
		spectra_arrays.append(Table.read(spectrum_file["col2"],format='ascii'))
		spectra_names.append(spectrum_file["col1"])
	except ValueError:
		bad_files.append(spectra_files[i])
		
#classifies each spectra by the type of host galaxy
host_info=Table.read('../../MalloryConlon/Galaxy/host_info.dat',format='ascii')
sn_name=host_info["col1"]
host_type=host_info["col2"]
elliptical=[]
S0=[]
spiral=[]
irregular=[]
anon=[]
for j in range(len(host_info)):
	if host_type[j]==1 or host_type[j]==2:
		elliptical.append(sn_name[j])
	if host_type[j]==3 or host_type[j]==4:
		S0.append(sn_name[j])
	if host_type[j]==5 or host_type[j]==6 or host_type[j]==7 or host_type[j]==8 or host_type[j]==9 or host_type[j]==10:
		spiral.append(sn_name[j])
	if host_type[j]==11:
		irregular.append(sn_name[j])
	if host_type[j]==0:
		anon.append(sn_name[j])

sn_elliptical=[]
for i in range(len(elliptical)):
	for j in range(len(spectra_arrays)):
		if spectra_names[j] in elliptical[i]:
			sn_elliptical.append(spectra_arrays[j])
			
sn_S0=[]
for i in range(len(S0)):
	for j in range(len(spectra_arrays)):
		if spectra_names[j] in S0[i]:
			sn_S0.append(spectra_arrays[j])

sn_spiral=[]
for i in range(len(spiral)):
	for j in range(len(spectra_arrays)):
		if spectra_names[j] in spiral[i]:
			sn_spiral.append(spectra_arrays[j])

sn_irregular=[]
for i in range(len(irregular)):
	for j in range(len(spectra_arrays)):
		if spectra_names[j] in irregular[i]:
			sn_irregular.append(spectra_arrays[j])

#finds average flux, RMS, and scatter
def gal_comp_res(spectra_arrays):
	#deredshift data
	parameters = Table.read('../../../data/cfa/cfasnIa_param.dat',format='ascii')
	sn_name = parameters["col1"]
	sn_z = parameters["col2"]
	for i in range(len(spectra_arrays)):
		old_spectrum=spectra_arrays[i]
		z=0
		for j in range(len(sn_name)):
			if sn_name[j] in spectra_arrays[i]:
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
	return wavelength, avg_flux, rms_flux, scatter


#finds Composite spectrum, RMS spectrum, and scatter for each type of host galaxy
e_wavelength, e_avg_flux, e_rms_flux, e_scatter = gal_comp_res(sn_elliptical)
e_wave_min=min(e_wavelength)
e_wave_max=max(e_wavelength)
S_wavelength, S_avg_flux, S_rms_flux, S_scatter = gal_comp_res(sn_S0)
S_wave_min=min(S_wavelength)
S_wave_max=max(S_wavelength)
s_wavelength, s_avg_flux, s_rms_flux, s_scatter = gal_comp_res(sn_spiral)
s_wave_min=min(s_wavelength)
s_wave_max=max(s_wavelength)
i_wavelength, i_avg_flux, i_rms_flux, i_scatter = gal_comp_res(sn_irregular)
i_wave_min=min(i_wavelength)
i_wave_max=max(i_wavelength)


#Plots spectra based on host galaxy type
plt.figure(1)
plt.subplot(211)
plot1,=plt.plot(e_wavelength,e_avg_flux,label='comp', color='k')
plot2,=plt.plot(e_wavelength,e_avg_flux+e_rms_flux,label='rms+', color='b')
plot3,=plt.plot(e_wavelength,e_avg_flux-e_rms_flux,label='rms-', color='c')
legend=plt.legend(loc='upper right', shadow=True)
plt.xlim(e_wave_min,e_wave_max)
plt.ylabel('Flux')
plt.subplot(212)
plot1,=plt.plot(e_wavelength,e_scatter)
plt.xlim(e_wave_min,e_wave_max)
plt.ylim(0,100)
plt.xlabel('Wavelength')
plt.ylabel('Rms Flux/Average Flux')
plt.savefig('EllipticalPlot.png')
plt.show()

plt.figure(2)
plt.subplot(211)
plot1,=plt.plot(S_wavelength,S_avg_flux,label='comp', color='k')
plot2,=plt.plot(S_wavelength,S_avg_flux+S_rms_flux,label='rms+', color='b')
plot3,=plt.plot(S_wavelength,S_avg_flux-S_rms_flux,label='rms-', color='c')
legend=plt.legend(loc='upper right', shadow=True)
plt.xlim(S_wave_min,S_wave_max)
plt.ylabel('Flux')
plt.subplot(212)
plot1,=plt.plot(S_wavelength,S_scatter)
plt.xlim(S_wave_min,S_wave_max)
plt.ylim(0,100)
plt.xlabel('Wavelength')
plt.ylabel('Rms Flux/Average Flux')
plt.savefig('S0Plot.png')
plt.show()

plt.figure(3)
plt.subplot(211)
plot1,=plt.plot(s_wavelength,s_avg_flux,label='comp', color='k')
plot2,=plt.plot(s_wavelength,s_avg_flux+s_rms_flux,label='rms+', color='b')
plot3,=plt.plot(s_wavelength,s_avg_flux-s_rms_flux,label='rms-', color='c')
legend=plt.legend(loc='upper right', shadow=True)
plt.xlim(s_wave_min,s_wave_max)
plt.ylabel('Flux')
plt.subplot(212)
plot1,=plt.plot(s_wavelength,s_scatter)
plt.xlim(s_wave_min,s_wave_max)
plt.ylim(0,100)
plt.xlabel('Wavelength')
plt.ylabel('Rms Flux/Average Flux')
plt.savefig('SpiralPlot.png')
plt.show()


plt.figure(4)
plt.subplot(211)
plot1,=plt.plot(i_wavelength,i_avg_flux,label='comp', color='k')
plot2,=plt.plot(i_wavelength,i_avg_flux+i_rms_flux,label='rms+', color='b')
plot3,=plt.plot(i_wavelength,i_avg_flux-i_rms_flux,label='rms-', color='c')
legend=plt.legend(loc='upper right', shadow=True)
plt.xlim(i_wave_min,i_wave_max)
plt.ylabel('Flux')
plt.subplot(212)
plot1,=plt.plot(i_wavelength,i_scatter)
plt.xlim(i_wave_min,i_wave_max)
plt.ylim(0,100)
plt.xlabel('Wavelength')
plt.ylabel('Rms Flux/Average Flux')
plt.savefig('IrregularPlot.png')
plt.show()