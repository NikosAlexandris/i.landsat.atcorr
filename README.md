Automatising atmospheric correction of Landsat scenes

Notes
=====

* `i.landsat.toar` derives, *by default*, Spectral Reflectance values (unitless), whether uncorrected or corrected (by some of the possible DOS methods).

* `i.atcorr` treats, *by default*, input bands as Spectral Radiance.

* To make things work, either derive Spectral Radiance values via `i.landsat.toar` by instructing the `-r` flag, or let `i.atcorr` treat the input as Spectral Reflectance via its own `-r` flag!

Confusing? ;-) 

Tested for:

- Landsat8 OLI using LC81840332014226LGN00:  Works. For example `i.landsat.atcorr -r sensor=oli mapsets=. inputprefix=B.Rad. mtl=cell_misc/LC81840332014226LGN00_MTL.txt atm=3 aer=5 aod=.111 alt=-.15 --v --o`. Note, some parameters were random.

To Do
=====

- Add support for .met metadata files (older format of Landsat metadata files)

To test for:

- Landsat7 ETM+
- Landsat5 TM
- Landsat4 MSS
