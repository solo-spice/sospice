from astropy.io import fits
import copy
import warnings

def pix_desat(hdul, nbHdu = None, thr = None):
    """
    Replace Nan from saturated elements by estimated value, depending on the saturated elements contribution

    Parameters
    ----------
    hdul: List of hdus
    nbHdu: (optionnal) None or int 
            Indicates the number of the hdu that must be processed (starting from 0)
            Processes all hdus if None
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
        # only 1 hdu
        if nbHdu < len(hdul) and nbHdu >= 0:
            hdul_corr = [hdul_corr[nbHdu]]
        else:
            warnings.warn("Wrong Hdu number")

    if thr is None or thr<0:
        thr = 1 #takes all estimated pixels
    
    for hdu in enumerate(hdul_corr) :

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
                print("No saturated pixel")
        

    return hdul_corr
