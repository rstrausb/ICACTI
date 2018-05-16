# -*- coding: utf-8 -*-
"""
Created on Fri Jan 17 11:52:43 2014

@author: Robert Strausbaugh and Nat Butler at ASU
"""
import ctypes as C
import ctypes.util as Cutil
import numpy as np
import math
from time import sleep
import pyfits
import datetime
from matplotlib import pyplot
import pylab

import IR_CAMERA

import os

import pygtk
pygtk.require('2.0')
import gtk

import serial

hdu = pyfits.PrimaryHDU()

#define some keywords:
hdu.header['USER']='Robert'
#hdu.header['EXPTIME']=0.017
hdu.header['CTYPE1']='RA---TAN'
hdu.header['CTYPE2']='DEC--TAN'
hdu.header['CD1_1']='0.001129'
hdu.header['CD2_2']='0.001129'
hdu.header['CD2_1']='0.'
hdu.header['CD1_2']='0.0'
hdu.header['CRPIX1']='160.'
hdu.header['CRPIX2']='120'

                            


###Needed for Zscale
MAX_REJECT = 0.5 
MIN_NPIXELS = 5 
GOOD_PIXEL = 0 
BAD_PIXEL = 1 
KREJ = 2.5 
MAX_ITERATIONS = 5 


###Twilight for reduction
twiflat = pyfits.open('twiflat_nozeros.fits')[0].data


class GUI:

    def delete_event(self, event, data=None):
        print 'delete event occured'
        return False
    
    def destroy(self, data=None):
        print "destroy signal occurred"        
        gtk.main_quit()
    
    def __init__(self):
       
        '''GUI Stuff'''        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect('destroy', self.destroy)
        self.window.set_border_width(100)
        self.window.set_title('IR Camera Interface')        
        
        self.BOX = gtk.VBox(False,0)
        self.window.add(self.BOX)
        
        self.box2 = gtk.HBox(False,0)

#        self.button=gtk.Button()
#        self.button.show()
#        self.box2.pack_start(self.button,True,True,0)
       
        self.box = gtk.HBox(False, 0)

        self.box3 = gtk.HBox(False,0)
        
        self.box4 = gtk.HBox(False, 0)
        
        self.box5=gtk.HBox(False,0)




        self.button_camera = gtk.Button('Initialize Camera')
        self.button_camera.connect('clicked', self.cameraStart)
        
        self.button_background = gtk.Button('Take Background')
        self.button_background.connect('clicked', self.background)
        
        blankspace_label = gtk.Label(' ')
        frame_label = gtk.Label('Number of Frames')
        expos_label = gtk.Label('Length of Exposure (s)')

        
        adj = gtk.Adjustment(0, 0, 540, 1, 1, 0)
        self.spinner = gtk.SpinButton(adj, 1, 2)
        self.spinner.set_wrap(True)
        self.spinner.set_size_request(10, -1)
#        adj.connect("value_changed", self.change_digits, self.spinner)
        self.button_run = gtk.Button('Run')
        self.button_run.connect('clicked', self.run)        
        
        self.button_snap = gtk.Button('Snap')
        self.button_snap.connect('clicked',self.snap)        
        
        self.button_quit = gtk.Button('Quit Program')
        self.button_quit.connect('clicked', self.destroy)        
        
        self.button_close = gtk.Button('Close Camera Interface')
        self.button_close.connect('clicked', self.close)    
        
                
        
        self.button_graphing = gtk.CheckButton('Graphing On')
        self.button_graphing.connect('toggled', self.graphing, "Graphing")
        
        self.button_writetodisk = gtk.CheckButton('Write to Disk')
        self.button_graphing.connect('toggled', self.saving, 'Write to Disk')
        
        self.enter_expos = gtk.Entry()
        self.enter_expos.set_max_length(5)
        self.enter_expos.connect('activate',self.setexpos)
        self.enter_expos.set_text("1")        
        
        self.enter_frame = gtk.Entry()
        self.enter_frame.set_max_length(5)
        self.enter_frame.connect('activate',self.setframe)
        self.enter_frame.set_text("1")         
        
        
        self.box.pack_start(self.button_camera, True, True, 0)
        self.box.pack_start(self.button_background, True, True, 0)
        self.box.pack_start(self.button_close, True, True, 0)  
        self.box.pack_start(self.button_quit, True, True, 0)
        
        
        
        self.box2.pack_start(expos_label,True,True,0)
        self.box2.pack_start(self.enter_expos,True,True,0)
        self.box2.pack_start(self.button_snap,True,True,0)

        self.box3.pack_start(frame_label,True,True,0)
        self.box3.pack_start(self.enter_frame,True,True,0)
        self.box3.pack_start(self.button_run, True, True, 0)
