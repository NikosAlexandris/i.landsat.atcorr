Automatising atmospheric correction of Landsat scenes

Notes
=====

* `i.landsat.toar` derives, *by default*, Spectral Reflectance values (unitless), whether uncorrected or corrected (by some of the possible DOS methods).

* `i.atcorr` treats, *by default*, input bands as Spectral Radiance.

* To make things work, either derive Spectral Radiance values via `i.landsat.toar` by instructing the `-r` flag, or let `i.atcorr` treat the input as Spectral Reflectance via its own `-r` flag!

Confusing? ;-) 

Tested for:

- Landsat8 OLI using LC81840332014226LGN00:  Works. For example `i.landsat.atcorr -r sensor=oli mapsets=. inputprefix=B.Rad. mtl=cell_misc/LC81840332014226LGN00_MTL.txt atm=3 aer=5 aod=.111 alt=-.15 --v --o`. Note, some parameters were random.

- Landsat7 ETM+ using <http://earthexplorer.usgs.gov/metadata/3372/LE70160352000091EDC00/> found in <http://grass.osgeo.org/sampledata/north_carolina/nc_spm_08_grass7.zip>

```
# i.landsat.toar likes common 'input_prefix'es
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


To Do
=====

- Add support for .met metadata files (older format of Landsat metadata files)

To test for:

- Landsat5 TM
- Landsat4 MSS
