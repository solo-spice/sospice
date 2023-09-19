0.0.7 (2023-09-19)
===========================================

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
