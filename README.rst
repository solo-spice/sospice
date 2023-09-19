sospice: Python data analysis tools for Solar Orbiter/SPICE
===========================================================

|Latest version| |Docs| |python| |CI|

.. |Latest version| image:: https://img.shields.io/pypi/v/sospice.svg
   :target: https://pypi.org/project/sospice/
   :alt: Latest version on PyPI
.. |Docs| image:: https://readthedocs.org/projects/sospice/badge/?version=latest
    :target: https://sospice.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. |python| image:: https://img.shields.io/pypi/pyversions/sunpy
   :alt: PyPI - Python Version
.. |CI| image:: https://github.com/solo-spice/sospice/actions/workflows/python-package.yml/badge.svg?branch=main
   :target: https://github.com/solo-spice/sospice/actions/workflows/python-package.yml

`SPICE <https://spice.ias.u-psud.fr/>`__ is an extreme-UV imaging
spectrometer on board the `Solar
Orbiter <http://sci.esa.int/solar-orbiter/>`__ mission.
A generic SPICE data analysis user’s manual (including Python and IDL
tips) is available `on the IAS
wiki <https://spice-wiki.ias.u-psud.fr/doku.php/data:data_analysis_manual>`__.

``sospice`` is intended to be a simple way of accessing all necessary
instrument-specific functionalities required for day-to-day SPICE data analysis,
in complement to more generic Python packages such as
`sunpy <https://sunpy.org/>`__ and
`sunraster <https://github.com/sunpy/sunraster/>`__.

This package is in its early stages of development. Please see the
`issues <https://github.com/solo-spice/sospice/issues>`__ to see how you
can contribute.

Documentation for this package is available on `Read the Docs <https://sospice.readthedocs.io/en/latest/>`__.


``sospice`` functionalities
---------------------------

-  Calibration: ``calibrate``

   -  ``spice_error``: Computation of uncertainties on data, coming from
      different noise components.

- Catalog: ``catalog``

   -  ``Catalog``: access and read catalog, find files in catalog.
   -  ``Release``: find and access releases.
   -  ``FileMetadata``: file metadata and download.

-  Instrument modelling: ``instrument_modelling``

   -  ``Spice``: instrument calibration parameters, effective area,
      quantum efficiency…
   -  ``Study``: study parameters.
   -  ``Observation``: a SPICE observation with some study (including
      low-level functions used to compute the uncertainties on the
      data).

Package philosophy
------------------

We want ``sospice`` to be:

-  Convenient to install. It is installable by ``pip`` and it is
   published on `PyPI <https://pypi.org/>`__
-  Useful, providing a single package for all SPICE-specific steps of
   your data analysis.
-  Easy to use, with simple interface functions to operations performed
   by lower-level functions.
-  Well documented. We use ``sphinx`` to build documentation from the
   Python docstrings.
-  Thoroughly tested. We use ``pytest`` and aim at a high test coverage
   ratio. Tests are run automatically with Github actions.
-  Well integrated in the `SunPy <https://sunpy.org>`__ ecosystem. In
   the long term, we aim at getting the `SunPy affiliated
   package <https://sunpy.org/project/affiliated>`__ status.

Contributions from the community are welcome, in particular as
`issues <https://github.com/solo-spice/sospice/issues>`__ or `pull
requests <https://github.com/solo-spice/sospice/pulls>`__.

Citation
--------

See the `citation <sospice/CITATION.rst>`__ file.
