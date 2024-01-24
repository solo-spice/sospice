Utilities
=========

Local sigma clipping
--------------------

This provides a version of
`astropy.stats.sigma_clip <https://docs.astropy.org/en/stable/api/astropy.stats.sigma_clip.html>`__
working on a local neighbourhood.

Plotting field-of-views over a background map
----------------------------------------------------

Once observations are selected from a ``Catalog``, their Field-Of-Views (FOVs) can be plotted using ``plot_fovs_with_background()``. Different background maps can be selected: maps with some specific data (e.g. a HMI synoptic map or Solar Orbiter/EUI/FSI), a blank map with some projection (in development), or any map already plotted by the user.

After

.. code:: python

    from sospice import Catalog, plot_fovs_with_background,
    cat = Catalog(release_tag="4.0")

one can select for example all files for which ``DATE-BEG`` is on a given day

.. code:: python

    observations = cat.find_files(date_min="2022-03-08", date_max="2022-03-09", level="L2")

and then plot them either with a HMI synoptic map as background

.. code:: python

   plot_fovs_with_background(observations, "HMI_synoptic")

or with EUI/FSI data

.. code:: python

    plot_fovs_with_background(observations, "EUI/FSI")

``plot_fovs_with_background()`` uses the lower-level methods of the ``FileMetadata`` and ``Catalog`` classes to compute and plot the FOVs. Advanced users can produce custom FOV plots using these methods and their options.
