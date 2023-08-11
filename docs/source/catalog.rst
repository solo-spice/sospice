Catalogs and releases
=====================

SPICE data release management
-----------------------------

SPICE data files are part of `data releases <https://spice.ias.u-psud.fr/spice-data/>`__. Released files are sent to the `Solar Orbiter Archive <http://soar.esac.esa.int/>`__, but these files can have several successive versions; a data release allows freezing the versions of different released files, and then makes it easy to reference file versions used for a specific analysis (using the release DOI).

The ``Release`` module of ``sospice`` helps access these releases and the file catalogs associated to them.
The associated functions are mostly meant to be used as back-end for the ``Catalog`` module, it is unlikely that you would like to use them directly.

.. code-block:: python

   from sospice import Release
   release = Release('2.0')   # a specific release
   release = Release()        # the latest release
   release.tag
   # Output: '3.0'
   release.url
   # Output: 'https://spice.osups.universite-paris-saclay.fr/spice-data/release-3.0/'
   release.is_latest
   # Output: True


SPICE data catalog management
-----------------------------

Each release contains a catalog of its files, as a CSV table, similar to the private CSV catalog of the latest versions of all files produced by the instrument team.

The ``Catalog`` module of ``sospice`` helps access and read these catalogs, and find data in them.

Data release catalogs are accessed automatically online from their release tag. As catalog files can be quite large, they are cached locally (using ``astropy``).

.. code-block:: python

   from sospice import Catalog
   catalog = Catalog(release_tag='2.0')

It is also possible to read a local file containing a SPICE catalog.

There are several functions to search files in a catalog, by keyword (including generic queries on keywords), by date range, or to find the closest file to a given date. The most generic search function is ``find_files()``, e.g.:

.. code-block:: python

   result = catalog.find_files(query="LEVEL=='L2' & NAXIS1 < 100 & 600 < CRVAL1 < 700")
   result = catalog.find_files(soopname='L_SMALL_HRES_HCAD_Slow-Wind-Connection', closest_to_date='2022-03-21')
