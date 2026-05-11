0.0.9 (2026-05-09)
==================

New Features
------------

- EUI/FSI background image for FOV plots is cached in user's directory. Also, the target time and
  tolerance for finding this background image can now be set by the user. (`#47 <https://github.com/solo-spice/sospice/pull/47>`__)
- Compute mid-time for a SPICE observation. (`#54 <https://github.com/solo-spice/sospice/pull/54>`__)
- All files from a SPICE catalog can be downloaded at once (up to a user-defined maximum number of files). (`#57 <https://github.com/solo-spice/sospice/pull/57>`__)
- Implement SPICE colormaps depending on temperature. (`#72 <https://github.com/solo-spice/sospice/pull/72>`__)


0.0.8 (2024-02-02)
==================

New Features
------------

- Add local sigma clipping. (`#35 <https://github.com/solo-spice/sospice/pull/35>`__)
- Add field of view plotting on a background (including a SDO/HMI synoptic map or a Solar Orbiter/EUI/FSI image). (`#43 <https://github.com/solo-spice/sospice/pull/43>`__)


Internal Changes
----------------

- Update package versions and CI tests Python versions and Github actions. (`#1 <https://github.com/solo-spice/sospice/pull/1>`__)


0.0.7 (2023-09-19)
==================

Removals
--------

- Drop Python<3.8 support.


New Features
------------

- Take into account effect of dark map subtraction on read and dark noises. (`#29 <https://github.com/solo-spice/sospice/pull/29>`__)
- Get wavelength ranges (when available) from catalog. (`#33 <https://github.com/solo-spice/sospice/pull/33>`__)


Bug Fixes
---------

- Take dark map subtraction effect on read and dark noises. (`#29 <https://github.com/solo-spice/sospice/pull/29>`__)
- Fix non-update of cache when cache update was requested. (`#33 <https://github.com/solo-spice/sospice/pull/33>`__)


Internal Changes
----------------

- Configure ``towncrier``. (`#30 <https://github.com/solo-spice/sospice/pull/30>`__)
- Make ``FileMetadata`` accept a one-row ``DataFrame`` instead of a ``Series``. (`#33 <https://github.com/solo-spice/sospice/pull/33>`__)
- Save version information properly, and then remove unnecessary build dependencies.
