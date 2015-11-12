import os
import logging
import glob

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
    reTslo = {'fix_x': re.compile('x pos \[deg\].s*(\d.\d+)'),
              'fix_y': re.compile('y pos \[deg\]\s*(\d.\d+)')}
    
    reSlo = {'scanSize_x': re.compile('H size \[deg\]\s*(\d+.\d+)'),
             'scanSize_y': re.compile('V size \[deg\]\s*(\d+.\d+)'),
             'scanPos_x': re.compile('H offset \[deg\]\s*(\d+.\d+)'),
             'scanPos_y': re.complie('V offset \[deg\]\s*(\d+.\d+)')}    
    
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
        if not output[key]:
            logger.warning('Value not found for {} in file {}').format(key,sloInfoPath)
            
    # TODO: convert to retinal coordinates here
    return output

def getImageingSessionInfo(srcFolder,recType,outFile=None,append=False):
    """Process the data from an imaging session,
    write the scan locations to a file if requested"""
    if recType not in ['SLO']:
        logger.error('Processing recordings of type:{} not supported.'.format(recType))
    if outfile:
        try:
            if append:
                outfile = open(outFile,'w+')
            else:
                outfile = open(outFile,'w')
        except IOError:
            logger.error('Could not open file:{} for writing'.format(outfile))
            
    if not append:
        f.write('Filename,Type,Timestamp,Eye,Index,ScanSizeX,ScanSizeY,XPos,YPos')
    
    recordings = getRecordings(srcFolder, type=recType)
    for recording in recordings:
        coordinates = getImagingFileInfo(srcFolder, recording)
        
    
        