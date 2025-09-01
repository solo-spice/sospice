from astropy.io import fits
import copy
import warnings

def pix_desat(hdul, nbHdu = None, hduName = None, thr = None):
    """
    Replace Nan from saturated elements by estimated value, depending on the saturated elements contribution

    Parameters
    ----------
    hdul: List of hdus
    nbHdu: (optionnal) None or List of int 
            nbHdu or hduName, will only process nbHdu if both
            Indicates the numbers of the hdus that must be processed (starting from 0)
            Processes all hdus if None
    hduName: (optionnal) None or List of string
            nbHdu or hduName, will only process nbHdu if both
            Indicates the names of the hdus that must be processed
    thr: (optionnal) None or float between 0 and 1
            Pixels are replaced only if the saturated elements contribution is under or equal to the threshold
            if None the threshold is set to 1 (all pixels are retrieved)

    Return
    ------
    hdu list
        A new hdu list with the desaturated pixels
        Contains only 1 hdu (the one processed) if the nbHdu option is selected
    """
    
    hdul_corr = copy.deepcopy(hdul)

    if nbHdu is not None:
        if all(0 <= i < len(hdul) for i in nbHdu):
            hdul_corr = [hdul_corr[nbH] for nbH in nbHdu]
        else:
            warnings.warn("Wrong Hdu number, full hdu list processed")
    elif hduName is not None:
            try:
                hdul_corr = [hdul_corr[name] for name in hduName]
            except KeyError:
                warnings.warn("Unknown hdu name, full hdu list processed")

    if thr is None or thr<0:
        thr = 1 #takes all estimated pixels
    
    for ii, hdu in enumerate(hdul_corr):

        # Select only Image HDU
        if isinstance(hdu, (fits.PrimaryHDU, fits.ImageHDU)) : 
            
            Head = hdu.header 

            if "PIXLISTS" in Head: 

                print("PIX saturation detected")
                
                tabName = Head['PIXLISTS'].split(';')[0]
                if tabName in hdul:
                    table_hdu = hdul[tabName]
                    
                    dataTab = table_hdu.data

                    for pix in dataTab:
                        if pix[5]<=thr:
                            hdu.data[int(pix[3])-1,int(pix[2])-1,int(pix[1])-1,int(pix[0])-1] = pix[4]
                else:
                    warnings.warn("Missing associated table")

            else:
                warnings.warn("No saturated pixel")
        

    return hdul_corr
