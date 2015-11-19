import csv
import argparse
import logging
import os
import sys
import tempfile
import shutil
import processPsiAo.psiSession as psiSession
import AoRecording as AoRecording
import StackTools as StackTools

logger = logging.getLogger(__name__)

def writeLocations(srcDir,outfile,overwrite=True):
    """Extract the recording locations and write to a csv file"""
    try:
        if overwrite:
            f = open(outfile,'w')
        else:
            f = open(outfile,'w+')
    except IOError as e:
        logger.error('Could not open file:{} for writing. {}'.format(outfile,e))

    recordingCoords = psiSession.getImagingSessionInfo(srcDir)
        
    csv_writer = csv.DictWriter(f,
                                delimiter=',',
                                fieldnames=recordingCoords[0].keys())
    if overwrite:
        csv_writer.writeheader()
        
    for row in recordingCoords:
        csv_writer.writerow(row)

    f.close()

def alignSloFile(srcDir, fileInfo, outDir, moveLocal, writeStabilised, genFrames):
    # copy the file to a temporary location
    sourceFile = os.path.join(srcDir,fileInfo['filename'] + '.avi')
    if moveLocal:
        logger.info('Copying file {}'.format(sourceFile))
        workDir = tempfile.mkdtemp()
        shutil.copy(sourceFile,
                    workDir)
        workingFile = os.path.join(workDir,fileInfo['filename'] + '.avi')
        workingOutDir = os.path.join(workDir,fileInfo['timestamp'])
        try:
            os.mkdir(workingOutDir)
        except OSError as e:
            if e.errno == 17:
                # already exists
                pass
            else:
                logger.error('Failed to create temporary output dir {}. {}'.format(workingOutDir,e))
                return
                
        logger.info('Copied file {} to {}'.format(sourceFile, workingFile))
    else:
        workingFile = sourceFile
        workingOutDir = os.path.join(outDir, fileInfo['timestamp'])
        try:
            os.mkdir(workingOutDir)
        except OSError as e:
            if e.errno == 17:
                # already exists
                pass
            else:
                logger.error('Failed to create output dir {}. {}'.format(workingOutDir,e))
                return
    
    # process the file
    logger.info('Starting work on file:{}'.format(workingFile))
    vid = AoRecording.AoRecording(filepath = workingFile)
    vid.load_video()

    try:
        logger.info('Filtering frames')
        vid.filter_frames()
        logger.info('Fixed aligning frames')
        vid.fixed_align_frames()        
    except RuntimeError as e:
        logger.warning('Error filtering frames):{}'.format(e))
        shutil.rmtree(workDir)
        return

    logger.info('Performing complete align')
    #vid.complete_align_parallel()
    try:
        vid.complete_align_parallel()
    except:
        logger.warning('Alignment failed')

    if writeStabilised:
        logger.info('Writing stabalised movie')
        vid.write_video(os.path.join(workingOutDir,
                                     fileInfo['filename'] + '_stabalised.avi'))
    if genFrames:
        logger.info('Generating frames')
        vid.create_average_frame('mean')
        vid.write_frame(os.path.join(workingOutDir,
                                     fileInfo['filename'] + 'mean.png'),
                        'average')
        try:
            vid.create_average_frame('lucky')
            vid.write_frame(os.path.join(workingOutDir,
                                 fileInfo['filename'] + 'lucky.png'),
                            'average')
        except ValueError:
            logger.warning('Lucky frame not calculated')
        
        try:
            vid.create_stdev_frame()
            vid.write_frame(os.path.join(workingOutDir,
                                         fileInfo['filename'] + 'stdev.png'),
                            'stdev')
        except ValueError:
            logger.warning('Stdev frame not calculated')
        
    if moveLocal:
        try:
            shutil.move(workingOutDir, outDir)
            shutil.rmtree(workDir)
        except shutil.Error as e:
            logger.error('Failed copying temp dir {} to {}.{}'.format(workingOutDir,outDir,e))
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Process a PSI AO recording session')
    parser.add_argument("sourceDir", help="Directory to process")
    parser.add_argument('-o','--outDir', help="""Path to store output files, 
    we will try to create this if id doesn't exist.""")
    parser.add_argument('--overwrite', help="overwrite existing files", action="store_true")
    parser.add_argument('-v','--verbosity',help='Increase the amount of output', action='count')
    parser.add_argument('--moveLocal', help='Move files to a local directory for processing', action="store_true")
    parser.add_argument('--writeStable', help='Write the stabalised movie to outDir', action="store_true")
    parser.add_argument('--writeFrames', help='Write the average frames to outDir', action="store_true")
    args = parser.parse_args()

    # setup logging
    if args.verbosity >=3:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbosity == 2:
        logging.basicConfig(level=logging.INFO)
    elif args.verbosity == 1:
        logging.basicConfig(level=logging.WARNING)
    else: 
        logging.basicConfig(level=logging.ERROR)
    logger=logging.getLogger()
    logger.info('started')
    # check the source dir exists    
    if not os.path.isdir(args.sourceDir):
        logger.error('Could not access source directory {}'.format(args.sourceDir))
        sys.exit()
    
    # check the outdir exists
    if args.outDir:
        try:
            os.mkdir(args.outDir)
        except OSError as e:
            if e.errno == 17:
                #already exists
                pass
            else:
                logger.error('Failed to create output dir {}. {}'.format(args.outDir,e))
            
    if args.outDir:
        writeLocations(args.sourceDir,
                       os.path.join(args.outDir,'locations.csv'),
                       args.overwrite)
    else:
        print psiSession.getImagingSessionInfo(args.sourceDir)
        

    #now align the files
    recordings = psiSession.getRecordings(args.sourceDir)
    #for recording in recordings[0]:
    for recording in recordings:
        alignSloFile(args.sourceDir,
                     recording,
                     args.outDir,
                     args.moveLocal, 
                     args.writeStable, 
                     args.writeFrames)
    