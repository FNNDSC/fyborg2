#
# FYBORG3000
#

# standard imports
import os, sys, subprocess, multiprocessing, time

# third-party imports
import dipy.align.aniso2iso as resampler
import nibabel

# fyborg imports
import config
from utility import Utility

class Registration():
  '''
  Registration steps and related actions.
  '''

  @staticmethod
  def resample( input_file, target_file, output_file, interpolation=0 ):
    '''
    Resample the input image to match the target image.
    
    input_file
      the input file path
    target_file
      the target file path
    output_file
      the output file path    
    '''
    # load the input image
    input_image = nibabel.load( input_file )

    # load the target image
    target_image = nibabel.load( target_file )

    # configure the zooms
    old_zooms = input_image.get_header().get_zooms()[:3]
    new_zooms = target_image.get_header().get_zooms()[:3]

    # .. and the affine
    affine = input_image.get_affine()
    # .. and header
    header = input_image.get_header()

    # resample the input to match the target
    resampled_data, new_affine = resampler.resample( input_image.get_data(), affine, old_zooms, new_zooms, interpolation )

    # save the resampled image
    klass = input_image.__class__
    nibabel.save( klass( resampled_data, new_affine, header ), output_file )


  @staticmethod
  def splitDiffusion( diffusion_file, output_directory ):
    '''
    Split a diffusion or other 4d image into its component images.
    
    diffusion_file
      the 4D input image
    output_directory
      the output directory to save the component images
    
    '''

    # load the diffusion image
    diffusion_image = nibabel.load( diffusion_file )
    diffusion_image_basename = os.path.basename( diffusion_file )
    diffusion_image_name = os.path.splitext( diffusion_image_basename )[0]
    diffusion_image_extension = os.path.splitext( diffusion_image_basename )[1]
    # check if we have a .nii.gz file
    if diffusion_image_extension == '.gz':
      diffusion_image_extension = '.nii.gz'
      diffusion_image_name = os.path.splitext(diffusion_image_name)[0]

    # split 4d diffusion image
    splitted_images = nibabel.four_to_three( diffusion_image )

    output_paths = []

    # save each of the splitted_images
    for number, image in enumerate( splitted_images ):
      
      component_output_path = os.path.join( output_directory, diffusion_image_name + str( number ) + diffusion_image_extension )
      print component_output_path
      nibabel.save( image, component_output_path )
      output_paths.append( component_output_path )

    # and return the file paths of the component images
    return output_paths


  @staticmethod
  def mergeDiffusion( diffusion_files, output_file ):
    '''
    Merge a list of diffusion files into one output_file.
    
    diffusion_files
      a list of diffusion file paths
    output_file
      the output file path
    '''

    diffusion_images = []

    # load all diffusion images
    for d in diffusion_files:
      diffusion_images.append( nibabel.load( d ) )

    # merge all diffusion images to one
    merged_image = nibabel.concat_images( diffusion_images )

    # store the image
    nibabel.save( merged_image, output_file )


  @staticmethod
  def register( input_file, target_file, output_directory ):
    '''
    Register the input image to match the target image using ANTs.
    
    input
      the input file path
    target
      the target file path
    output_directory
      the output directory
      
    The final output file is deformed.nii.gz in the output directory.
    '''

    #output_prefix = os.path.join( output_directory, os.path.splitext( os.path.basename( input_file ) )[0] )
    output_prefix = os.path.normpath(output_directory) + os.sep

    # configure the ANTs environment
    cmd = 'export ANTSPATH=' + config.ANTS_BIN_DIR + ';'
    # change to ouput directory
    cmd += 'cd ' + output_directory + ';'
    # run ants.sh
    cmd += '$ANTSPATH/ants.sh 3 ' + target_file + ' ' + input_file + ' ' + output_prefix
    sp = subprocess.Popen( ["/bin/bash", "-i", "-c", cmd], bufsize=0, stdout=sys.stdout, stderr=sys.stderr )
    sp.communicate()

  @staticmethod
  def warp( input_file, target_file, transform_file, output_file ):
    '''
    Warp an image using an existing transform.
    '''
    
    # configure the ANTs environment
    cmd = 'export ANTSPATH=' + config.ANTS_BIN_DIR + ';'
    # run ants.sh
    cmd += '$ANTSPATH/antsApplyTransforms -i ' + input_file + ' -r ' + target_file + ' -o ' + output_file + ' -t ' + transform_file + ' --interpolation NearestNeighbor'
    sp = subprocess.Popen( ["/bin/bash", "-i", "-c", cmd], bufsize=0, stdout=sys.stdout, stderr=sys.stderr )
    sp.communicate()
