Unsorted Notes

* The file  'landsat_MTL.txt'  is hand-crafted, used for a quick test of  
'i.landsat.atcorr'  for the  'lsat7_2000_#' (where #, some number) bands found 
in found in 
<http://grass.osgeo.org/sampledata/north_carolina/nc_spm_08_grass7.zip>.

* The script  'i.landsat.atcorr'  *requires* the metadata filename's prefix to 
be identical to the name of the *current* Mapset. The idea is to import a 
landsat scene in one Mapset, using the import script found in 
<http://grasswiki.osgeo.org/wiki/LANDSAT#Automated_data_import> which copies the 
MTL file in the cell_misc directory of the corresponding Mapset of interest.
