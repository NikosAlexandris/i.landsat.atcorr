#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MODULE:         i.landsat5.atcorr

AUTHOR(S):      Nikos Alexandris <nik@nikosalexandris.net>
                Converted from a bash shell script (written in Feb. 2013)
                Trikala, Nov. 2014
                Based on a script provided by Yann Chemin

PURPOSE:        Scripting atmospheric correction of Landsat5 TM acquisitions

"""

#%Module
#%  description: Scripting atmospheric correction of Landsat5 acquisitions
#%  keywords: landsat, atmospheric correction
#%End

#%flag
#%  key: r
#%  description: Flag for Radiance as input
#%end

#%flag
#%  key: e
#%  description: Equalize histogram of output bands (r.colors -e)
#%end

#%option
#% key: mapsets
#% key_desc: Mapsets
#% type: string
#% label: Mapsets corresponding to scenes
#% description: Mapsets, corresponding to Landsat5 TM scenes, for which to perform atmospheric correction
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
#% answer: hpf
#%end

#%option
#% key: mtl
#% key_desc: MTL file
#% type: string
#% label: Acquisition's metadata file (MTL)
#% description: Landsat5 TM bands imported in GRASS' data base begin with this prefix
#% required: yes
#%end

#%option
#% key: atm
#% key_desc: index
#% type: integer
#% label: Atmospheric model
#% description: Index of the amtospheric model (refer to i.atcorr's manual)
#% options: 0-8
#% guisection: Parameters
#% required: yes
#%end

#%option
#% key: aer
#% key_desc: index
#% type: integer
#% label: Aerosols model
#% description: Index of the aerosols model (refer to i.atcorr's manual)
#% options: 0-11
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
geo = 7  # Geometrical conditions
xpp = -1000  # Satellite borne [-1000]
bnd = {1: 25, 2: 26, 3: 27, 4: 28, 5: 29, 7: 30}  # Spectral conditions index

# globals ------------------------------------------------------------------
g.message(msg)
rad_flg = ''

# helper functions ----------------------------------------------------------
def cleanup():
    """Clean up temporary maps"""
    grass.run_command('g.remove', flags='f', type="rast",
                      pattern='tmp.%s*' % os.getpid(), quiet=True)

def run(cmd, **kwargs):
    """Help function executing grass commands with 'quiet=True'"""
    grass.run_command(cmd, quiet=True, **kwargs)


def run(cmd, **kwargs):
    """Pass quiet flag to grass commands"""
    grass.run_command(cmd, quiet=True, **kwargs)


def main():
    """ """
    mapsets = options['mapsets']

    prefix = options['inputprefix']
    suffix = options['outputsuffix']

    mtl = options['mtl']
    atm = options['atm']  # Atmospheric model [index]
    aer = options['aer']  # Aerosols model [index]
    vis = options['vis']  # Visibility [km]
    aod = options['aod']  # Aerosol Optical Depth at 550nm
    alt = options['alt']  # Mean Target Altitude [negative km]

    if not alt:
        msg = "Note, this value will be overwritten if a DEM raster has been "\
              "defined as an input!"
        g.message(msg)

    elevation = options['elevation']
    visibility = options['visibility']
    
    radiance = flags['r']
    if radiance:
        global rad_flg
        rad_flg = 'r'

    # If the scene to be processed was imported via the (custom) python
    # Landsat import script, then, Mapset name == Scene identifier

    mapset = grass.gisenv()['MAPSET']
    if mapset == 'PERMANENT':
        grass.fatal(_('Please change to another Mapset than the PERMANENT'))
    
    if 'L' not in mapset:
        msg = "Assuming the Landsat scene(s) ha-s/ve been imported using the "\
              "custom python import script, the Mapset's name *should* begin "\
              "with the letter L!"
        grass.fatal(_(msg))

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

    msg = "Acquisition metadata"
    g.message(msg)

    # Month, day
    date = grass.parse_command('i.landsat.toar', flags='p',
                               input='dummy', output='dummy',
                               metfile=mtl, lsatmet='date')
    mon = date['date'][5:7]  # Month of acquisition
    day = date['date'][8:10]  # Day of acquisition

    # GMT in decimal hours
    gmt = grass.read_command('i.landsat.toar', flags='p',
                             input='dummy', output='dummy',
                             metfile=mtl, lsatmet='time')
    gmt = gmt.rstrip('\n')

    # Scene's center coordinates
    cll = grass.parse_command('g.region', flags='clg')
    lon = cll['center_long']  # Center Longitude [decimal degrees]
    lat = cll['center_lat']  # Center Latitude [decimal degrees]
    msg = "The scene's center geographic coordinates (in decimal degrees): " \
        "${Long_NonProj} $Lat_NonProj ($Long $Lat)"

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


    # access only to specific mapsets! - currently, by hand!
    # g.mapsets mapset=`g.mapsets -l --v sep=comma` operator=remove
    msg = "Performing atmospheric correction for %s" % mapsets
    g.message(msg)

    for scene in scenes:

        # ensure access only to *current* mapset
        run('g.mapsets', mapset='.', operation='set')

        # scene's basename as in GRASS' db
        basename = grass.read_command('g.mapset', flags='p') #LT5_Basename=$(basename $BAND _MTL.txt)
        msg = "The scene's base name is %s" % basename

        # loop over Landsat bands in question
        for band in bnd.keys():

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
            p6s = Parameters(geo=7,
                       mon=11, day=21, gmt=14.5, lon=21.2, lat=23.3,
                       atm=3,
                       aer=1,
                       vis=100,
                       aod=None,
                       xps=150, xpp=-1000,
                       bnd=64)

            dst_dir = grass.gisenv()['GISDBASE'] + \
            '/' + grass.gisenv()['LOCATION_NAME'] + \
            '/' + grass.gisenv()['MAPSET'] + \
            '/cell_misc/'
            
            p6s.export_ascii(dst_dir)

            msg = "Processing band %s (spectral conditions index: %s)"
            g.message(msg)


              # Process band-wise atmospheric correction with 6s
            msg = "Using the following parameters:"
            g.message(msg)

        #    cat $Parameters_Pool/${Basename}_icnd_${Band_No}.txt | tr "\n" " "

        # -------------------------------------------------------------------
        # Applying 6S Atmospheric Correction algorithm 
        # -------------------------------------------------------------------

        if visibility:
            pass

        if elevation:
            """Using an elevation map.
            Attention: does the elevation cover the area of the images?"""
            run('i.atcorr', flags=rad_flg,
                input=band,
                range=(0.,1.),
                elevation=elevation,
                parameters=tmp_p6s,
                output=tmp_cor_out,
                rescale=(0,1.))

        else:
            run('i.atcorr', flags=rad_flg,
                input=band,
                range=(0, 1),
                parameters=tmp_p6s,
                output=tmp_cor_out,
                rescale=(0, 1))        

        # inform about output's range?
        run('r.info', flags='r', map=tmp_cor_out)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
