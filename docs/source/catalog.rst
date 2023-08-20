Catalogs and releases
=====================

SPICE data release management
-----------------------------

SPICE data files are part of `data releases <https://spice.ias.u-psud.fr/spice-data/>`__. Released files are sent to the `Solar Orbiter Archive <http://soar.esac.esa.int/>`__, but these files can have several successive versions; a data release allows freezing the versions of different released files, and then makes it easy to reference file versions used for a specific analysis (using the release DOI).

The ``Release`` module of ``sospice`` helps access these releases and the file catalogs associated to them.
The associated functions are mostly meant to be used as back-end for the ``Catalog`` module, it is unlikely that you would like to use them directly.

.. code-block:: python

   from sospice import Release
   release = Release("2.0")   # a specific release
   release = Release()        # the latest release
   release.tag
   # Output: "3.0"
   release.url
   # Output: "https://spice.osups.universite-paris-saclay.fr/spice-data/release-3.0/"
   release.is_latest
   # Output: True


SPICE data catalog management
-----------------------------

Each release contains a catalog of its files, as a CSV table, similar to the private CSV catalog of the latest versions of all files produced by the instrument team.

The ``Catalog`` module of ``sospice`` helps access and read these catalogs, and find data in them.

Data release catalogs are accessed automatically online from their release tag. As catalog files can be quite large, they are cached locally (using ``astropy.utils.data``).

.. code-block:: python

   from sospice import Catalog
   catalog = Catalog(release_tag="2.0")

It is also possible to read a local file containing a SPICE catalog.

There are several functions to search files in a catalog, by keyword (including generic queries on keywords), by date range, or to find the closest file to a given date. The most generic search function is ``find_files()``, e.g.:

.. code-block:: python

   # Files with some constraints on headers
   result = catalog.find_files(
      query="LEVEL='L2' & NAXIS1 < 100 & 600 < CRVAL1 < 700"
   )
   # Closest file to some date, for a given SOOP
   result = catalog.find_files(
      soopname="L_SMALL_HRES_HCAD_Slow-Wind-Connection",
      closest_to_date="2022-03-21"
   )
   # All files for a SOOP, in some time range
   result = catalog.find_files(
      soopname="L_SMALL_HRES_HCAD_Slow-Wind-Connection",
      date_min="2022-03-01",
      date_max="2022-04-01"
   )

The ``Catalog`` class derives from the ``pandas.DataFrame`` class, and so benefits from the ``pandas`` library functionalities.


SPICE file metadata
-------------------

A row in a ``Catalog`` object contains the metadata for one SPICE data file.
It is a ``pandas.Series`` object, and it can be transformed into a ``FileMetadata`` object, e.g.:

.. code-block:: python

   from sospice import FileMetadata
   metadata = FileMetadata(result.iloc[0])


Downloading files
-----------------

From a ``FileMetadata``, it is possible to download the data file (in FITS format).
Various options are available to download the file from a SPICE release file repository, from some other online file tree, or from SOAR.
The file can then be put at any location on disk (optionally keeping the original LEVEL/year/month/day directory structure):

.. code-block:: python

   metadata.download_file()  # no argument → download from SOAR

These downloads are internally managed using the ``parfive`` package, this provides the option to enqueue different files for download, and then to run the downloads in parallel. This example shows how to download the files corresponding to the first 10 rows of ``results`` from release 2.0 (from which the catalog has been extracted):

.. code-block:: python

   from parfive import Downloader
   downloader = Downloader()
   result.iloc[:10].apply(
      lambda row: FileMetadata(row).download_file(
         "/tmp/spice-files",  # base directory
         release="2.0",
         downloader=downloader
      ),
      axis=1
   )
   downloader.download()

In any case, files are not re-downloaded if they already exist (please remove them before re-downloading them if an update is really necessary); released files should never be modified anyways (although there will probably be newer versions in the following releases).

Alternatively, files can be downloaded to or taken from the local ``astropy.utils.data`` cache using ``FileMetadata.cache_file()``.
