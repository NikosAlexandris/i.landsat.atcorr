#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MODULE:         i.landsat.atcorr

AUTHOR(S):      Nikos Alexandris <nik@nikosalexandris.net>
                Converted from a bash shell script (written in Feb. 2013)
                Trikala, Nov. 2014
                Based on a script provided by Yann Chemin

PURPOSE:        Scripting atmospheric correction of Landsat5 TM acquisitions

"""

#%Module
#%  description: Atmospheric correction of Landsat scenes. Acquisitions should be imported in GRASS' database in a one Mapset per scene manner! 
#%  keywords: landsat, atmospheric correction
#%End

#%flag
#%  key: r
#%  description: Input is Spectral Radiance
#%end

#%flag
#%  key: e
#%  description: Equalize histogram of output bands (r.colors -e)
#%end

#%option
#% key: sensor
#% key_desc: Sensor
#% type: string
#% label: Landsat sensor
#% description: Landsat sensor selecting spectral conditions indexing
#% options: tm,mss,etm,oli
#% descriptions: tm;Landsat5 Thematic Mapper;mss;Landsat5 Multi-Spectral Scanner;etm;Landsat7 Enhanced Thematic Mapper;oli;Landsat8 OLI
#% required: yes
#% multiple: no
#%end

#%option
#% key: mapsets
#% key_desc: Mapsets
#% type: string
#% label: Mapsets corresponding to scenes
#% description: Scenes to process
#% options: all,.,selected
#% descriptions: all;All mapsets except of PERMANENT;.;Current mapset;selected;Only selected mapsets
#% answer: all
#% required: no
#%end

#%option G_OPT_R_BASENAME_INPUT
#% key: inputprefix
#% key_desc: prefix string
#% type: string
#% label: Prefix of input bands
#% description: Landsat5 TM bands imported in GRASS' data base begin with this prefix
#% required: yes
#%end

#%option G_OPT_R_BASENAME_OUTPUT
#% key: outputsuffix
#% key_desc: suffix string
#% type: string
#% label: Suffix for output image(s)
#% description: Names of atmospherically corrected Landsat5 TM bands image(s) will end with this suffix
#% required: yes
#% answer: AtmCor
#%end

#%option
#% key: mtl
#% key_desc: MTL file
#% type: string
#% label: Acquisition's metadata file (MTL)
#% description: Metadata file that accompanies the Landsat acquisition
#% required: yes
#%end

#%option
#% key: atm
#% key_desc: index
#% type: integer
#% label: Atmospheric model
#% description: Index of the atmospheric model
#% options: 0,1,2,3,4,5,6,7,8
#% descriptions: 0;no gaseous absorption;1;tropical;2;milatitude summer;3;midlatitude winter;4;subarctic summer;5;subarctic winter;6;us standard 62;7;user defined;8;user defined
#% guisection: Parameters
#% required: yes
#%end

#%option
#% key: aer
#% key_desc: index
#% type: integer
#% label: Aerosols model
#% description: Index of the aerosols model
#% options: 0,1,2,3,4,5,6,7,8,9,10,11
#% descriptions: 0;no aerosols;1;continental;2;maritime;3;urban;4;shettle;5;biomass;6;stratospheric;7;user defined;8;user defined;9;user defined;10;user defined;11;user defined
#% guisection: Parameters
#% required: yes
#%end

#%option
#% key: vis
#% key_desc: distance or concentration
#% type: double
#% label: Visibility
#% description: Visibility [km] or Aerosols Optical Depth at 550nm (refer to i.atcorr's manual)
#% guisection: Parameters
#% required: yes
#%end

#%option
#% key: aod
#% key_desc: concentration
#% type: double
#% label: AOD
#% description: Aerosols Optical Depth at 550nm (refer to i.atcorr's manual)
#% guisection: Parameters
#% required: no
#%end

#%option
#% key: alt
#% key_desc: altitude
#% type: double
#% label: Target or Sensor Altitude
#% description: Mean target or sensor altitude (refer to i.atcorr's manual)
#% guisection: Parameters
#% required: yes
#%end

#%option
#% key: elevation
#% key_desc: elevation map
#% type: double
#% label: Elevation map
#% description: Elevation raster map as an input for i.atcorr (refer to i.atcorr's manual)
#% guisection: Optional maps
#% required: no
#%end

#%option
#% key: visibility
#% key_desc: visibility map
#% type: double
#% label: Visibility map
#% description: Visibility raster map as an input for i.atcorr (refer to i.atcorr's manual)
#% guisection: Optional maps
#% required: no
#%end

# required librairies -------------------------------------------------------
import os
import sys
import atexit
import grass.script as grass
from grass.pygrass.modules.shortcuts import general as g
from parameters import Parameters

msg = '''Usage: $0 [Meant Target Elevation] [AOD]\n
      Note, the script has to be eXecuted from the directory that contains\n
      the *MTL.txt metadata and within from the GRASS environment!'''

# constants -----------------------------------------------------------------
geo = {'tm': 7, 'mss': 7, 'etm': 8, 'oli': 18}  # Geometrical conditions
xpp = -1000  # Satellite borne [-1000]

# Spectral conditions index
sensors = {
'tm':  {1: 25, 2: 26, 3: 27, 4: 28, 5: 29, 7: 30},
'mss': {1: 31, 2: 32, 3: 33, 4: 34},
'etm': {1: 61, 2: 62, 3: 63, 4: 64, 5: 65, 7: 66, 8: 67},
'oli': {1: 115, 2: 116, 3: 117, 4: 118, 5: 119, 6: 120, 7: 121, 8: 122, 9: 123}
}


# globals ------------------------------------------------------------------
g.message(msg)
rad_flg = ''


# helper functions ----------------------------------------------------------
def cleanup():
    """Clean up temporary maps"""
    grass.run_command('g.remove', flags='f', type="rast",
                      pattern='tmp.%s*' % os.getpid(), quiet=True)


def run(cmd, **kwargs):
    """Pass quiet flag to grass commands"""
    grass.run_command(cmd, quiet=True, **kwargs)


def main():
    """ """
    sensor = options['sensor']
    
    mapsets = options['mapsets']
    prefix = options['inputprefix']
    suffix = options['outputsuffix']

    mtl = options['mtl']
    atm = int(options['atm'])  # Atmospheric model [index]
    aer = int(options['aer'])  # Aerosols model [index]

    vis = options['vis']  # Visibility [km]
    aod = options['aod']
    if not aod:
        aod = None
    else:
        aod = float(options['aod'])  # Aerosol Optical Depth at 550nm

    xps = options['alt']  # Mean Target Altitude [negative km]
    if not xps:
        msg = "Note, this value will be overwritten if a DEM raster has been "\
              "defined as an input!"
        g.message(msg)

    elevation = options['elevation']
    visibility = options['visibility']

    radiance = flags['r']
    if radiance:
        global rad_flg
        rad_flg = 'r'
    else:
        rad_flg = ''

    # If the scene to be processed was imported via the (custom) python
    # Landsat import script, then, Mapset name == Scene identifier

    mapset = grass.gisenv()['MAPSET']
    if mapset == 'PERMANENT':
        grass.fatal(_('Please change to another Mapset than the PERMANENT'))

#    elif 'L' not in mapset:
#        msg = "Assuming the Landsat scene(s) ha-s/ve been imported using the "\
#              "custom python import script, the Mapset's name *should* begin "\
#              "with the letter L!"
#        grass.fatal(_(msg))

    else:
        mtl = mapset + '_MTL.txt'
        result = grass.find_file(element='cell_misc', name=mtl, mapset='.')
        if not result['file']:
            grass.fatal("The metadata file <%s> is not in GRASS' data base!"
                        % mtl)
        else:
            mtl = result['file']

    # -----------------------------------------------------------------------
    # Acquisition's metadata
    # -----------------------------------------------------------------------

    msg = "Acquisition metadata for 6S code (line 2 in Parameters file)\n"

    # Month, day
    date = grass.parse_command('i.landsat.toar', flags='p',
                               input='dummy', output='dummy',
                               metfile=mtl, lsatmet='date')
    mon = int(date['date'][5:7])  # Month of acquisition
    day = int(date['date'][8:10])  # Day of acquisition

    # GMT in decimal hours
    gmt = grass.read_command('i.landsat.toar', flags='p',
                             input='dummy', output='dummy',
                             metfile=mtl, lsatmet='time')
    gmt = float(gmt.rstrip('\n'))

    # Scene's center coordinates
    cll = grass.parse_command('g.region', flags='clg')
    lon = float(cll['center_long'])  # Center Longitude [decimal degrees]
    lat = float(cll['center_lat']) # Center Latitude [decimal degrees]

    msg += str(mon) + ' ' + str(day) + ' ' + str(gmt) + ' ' + \
        str(lon) + ' ' + str(lat)
    g.message (msg)

    # -----------------------------------------------------------------------
    # Mapsets are Scenes. Read'em all!
    # -----------------------------------------------------------------------

    if mapsets == 'all':
        scenes = grass.mapsets()

    elif mapsets == '.':
        scenes = mapset

    else:
        scenes = mapsets.split(',')

    if 'PERMANENT' in scenes:
        scenes.remove('PERMANENT')

    # access only to specific mapsets!
    

    for scene in scenes:
        
        msg = "\n|* Performing atmospheric correction for scene:  %s" % scene
        g.message(msg)

        # ensure access only to *current* mapset
        run('g.mapsets', mapset='.', operation='set')

        # scene's basename as in GRASS' db
        basename = grass.read_command('g.mapset', flags='p')
        msg = "Processing scene:  %s" % basename
        g.message(msg)

        # loop over Landsat bands in question
        for band in sensors[sensor].keys():

            inputband = prefix + str(band)
            msg = "\n|> Processing band:  %s" % inputband
            g.message(msg)

            """
            Things to check:
            
            # elaborate on Visibillity -- lines below from YannC's code
            # # vis_list=(10 10 8 9.7 15 8 7 10 10 9.7 12 9.7 7 12 12 12 3 15 12 9.7 6 15)
            # # vis_len=${#vis_list[*]}
            # # echo $vis_len
            # # i=0
            
            # AOD_Winter=0.111
            # AOD_Summer=0.222
            # AOD="${AOD_Winter}" # set to winter AOD
            #   if [ ${Month} -gt 4 ] && [ ${Month} -lt 10 ]; # compare month of acquisition
            #       then AOD="${AOD_Summer}"  # set to summer AOD if...
            #   fi
            """

            # Generate the parameterization file (icnd_landsat5)
            p6s = Parameters(geo=geo[sensor],
                       mon=mon, day=day, gmt=gmt, lon=lon, lat=lat,
                       atm=atm,
                       aer=aer,
                       vis=vis,
                       aod=aod,
                       xps=xps, xpp=xpp,
                       bnd=sensors[sensor][band])

            
            dst_dir = grass.gisenv()['GISDBASE'] + \
            '/' + grass.gisenv()['LOCATION_NAME'] + \
            '/' + grass.gisenv()['MAPSET'] + \
            '/cell_misc/'

            # ========================================== Temporary files ====
            tmpfile = grass.tempfile()  # replace with os.getpid?
            tmp = "tmp." + grass.basename(tmpfile)  # use its basename
            tmp_p6s = grass.tempfile()  # ASCII file

            tmp_cor_out = "%s_cor_out" % tmp  # HPF image
            # Temporary files ===============================================

            p6s.export_ascii(tmp_p6s)

            # Process band-wise atmospheric correction with 6s
            msg = "Using the following parameters:\n\n"
            msg += p6s.parameters
            g.message(msg)

            # ---------------------------------------------------------------
            # Applying 6S Atmospheric Correction algorithm
            # ---------------------------------------------------------------

            if visibility:
                pass

            if elevation:
                grass.debug("Now atcorring")
                """Using an elevation map.
                Attention: does the elevation cover the area of the images?"""
#                run('i.atcorr', flags=rad_flg,
#                    input=prefix_band,
#                    range=(0,1),
#                    elevation=elevation,
#                    parameters=tmp_p6s,
#                    output=tmp_cor_out,
#                    rescale=(0,1))
                pass

            else:
                grass.debug("Now atcorring")
                """ """
                print rad_flg
                print "******"
                print inputband
                print tmp_p6s
                print tmp_cor_out

                print "ATMCOR-ing band: ", inputband
                run('i.atcorr',
                    input=inputband,
                    parameters=tmp_p6s,
                    output=tmp_cor_out)

            # inform about output's range?
            run('r.info', flags='r', map=tmp_cor_out)

        # add suffix to basename & rename end product
#        cor_nam = ("%s.%s" % (msx.split('@')[0], outputsuffix))
            run('g.rename', rast=(tmp_cor_out, "ATMCOR_TEST"))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
