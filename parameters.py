#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: nik | Created on Wed Nov 19 20:41:35 2014
"""

#import sys

P6S = {'geo': 'Geometrical conditions',
       'mon': 'Month of acquisition',
       'day': 'Day of acquisition',
       'gmt': 'Time of acquisition (GMT) [decimal hours]',
       'mdg': 'Month Day GMT',
       'lon': 'Center Longitude [decimal degrees]',
       'lat': 'Center Latitude [decimal degrees]',
       'cll': 'Center Longitude Latitude [DD]',
       'atm': 'Atmospheric model [index]',
       'aer': 'Aerosols model [index]',
       'vis': 'Visibility [km]',
       'aod': 'Aerosol Optical Depth at 550nm',
       'xps': 'Mean Target Altitude [negative km]',
       'xpp': 'Sensor Altitude rel. to xps [negative km]'
              ' or SatelliteBorn [-1000]',
       'bnd': 'Satellite Band Number [index]'}


class Parameters:

    """6S Parameters (file) for i.atcorr"""

    def __init__(self, geo,
                 mon, day, gmt,
                 lon, lat,
                 atm, aer, vis, aod, xps, xpp, bnd):

        self.geo = int(geo)

        if 1 <= mon <= 12:
            self.mon = int(mon)  # month
        else:
            raise ValueError("Invalid value for Month")

        if 1 <= day <= 31:
            self.day = int(day)  # day
        else:
            raise ValueError("Error")

        if type(gmt) == float:
            self.gmt = gmt  # decimal hours
        elif ':' in str(gmt):
            self.gmt = float(gmt[0:2]) + (float(gmt[3:5]) * 100 / 60) / 100

        self.mdg = "%d %d %.2f" % (self.mon, self.day, self.gmt)  # combine

        if -180 <= float(lon) <= 180:
            self.lon = float(lon)  # scene's center longitude
        else:
            raise ValueError("Invalid Longitude")

        if -90 <= float(lat) <= 90:
            self.lat = float(lat)  # scene's center latitude
        else:
            raise ValueError("Invalid Latitude")

        self.acq = '%s %f %f' % (self.mdg, lon, lat)  # 2nd line of parameters
        if len(self.acq.split(' ')) < 5:
            raise ValueError("For line 2 in parameters file, "
                             "Something is missing...")

        if 0 <= atm <= 8:
            self.atm = int(atm)
        else:
            raise ValueError("Invalid atmospheric model index")

        if 0 <= aer <= 11:
            self.aer = int(aer)
        else:
            raise ValueError("Invalid aerosols model index")

        if not aod < 0:

            if aod > 0:
                self.vis = 0  # set visibility to 0 if aod value defined
                self.aod = float(aod)

            elif float(aod) == float(0):
                self.vis = -1  # set visibility to -1 if aod set to 0
                self.aod = None

            else:
                self.vis = float(vis)

        elif aod < 0:
            raise ValueError("Invalid AOD value")

        else:
            self.aod = None

        self.xps = float(xps)  # xps <= 0 | xps >= 0 == 'target at sea level'

        if 1 <= geo <= 18:
            self.xpp = -1000
        elif (geo == 0 or geo > 18) and -100 <= xpp <= 0:
            self.xpp = float(xpp)  # -100 < alt < 0

        if 2 <= bnd <= 123:
            self.bnd = int(bnd)

#        # build parameters string
        tabs = 4 * '\t'
        self.parameters = str(self.geo) + '%s# %s' % (tabs, P6S['geo']) + '\n'
        self.parameters += str(self.acq) + '\t# %s %s' \
            % (P6S['mdg'], P6S['cll']) + '\n'
        self.parameters += str(self.atm) + '%s# %s' % (tabs, P6S['atm']) + '\n'
        self.parameters += str(self.aer) + '%s# %s' % (tabs, P6S['aer']) + '\n'
        self.parameters += str(self.vis) + '%s# %s' % (tabs, P6S['vis']) + '\n'
        if aod > 0 :
            self.parameters += str(self.aod) + '%s# %s' % (tabs, P6S['aod']) + '\n'
        elif aod == None:
            pass
        self.parameters += str(self.xps) + '%s# %s' % (tabs, P6S['xps']) + '\n'
        self.parameters += str(self.xpp) + '%s# %s' % (tabs, P6S['xpp']) + '\n'
        self.parameters += str(self.bnd) + '%s# %s' % (tabs, P6S['bnd']) + '\n'

#    def usage(self):
#        msg = "Input the parameters of interest, one by one:"
#        msg += P6S.keys()

    def __str__(self):
        msg = "Parameters for the 6S atmospheric correction model:"
        return msg + '\n' + self.parameters

    def export_ascii(self, destination):
        """Exporting parameters parameters for i.atcorr in an ASCII file"""

        # structure informative message
        #    msg = "   > %sFilter Properties: size: %s, center: %s" % \
        #        (msg_ps2, filter.size, center)
        #    g.message(msg, flags='v')

        # open, write and close file
        asciif = open(destination, 'w')
        asciif.write(self.parameters)
        asciif.close()


#def main():
#    Parameters()

#if __name__ == "__main__":
#    sys.exit(main())

# Random example
"""
print Parameters(geo=8,
 mon=11, day=22, gmt='02:15',
 lon=22.2, lat=33.3,
 atm=3, aer=3, vis=10, aod=None,
 xps=-200, xpp=-1000,
 bnd=26)
"""


"""
2012-11-08T23:42:37Z
Parameters(geo=8,
 mon=11, day=08, gmt='23:42',
 lon=22.2, lat=33.3,
 atm=2, aer=1, vis=10, aod=None,
 xps=-200, xpp=-1000,
 bnd=26)
"""