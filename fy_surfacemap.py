#!/usr/bin/env python

#
# FYBORG3000
#

# standard imports
import glob, os, shutil, sys, tempfile

# fyborg imports
from _core import *


class FySurfaceMap():
  '''
  Map Freesurfer vertices to a TrackVis file.
  '''

  @staticmethod
  def run( input, brain, left_hemi, right_hemi, decimate, output, tempdir ):
    '''
    Runs the mapping stage.
    '''

    # validate inputs
    if not os.path.exists( input ):
      raise Exception( 'Could not find the input fibers file!' )

    if not os.path.exists( brain ):
      raise Exception( 'Could not find the input brain file!' )

    if not os.path.exists( left_hemi ):
      raise Exception( 'Could not find the input left hemisphere surface file!' )

    if not os.path.exists( right_hemi ):
      raise Exception( 'Could not find the input right hemisphere surface file!' )

    # use a temporary workspace
    # .. and copy all working files
    input_file = os.path.join( tempdir, os.path.basename( input ) )
    brain_file = os.path.join( tempdir, os.path.basename( brain ) )
    identity_matrix_file = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), 'identity.xfm' )
    left_hemi_file = os.path.join( tempdir, os.path.basename( left_hemi ) )
    left_hemi_nover2ras_file = left_hemi_file + '.nover2ras'
    left_hemi_splitext = os.path.splitext( left_hemi_file )
    left_hemi_decimate_file = os.path.join( tempdir, left_hemi_splitext[0] + '.decimated' + left_hemi_splitext[1] )
    left_hemi_inflate_file = os.path.join( tempdir, left_hemi_splitext[0] + '.decimated.inflated' )
    right_hemi_file = os.path.join( tempdir, os.path.basename( right_hemi ) )
    right_hemi_nover2ras_file = right_hemi_file + '.nover2ras'
    right_hemi_splitext = os.path.splitext( right_hemi_file )
    right_hemi_decimate_file = os.path.join( tempdir, right_hemi_splitext[0] + '.decimated' + right_hemi_splitext[1] )
    right_hemi_inflate_file = os.path.join( tempdir, right_hemi_splitext[0] + '.decimated.inflated' )

    print output, tempdir
    output_file = os.path.join( tempdir, os.path.basename( output ) )

    shutil.copy( input, input_file )
    shutil.copy( brain, brain_file )
    shutil.copy( left_hemi, left_hemi_file )
    shutil.copy( right_hemi, right_hemi_file )
    shutil.copy( left_hemi, left_hemi_decimate_file )
    shutil.copy( right_hemi, right_hemi_decimate_file )

    # 1. STEP: decimate the input surfaces
    # only performs decimation if decimation level is <1.0
    SurfaceMapping.decimate( left_hemi_file, decimate, left_hemi_decimate_file )
    SurfaceMapping.decimate( right_hemi_file, decimate, right_hemi_decimate_file )

    # 2. STEP: transform the decimated surfaces
    SurfaceMapping.transform( left_hemi_decimate_file, identity_matrix_file, left_hemi_nover2ras_file )
    SurfaceMapping.transform( right_hemi_decimate_file, identity_matrix_file, right_hemi_nover2ras_file )

    # 3. STEP: create inflated versions of the decimated and transformed surfaces
    SurfaceMapping.inflate( left_hemi_nover2ras_file, left_hemi_inflate_file )
    SurfaceMapping.inflate( right_hemi_nover2ras_file, right_hemi_inflate_file )

    # 4. STEP: map the vertices
    SurfaceMapping.map( input_file, brain_file, left_hemi_nover2ras_file, right_hemi_nover2ras_file, output_file, left_hemi_splitext[1].replace( '.', '' ) )

    # 5. STEP: copy data to the proper output places
    if float( decimate ) < 1.0:
      # if the surfaces were decimated, also copy them
      shutil.copy( left_hemi_decimate_file, os.path.dirname( output ) )
      shutil.copy( right_hemi_decimate_file, os.path.dirname( output ) )

    shutil.copy( left_hemi_inflate_file, os.path.dirname( output ) )
    shutil.copy( right_hemi_inflate_file, os.path.dirname( output ) )
    shutil.copyfile( output_file, output )

    return output, decimate, os.path.join( os.path.dirname( output ), os.path.basename( left_hemi_inflate_file ) ), os.path.join( os.path.dirname( output ), os.path.basename( right_hemi_inflate_file ) )

#
# entry point
#
if __name__ == "__main__":
  entrypoint = Entrypoint( description='Map Freesurfer vertices to a TrackVis file. Decimate surfaces on request and always create inflated surfaces as well. The scalar name is the file extension of the left hemisphere surface.' )

  entrypoint.add_input( 'i', 'input', 'The input TrackVis file.' )
  entrypoint.add_input( 'b', 'brain', 'The brain scan as the reference space.' )
  entrypoint.add_input( 'lh', 'left_hemi', 'The left hemisphere Freesurfer surface.' )
  entrypoint.add_input( 'rh', 'right_hemi', 'The right hemisphere Freesurfer surface.' )
  entrypoint.add_input( 'd', 'decimate', 'Surface decimation level to reduce the number of vertices. f.e. -d 0.333 reduces vertex count to 1/3. DEFAULT: 1.0 which means no decimation.', False, 1.0 )
  entrypoint.add_input( 'o', 'output', 'The output TrackVis file.' )

  options = entrypoint.parse( sys.argv )

  # attach a temporary environment
  tempdir = Utility.setupEnvironment()

  print '-' * 80
  print os.path.splitext( os.path.basename( __file__ ) )[0] + ' running..'

  if not options.verbose:
    sys.stdout = open( os.devnull, 'wb' )
    sys.stderr = open( os.devnull, 'wb' )

  a, c, d, e = FySurfaceMap.run( options.input, options.brain, options.left_hemi, options.right_hemi, options.decimate, options.output, tempdir )

  sys.stdout = sys.__stdout__
  sys.stderr = sys.__stderr__

  print 'Decimation Level: ', str( c )
  print 'Output mapped TrackVis file: ', a
  print 'Output inflated left hemisphere surface: ', d
  print 'Output inflated right hemisphere surface: ', e
  print 'Done!'
  print '-' * 80

  # clean up temporary environment
  Utility.teardownEnvironment( tempdir )
