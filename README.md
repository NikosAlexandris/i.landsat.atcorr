* Automatising atmospheric correction of Landsat scenes
*  **Work under progress**, option names for the module might change!
* Currently not working! May 2nd, 2015

Usage
=====

*To complete...*

## One Mapset per Landsat scene
Using this script, pre-requires importing Landsat scenes each in its own Mapset.
This can be performed using the import script from
<https://github.com/NikosAlexandris/i.landsat.import>. The latter copies the
respective acquisition metadata file (MTL.txt) in the `cell_misc` directory of
the corresponding Mapset. 


Notes
=====

An overview of options to get *corrected* spectral reflectance values:

```
+------------------------------------------------------------------------------+
|                                                                              |
| Digital Numbers                                                              |
|        |                                                                     |
|  +-----v-----+                                                               |
|  |  i.*.toar | ---> Reflectance                                              |
|  +-----+-----+     (uncorrected)~~~(DOS methods)--+                          |
|        |                 +                        |                          |
|    (-r flag)         (-r flag)                    +--> "Corrected"           |
|        |                 |                        |     Reflectance          |
|        v           +-----v----+                   |                          |
|     Radiance ------> i.atcorr +-------------------+                          |
|                    +----------+                                              |
|                                                                        ;-)   |
+------------------------------------------------------------------------------+
```

* `i.landsat.atcorr` *requires* the metadata filename's prefix to be identical to the name of the *current* Mapset.

* `i.landsat.toar` derives, *by default*, Spectral Reflectance values (unitless, ranging in [0,1]), whether uncorrected or corrected (by some of the possible DOS methods).

* `i.atcorr` treats, *by default*, input bands as Spectral Radiance.

* To make things work,
  * either derive Spectral Radiance values via `i.landsat.toar` by instructing the `-r` flag,
  * or let `i.atcorr` treat the input as Spectral Reflectance via its own `-r` flag!

* The value for aerosols optical depth (AOD), is set to `0.111` for winter and `0.222` for summer acquisitions to get going.

* Tested for Landsat8 OLI, Landsat7 ETM+, Landsat5 TM

Examples
========

The following are simply proof-of-concept examples. Parameters fed, such as `aod=` are arbitrarily chosen.

- Landsat8 OLI using LC81840332014226LGN00:  Works. For example `i.landsat.atcorr -r sensor=oli mapsets=. inputprefix=B.Rad. mtl=cell_misc/LC81840332014226LGN00_MTL.txt atm=3 aer=5 aod=.111 alt=-.15 --v --o`.

- Landsat7 ETM+ using <http://earthexplorer.usgs.gov/metadata/3372/LE70160352000091EDC00/> found in <http://grass.osgeo.org/sampledata/north_carolina/nc_spm_08_grass7.zip>

```
# i.landsat.toar likes common 'input_prefix'es and a _single_ band numbering scheme
g.copy rast=lsat7_2000_10,lsat7_2000_1
g.copy rast=lsat7_2000_20,lsat7_2000_2
g.copy rast=lsat7_2000_30,lsat7_2000_3
g.copy rast=lsat7_2000_40,lsat7_2000_4
g.copy rast=lsat7_2000_50,lsat7_2000_5
g.copy rast=lsat7_2000_60,lsat7_2000_6

# we need a 62 also -- it's missing, thus
g.copy rast=lsat7_2000_61,lsat7_2000_62
g.copy rast=lsat7_2000_70,lsat7_2000_7
g.copy rast=lsat7_2000_80,lsat7_2000_8

# convert DN to Spectral Radiance values
# use custom lsat7_2000_MTL.txt file!
i.landsat.toar -r input_prefix=lsat7_2000_ metfile=landsat_MTL.txt method=uncorrected output_prefix=lsat7_2000.Rad. product_date=2000-03-31

# check output
for Band in $(g.list type=rast pattern=*Rad*); do r.info -r ${Band}; done

min=41.5212598425197
max=191.6
min=18.3633858267717
max=196.5
min=7.43307086614173
max=152.9
min=-2.19212598425197
max=206.205511811024
min=-1
max=31.06
min=6.23905511811023
max=11.1363779527559
min=6.66003937007874
max=9.3759842519685
min=-0.35
max=10.8
min=4.08031496062992
max=243.1

# apply 6s algorithm
i.landsat.atcorr sensor=etm mapsets=current inputprefix=lsat7_2000.Rad. outputsuffix=AtmCor metafile=landsat_MTL.txt atm=3 aer=1 vis=11 aod=.111 alt=-.1

# check output -- Spectral Reflectance (unitless, ranging in [0,1])
for Band in $(g.list type=rast pattern=*AtmCor*); do r.info -r ${Band}; done

min=0.0009810156
max=1
min=0.0006285605
max=1
min=0.001880044
max=1
min=0.001980251
max=1
min=4.898617e-14
max=1
min=0.001096191
max=1
min=-nan
max=-nan


# something went wrong with the last band... !?

# apply colors
for Band in $(g.list type=rast pattern=*AtmCor*); do r.colors ${Band} color=grey1.0; done

# then check visually...
```

