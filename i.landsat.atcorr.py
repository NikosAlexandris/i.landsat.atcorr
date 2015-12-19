#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 MODULE:        i.landsat.atcorr

 AUTHOR(S):     Nikos Alexandris <nik@nikosalexandris.net>
                Converted from a bash shell script (written in Feb. 2013)
                Trikala, Nov. 2014
                Based on an earlier script provided by Yann Chemin

 PURPOSE:       Scripting i.atcorr for Landsat satellite acquisitions

 COPYRIGHT:    (C) 2013 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

#%Module
#%  description: Atmospheric correction of Landsat scenes. Acquisitions should be imported in GRASS' database in a one Mapset per scene manner! 
#%  keywords: landsat
#%  keywords: atmospheric correction
#%End

#%flag
#%  key: r
#%  description: Input is Spectral Radiance
#%end

#%flag
#%  key: e
#%  description: Equalize histogram of output bands (r.colors -e)
#%end


# Get sensor from the MetaData file! ------------------------------------ To Do --
#%option
#% key: sensor
#% key_desc: Sensor
#% type: string
#% label: Landsat sensor
#% description: Landsat sensor selecting spectral conditions indexing
#% options: mss, mss4, tm, etm, oli
#% descriptions: mss;mss1, mss2 or mss3: Multi Spectral Scanner on Landsat1-3. Bands 4, 5, 6, 7;mss4;or mss5: MSS on Landsat4-5. Bands 1, 2, 3, 4;tm;tm4 or tm5: Thematic Mapper on Landsat5. Bands 1, 2, 3, 4, 5, 6, 7;etm;Enhanced Thematic Mapper on Landsat7. Bands 1, 2, 3, 4, 5, 6, 7;oli;Operational Land Imager & Thermal Infrared Sensor on Landsat8. Bands 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
#% required: yes
#% multiple: no
#%end
# -- To Do ------------------------------------------------------------------

#%option
#% key: mapsets
#% key_desc: Mapsets
#% type: string
#% label: Mapsets to process
#% description: Scenes to process given bands of a scene imported in independent Mapsets
#% options: all,current,selected
#% descriptions: all;All mapsets except of PERMANENT;current;Current mapset;selected;Only selected mapsets
#% answer: current
#% required: no
#%end

#%option G_OPT_R_BASENAME_INPUT
#% key: input_prefix
#% key_desc: prefix string
#% type: string
#% label: Prefix of input bands
#% description: Prefix of Landsat bands imported in GRASS' data base
#% required: yes
#%end

#%option G_OPT_R_BASENAME_OUTPUT
#% key: output_suffix
#% key_desc: suffix string
#% type: string
#% label: Suffix for output image(s)
#% description: Names of atmospherically corrected Landsat5 TM bands image(s) will end with this suffix
#% required: yes
#% answer: AtmCor
#%end

#%option
#% key: metafile
#% key_desc: Metadata file
#% type: string
#% label: Acquisition's metadata file ()
#% description: Landsat acquisition metadata file (.met or MTL.txt)
#% required: yes
#%end

#%option
#% key: atmospheric_model
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
#% key: aerosols_model
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
#% key: visual_range
#% key_desc: distance or concentration
#% type: double
#% label: Visibility
#% description: Visibility [km] or Aerosols Optical Depth at 550nm (refer to i.atcorr's manual)
#% guisection: Parameters
#% required: no
#%end

#%option
#% key: aod
#% key_desc: concentration
#% type: double
#% label: AOD
#% description: Aerosols Optical Depth at 550nm (refer to i.atcorr's manual). Based on the metadata, defaults to 0.111 for winter or 0.222 for summer acquisitions.
#% guisection: Parameters
#% required: no
#%end

#%option
#% key: altitude
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


# Yet to work-out on options and flags relationships! -----------------------
# %rules
# %required inputprefix,outputsuffix
# %end


# required librairies -------------------------------------------------------
import os
import sys
sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]),
                                'etc', 'i.landsat.atcorr'))
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
'mss': {1: 31, 2: 32, 3: 33, 4: 34},
'tm':  {1: 25, 2: 26, 3: 27, 4: 28, 5: 29, 7: 30},
'etm': {1: 61, 2: 62, 3: 63, 4: 64, 5: 65, 7: 66, 8: 67},
'oli': {1: 115, 2: 116, 3: 117, 4: 118, 8: 119, 5: 120, 9: 121, 6: 122, 7: 123}
}


# globals
g.message(msg)
radiance_flag = ''


# helper functions
def cleanup():
    """Clean up temporary maps"""
    grass.run_command('g.remove', flags='f', type="rast",
                      pattern='tmp.%s*' % os.getpid(), quiet=True)


def run(cmd, **kwargs):
    """
    Pass quiet flag to grass commands
    """
    grass.run_command(cmd, quiet=True, **kwargs)


def run_i_atcorr(radiance_flag, input_band, input_range, elevation, visibility,
                 parameters, output, output_range):
    '''
    Run i.atcorr using the provided options. Except for the required
    parameters, the function updates the list of optional/selected parameters.

    Optional inputs:

    - range
    - elevation
    - visibility
    - rescale
    '''
    params = {}

    # inputs
    if input_range:
        params.update({'range': (input_range['min'], input_range['max'])})

    if elevation:
        params.update({'elevation': elevation})

    if visibility:
        params.update({'visibility': visibility})

    if output_range:
        params.update({'rescale': (output_range[0], output_range[1])})

    print "Parameters given:", params
    print

    run('i.atcorr',
        flags=radiance_flag,
        input=input_band,
        parameters=parameters,
        output=output,
        **params)

