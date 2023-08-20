Calibration
===========

Error computation
-----------------

For a given spectral window in a SPICE L2 file, represented as an ``astropy.io.fits`` HDU object, the average dark current as well as the uncertainties coming from noises can be obtained with

.. code-block:: python

   dark_noise, sigma = spice_error(hdu)

``sigma`` is a dictionary containing the dark current noise, the background signal noise, the read noise, and the photon noise, and the total of these noise components. Values are given for each pixel when relevant.