#        self.box3.pack_start(self.spinner, True, True, 0)
        
        
        self.box4.pack_start(self.button_graphing,True,True,0)
        self.box4.pack_start(self.button_writetodisk,True,True,0)

        self.box5.pack_start(blankspace_label,True,True,0)
        
        self.BOX.pack_start(self.box,True,True,0)
        self.BOX.pack_start(self.box5,True,True,0)
        self.BOX.pack_start(self.box2, True,True,0)
        self.BOX.pack_start(self.box3, True, True, 0)
        self.BOX.pack_start(self.box4, True, True, 0)
        
        
        self.button_camera.show()
        self.button_background.show()
        self.button_run.show() 
        self.button_snap.show()
        self.button_graphing.show()           
        self.button_close.show()
        self.button_quit.show() 
        frame_label.show()
        expos_label.show()
        blankspace_label.show()
        self.spinner.show()
        self.button_writetodisk.show()
        self.enter_expos.show()
        self.enter_frame.show()
        
            
        self.box.show()
    
        self.box5.show()        
        
        self.box2.show()    
        
        self.box3.show()
        
        self.box4.show()
        
        self.BOX.show()
        
        self.window.show() 
        
   
        self.sleep_offset = 1.0
        
        
        '''setting up stuff for the camera/data'''
        imaqlib_path = Cutil.find_library('imaq')
        self.imaq = C.windll.LoadLibrary(imaqlib_path)
        
        self.current = str(np.datetime64(datetime.datetime.now()))
#        self.date = 'E://'+self.current[0:4]+ '_' + self.current[5:7]+'_' + self.current[8:10]
        self.date = 'C://'+self.current[0:4]+ '_' + self.current[5:7]+'_' + self.current[8:10]

        if os.path.exists(self.date):
            None
        else:
            os.mkdir(self.date)
            os.mkdir(str(self.date)+'/Data')
            os.mkdir(str(self.date)+'/Dark') 
            
        self.background=0
   
        self.darkArray = 0
        
        if __name__ == "__main__":
            self.camera = IR_CAMERA.SWIR_img_session()
            sleep(2)

            ser = serial.Serial(port =0, baudrate = 57600)
            sleep(2)
            ser.write("opr 15\r")
            ser.close()
        
        
        
    def cameraStart(self, widget):
        '''Initialize Camera'''
        expos=np.float(self.enter_expos.get_text())
        self.camera.cameraInit(expos)
        
        hdu.header['EXPTIME']=expos

        
        
        
        
        
        
        
        
        
        
        
    def snap(self,widget):
        
        '''Capture Single Image'''        
        
        self.camera.expos()
#        print self.camera.img
        
        hdu.header['DATE-OBS']=str(self.camera.start_time)
        hdu.header['DATE-OBE']=str(self.camera.stop_time)
        hdu.header['CAM-TEMP']=str(self.camera.TEMP)

        
        if self.button_graphing.get_active()==True:           
                
#                reduction = (self.array - self.darkArray)/twiflat
                reduction = self.camera.img-self.background
                """Zscaling the image for viewing"""
                self.zscale(reduction)
    #            print 'result',reduction.min(),reduction.max()
                
    #            print 'option'+str(self.option)
                pylab.figure(1)
                ax1 = pyplot.subplot2grid((8,8), (0,0), colspan=8, rowspan=6)
    #            pylab.subplot(331)
                self.im = pyplot.imshow(reduction, cmap=pylab.cm.gray)
                
                ax2 = pyplot.subplot2grid((8,8), (6,0), colspan=8, rowspan=2)            
    #            pylab.subplot(3,3,2)
                pyplot.subplots_adjust(hspace=2)
                self.hist= pyplot.hist(self.camera.img.reshape(320*240),bins=420, log=True, color='k')
                
                pyplot.show(block=False)
                pyplot.pause(0.00001)
    
#                self.im.remove()
#                pyplot.cla()
                
        else:
            None
        
        if self.button_writetodisk.get_active()==True:
            ##Saves Data to File#####
         #Relates the file name to time
            current = np.datetime_as_string(np.datetime64(datetime.datetime.utcnow()))
#            hour = int(current[11:13])-5
#            if hour < 10:
#                hour = str(0)+str(hour)
#            else:
#                hour = str(hour)
            now = current[0:4]+ '_' + current[5:7]+ '_' + current[8:10]+ '_h' + current[11:13]+ '_m' + current[14:16]+'_s' + current[17:19]+ '.' + current[20:26]     
            
            self.filename = str(self.date)+'/Data/'+str(now)+'.fits'
            try:
                pyfits.writeto(self.filename, self.camera.img, hdu.header)
            except:
                pass
        
        
        else:
            None
        
        
        
        print "Image Taken"
    
    def background(self, widget):
        """
        Take a background image
        """
        
        self.camera.expos()
