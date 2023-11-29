import csv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 
import sunpy_soar
import astropy as ap
import scipy as sp
import datetime as dt

from astropy import units as u
import astropy.constants as const
from astropy.wcs import WCS, FITSFixedWarning
from astropy.io import fits
from astropy.coordinates import SkyCoord


from sunpy.coordinates import frames
from sunpy.coordinates import Helioprojective, HeliographicStonyhurst, propagate_with_solar_surface
import sunpy.map
from sunpy.coordinates.utils import GreatArc
from sunpy.net import Fido, attrs

from astropy.visualization import SqrtStretch, AsymmetricPercentileInterval, ImageNormalize
from astropy.time import Time, TimeDelta
from astropy.utils.data import download_file


import warnings
import astropy.units as u
from sospice import Catalog


    
    


class spice_fov(object):
    
    def __init__(self, catalog_row):
        """
        Class to calculate the FOV for a SPICCE observation at the given time. 
        This class should not be called directly by the end-user but is a backend for the spice_plotfovs class (see below).
        
        input: catalog_row is catalog dataframe with only one row
        """
        self.cat=catalog_row
        
        #read out parameters from catalogue necessary for FOV visualization
        self.NAXIS1=self.cat["NAXIS1"]
        self.NAXIS2=self.cat["NAXIS2"]
        self.CRVAL1=self.cat["CRVAL1"]*u.arcsec
        self.CDELT1=self.cat["CDELT1"]*u.arcsec
        self.CRVAL2=self.cat["CRVAL2"]*u.arcsec
        self.CDELT2=self.cat["CDELT2"]*u.arcsec
        self.CROTA=self.cat["CROTA"]*u.deg
        self.DATE_BEG=self.cat['DATE-BEG']        
        self.DSUN_AU=self.cat['DSUN_AU']*u.AU
        self.HGLT_OBS=self.cat['HGLT_OBS']*u.deg
        self.HGLN_OBS=self.cat['HGLN_OBS']*u.deg        
        self.CRPIX1=self.NAXIS1/2+0.5
        self.CRPIX2=self.NAXIS2/2+0.5
        self.filename=self.cat["FILENAME"]
        self.spiobs_id=self.cat["SPIOBSID"]
        self.raster_no=self.cat["RASTERNO"]
        self.datebeg_label=str(self.DATE_BEG)[0:-7]
        self.studytyp_label=self.filename[16:19]
        
        #get coordinates from pixels 
        self.PC1_1, self.PC1_2, self.PC2_1, self.PC2_2 = self.get_PC()
        self.WCS=self.get_WCS()
        self.OBS_STH=self.get_OBS()
        self.FOV_COORDS_STH, self.FOV_COORDS_CAR=self.get_FOV()
 
        
    def get_PC(self):
        CDELT_ratio=self.CDELT2/self.CDELT1
        PC1_1=(np.cos(self.CROTA)).value
        PC1_2=(-np.sin(self.CROTA)*CDELT_ratio).value
        PC2_1=(np.sin(self.CROTA)/CDELT_ratio).value
        PC2_2=(np.cos(self.CROTA)).value
        return PC1_1, PC1_2, PC2_1, PC2_2
    
    
    def get_WCS(self):
        header_dict = self.cat.to_dict()
        header_dict['DATE-BEG'] = header_dict['DATE-BEG'].isoformat()
        header_dict.pop('LEVEL')
        header_dict.pop('CROTA')
        header_dict['CRPIX1']=self.CRPIX1
        header_dict['CRPIX2']=self.CRPIX2
        header_dict['PC1_1']=self.PC1_1
        header_dict['PC1_2']=self.PC1_2
        header_dict['PC2_1']=self.PC2_1
        header_dict['PC2_2']=self.PC2_2
        
        with warnings.catch_warnings():
            # Ignore a warning on using DATE-OBS in place of MJD-OBS
            warnings.filterwarnings('ignore', message="'datfix' made the change",category=FITSFixedWarning)
            header = fits.Header(header_dict)
        return WCS(header)    
 

    def get_OBS(self):
        """
        Get observer position and time for an observation

        Parameters
        ----------
        cat_row: oandas.Series
            Catalog row corresponding to the observation

        Return
        ------
        atropy.coordinates.SkyCoord
            Observer coordinates
        """
        observer_sth = HeliographicStonyhurst(self.HGLN_OBS, self.HGLT_OBS, self.DSUN_AU, obstime=self.DATE_BEG)  # average date?
        return observer_sth

 
            
    def get_FOV(self):
        """
        Get the FOV coordinates (bottom left and top right vertices of rectangle
        in helioprojective coordinates) for an observation

        Parameters
        ----------
        cat_row: pandas.Series
            Catalog row corresponding to the observation
        """
        wcs = self.WCS
        vertices_pixels = [[0, 0], [self.NAXIS1 - 1, 0], [self.NAXIS1 - 1, self.NAXIS2 - 1], [0, self.NAXIS2 - 1]]
        vertices_world = np.array(wcs.pixel_to_world_values(vertices_pixels))
        vertices_world[(vertices_world[:, 0] < -180), 0] += 360  # some longitudes were centered on -360°...
        frame_sth = Helioprojective(observer=self.OBS_STH, obstime=self.DATE_BEG)
        fov_coords_sth = SkyCoord(vertices_world * u.deg, frame=frame_sth)
        
        fov_coords_car=[]
        for c_sth in fov_coords_sth:
            c_car=c_sth.transform_to(frames.HeliographicCarrington)
            fov_coords_car.append(c_car)
        fov_coords_car=np.array(fov_coords_car)
        
        return fov_coords_sth, fov_coords_car
        
   

   
