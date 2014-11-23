MODULE_TOPDIR = ../..

PGM = i.landsat.atcorr

ETCFILES = parameters

include $(MODULE_TOPDIR)/include/Make/Script.make
include $(MODULE_TOPDIR)/include/Make/Python.make

default: script
