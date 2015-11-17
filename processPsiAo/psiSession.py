import os
import logging
import glob
import re
import csv

logger = logging.getLogger(__name__)

def getRecordings(srcFolder,type='SLO'):
    """Get a list of videos from a session folder
    Returns [{filename,eye,index,timestamp}]"""
    if type is 'SLO':
        baseMask = 'SLO_refl_video'
    else:
        logger.warning('type {} not supported'.format(type))
        return
    
    files = glob.glob(os.path.join(srcFolder,baseMask + '*.avi'))
    if not files:
        logger.warning('No {} files found in folder {}'
                       .format(type,srcFolder))
        return
    else:
        logger.info('{} files found in folder {}'
                    .format(len(files),srcFolder))
        
    regex = re.compile('(SLO_refl_video.*(OD|OS).*(\d{1}).*(\d{6})).*')
    output = [{'filename':m.group(1),
               'eye':m.group(2),
               'index':m.group(3),
               'timestamp':m.group(4)}
              for m in [re.search(regex,file) for file in files]]

    return output

def getImagingFileInfo(srcDir, file):
    """Extracts the imaging info from the TSLO_info and SLO_info files
    file should be a dict object with fields {timestamp,eye,index}"""
    reTslo = {'fix_x': re.compile('x pos \[deg\]\s*([-]?\d+.\d+)'),
              'fix_y': re.compile('y pos \[deg\]\s*([-]?\d+.\d+)')}
    
    reSlo = {'scanSize_x': re.compile('H size \[deg\]\s*([-]?\d+.\d+)'),
             'scanSize_y': re.compile('V size \[deg\]\s*([-]?\d+.\d+)'),
             'scanPos_x': re.compile('H offset \[deg\]\s*([-]?\d+.\d+)'),
             'scanPos_y': re.compile('V offset \[deg\]\s*([-]?\d+.\d+)')}    
    
    sloInfoPath = 'SLO_info__{}_{}_{}.txt'.format(file['eye'],
                                                  file['index'],
                                                  file['timestamp'])
    tsloInfoPath = 'TSLO_info__{}_{}_{}.txt'.format(file['eye'],
                                                    file['index'],
                                                    file['timestamp'])    
    
    try:
        tsloFile = open(os.path.join(srcDir,tsloInfoPath),'r')
    except IOError:
        logger.error('unable to open TSLO info File {} in folder'
                     .format(tsloInfoPath,srcDir))
        return
    
    try:
        sloFile = open(os.path.join(srcDir,sloInfoPath),'r')
    except IOError:
        logger.error('unable to open SLO info File {} in folder'
                     .format(sloInfoPath,srcDir))
        return
    
    output = {}
    for line in tsloFile:
        for key,expr in reTslo.items():
            match = re.search(expr,line)
            if match:
                output[key] = float(match.group(1))
    tsloFile.close()

    for line in sloFile:
        for key,expr in reSlo.items():
            match = re.search(expr,line)
            if match:
                output[key] = float(match.group(1))
    sloFile.close()
    
    #flatten the keys
    idx = [item for keys in [reTslo.keys(),reSlo.keys()] for item in keys]
    for key in idx:
        if key not in output.keys():
            logger.warning('Value not found for {} in file {}'.format(key,sloInfoPath))
            
    #invert the scan location x and y coordinates, they are wrong in the info files
    output['scanPos_x'], output['scanPos_y'] = output['scanPos_y'], output['scanPos_x']
    # convert to retinal coordinates here
    output['ret_x'] = output['fix_x'] + output['scanPos_x']
    output['ret_y'] = output['fix_y'] + (0 - output['scanPos_y'])
    if output['ret_x'] > 0:
        output['hemi_x'] = 'T'
    elif output['ret_x'] < 0:
        output['hemi_x'] = 'N'
    else:
        output['hemi_x'] = None
        
    if output['ret_y'] > 0:
        output['hemi_y'] = 'S'
    elif output['ret_y'] < 0:
        output['hemi_y'] = 'I'
    else:
        output['hemi_y'] = None
        
    return output

def getImagingSessionInfo(srcFolder,recType='SLO'):
    """Process the data from an imaging session,
    write the scan locations to a file if requested"""
    if recType not in ['SLO']:
        logger.error('Processing recordings of type:{} not supported.'.format(recType))
        return
    
    recordings = getRecordings(srcFolder, type=recType)
    recordingCoords = []
    for recording in recordings:
        coordinates = getImagingFileInfo(srcFolder, recording)
        coordinates['filename'] = recording['filename']
        coordinates['eye'] = recording['eye']
        coordinates['timestamp'] = recording['timestamp']
        recordingCoords.append(coordinates)
    return recordingCoords