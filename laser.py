#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
import time

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg

# https://www.institutoptique.fr/content/download/3234/22015/file/Optique%20Statistique%20cours%20ecrit.pdf

class Laser:
        
    def __init__(self, fs, n, D_phi):    
        # Sampling frequency (Hz)
        self.fs = fs
        # Number of points in time    
        self.n = n

        self.D_phi = D_phi   
        
        self.n_max = 2 * self.n
        
        # Time grid (s)
        self.t = np.arange(n)/fs
        # Time steps (s)
        self.dt = 1/fs
        self.fft_freq = np.fft.fftfreq(n)/self.dt
        
        self.phase = np.zeros(self.n_max) + 2* np.pi * np.random.rand()
        self.update_phase(self.n)
        
        self.interferometer_phase = np.pi/4

    def update_phase(self, n_update):
        phase_steps = np.sqrt(2*self.D_phi*self.dt) * np.random.randn(n_update)
        self.phase = np.roll(self.phase, -n_update)
        self.phase[-n_update-1:-1] = np.cumsum(phase_steps) + self.phase[-n_update-2]
     
    def interference_signal(self,delay):
        signal = 0.5*(1 + np.real(np.exp(1j * self.interferometer_phase) * \
                 np.exp(1j * (self.phase - np.roll(self.phase, np.int(delay / self.dt))))))
        return signal
        

class KoheronWindow(QtGui.QMainWindow):
    def __init__(self, app, laser):
        super(KoheronWindow, self).__init__()
        self.app = app        
        self.laser = laser
        
        self.max_dphi = 10e6
        self.dphi_step = 10e3
        
        self.delay = 0.1e-6
        self.max_delay = 1e-6
        self.delay_step = 0.001e-6
                
        self.setWindowTitle("Koheron Simulation of laser phase noise") # Title
        self.setWindowIcon(QtGui.QIcon('icon_koheron.png'))
        self.resize(800, 600) # Size

        # Layout
        self.centralWid = QtGui.QWidget()
        self.setCentralWidget(self.centralWid)
        
        self.lay = QtGui.QVBoxLayout()
        self.button_sublayout = QtGui.QHBoxLayout()   
        self.hlay1 = QtGui.QHBoxLayout()   

        self.value_layout = QtGui.QVBoxLayout()         
        self.slider_layout = QtGui.QVBoxLayout()  
                
        
        self.centralWid.setLayout(self.lay)
                
        # Widgets : Buttons, Sliders, PlotWidgets
      
        # D_phi
        self.dphi_label = QtGui.QLabel()
        self.dphi_label.setText('Linewitdth (kHz): '+"{:.2f}".format(self.laser.D_phi/(2*np.pi)))
        self.dphi_slider = QtGui.QSlider()
        self.dphi_slider.setMinimum(0)
        self.dphi_slider.setMaximum(self.max_dphi/self.dphi_step)
        self.dphi_slider.setOrientation(QtCore.Qt.Horizontal)
        
        # D_phi
        self.delay_label = QtGui.QLabel()
        self.delay_label.setText('Delay (ns): '+"{:.2f}".format(self.delay))
        self.delay_slider = QtGui.QSlider()
        self.delay_slider.setMinimum(0)
        self.delay_slider.setMaximum(self.max_delay/self.delay_step)
        self.delay_slider.setOrientation(QtCore.Qt.Horizontal)        
        
        
        # Plot Widget   
        self.plotWid = pg.PlotWidget(name="data")
        self.dataItem = pg.PlotDataItem(1e-6 * np.fft.fftshift(self.laser.fft_freq),0*self.laser.t, pen=(0,4))
        self.plotWid.addItem(self.dataItem)
        self.plotItem = self.plotWid.getPlotItem()
        self.plotItem.setMouseEnabled(x=False, y = True)
        #specItem.setYRange(-8192, 8192)
        # Axis
        self.plotAxis = self.plotItem.getAxis("bottom")
        self.plotAxis.setLabel("Frequency (MHz)")

        
        # Add Widgets to layout
        
        

        
        self.value_layout.addWidget(self.dphi_label,0)        
        self.slider_layout.addWidget(self.dphi_slider,0)
        
        self.value_layout.addWidget(self.delay_label,0)        
        self.slider_layout.addWidget(self.delay_slider,0)        
        
        
        self.hlay1.addLayout(self.value_layout)     
        self.hlay1.addLayout(self.slider_layout) 
        
        self.lay.addLayout(self.hlay1)
        self.lay.addWidget(self.plotWid)
        
        self.dphi_slider.valueChanged.connect(self.change_dphi)
        self.delay_slider.valueChanged.connect(self.change_delay)
        
        self.show()
        
        # Define events
        
    #@profile
    def update(self):        
        self.laser.update_phase(16)
        signal = self.laser.interference_signal(self.delay)
        psd = np.abs(np.square(np.fft.fft(signal[-self.laser.n-1:-1])));
        self.dataItem.setData(1e-6 * np.fft.fftshift(self.laser.fft_freq),np.fft.fftshift(10*np.log10(psd)))
    
  
    def change_dphi(self):
        self.laser.D_phi = self.dphi_slider.value()*self.dphi_step    
        self.dphi_label.setText('Linewidth (kHz) : '+"{:.2f}".format(1e-3 * self.laser.D_phi / (2*np.pi)))
        
    def change_delay(self):
        self.delay = self.delay_slider.value()*self.delay_step 
        self.delay_label.setText('Delay (ns) : '+"{:.2f}".format(1e9 * self.delay))
        
     
        
        
def main():        
    fs = 250e6
    n = 1024
    linewidth = 100e3; 
    D_phi = 2*np.pi*linewidth
    
    # Interferometer delay (s)
    delay = 0.1e-6  
    
    las = Laser(fs, n, D_phi)        
    
    app = QtGui.QApplication.instance()
    if app == None:
        app = QtGui.QApplication([])
    app.quitOnLastWindowClosed()    
    
    khw = KoheronWindow(app, las)    
    
    while True:         
        khw.update()
        QtGui.QApplication.processEvents()
    
    
    
    # Plot settings
    fig = plt.figure(figsize=(16,12))
    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)
    line1, = ax1.plot(np.fft.fftshift(las.fft_freq),np.linspace(-50,50,las.n))
    line11, = ax1.plot(np.fft.fftshift(las.fft_freq),np.linspace(-50,50,las.n))
    line2, = ax2.plot(las.t,np.linspace(0,1,las.n))
    line3, = ax3.plot(las.t,np.linspace(-10.1,10.1,las.n))
    line31, = ax3.plot(las.t,np.linspace(-10.1,10.1,las.n))
    
    psd_avg = np.zeros(las.n)
    
    for i in range(1):
        las.update_phase(16)
        signal = las.interference_signal(delay)
        psd = np.abs(np.square(np.fft.fft(signal[-las.n-1:-1])));
        psd_avg = (i * psd_avg + psd)/(i+1) 
        line1.set_ydata(np.fft.fftshift(10*np.log10(psd)))
        line11.set_ydata(np.fft.fftshift(10*np.log10(psd_avg)))
        line2.set_ydata(signal[-las.n-1:-1])   
        line3.set_ydata(las.phase[-las.n-1:-1])
        tmp = np.roll(las.phase, np.int(delay / las.dt))
        line31.set_ydata(tmp[-las.n-1:-1])
        fig.canvas.draw()
        time.sleep(0.01)

if __name__ == '__main__':
    import sys    
    main()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()     

         