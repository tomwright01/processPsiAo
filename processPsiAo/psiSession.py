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