#        print self.camera.img
        
        hdu.header['DATE-OBS']=str(self.camera.start_time)
        hdu.header['DATE-OBE']=str(self.camera.stop_time)
        hdu.header['CAM-TEMP']=str(self.camera.TEMP)

        
        if self.button_graphing.get_active()==True:           
                
#                reduction = (self.array - self.darkArray)/twiflat
                reduction = self.camera.img-self.background
                """Zscaling the image for viewing"""
                self.zscale(reduction)
    #            print 'result',reduction.min(),reduction.max()
                
    #            print 'option'+str(self.option)
                pylab.figure(1)
                ax1 = pyplot.subplot2grid((8,8), (0,0), colspan=8, rowspan=6)
    #            pylab.subplot(331)
                self.im = pyplot.imshow(reduction, cmap=pylab.cm.gray)
                
                ax2 = pyplot.subplot2grid((8,8), (6,0), colspan=8, rowspan=2)            
    #            pylab.subplot(3,3,2)
                pyplot.subplots_adjust(hspace=2)
                self.hist= pyplot.hist(self.camera.img.reshape(320*240),bins=420, log=True, color='k')
                
                pyplot.show(block=False)
                pyplot.pause(0.00001)
    
#                self.im.remove()
#                pyplot.cla()
                
        else:
            None
        
        if self.button_writetodisk.get_active()==True:
            ##Saves Data to File#####
         #Relates the file name to time
            current = np.datetime_as_string(np.datetime64(datetime.datetime.utcnow()))
#            hour = int(current[11:13])-5
#            if hour < 10:
#                hour = str(0)+str(hour)
#            else:
#                hour = str(hour)
            now = current[0:4]+ '_' + current[5:7]+ '_' + current[8:10]+ '_h' + current[11:13]+ '_m' + current[14:16]+'_s' + current[17:19]+ '.' + current[20:26]     
            
            self.filename = str(self.date)+'/Dark/'+str(now)+'.fits'
            try:
                pyfits.writeto(self.filename, self.camera.img, hdu.header)
            except:
                pass
        
        
        else:
            None
        
       
        
        self.background=self.camera.img
        
        
        
        print 'Background Stored'



 
    def zscale(self, image, nsamples=1000, contrast=0.25, bpmask=None, zmask=None): 
        """Implement IRAF zscale algorithm 
        nsamples=1000 and contrast=0.25 are the IRAF display task defaults 
        bpmask and zmask not implemented yet 
        image is a 2-d numpy array 
        returns (z1, z2) 
        """ 
    
        # Sample the image 
        samples = self.zsc_sample(image, nsamples, bpmask, zmask) 
        npix = len(samples) 
        samples.sort() 
        zmin = samples[0] 
        zmax = samples[-1] 
        # For a zero-indexed array 
        center_pixel = (npix - 1) // 2 
        if npix%2 == 1: 
           median = samples[center_pixel] 
        else: 
           median = 0.5 * (samples[center_pixel] + samples[center_pixel + 1]) 
    
       # 
       # Fit a line to the sorted array of samples 
        minpix = max(MIN_NPIXELS, int(npix * MAX_REJECT)) 
        ngrow = max (1, int (npix * 0.01)) 
        ngoodpix, zstart, zslope = self.zsc_fit_line(samples, npix, KREJ, ngrow, MAX_ITERATIONS) 
    
        if ngoodpix < minpix: 
           z1 = zmin 
           z2 = zmax 
        else: 
           if contrast > 0: 
               zslope = zslope / contrast 
               z1 = max (zmin, median - (center_pixel - 1) * zslope) 
               z2 = min (zmax, median + (npix - center_pixel) * zslope) 
#           return z1, z2 
        image[:,:]=image.clip(z1,z2)
       
