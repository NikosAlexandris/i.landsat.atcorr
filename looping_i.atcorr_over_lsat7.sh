#!/bin/bash

# echo "6S Atmospheric Correction algorithm)"

# A shell script to loop over all bands of a single Landsat7 acquisition

  # based on a script provided by Yann Chemin!
  # for grass70
  # contains hardcoded stuff!

# Operate in a Mapset which contains bands of a single acquisition!

  # Bands imported using custom python script
  # The MTL file is copied over in the 'cell_misc' subdirectory
  # hence,
  eval $(g.findfile element=cell_misc file=$(echo `g.mapset -p`_MTL.txt) -n)
  echo "The metadata file is:"
  echo "<$file>."


# first, remove access to all mapsets but the current
g.mapsets mapset=. oper=set

# access only to specific mapsets! - currently, by hand!
# g.mapsets mapset=`g.mapsets -l --v sep=comma` operator=remove
# Scenes_To_Correct=$(g.mapsets -p)
# echo "Correcting scenes: $Scenes_To_Correct"

echo "Acquisition metadata"
echo

# scene's basename as in GRASS' db
Basename=$(g.mapset -p) #LT5_Basename=$(basename $BAND _MTL.txt)
echo "The scene's base name is ${Basename}"

# acquisition date
Date_Acquired=$(grep -a DATE_ACQUIRED $file | cut -d" " -f7)
Month=$(echo "${Date_Acquired}" | cut -d"-" -f2) # grep Month
Day=$(echo "${Date_Acquired}" | cut -d"-" -f3) # grep Day

# GMT in decimal hours
GMT=$(grep -a -e "TIME" "${file}" | cut -d" " -f7 | sed 's:^\(.*\)Z$:\1:' | awk -F: '{print $1 + ( $2 / 60) + ($3 / 3600) }')

  # Merge in one variable
  MDH="$Month $Day $GMT"
  echo "Month, Day and UTC Decimal Hours of the acquisition: $MDH"
  
  
#Get the scene's central Lat/Long
Long_NonProj=`g.region -c | grep easting | sed 's/center\ easting:\ \(.*\)/\1/'`
Lat_NonProj=`g.region -c | grep northing | sed 's/center\ northing:\ \(.*\)/\1/'`
Long=`g.region -cgl | grep center_long | sed 's/center_long=\(.*\)/\1/'`
Lat=`g.region -cgl | grep center_lat | sed 's/center_lat=\(.*\)/\1/'`

echo "The scene's center geographic coordinates (in decimal degrees): ${Long_NonProj} $Lat_NonProj ($Long $Lat)"



echo " "
echo "Required parameters"

Geometry=8 # Geometrical conditions (L7ETM+)
echo "- Geometrical conditions index for Landsat 7 ETM+ : $Geometry"

Sensor_Height=-1000 # for satellite borne sensors set to -1000
echo "- Sensor's height:          $Sensor_Height"

Atmospheric_Mode=1 # here: tropical
echo "- Atmospheric mode:             $Atmospheric_Mode"

Aerosol_Model=2 # here: maritime
echo "- Aerosol model:                $Aerosol_Model"

# get first parameter $1 or read MTE!
if [ -z $1 ]
  then
	echo "Please provide a Mean Target Elevation (negatively signed Km)"
	echo "(For Kembung River region: Mean ASTER GDEM elevation= 10.2072)"
	echo "(For Jankgang River region: Mean ASTER GDEM elevation= )"
	read MeanTargetElevation
  else MeanTargetElevation=$1
fi

# MeanTargetElevation=-0.500 # Km, should be negative in the parameters file
echo " - Mean target elevation:        $MeanTargetElevation"
# note, will be overwritten by the DEM raster input!

# Location of parameter file(s)
eval `g.gisenv`
Parameters_Pool=$(echo "$GISDBASE/$LOCATION_NAME/$MAPSET/cell_misc")
echo
echo "[Parameter file(s) will be stored at: $Parameters_Pool]"
# wait a bit!
sleep 1