- Landsat5 TM

```
# outside of grass
grass70 -c LT51830332007136MOR00/L5183033_03320070516_B10.TIF /grassdb/landsat_utm_z34n

# inside grass (PERMANENT Mapset), import bands (will copy MTL file in cell_misc)
python import_landsat_custom.py LT51830332007136MOR00

# exit & re-launch grass session (or change mapset!)
exit
grass70 landsat_utm_z34n/LT51830332007136MOR00/

# rename bands -- i.landsat.toar likes single-band-number-indices!
g.copy rast=B10,B1
!!:gs/1/2
!!:gs/2/3
!!:gs/3/4
!!:gs/4/5
!!:gs/5/6
!!:gs/6/7

# check range of DN
for B in `g.list type=rast pat=[B]*[1234567]`; do r.info -r ${B}; done

min=0
max=255
min=0
max=255
min=0
max=255
min=0
max=255
min=0
max=255
min=0
max=220
min=0
max=255

# convert to spectral radiance (remember: MTL file stored in cell_misc)
i.landsat.toar input_prefix=B output_prefix=Rad. metfile=/geo/grassdb/landsat_utm_z34n/LT51830332007136MOR00/cell_misc/L5183033_03320070516_MTL.txt

# check output!
for B in `g.list type=rast pat=[R]*[1234567]`; do r.info -r ${B}; done

min=-0.00279458552443127
max=0.354838819878444
min=-0.00559605803399942
max=0.719211683947109
min=-0.00270894064952713
max=0.611248146559968
min=-0.0052442312574179
max=0.767533184032686
min=-0.00619195664744627
max=0.505397542575344
min=203.371307953013
max=328.364927858343
min=-0.00669027308052299
max=0.735930038857529

# loop i.atcorr over all bands
i.landsat.atcorr sensor=tm input_prefix=Rad. output=AtmCor metafile=/geo/grassdb/landsat_utm_z34n/LT51830332007136MOR00/cell_misc/L5183033_03320070516_MTL.txt atm=2 aer=1 visual=11 aod=.111 alt=.1 --o --v

# check output ranges
for B in `g.list type=rast pat=*Atm*`; do r.info -r ${B}; done

min=1.58162e-07
max=0.001280316
min=8.194314e-07
max=0.002430856
min=1.210253e-06
max=0.002343489
min=2.804616e-06
max=0.002441876
min=3.624363e-07
max=0.01023893
min=1.828974e-05
max=0.04095656
```

To Do
=====

- Does `i.atcorr` support the old `.met` files properly?

To test for:

- Landsat4 MSS

- Do entries in i.atcorr for mss cover all of the mss'es? Official band designations differ for "mss1-3" and "mss4-5". 

References
==========

- <http://landsat.usgs.gov/band_designations_landsat_satellites.php>

- To add more