#        print z1,z2

    def zsc_sample(self, image, maxpix, bpmask=None, zmask=None): 
           
          # Figure out which pixels to use for the zscale algorithm 
          # Returns the 1-d array samples 
          # Don't worry about the bad pixel mask or zmask for the moment 
          # Sample in a square grid, and return the first maxpix in the sample 
        nc = image.shape[0] 
        nl = image.shape[1] 
        stride = max (1.0, math.sqrt((nc - 1) * (nl - 1) / float(maxpix))) 
        stride = int (stride) 
        samples = image[::stride,::stride].flatten() 
        return samples[:maxpix]
        
    def zsc_fit_line(self, samples, npix, krej, ngrow, maxiter): 
      
        # 
        # First re-map indices from -1.0 to 1.0 
        xscale = 2.0 / (npix - 1) 
        xnorm = np.arange(npix) 
        xnorm = xnorm * xscale - 1.0 
    
        ngoodpix = npix 
        minpix = max (MIN_NPIXELS, int (npix*MAX_REJECT)) 
        last_ngoodpix = npix + 1 
    
        # This is the mask used in k-sigma clipping.  0 is good, 1 is bad 
        badpix = np.zeros(npix, dtype="int32") 
    
        # 
        #  Iterate 
    
        for niter in range(maxiter): 
    
            if (ngoodpix >= last_ngoodpix) or (ngoodpix < minpix): 
                break 
            
            # Accumulate sums to calculate straight line fit 
            goodpixels = np.where(badpix == GOOD_PIXEL) 
            sumx = xnorm[goodpixels].sum() 
            sumxx = (xnorm[goodpixels]*xnorm[goodpixels]).sum() 
            sumxy = (xnorm[goodpixels]*samples[goodpixels]).sum() 
            sumy = samples[goodpixels].sum() 
            sum = len(goodpixels[0]) 
            delta = sum * sumxx - sumx * sumx 
            # Slope and intercept 
            intercept = (sumxx * sumy - sumx * sumxy) / delta 
            slope = (sum * sumxy - sumx * sumy) / delta 
            
            # Subtract fitted line from the data array 
            fitted = xnorm*slope + intercept 
            flat = samples - fitted 
     
            # Compute the k-sigma rejection threshold 
            ngoodpix, mean, sigma = self.zsc_compute_sigma (flat, badpix, npix) 
    
            threshold = sigma * krej 
       
            # Detect and reject pixels further than k*sigma from the fitted line 
            lcut = -threshold 
            hcut = threshold 
            below = np.where(flat < lcut) 
            above = np.where(flat > hcut) 
       
            badpix[below] = BAD_PIXEL 
            badpix[above] = BAD_PIXEL 
               
            # Convolve with a kernel of length ngrow 
            kernel = np.ones(ngrow,dtype="int32") 
            badpix = np.convolve(badpix, kernel, mode='same') 
       
            ngoodpix = len(np.where(badpix == GOOD_PIXEL)[0]) 
               
            niter += 1 
       
          # Transform the line coefficients back to the X range [0:npix-1] 
            zstart = intercept - slope 
            zslope = slope * xscale 
        
            return ngoodpix, zstart, zslope 


    def zsc_compute_sigma(self, flat, badpix, npix): 
      
        # Compute the rms deviation from the mean of a flattened array. 
        # Ignore rejected pixels 
    
        # Accumulate sum and sum of squares 
        goodpixels = np.where(badpix == GOOD_PIXEL) 
        sumz = flat[goodpixels].sum() 
        sumsq = (flat[goodpixels]*flat[goodpixels]).sum() 
        ngoodpix = len(goodpixels[0]) 
        if ngoodpix == 0: 
           mean = None 
           sigma = None 
        elif ngoodpix == 1: 
           mean = sumz 
           sigma = None 
        else: 
           mean = sumz / ngoodpix 
           temp = sumsq / (ngoodpix - 1) - sumz*sumz / (ngoodpix * (ngoodpix - 1)) 
           if temp < 0: 
              sigma = 0.0 
           else: 
              sigma = math.sqrt (temp) 
       
        return ngoodpix, mean, sigma 


#
#    def get_value(self):
#        observetime = self.spinner.get_value_as_int()*60   #controls number of files created
##        print observetime
#        return observetime
        
        
    def graphing(self, widget, data=None):
        '''Toggle for Graphing'''
#        self.state = (data, ("OFF", "ON")[widget.get_active()])        
#        print "%s was toggled %s" % self.state
#        return self.state[1]     
        return widget.get_active()
        
    def saving(self, widget, data=None):
        '''Toggle for Writing data to disk'''
        return widget.get_active()
        
    
    def setexpos(self,widget):
        self.expos=np.int(self.enter_expos.get_text())
#        print type(self.expos)
        
    def setframe(self,widget):
        self.frameNum=np.int(self.enter_frame.get_text())
        return self.frameNum
        
    def run(self, frameNum=1):
#        observetime = self.spinner.get_value_as_int()  #controls number of files created

       for i in range(np.int(self.enter_frame.get_text())):
            print i
           
            self.snap(self)
            print 'Frame Median:' + str(np.median(self.camera.img))
#            print self.camera.TEMP
            if self.button_graphing.get_active()==True:            
                self.im.remove()
                pyplot.cla()
            else:
                None
#            
             
       print 'done'    

    def close(self, widget):
        """
        just close the session
        """
        self.camera.close()
    def main(self):
        gtk.main()

print __name__
if __name__ == "__main__":
    win = GUI()
    win.main()