class spice_plotfovs(object):  
    
    def __init__(self, catalog, date_min, date_max,Level="L2", Studytype="All"):
        """
        Class to plot the FOVs for a number SPICE observation within a given time frame (< 1  Carrington rotation). The only method of this class to be used by the end-user is: plot_SPICE_FOV() 
        
        Input parameters
        ----------
            catalog: sospice catalogue object
            
            date_min: date of earliest observation, format: np.datetime64('2022-03-05T12:00:00.00')
            
            data_max: date of latest observation, format: np.datetime64('2022-03-05T12:00:00.00')
            
            Level: "L1 or "L2"
            
            Studytype: "raster", "Sit-and-stare", "Single Exposure", or "All"
        
        Return
        ------
        spice_plotfovs object that contains all observation information necessary to plot SPICE FOVs 
        """
   
        catalog_red=self.reduce_cat(catalog)
        catalog_redfilt=self.filter_cat(catalog_red, date_min, date_max, Level, Studytype)
        self.spice_fovs=[]
        i=0
        while i<len(catalog_redfilt):
            self.spice_fovs.append(spice_fov(catalog_redfilt.iloc[i]))
            i+=1
        self.fsi_path="fsi_data"
        self.cat_rf=catalog_redfilt
    
    
    def reduce_cat(self, catalog):    
        """
        Method to reduce catalog dataframe to parameter-set that is necessary to calculate SPICE FOVs, should not be used by end-user
        """
        cat=catalog
        keys_redcat = [ 'NAXIS1', 'NAXIS2', 'LEVEL', "FILENAME", "SPIOBSID", "RASTERNO", "STUDYTYP", 'DATE-BEG', 'CNAME1', 'CRVAL1', 'CDELT1', 'CUNIT1', 'CTYPE1', 'CNAME2', 'CRVAL2', 'CDELT2', 'CUNIT2', 'CTYPE2', 'CROTA', 'DSUN_AU', 'HGLT_OBS', 'HGLN_OBS']
        redcat=cat[keys_redcat]
        return redcat


    def filter_cat(self, catalog, date_min, date_max,Level="L2",Studytype="All"):
        """
        Method to filter catalog for rows(s) that correspond(s) to specific time stamps(s), should not be used by end-user
        """
        cat=catalog
        if Studytype=="All":
            filtcat = cat.loc[(cat['DATE-BEG'] >= date_min) * (cat['DATE-BEG'] <= date_max) * (cat['LEVEL'] == Level)]
        else:    
            filtcat = cat.loc[(cat['DATE-BEG'] >= date_min) * (cat['DATE-BEG'] <= date_max) * (cat['LEVEL'] == Level) * (cat['STUDYTYP'] == Studytype)] 
        return filtcat

    
    def plot_HMI_map(self, CR=2554, figx=18, figy=8,download_mapfile=True,map_path="/Users/nils.janitzek/Projects/SolO/RS_Coordination_Tool/SPICE_FOV/"):
        """
        Method to plot synoptic Carrington HMI_map, should not be used by end-user
        (Normal use is to download the map from jsoc (see link below).
        Yet, for testing it is faster to use a local version of the map-file (in given map_path)).
        """
        self.CR=CR
        if download_mapfile==True:
            url='http://jsoc.stanford.edu/data/hmi/synoptic/hmi.Synoptic_Mr.%s.fits'%(self.CR)
            filename = download_file(url)#, cache=True) file is saved in C:\Users\user\AppData\Local\Temp
            self.hmi_syn_map = sunpy.map.Map(filename)
        else:
           filename = "HMI_map_CR%i"%(self.CR)
           self.hmi_syn_map = sunpy.map.Map(map_path+filename)

        self.hmi_fig = plt.figure(figsize=(figx, figy))
        print("map test:", self.hmi_syn_map)
        self.hmi_ax = plt.subplot(projection=self.hmi_syn_map)
        self.hmi_im = self.hmi_syn_map.plot(axes=self.hmi_ax)
        plt.title("SDO/HMI synoptic map for CR %i"%(CR),fontsize=14)
        plt.show()
    
    
    def plot_SPICE_FOV_HMI(self,plot_fov_labels=True, plot_repeated_obsid=True, save_figure=False, figname="spicefovs_test_V1-0"):
        """
        Method to plot SPICE FOV on HMI synoptic Carrington map, should not be used by end-user  
        """
        i=0
        obs_id=0
        fov_last=self.spice_fovs[-1]
        
        for i, fov in enumerate(self.spice_fovs):
            point_coord1 = fov.FOV_COORDS_CAR[0]
            point_coord2 = fov.FOV_COORDS_CAR[1]
            point_coord3 = fov.FOV_COORDS_CAR[2]
            point_coord4 = fov.FOV_COORDS_CAR[3]
            arc1 = GreatArc(point_coord1, point_coord2)
            arc2 = GreatArc(point_coord2, point_coord3)
            arc3 = GreatArc(point_coord3, point_coord4)
            arc4 = GreatArc(point_coord4, point_coord1)

            if fov.spiobs_id==obs_id:
                if plot_repeated_obsid==True:
                    if i==(len(self.spice_fovs)-1) or (self.spice_fovs[i+1]).spiobs_id!=fov.spiobs_id:
                        self.hmi_ax.plot_coord(arc1.coordinates(), color=pcolor, linewidth=2,label="%s - \n%s, %s"%(fov_first.datebeg_label, fov.datebeg_label, fov.studytyp_label))
                    else:
                        self.hmi_ax.plot_coord(arc1.coordinates(), color=pcolor ,linewidth=2)
                    pcolor=p[0].get_color()
                    self.hmi_ax.plot_coord(arc2.coordinates(), color=pcolor, linewidth=2)
                    self.hmi_ax.plot_coord(arc3.coordinates(), color=pcolor, linewidth=2)
                    self.hmi_ax.plot_coord(arc4.coordinates(), color=pcolor, linewidth=2)
                else:
                    pass
            else:
                fov_first=fov
                if i==(len(self.spice_fovs)-1) or (self.spice_fovs[i+1]).spiobs_id!=fov.spiobs_id or plot_repeated_obsid==False:
                    p=self.hmi_ax.plot_coord(arc1.coordinates(), linewidth=2, label="%s, %s"%(fov_first.datebeg_label, fov.studytyp_label))
                else:    
                    p=self.hmi_ax.plot_coord(arc1.coordinates(), linewidth=2)
                pcolor=p[0].get_color()
                self.hmi_ax.plot_coord(arc2.coordinates(), color=pcolor, linewidth=2)
                self.hmi_ax.plot_coord(arc3.coordinates(), color=pcolor, linewidth=2)
                self.hmi_ax.plot_coord(arc4.coordinates(), color=pcolor, linewidth=2)
            obs_id=fov.spiobs_id

        if plot_fov_labels==True:
            self.hmi_ax.legend(loc="upper right", prop = { "size": 15 })
        self.hmi_ax.set_title("SDO/HMI synoptic map for CR %i"%(self.CR),fontsize=20)
        self.hmi_ax.set_xlabel("Carrington longitude [deg]",fontsize=20)
        self.hmi_ax.set_ylabel("latitude [deg]",fontsize=20)
        self.hmi_ax.tick_params(axis="x", labelsize=15)
        self.hmi_ax.tick_params(axis="y", labelsize=15)      
        if save_figure==True:
                plt.savefig(figname,bbox_inches='tight')
        


    def download_simult_FSI_file(self, date_min, compartime_minutes=60):
        """
        Method to load EUI/FSI-174A file closest in time to SPICE observation, should not be used by end-user
        """
        
        delta_t = np.timedelta64(compartime_minutes, 'm')
        tmin=str(date_min)
        tmax=str(date_min+delta_t)
        print(tmin,tmax)
        
        results_fsi = Fido.search(attrs.Time(tmin, tmax),attrs.soar.Product('eui-fsi174-image'),attrs.Level(2))
        N_filesfound=len(results_fsi[0])
        print("%s files found"%(N_filesfound)) 
        if len(results_fsi[0])>0:
            print("EUI-FSI174 file closest in time is downloaded:")
            fsi_file = Fido.fetch(results_fsi[0][-1], path="%s/{file}"%(self.fsi_path))
            self.fsi_filename=fsi_file[0]
        else: 
            print("no EUI-FSI174 files found in this time interval")
        
        
    def plot_FSImap(self,filename=None):
        """
        Method to plot EUI/FSI-174A map, should not be used by end-user  
        """        
        if filename==None:
            filename=self.fsi_filename
            print("EUI-FSI filename:", filename)
        self.fsi_fig=plt.figure(figsize=(10,10))
        self.fsi_map = sunpy.map.Map(filename)
        self.fsi_ax = self.fsi_fig.add_subplot(projection=self.fsi_map)
        p=self.fsi_map.plot()
        plt.show()


    def plot_SPICE_FOV_FSI(self,plot_fov_labels=True, plot_repeated_obsid=True, save_figure=False, figname="spicefovs_test_V1-0"):
        """
        Method to plot SPICE FOV on EUI/FSI-174A map, should not be used by end-user  
        """
        i=0
        obs_id=0
        fov_last=self.spice_fovs[-1]
        
        for i, fov in enumerate(self.spice_fovs):
            point_coord1 = fov.FOV_COORDS_STH[0]
            point_coord2 = fov.FOV_COORDS_STH[1]
            point_coord3 = fov.FOV_COORDS_STH[2]
            point_coord4 = fov.FOV_COORDS_STH[3]
            arc1 = GreatArc(point_coord1, point_coord2)
            arc2 = GreatArc(point_coord2, point_coord3)
            arc3 = GreatArc(point_coord3, point_coord4)
            arc4 = GreatArc(point_coord4, point_coord1)

            if fov.spiobs_id==obs_id:
                if plot_repeated_obsid==True:
                    if i==(len(self.spice_fovs)-1) or (self.spice_fovs[i+1]).spiobs_id!=fov.spiobs_id:
                        self.fsi_ax.plot_coord(arc1.coordinates(), color=pcolor, linewidth=2,label="%s - \n%s, %s"%(fov_first.datebeg_label, fov.datebeg_label, fov.studytyp_label))
                    else:
                        self.fsi_ax.plot_coord(arc1.coordinates(), color=pcolor ,linewidth=2)
                    pcolor=p[0].get_color()
                    self.fsi_ax.plot_coord(arc2.coordinates(), color=pcolor, linewidth=2)
                    self.fsi_ax.plot_coord(arc3.coordinates(), color=pcolor, linewidth=2)
                    self.fsi_ax.plot_coord(arc4.coordinates(), color=pcolor, linewidth=2)
                else:
                    pass
            else:
                fov_first=fov
                if i==(len(self.spice_fovs)-1) or (self.spice_fovs[i+1]).spiobs_id!=fov.spiobs_id or plot_repeated_obsid==False:
                    p=self.fsi_ax.plot_coord(arc1.coordinates(), linewidth=2, label="%s, %s"%(fov_first.datebeg_label, fov.studytyp_label))
                else:    
                    p=self.fsi_ax.plot_coord(arc1.coordinates(), linewidth=2)
                pcolor=p[0].get_color()
                self.fsi_ax.plot_coord(arc2.coordinates(), color=pcolor, linewidth=2)
                self.fsi_ax.plot_coord(arc3.coordinates(), color=pcolor, linewidth=2)
                self.fsi_ax.plot_coord(arc4.coordinates(), color=pcolor, linewidth=2)
            obs_id=fov.spiobs_id

        if plot_fov_labels==True:
            self.fsi_ax.legend(loc="upper right", prop = { "size": 15 })
        if save_figure==True:
                plt.savefig(figname,bbox_inches='tight')



    def plot_SPICE_FOV(self, background_map="FSI", Carr_rot=None, plot_fov_labels=True, plot_repeated_obsid=True):
        """
        Method to plot Field-of-view (FOV) for SPICE observatons on-top of solar background map.

        Input parameters
        ----------
        background map: 
            Background map on which the SPICE FOV is plotted. Can be chosen between "FSI" or "HMI_CR":
            - "FSI" selects the EUI/FSI-174A image from the SOAR which is closest to he first observation within the selected time window   
            - "HMI_CR" selects the synoptic Carrington map of a given Carrington rotation number (=Carr_rot) from JSOC. It is mandatory to select the (correct) Carr_rot value manually (see below).   
            
        Carr_rot: 
            Carrington rotation number corresponding to the selected time window of SPICE observations. Only needed if "HMI_CR" is selected as background map.       

        plot_fov_labels:
            IF True, a legend will be plotted with the observation times and study type of the plotted SPICE FOVs

        plot_repeated_obsid: 
            If True, the FOVS of all selected SPICE observations in the given time window will be shown. Otherwise only one FOV per SPICE observation ID (SPIOBSID) will be shown. The latter is recommended for visualization of longer time periods (1 day < T < 1 Carrington rotation) to reduce the method run time.  
        
        Return
        ------
        Solar map with SPICE FOVs
        """

        if background_map=="FSI":
            date_min=self.cat_rf["DATE-BEG"].to_numpy()[0]
            self.download_simult_FSI_file(date_min, compartime_minutes=60)
            self.plot_FSImap(filename=None)
            self.plot_SPICE_FOV_FSI(plot_fov_labels, plot_repeated_obsid, save_figure=False, figname=None)

        elif background_map=="HMI_CR":
            self.plot_HMI_map(CR=Carr_rot,download_mapfile=True)#Can be changed to False if the map is already downloaded (to speed up the method).
            self.plot_SPICE_FOV_HMI(plot_fov_labels, plot_repeated_obsid, save_figure=False, figname=None)
        else:        
            print("ERROR: Please select a valid background_map (FSI or HMI_CR)")



"""
#Main Example   
cat=Catalog(release_tag=2.0)#initialize catalogue 
date1=np.datetime64('2022-03-05T00:00:00.00')#define start date of observations    
date2=np.datetime64('2022-03-05T23:59:00.00')#define end date of observations            

#plot all raster observations for 05/03/22 on synoptic Carrington map of CR 2254   
p=spice_plotfovs(cat,date_min=date1, date_max=date2, Level="L2", Studytype="Raster")    
p.plot_SPICE_FOV(background_map="HMI_CR",Carr_rot=2254, plot_repeated_obsid=True, plot_fov_labels=True)

#plot all observations for 05/03/22 on EUI-FSI174 map (closest in time to first observation). For each SPIOBSID only the first observation is plotted.  
p=spice_plotfovs(cat,date_min=date1, date_max=date2, Level="L2", Studytype="All")
p.plot_SPICE_FOV(background_map="FSI", plot_repeated_obsid=False, plot_fov_labels=True)
"""