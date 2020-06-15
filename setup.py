# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import defaultdict
from Cython.Distutils import build_ext
from distutils.core import setup
from distutils.extension import Extension
# from Cython.Build import cythonize    # MacOS NG
from setuptools import setup, find_packages, Extension

import subprocess
import numpy
import sys
import platform
import os
import time

import shutil
from ctypes.util import find_library
setup_requires = []
install_requires = [
    'filelock',
    'mock',
    'nose',
    # RuntimeWarning: numpy.dtype size changed, may indicate binary incompatibility
    # https://github.com/scikit-image/scikit-image/issues/3655
    # 'numpy>=1.15.1,!=1.50.0',
    # numpy.ufunc size changed, may indicate binary incompatibility.
    'numpy>=1.16.1,!=1.16.2',
    'Cython>=0.26.0',
]


def pkgconfig(flag):
    # Equivalent in Python 2.7 (but not 2.6):
    # subprocess.check_output(['pkg-config', flag] + pcl_libs).split()
    p = subprocess.Popen(['pkg-config', flag] +
                         pcl_libs, stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    # Assume no evil spaces in filenames; unsure how pkg-config would
    # handle those, anyway.
    # decode() is required in Python 3. TODO how do know the encoding?
    return stdout.decode().split()


def pkgconfig_win(flag, cut):
    # Equivalent in Python 2.7 (but not 2.6):
    # subprocess.check_output(['pkg-config', flag] + pcl_libs).split()
    p = subprocess.Popen(['.\\pkg-config\\pkg-config.exe', flag] +
                         pcl_libs, stdout=subprocess.PIPE)
    stdout, _ = p.communicate()
    # Assume no evil spaces in filenames; unsure how pkg-config would
    # handle those, anyway.
    # decode() is required in Python 3. TODO how do know the encoding?
    # return stdout.decode().split()
    # Windows
    return stdout.decode().replace('\r\n', '').replace('\ ', ' ').replace('/', '\\').split(cut)

if True:
    # Not 'Windows'
    if sys.platform == 'darwin':
        os.environ['ARCHFLAGS'] = ''

    # Try to find PCL. XXX we should only do this when trying to build or install.
    PCL_SUPPORTED = ["-1.9", "-1.8", "-1.7", "-1.6", ""]    # in order of preference

    for pcl_version in PCL_SUPPORTED:
        if subprocess.call(['pkg-config', 'pcl_common%s' % pcl_version]) == 0:
            break
    else:
        print("%s: error: cannot find PCL, tried" %
              sys.argv[0], file=sys.stderr)
        for version in PCL_SUPPORTED:
            print('    pkg-config pcl_common%s' % version, file=sys.stderr)
        sys.exit(1)

    # Find build/link options for PCL using pkg-config.
    # version 1.6
    # pcl_libs = ["common", "features", "filters", "io", "kdtree", "octree",
    #             "registration", "sample_consensus", "search", "segmentation",
    #             "surface", "tracking", "visualization"]
    # version 1.7
    if pcl_version == '-1.7':
        pcl_libs = ["common", "features", "filters", "geometry",
                    "io", "kdtree", "keypoints", "octree", "outofcore", "people",
                    "recognition", "registration", "sample_consensus", "search",
                    "segmentation", "surface", "tracking", "visualization"]
    else:
        # version 1.8
        pcl_libs = ["2d", "common", "features", "filters", "geometry",
                    "io", "kdtree", "keypoints", "ml", "octree", "outofcore", "people",
                    "recognition", "registration", "sample_consensus", "search",
                    "segmentation", "stereo", "surface", "tracking", "visualization"]
    pcl_libs = ["pcl_%s%s" % (lib, pcl_version) for lib in pcl_libs]

    ext_args = defaultdict(list)
    ext_args['include_dirs'].append(numpy.get_include())

    for flag in pkgconfig('--cflags-only-I'):
        ext_args['include_dirs'].append(flag[2:])

    # OpenNI?
    # "-I/usr/include/openni"
    # "-I/usr/include/openni"
    # /usr/include/ni
    ext_args['include_dirs'].append('/usr/include/ni')
    # ext_args['library_dirs'].append()
    # ext_args['libraries'].append()
    # OpenNI2
    ext_args['include_dirs'].append('/usr/include/openni2')

    # VTK use
    if sys.platform == 'darwin':
        # pcl 1.8.1(MacOSX)
        # if pcl_version == '-1.8':
        #     vtk_version = '8.0'
        #     ext_args['include_dirs'].append('/usr/local/include/vtk-' + vtk_version)
        #     ext_args['library_dirs'].append('/usr/local/lib')
        #     ext_args['include_dirs'].append('/usr/local/Cellar/vtk/8.0.1/include')
        #     ext_args['library_dirs'].append('/usr/local/Cellar/vtk/8.0.1/lib')
        if pcl_version == '-1.9':
            # pcl 1.9.1
            # build install?
            # vtk_version = '8.1'
            # vtk_include_dir = os.path.join('/usr/local' ,'include/vtk-8.1')
            # vtk_library_dir = os.path.join('/usr/local', 'lib')
            # homebrew(MacOSX homebrew)
            # (pcl 1.9.1_3)
            # vtk_version = '8.1.2_3'
            # vtk_include_dir = os.path.join('/usr/local/Cellar/vtk', vtk_version ,'include/vtk-8.2')
            # 2019/05/08 check(pcl 1.9.1_4)
            vtk_version = '8.2.0'
            vtk_include_dir = os.path.join('/usr/local/Cellar/vtk', vtk_version ,'include/vtk-8.2')
            vtk_library_dir = os.path.join('/usr/local/Cellar/vtk', vtk_version, 'lib')
        pass
    else:
        # pcl 1.7.0?(Ubuntu 14.04)
        # vtk_version = '5.8'
        # ext_args['include_dirs'].append('/usr/include/vtk-' + vtk_version)
        # ext_args['library_dirs'].append('/usr/lib')
        # pcl 1.7.2(Ubuntu 16.04)(xenial)
        if pcl_version == '-1.7':
            vtk_version = '6.2'
            vtk_include_dir = os.path.join('/usr/include/vtk-' + vtk_version)
            vtk_library_dir = os.path.join('/usr/lib')
        elif pcl_version == '-1.8':
            # pcl 1.8.0/1?(Ubuntu 18.04)(melodic)
            vtk_version = '6.3'
            # pcl 1.8.1?
            # vtk_version = '8.0'
            vtk_include_dir = os.path.join('/usr/include/vtk-' + vtk_version)
            vtk_library_dir = os.path.join('/usr/lib')
        elif pcl_version == '-1.9':
            # pcl 1.9.1
            # build install?
            vtk_version = '6.3'
            vtk_include_dir = os.path.join('/usr/include/vtk-' + vtk_version)
            vtk_library_dir = os.path.join('/usr/lib')
        else:
            pass

    # other
    # pcl 1.9.1(Conda)
    # vtk_version = '8.1'
    # vtk_include_dir = os.path.join(os.environ["PREFIX"] ,'include/vtk-8.1')
    # vtk_library_dir = os.path.join(os.environ["PREFIX"], 'lib')

    ext_args['include_dirs'].append(vtk_include_dir)
    ext_args['library_dirs'].append(vtk_library_dir)

    if vtk_version == '5.8':
        vtklibreleases = ['vtkInfovis', 'MapReduceMPI', 'vtkNetCDF', 'QVTK', 'vtkNetCDF_cxx', 'vtkRendering', 'vtkViews', 'vtkVolumeRendering', 'vtkWidgets', 'mpistubs', 'vtkalglib', 'vtkCharts', 'vtkexoIIc', 'vtkexpat', 'vtkCommon', 'vtkfreetype', 'vtkDICOMParser', 'vtkftgl', 'vtkFiltering', 'vtkhdf5', 'vtkjpeg', 'vtkGenericFiltering', 'vtklibxml2', 'vtkGeovis', 'vtkmetaio', 'vtkpng', 'vtkGraphics', 'vtkproj4', 'vtkHybrid', 'vtksqlite', 'vtksys', 'vtkIO', 'vtktiff', 'vtkImaging', 'vtkverdict', 'vtkzlib']
    elif vtk_version == '6.3':
        vtklibreleases = ['vtkalglib-' + vtk_version, 'vtkChartsCore-' + vtk_version, 'vtkCommonColor-' + vtk_version, 'vtkCommonComputationalGeometry-' + vtk_version, 'vtkCommonCore-' + vtk_version, 'vtkCommonDataModel-' + vtk_version, 'vtkCommonExecutionModel-' + vtk_version, 'vtkCommonMath-' + vtk_version, 'vtkCommonMisc-' + vtk_version, 'vtkCommonSystem-' + vtk_version, 'vtkCommonTransforms-' + vtk_version, 'vtkDICOMParser-' + vtk_version, 'vtkDomainsChemistry-' + vtk_version, 'vtkexoIIc-' + vtk_version, 'vtkFiltersAMR-' + vtk_version, 'vtkFiltersCore-' + vtk_version, 'vtkFiltersExtraction-' + vtk_version, 'vtkFiltersFlowPaths-' + vtk_version, 'vtkFiltersGeneral-' + vtk_version, 'vtkFiltersGeneric-' + vtk_version, 'vtkFiltersGeometry-' + vtk_version, 'vtkFiltersHybrid-' + vtk_version, 'vtkFiltersHyperTree-' + vtk_version, 'vtkFiltersImaging-' + vtk_version, 'vtkFiltersModeling-' + vtk_version, 'vtkFiltersParallel-' + vtk_version, 'vtkFiltersParallelImaging-' + vtk_version, 'vtkFiltersProgrammable-' + vtk_version, 'vtkFiltersSelection-' + vtk_version, 'vtkFiltersSMP-' + vtk_version, 'vtkFiltersSources-' + vtk_version, 'vtkFiltersStatistics-' + vtk_version, 'vtkFiltersTexture-' + vtk_version, 'vtkFiltersVerdict-' + vtk_version, 'vtkGeovisCore-' + vtk_version, 'vtkImagingColor-' + vtk_version, 'vtkImagingCore-' + vtk_version, 'vtkImagingFourier-' + vtk_version, 'vtkImagingGeneral-' + vtk_version, 'vtkImagingHybrid-' + vtk_version, 'vtkImagingMath-' + vtk_version, 'vtkImagingMorphological-' + vtk_version, 'vtkImagingSources-' + vtk_version, 'vtkImagingStatistics-' + vtk_version, 'vtkImagingStencil-' + vtk_version, 'vtkInfovisCore-' + vtk_version, 'vtkInfovisLayout-' + vtk_version, 'vtkInteractionImage-' + vtk_version, 'vtkInteractionStyle-' + vtk_version, 'vtkInteractionWidgets-' + vtk_version, 'vtkIOAMR-' + vtk_version, 'vtkIOCore-' + vtk_version, 'vtkIOEnSight-' + vtk_version, 'vtkIOExodus-' + vtk_version, 'vtkIOExport-' + vtk_version, 'vtkIOGeometry-' + vtk_version, 'vtkIOImage-' + vtk_version, 'vtkIOImport-' + vtk_version, 'vtkIOInfovis-' + vtk_version, 'vtkIOLegacy-' + vtk_version, 'vtkIOLSDyna-' + vtk_version, 'vtkIOMINC-' + vtk_version, 'vtkIOMovie-' + vtk_version, 'vtkIONetCDF-' + vtk_version, 'vtkIOParallel-' + vtk_version, 'vtkIOParallelXML-' + vtk_version, 'vtkIOPLY-' + vtk_version, 'vtkIOSQL-' + vtk_version, 'vtkIOVideo-' + vtk_version, 'vtkIOXML-' + vtk_version, 'vtkIOXMLParser-' + vtk_version, 'vtkmetaio-' + vtk_version, 'vtkParallelCore-' + vtk_version, 'vtkRenderingAnnotation-' + vtk_version, 'vtkRenderingContext2D-' + vtk_version, 'vtkRenderingContextOpenGL-' + vtk_version, 'vtkRenderingCore-' + vtk_version, 'vtkRenderingFreeType-' + vtk_version, 'vtkRenderingGL2PS-' + vtk_version, 'vtkRenderingImage-' + vtk_version, 'vtkRenderingLabel-' + vtk_version, 'vtkRenderingLIC-' + vtk_version, 'vtkRenderingLOD-' + vtk_version, 'vtkRenderingOpenGL-' + vtk_version, 'vtkRenderingVolume-' + vtk_version, 'vtkRenderingVolumeOpenGL-' + vtk_version, 'vtksys-' + vtk_version, 'vtkverdict-' + vtk_version, 'vtkViewsContext2D-' + vtk_version, 'vtkViewsCore-' + vtk_version, 'vtkViewsInfovis-' + vtk_version]
    elif vtk_version == '7.0':
        # apt package?(vtk use OpenGL?)
        vtklibreleases = ['vtkalglib-' + vtk_version, 'vtkChartsCore-' + vtk_version, 'vtkCommonColor-' + vtk_version, 'vtkCommonComputationalGeometry-' + vtk_version, 'vtkCommonCore-' + vtk_version, 'vtkCommonDataModel-' + vtk_version, 'vtkCommonExecutionModel-' + vtk_version, 'vtkCommonMath-' + vtk_version, 'vtkCommonMisc-' + vtk_version, 'vtkCommonSystem-' + vtk_version, 'vtkCommonTransforms-' + vtk_version, 'vtkDICOMParser-' + vtk_version, 'vtkDomainsChemistry-' + vtk_version, 'vtkexoIIc-' + vtk_version, 'vtkexpat-' + vtk_version, 'vtkFiltersAMR-' + vtk_version, 'vtkFiltersCore-' + vtk_version, 'vtkFiltersExtraction-' + vtk_version, 'vtkFiltersFlowPaths-' + vtk_version, 'vtkFiltersGeneral-' + vtk_version, 'vtkFiltersGeneric-' + vtk_version, 'vtkFiltersGeometry-' + vtk_version, 'vtkFiltersHybrid-' + vtk_version, 'vtkFiltersHyperTree-' + vtk_version, 'vtkFiltersImaging-' + vtk_version, 'vtkFiltersModeling-' + vtk_version, 'vtkFiltersParallel-' + vtk_version, 'vtkFiltersParallelImaging-' + vtk_version, 'vtkFiltersProgrammable-' + vtk_version, 'vtkFiltersSelection-' + vtk_version, 'vtkFiltersSMP-' + vtk_version, 'vtkFiltersSources-' + vtk_version, 'vtkFiltersStatistics-' + vtk_version, 'vtkFiltersTexture-' + vtk_version, 'vtkFiltersVerdict-' + vtk_version, 'vtkfreetype-' + vtk_version, 'vtkGeovisCore-' + vtk_version, 'vtkgl2ps-' + vtk_version, 'vtkhdf5-' + vtk_version, 'vtkhdf5_hl-' + vtk_version, 'vtkImagingColor-' + vtk_version, 'vtkImagingCore-' + vtk_version, 'vtkImagingFourier-' + vtk_version, 'vtkImagingGeneral-' + vtk_version, 'vtkImagingHybrid-' + vtk_version, 'vtkImagingMath-' + vtk_version, 'vtkImagingMorphological-' + vtk_version, 'vtkImagingSources-' + vtk_version, 'vtkImagingStatistics-' + vtk_version, 'vtkImagingStencil-' + vtk_version, 'vtkInfovisCore-' + vtk_version, 'vtkInfovisLayout-' + vtk_version, 'vtkInteractionImage-' + vtk_version, 'vtkInteractionStyle-' + vtk_version, 'vtkInteractionWidgets-' + vtk_version, 'vtkIOAMR-' + vtk_version, 'vtkIOCore-' + vtk_version, 'vtkIOEnSight-' + vtk_version, 'vtkIOExodus-' + vtk_version, 'vtkIOExport-' + vtk_version, 'vtkIOGeometry-' + vtk_version, 'vtkIOImage-' + vtk_version, 'vtkIOImport-' + vtk_version, 'vtkIOInfovis-' + vtk_version, 'vtkIOLegacy-' + vtk_version, 'vtkIOLSDyna-' + vtk_version, 'vtkIOMINC-' + vtk_version, 'vtkIOMovie-' + vtk_version, 'vtkIONetCDF-' + vtk_version, 'vtkIOParallel-' + vtk_version, 'vtkIOParallelXML-' + vtk_version, 'vtkIOPLY-' + vtk_version, 'vtkIOSQL-' + vtk_version, 'vtkIOVideo-' + vtk_version, 'vtkIOXML-' + vtk_version, 'vtkIOXMLParser-' + vtk_version, 'vtkjpeg-' + vtk_version, 'vtkjsoncpp-' + vtk_version, 'vtklibxml2-' + vtk_version, 'vtkmetaio-' + vtk_version, 'vtkNetCDF-' + vtk_version, 'vtkoggtheora-' + vtk_version, 'vtkParallelCore-' + vtk_version, 'vtkpng-' + vtk_version, 'vtkproj4-' + vtk_version, 'vtkRenderingAnnotation-' + vtk_version, 'vtkRenderingContext2D-' + vtk_version, 'vtkRenderingContextOpenGL-' + vtk_version, 'vtkRenderingCore-' + vtk_version, 'vtkRenderingFreeType-' + vtk_version, 'vtkRenderingGL2PS-' + vtk_version, 'vtkRenderingImage-' + vtk_version, 'vtkRenderingLabel-' + vtk_version, 'vtkRenderingLIC-' + vtk_version, 'vtkRenderingLOD-' + vtk_version, 'vtkRenderingOpenGL-' + vtk_version, 'vtkRenderingVolume-' + vtk_version, 'vtkRenderingVolumeOpenGL-' + vtk_version, 'vtksqlite-' + vtk_version, 'vtksys-' + vtk_version, 'vtktiff-' + vtk_version, 'vtkverdict-' + vtk_version, 'vtkViewsContext2D-' + vtk_version, 'vtkViewsCore-' + vtk_version, 'vtkViewsInfovis-' + vtk_version, 'vtkzlib-' + vtk_version]
    elif vtk_version == '8.0':
        # vtklibreleases = ['vtkalglib-' + vtk_version, 'vtkChartsCore-' + vtk_version, 'vtkCommonColor-' + vtk_version, 'vtkCommonComputationalGeometry-' + vtk_version, 'vtkCommonCore-' + vtk_version, 'vtkCommonDataModel-' + vtk_version, 'vtkCommonExecutionModel-' + vtk_version, 'vtkCommonMath-' + vtk_version, 'vtkCommonMisc-' + vtk_version, 'vtkCommonSystem-' + vtk_version, 'vtkCommonTransforms-' + vtk_version, 'vtkDICOMParser-' + vtk_version, 'vtkDomainsChemistry-' + vtk_version, 'vtkexoIIc-' + vtk_version, 'vtkFiltersAMR-' + vtk_version, 'vtkFiltersCore-' + vtk_version, 'vtkFiltersExtraction-' + vtk_version, 'vtkFiltersFlowPaths-' + vtk_version, 'vtkFiltersGeneral-' + vtk_version, 'vtkFiltersGeneric-' + vtk_version, 'vtkFiltersGeometry-' + vtk_version, 'vtkFiltersHybrid-' + vtk_version, 'vtkFiltersHyperTree-' + vtk_version, 'vtkFiltersImaging-' + vtk_version, 'vtkFiltersModeling-' + vtk_version, 'vtkFiltersParallel-' + vtk_version, 'vtkFiltersParallelImaging-' + vtk_version, 'vtkFiltersProgrammable-' + vtk_version, 'vtkFiltersSelection-' + vtk_version, 'vtkFiltersSMP-' + vtk_version, 'vtkFiltersSources-' + vtk_version, 'vtkFiltersStatistics-' + vtk_version, 'vtkFiltersTexture-' + vtk_version, 'vtkFiltersVerdict-' + vtk_version, 'vtkGeovisCore-' + vtk_version, 'vtkgl2ps-' + vtk_version, 'vtkhdf5-' + vtk_version, 'vtkhdf5_hl-' + vtk_version, 'vtkImagingColor-' + vtk_version, 'vtkImagingCore-' + vtk_version, 'vtkImagingFourier-' + vtk_version, 'vtkImagingGeneral-' + vtk_version, 'vtkImagingHybrid-' + vtk_version, 'vtkImagingMath-' + vtk_version, 'vtkImagingMorphological-' + vtk_version, 'vtkImagingSources-' + vtk_version, 'vtkImagingStatistics-' + vtk_version, 'vtkImagingStencil-' + vtk_version, 'vtkInfovisCore-' + vtk_version, 'vtkInfovisLayout-' + vtk_version, 'vtkInteractionImage-' + vtk_version, 'vtkInteractionStyle-' + vtk_version, 'vtkInteractionWidgets-' + vtk_version, 'vtkIOAMR-' + vtk_version, 'vtkIOCore-' + vtk_version, 'vtkIOEnSight-' + vtk_version, 'vtkIOExodus-' + vtk_version, 'vtkIOExport-' + vtk_version, 'vtkIOGeometry-' + vtk_version, 'vtkIOImage-' + vtk_version, 'vtkIOImport-' + vtk_version, 'vtkIOInfovis-' + vtk_version, 'vtkIOLegacy-' + vtk_version, 'vtkIOLSDyna-' + vtk_version, 'vtkIOMINC-' + vtk_version, 'vtkIOMovie-' + vtk_version, 'vtkIONetCDF-' + vtk_version, 'vtkIOParallel-' + vtk_version, 'vtkIOParallelXML-' + vtk_version, 'vtkIOPLY-' + vtk_version, 'vtkIOSQL-' + vtk_version, 'vtkIOVideo-' + vtk_version, 'vtkIOXML-' + vtk_version, 'vtkIOXMLParser-' + vtk_version, 'vtkjsoncpp-' + vtk_version, 'vtkmetaio-' + vtk_version, 'vtkNetCDF-' + vtk_version, 'vtkoggtheora-' + vtk_version, 'vtkParallelCore-' + vtk_version, 'vtkproj4-' + vtk_version, 'vtkRenderingAnnotation-' + vtk_version, 'vtkRenderingContext2D-' + vtk_version, 'vtkRenderingCore-' + vtk_version, 'vtkRenderingFreeType-' + vtk_version, 'vtkRenderingGL2PSOpenGL2-' + vtk_version, 'vtkRenderingImage-' + vtk_version, 'vtkRenderingLabel-' + vtk_version, 'vtkRenderingLOD-' + vtk_version, 'vtkRenderingOpenGL-' + vtk_version, 'vtkRenderingVolume-' + vtk_version, 'vtkRenderingVolumeOpenGL-' + vtk_version, 'vtksqlite-' + vtk_version, 'vtksys-' + vtk_version, 'vtktiff-' + vtk_version, 'vtkverdict-' + vtk_version, 'vtkViewsContext2D-' + vtk_version, 'vtkViewsCore-' + vtk_version, 'vtkViewsInfovis-' + vtk_version, 'vtkzlib-' + vtk_version]
        # apt package?(vtk use OpenGL?)
        vtklibreleases = ['vtkalglib-' + vtk_version, 'vtkChartsCore-' + vtk_version, 'vtkCommonColor-' + vtk_version, 'vtkCommonComputationalGeometry-' + vtk_version, 'vtkCommonCore-' + vtk_version, 'vtkCommonDataModel-' + vtk_version, 'vtkCommonExecutionModel-' + vtk_version, 'vtkCommonMath-' + vtk_version, 'vtkCommonMisc-' + vtk_version, 'vtkCommonSystem-' + vtk_version, 'vtkCommonTransforms-' + vtk_version, 'vtkDICOMParser-' + vtk_version, 'vtkDomainsChemistry-' + vtk_version, 'vtkDomainsChemistryOpenGL2-' + vtk_version, 'vtkexoIIc-' + vtk_version, 'vtkFiltersAMR-' + vtk_version, 'vtkFiltersCore-' + vtk_version, 'vtkFiltersExtraction-' + vtk_version, 'vtkFiltersFlowPaths-' + vtk_version, 'vtkFiltersGeneral-' + vtk_version, 'vtkFiltersGeneric-' + vtk_version, 'vtkFiltersGeometry-' + vtk_version, 'vtkFiltersHybrid-' + vtk_version, 'vtkFiltersHyperTree-' + vtk_version, 'vtkFiltersImaging-' + vtk_version, 'vtkFiltersModeling-' + vtk_version, 'vtkFiltersParallel-' + vtk_version, 'vtkFiltersParallelImaging-' + vtk_version, 'vtkFiltersPoints-' + vtk_version, 'vtkFiltersProgrammable-' + vtk_version, 'vtkFiltersPython-' + vtk_version, 'vtkFiltersSelection-' + vtk_version, 'vtkFiltersSMP-' + vtk_version, 'vtkFiltersSources-' + vtk_version, 'vtkFiltersStatistics-' + vtk_version, 'vtkFiltersTexture-' + vtk_version, 'vtkFiltersTopology-' + vtk_version, 'vtkFiltersVerdict-' + vtk_version, 'vtkGeovisCore-' + vtk_version, 'vtkgl2ps-' + vtk_version, 'vtkglew-' + vtk_version, 'vtkImagingColor-' + vtk_version, 'vtkImagingCore-' + vtk_version, 'vtkImagingFourier-' + vtk_version, 'vtkImagingGeneral-' + vtk_version, 'vtkImagingHybrid-' + vtk_version, 'vtkImagingMath-' + vtk_version, 'vtkImagingMorphological-' + vtk_version, 'vtkImagingSources-' + vtk_version, 'vtkImagingStatistics-' + vtk_version, 'vtkImagingStencil-' + vtk_version, 'vtkInfovisCore-' + vtk_version, 'vtkInfovisLayout-' + vtk_version, 'vtkInteractionImage-' + vtk_version, 'vtkInteractionStyle-' + vtk_version, 'vtkInteractionWidgets-' + vtk_version, 'vtkIOAMR-' + vtk_version, 'vtkIOCore-' + vtk_version, 'vtkIOEnSight-' + vtk_version, 'vtkIOExodus-' + vtk_version, 'vtkIOExport-' + vtk_version, 'vtkIOExportOpenGL2-' + vtk_version, 'vtkIOGeometry-' + vtk_version, 'vtkIOImage-' + vtk_version, 'vtkIOImport-' + vtk_version, 'vtkIOInfovis-' + vtk_version, 'vtkIOLegacy-' + vtk_version, 'vtkIOLSDyna-' + vtk_version, 'vtkIOMINC-' + vtk_version, 'vtkIOMovie-' + vtk_version, 'vtkIONetCDF-' + vtk_version, 'vtkIOParallel-' + vtk_version, 'vtkIOParallelXML-' + vtk_version, 'vtkIOPLY-' + vtk_version, 'vtkIOSQL-' + vtk_version, 'vtkIOTecplotTable-' + vtk_version, 'vtkIOVideo-' + vtk_version, 'vtkIOXML-' + vtk_version, 'vtkIOXMLParser-' + vtk_version, 'vtklibharu-' + vtk_version, 'vtkmetaio-' + vtk_version, 'vtkoggtheora-' + vtk_version, 'vtkParallelCore-' + vtk_version, 'vtkproj4-' + vtk_version, 'vtkPythonInterpreter-' + vtk_version, 'vtkRenderingAnnotation-' + vtk_version, 'vtkRenderingContext2D-' + vtk_version, 'vtkRenderingContextOpenGL2-' + vtk_version, 'vtkRenderingCore-' + vtk_version, 'vtkRenderingFreeType-' + vtk_version, 'vtkRenderingGL2PS-' + vtk_version, 'vtkRenderingImage-' + vtk_version, 'vtkRenderingLabel-' + vtk_version, 'vtkRenderingLOD-' + vtk_version, 'vtkRenderingMatplotlib-' + vtk_version, 'vtkRenderingOpenGL2-' + vtk_version, 'vtkRenderingVolume-' + vtk_version, 'vtkRenderingVolumeOpenGL2-' + vtk_version, 'vtksqlite-' + vtk_version, 'vtksys-' + vtk_version, 'vtkverdict-' + vtk_version, 'vtkViewsContext2D-' + vtk_version, 'vtkViewsCore-' + vtk_version, 'vtkViewsInfovis-' + vtk_version, 'vtkWrappingTools-' + vtk_version]
    elif vtk_version == '8.1':
        # pcl_version 1.9.1
        # conda or build module, MacOS X
        vtklibreleases = ['vtkalglib-' + vtk_version, 'vtkChartsCore-' + vtk_version, 'vtkCommonColor-' + vtk_version, 'vtkCommonComputationalGeometry-' + vtk_version, 'vtkCommonCore-' + vtk_version, 'vtkCommonDataModel-' + vtk_version, 'vtkCommonExecutionModel-' + vtk_version, 'vtkCommonMath-' + vtk_version, 'vtkCommonMisc-' + vtk_version, 'vtkCommonSystem-' + vtk_version, 'vtkCommonTransforms-' + vtk_version, 'vtkDICOMParser-' + vtk_version, 'vtkDomainsChemistry-' + vtk_version, 'vtkDomainsChemistryOpenGL2-' + vtk_version, 'vtkexoIIc-' + vtk_version, 'vtkFiltersAMR-' + vtk_version, 'vtkFiltersCore-' + vtk_version, 'vtkFiltersExtraction-' + vtk_version, 'vtkFiltersFlowPaths-' + vtk_version, 'vtkFiltersGeneral-' + vtk_version, 'vtkFiltersGeneric-' + vtk_version, 'vtkFiltersGeometry-' + vtk_version, 'vtkFiltersHybrid-' + vtk_version, 'vtkFiltersHyperTree-' + vtk_version, 'vtkFiltersImaging-' + vtk_version, 'vtkFiltersModeling-' + vtk_version, 'vtkFiltersParallel-' + vtk_version, 'vtkFiltersParallelImaging-' + vtk_version, 'vtkFiltersPoints-' + vtk_version, 'vtkFiltersProgrammable-' + vtk_version, 'vtkFiltersPython-' + vtk_version, 'vtkFiltersSelection-' + vtk_version, 'vtkFiltersSMP-' + vtk_version, 'vtkFiltersSources-' + vtk_version, 'vtkFiltersStatistics-' + vtk_version, 'vtkFiltersTexture-' + vtk_version, 'vtkFiltersTopology-' + vtk_version, 'vtkFiltersVerdict-' + vtk_version, 'vtkGeovisCore-' + vtk_version, 'vtkgl2ps-' + vtk_version, 'vtkglew-' + vtk_version, 'vtkImagingColor-' + vtk_version, 'vtkImagingCore-' + vtk_version, 'vtkImagingFourier-' + vtk_version, 'vtkImagingGeneral-' + vtk_version, 'vtkImagingHybrid-' + vtk_version, 'vtkImagingMath-' + vtk_version, 'vtkImagingMorphological-' + vtk_version, 'vtkImagingSources-' + vtk_version, 'vtkImagingStatistics-' + vtk_version, 'vtkImagingStencil-' + vtk_version, 'vtkInfovisCore-' + vtk_version, 'vtkInfovisLayout-' + vtk_version, 'vtkInteractionImage-' + vtk_version, 'vtkInteractionStyle-' + vtk_version, 'vtkInteractionWidgets-' + vtk_version, 'vtkIOAMR-' + vtk_version, 'vtkIOCore-' + vtk_version, 'vtkIOEnSight-' + vtk_version, 'vtkIOExodus-' + vtk_version, 'vtkIOExport-' + vtk_version, 'vtkIOExportOpenGL2-' + vtk_version, 'vtkIOGeometry-' + vtk_version, 'vtkIOImage-' + vtk_version, 'vtkIOImport-' + vtk_version, 'vtkIOInfovis-' + vtk_version, 'vtkIOLegacy-' + vtk_version, 'vtkIOLSDyna-' + vtk_version, 'vtkIOMINC-' + vtk_version, 'vtkIOMovie-' + vtk_version, 'vtkIONetCDF-' + vtk_version, 'vtkIOParallel-' + vtk_version, 'vtkIOParallelXML-' + vtk_version, 'vtkIOPLY-' + vtk_version, 'vtkIOSQL-' + vtk_version, 'vtkIOTecplotTable-' + vtk_version, 'vtkIOVideo-' + vtk_version, 'vtkIOXML-' + vtk_version, 'vtkIOXMLParser-' + vtk_version, 'vtklibharu-' + vtk_version, 'vtkmetaio-' + vtk_version, 'vtknetcdfcpp-' + vtk_version, 'vtkoggtheora-' + vtk_version, 'vtkParallelCore-' + vtk_version, 'vtkproj4-' + vtk_version, 'vtkPythonInterpreter-' + vtk_version, 'vtkRenderingAnnotation-' + vtk_version, 'vtkRenderingContext2D-' + vtk_version, 'vtkRenderingContextOpenGL2-' + vtk_version, 'vtkRenderingCore-' + vtk_version, 'vtkRenderingFreeType-' + vtk_version, 'vtkRenderingGL2PSOpenGL2-' + vtk_version, 'vtkRenderingImage-' + vtk_version, 'vtkRenderingLabel-' + vtk_version, 'vtkRenderingLOD-' + vtk_version, 'vtkRenderingMatplotlib-' + vtk_version, 'vtkRenderingOpenGL2-' + vtk_version, 'vtkRenderingVolume-' + vtk_version, 'vtkRenderingVolumeOpenGL2-' + vtk_version, 'vtksqlite-' + vtk_version, 'vtksys-' + vtk_version, 'vtkverdict-' + vtk_version, 'vtkViewsContext2D-' + vtk_version, 'vtkViewsCore-' + vtk_version, 'vtkViewsInfovis-' + vtk_version, 'vtkWrappingTools-' + vtk_version]
    else:
        vtklibreleases = []

    for librelease in vtklibreleases:
        ext_args['libraries'].append(librelease)

    for flag in pkgconfig('--cflags-only-other'):
        if flag.startswith('-D'):
            macro, value = flag[2:].split('=', 1)
            ext_args['define_macros'].append((macro, value))
        else:
            ext_args['extra_compile_args'].append(flag)

    # clang?
    # https://github.com/strawlab/python-pcl/issues/129
    # gcc base libc++, clang base libstdc++
    # ext_args['extra_compile_args'].append("-stdlib=libstdc++")
    # ext_args['extra_compile_args'].append("-stdlib=libc++")
    if sys.platform == 'darwin':
        # not use gcc?
        # ext_args['extra_compile_args'].append("-stdlib=libstdc++")
        # clang(min : 10.7?/10.9?)
        # minimum deployment target of OS X 10.9
        ext_args['extra_compile_args'].append("-stdlib=libc++")
        ext_args['extra_compile_args'].append("-mmacosx-version-min=10.9")
        ext_args['extra_link_args'].append("-stdlib=libc++")
        ext_args['extra_link_args'].append("-mmacosx-version-min=10.9")
        # vtk error : not set override function error.
        ext_args['extra_compile_args'].append("-std=c++11")
        # mac os using openmp
        # https://iscinumpy.gitlab.io/post/omp-on-high-sierra/
        # before setting.
        # $ brew install libomp
        # ext_args['extra_compile_args'].append('-fopenmp -Xpreprocessor')
        # ext_args['extra_link_args'].append('-fopenmp -Xpreprocessor -lomp')
        pass
    else:
        ext_args['extra_compile_args'].append("-std=c++11")
        ext_args['library_dirs'].append("/usr/lib/x86_64-linux-gnu/")
        # gcc? use standard library
        # ext_args['extra_compile_args'].append("-stdlib=libstdc++")
        # ext_args['extra_link_args'].append("-stdlib=libstdc++")
        # clang use standard library
        # ext_args['extra_compile_args'].append("-stdlib=libc++")
        # ext_args['extra_link_args'].append("-stdlib=libc++")
        # using openmp
        # ext_args['extra_compile_args'].append('-fopenmp')
        # ext_args['extra_link_args'].append('-fopenmp')
        pass

    for flag in pkgconfig('--libs-only-l'):
        if flag == "-lflann_cpp-gd":
            print(
                "skipping -lflann_cpp-gd (see https://github.com/strawlab/python-pcl/issues/29")
            continue
        ext_args['libraries'].append(flag[2:])

    for flag in pkgconfig('--libs-only-L'):
        ext_args['library_dirs'].append(flag[2:])

    for flag in pkgconfig('--libs-only-other'):
        ext_args['extra_link_args'].append(flag)

    # grabber?
    # -lboost_system
    # ext_args['extra_link_args'].append('-lboost_system')
    # MacOSX?
    # ext_args['extra_link_args'].append('-lboost_system_mt')
    # ext_args['extra_link_args'].append('-lboost_bind')

    # Fix compile error on Ubuntu 12.04 (e.g., Travis-CI).
    ext_args['define_macros'].append(
        ("EIGEN_YES_I_KNOW_SPARSE_MODULE_IS_NOT_STABLE_YET", "1"))

    if pcl_version == '-1.6':
        module = [Extension("pcl._pcl", ["pcl/_pcl.pyx", "pcl/minipcl.cpp", "pcl/ProjectInliers.cpp"], language="c++", **ext_args),
                  # Extension("pcl.pcl_visualization", ["pcl/pcl_visualization.pyx"], language="c++", **ext_args),
                  Extension("pcl.pcl_visualization", ["pcl/pcl_visualization_160.pyx"], language="c++", **ext_args),
                  # Extension("pcl.pcl_grabber", ["pcl/pcl_grabber.pyx", "pcl/grabber_callback.cpp"], language="c++", **ext_args),
                  # debug
                  # gdb_debug=True,
                  ]
    elif pcl_version == '-1.7':
        module = [Extension("pcl._pcl", ["pcl/_pcl_172.pyx", "pcl/minipcl.cpp", "pcl/ProjectInliers.cpp"], language="c++", **ext_args),
                  Extension("pcl.pcl_visualization", ["pcl/pcl_visualization.pyx"], language="c++", **ext_args),
                  # Extension("pcl.pcl_grabber", ["pcl/pcl_grabber.pyx", "pcl/grabber_callback.cpp"], language="c++", **ext_args),
                  # debug
                  # gdb_debug=True,
                  ]
    elif pcl_version == '-1.8':
        module = [Extension("pcl._pcl", ["pcl/_pcl_180.pyx", "pcl/minipcl.cpp", "pcl/ProjectInliers.cpp"], language="c++", **ext_args),
                  Extension("pcl.pcl_visualization", ["pcl/pcl_visualization.pyx"], language="c++", **ext_args),
                  # Extension("pcl.pcl_grabber", ["pcl/pcl_grabber.pyx", "pcl/grabber_callback.cpp"], language="c++", **ext_args),
                  # debug
                  # gdb_debug=True,
                  ]
    elif pcl_version == '-1.9':
        module = [Extension("pcl._pcl", ["pcl/_pcl_190.pyx", "pcl/minipcl.cpp", "pcl/ProjectInliers.cpp"], language="c++", **ext_args),
                  Extension("pcl.pcl_visualization", ["pcl/pcl_visualization.pyx"], language="c++", **ext_args),
                  # Extension("pcl.pcl_grabber", ["pcl/pcl_grabber.pyx", "pcl/grabber_callback.cpp"], language="c++", **ext_args),
                  # debug
                  # gdb_debug=True,
                  ]
    else:
        print('no pcl install or pkg-config missed.')
        sys.exit(1)

    listDlls = []
    data_files = None


setup(name='python-pcl',
      description='Python bindings for the Point Cloud Library (PCL). using Cython.',
      url='http://github.com/strawlab/python-pcl',
      version='0.3.0rc1',
      author='John Stowers',
      author_email='john.stowers@gmail.com',
      maintainer='Tooru Oonuma',
      maintainer_email='t753github@gmail.com',
      license='BSD',
      packages=[
          "pcl",
          # "pcl.pcl_visualization",
      ],
      zip_safe=False,
      setup_requires=setup_requires,
      install_requires=install_requires,
      classifiers=[
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ],
      tests_require=['mock', 'nose'],
      ext_modules=module,
      cmdclass={'build_ext': build_ext},
      data_files=data_files
      )