def main():
    """ """
    sensor = options['sensor']

    mapsets = options['mapsets']
    prefix = options['input_prefix']
    suffix = options['output_suffix']

    metafile = grass.basename(options['metafile'])

    # 6S parameter names shortened following i.atcorr's manual
    atm = int(options['atmospheric_model'])  # Atmospheric model [index]
    aer = int(options['aerosols_model'])  # Aerosols model [index]

    vis = options['visual_range']  # Visibility [km]
    aod = options['aod']  # Aerosol Optical Depth at 550nm

    xps = options['altitude']  # Mean Target Altitude [negative km]
    if not xps:
        msg = "Note, this value will be overwritten if a DEM raster has been "\
              "defined as an input!"
        g.message(msg)

    elevation_map = options['elevation']
    visibility_map = options['visibility']

    radiance = flags['r']
    if radiance:
        global rad_flg
        radiance_flag = 'r'
    else:
        radiance_flag = ''

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
        result = grass.find_file(element='cell_misc',
                                 name=metafile,
                                 mapset='.')
        if not result['file']:
            grass.fatal("The metadata file <%s> is not in GRASS' data base!"
                        % metafile)
        else:
            metafile = result['file']

    #
    # Acquisition's metadata
    #

    msg = "Acquisition metadata for 6S code (line 2 in Parameters file)\n"

    # Month, day
    date = grass.parse_command('i.landsat.toar', flags='p',
                               input='dummy', output='dummy',
                               metfile=metafile, lsatmet='date')
    mon = int(date['date'][5:7])  # Month of acquisition
    day = int(date['date'][8:10])  # Day of acquisition

    # GMT in decimal hours
    gmt = grass.read_command('i.landsat.toar', flags='p',
                             input='dummy', output='dummy',
                             metfile=metafile, lsatmet='time')
    gmt = float(gmt.rstrip('\n'))

    # Scene's center coordinates
    cll = grass.parse_command('g.region', flags='clg')
    lon = float(cll['center_long'])  # Center Longitude [decimal degrees]
    lat = float(cll['center_lat'])  # Center Latitude [decimal degrees]

    msg += str(mon) + ' ' + str(day) + ' ' + str(gmt) + ' ' + \
        str(lon) + ' ' + str(lat)
    g.message(msg)
   
    # 
    # AOD
    #
    if aod:
        aod = float(options['aod'])

    else:
        # sane defaults
        if 4 < mon < 10:
            aod = float(0.222)  # summer
        else:
            aod = float(0.111)  # winter

    #
    # Mapsets are Scenes. Read'em all!
    #

    if mapsets == 'all':
        scenes = grass.mapsets()

    elif mapsets == 'current':
        scenes = [mapset]

    else:
        scenes = mapsets.split(',')

    if 'PERMANENT' in scenes:
        scenes.remove('PERMANENT')

    # access only to specific mapsets!
    msg = "\n|* Performing atmospheric correction for scenes:  %s" % scenes
    g.message(msg)

    for scene in scenes:

        # ensure access only to *current* mapset
        run('g.mapsets', mapset='.', operation='set')

        # scene's basename as in GRASS' db
        basename = grass.read_command('g.mapset', flags='p')
        msg = "   | Processing scene:  %s" % basename
        g.message(msg)

        # loop over Landsat bands in question
        for band in sensors[sensor].keys():

            inputband = prefix + str(band)
            msg = '\n>>> Processing band: {band}'.format(band=inputband)
            g.message(msg)


            # Generate 6S parameterization file
            p6s = Parameters(geo=geo[sensor],
                             mon=mon, day=day, gmt=gmt, lon=lon, lat=lat,
                             atm=atm,
                             aer=aer,
                             vis=vis,
                             aod=aod,
                             xps=xps, xpp=xpp,
                             bnd=sensors[sensor][band])
            
            #
            # Temporary files
            #
            tmpfile = grass.tempfile()
            tmp = "tmp." + grass.basename(tmpfile)  # use its basename

            tmp_p6s = grass.tempfile()  # 6S Parameters ASCII file
            tmp_atm_cor = "%s_cor_out" % tmp  # Atmospherically Corrected Img

            p6s.export_ascii(tmp_p6s)

            # Process band-wise atmospheric correction with 6s
            msg = "6S parameters:\n\n"
            msg += p6s.parameters
            g.message(msg)

            # inform about input's range?
            input_range = grass.parse_command('r.info', flags='r', map=inputband)
            input_range['min'] = float(input_range['min'])
            input_range['max'] = float(input_range['max'])
            msg = "Input range: %.2f ~ %.2f" % (input_range['min'], input_range['max'])
            g.message(msg)

            #
            # Applying 6S Atmospheric Correction algorithm
            #
            run_i_atcorr(radiance_flag,
                         inputband,
                         input_range,
                         elevation_map,
                         visibility_map,
                         tmp_p6s,
                         tmp_atm_cor,
                         (0,1))
        
            # inform about output's range?
            output_range = grass.parse_command('r.info', flags='r', map=tmp_atm_cor)
            output_range['min'] = float(output_range['min'])
            output_range['max'] = float(output_range['max'])
            msg = "Output range: %.2f ~ %.2f" \
                % (output_range['min'], output_range['max'])
            g.message(msg)

            # add suffix to basename & rename end product
            atm_cor_nam = ("%s%s.%s" % (prefix, suffix, band))
            run('g.rename', rast=(tmp_atm_cor, atm_cor_nam))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