# aerosol depth, summer vs winter
AOD=$2	;	AOD_Winter=0.976	;	AOD_Summer=0.976

if [ -z $AOD ]
  then
  AOD=$AOD_Winter # set to winter AOD
  if (( $Month > 4 )) && (( $Month < 10 )) # compare month of acquisition
	then AOD=$AOD_Summer  # set to summer AOD if...
  fi
fi
echo "The provided aerosol optical depth: ${AOD} (unitless)"

# if AOD provided, set Visibility to Zero
  if [[ $( echo "$AOD > 0" | bc ) -eq 1 ]]
	then Visibility=0 ; echo "Visibility set to zero since AOD (=$AOD) is provided!"
  fi


# spectral conditions index for L5TM:
# 61, 62, 63, 64, 65, 66, 67 respectively for bands 1, 2, 3, 4, 5, 7, 8
Satellite_Band_No=61 # 1st L5TM band to undergo atmospheric correction -- counter!


### What about visibility maps? ###

# loop over Landsat bands in question
for Band_No in 1 2 3 4 5 7 8
  do # Generate the parameterization file (icnd_l7)

  echo
  echo "Processing band $Band_No (spectral conditions index: $Satellite_Band_No)"

  #   echo "$Geometry - geometrical conditions=Landsat 5 TM" > $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$Geometry # Geometrical conditions"> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  #   echo "$MDH $Long $Lat - month day hh.ddd longitude latitude" >>  $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$MDH $Long $Lat # Month, Day, GMT (decimal hours), Longitude, Latitude" >>  $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  #   echo "$Atmospheric_Mode - atmospheric mode=tropical" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$Atmospheric_Mode # Atmospheric Mode" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  #   echo "$Aerosol_Model - aerosols model=continental" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$Aerosol_Model # Aerosol Model" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  #   echo "$Visibility - visibility [km] (aerosol model concentration), not used as there is raster input" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$Visibility # Visibility" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  #   echo "$AOD - aerosol optical depth at 550nm" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$AOD # Aerosol Optical Depth (550nm)" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  # echo "$MeanTargetElevation - mean target elevation above sea level [km] (here 600m asl), not used as there is raster input" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$MeanTargetElevation # Mean Target Elevation" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  #   echo "$Sensor_Height - sensor height (here, sensor on board a satellite)" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$Sensor_Height # Sensor's Height" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  #   echo "$Satellite_Band_No - band ${Band_No} of TM Landsat 5" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt
  echo "$Satellite_Band_No # Satellite's Band Number" >> $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

	# Process band-wise atmospheric correction with 6s
	echo "Using the following parameters:"
	cat $Parameters_Pool/${Basename}_icnd_${Band_No}.txt

  # echo "Executing: i.atcorr -r input=$L5_Basename.ToAR.$Band_No elevation=$DEM visibility=$Visibility parameters=$Parameter_Pool/${Basename}_icnd_${Band_No}.txt output=Test_$LT5_Basename.ToCR.$Band_No range=0,1 rescale=0,1 --overwrite"
  
# Attention!
  ## input is radiance or reflectance?
  ## flag "-r" ?
  ## does the elevation cover the area of the images?
  ## input and output is converted in to float values anyway!

# i.atcorr -r --overwrite \
# input=B.Trimmed.ToAR.$Band_No \
# range=0,1 \
# elevation=aster_gdem2_ellas \
# parameters=$Parameters_Pool/${Basename}_icnd_${Band_No}.txt \
# output=Test_$Basename_$Band_No \
# rescale=0,1

# without elevation here!
i.atcorr -r -a --overwrite \
input=KR_B.DOS3.$Band_No \
range=0,1 \
parameters=$Parameters_Pool/${Basename}_icnd_${Band_No}.txt \
output=Test_$Basename_$Band_No \
rescale=0,1

r.info Test_$Basename_$Band_No
sleep 1

  Satellite_Band_No=$(($Satellite_Band_No+1))
  if [ $Satellite_Band_No -gt 67 ]
   then Satellite_Band_No=61
  fi

 done
