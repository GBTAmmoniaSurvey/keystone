import os
import subprocess
import glob
import warnings
from astropy.time import Time
from . import catalogs
import numpy as np

def move_files(region='W3', session=81,
               prefix='W3_map_1_scan_29_76'):
    """
    Sometimes the pipeline fails to move the calibrated files into the proper 
    folder.

    move_files(region='Cepheus_L1251', session='81', prefix='Cepheus_L1251_map_1_scan_26_49')

    region : string
        Region name. The files will be moved to folders like 
        region+line_name (eg NGC1333_C2S).

    session : int
        Session number of the observations. This is added to the 
        original filename.

    prefix : string
        The prefix of files to be searched for.
    """
    folder=[ region+'_NH3_11',
             region+'_NH3_22',
             region+'_NH3_33',
             region+'_NH3_44',
             region+'_NH3_55',
             region+'_CH3OH_10_9',
             region+'_CH3OH_12_11',
             region+'_C2S_2_1',
             region+'_HNCO_1_0',
             region+'_H2O',
             region+'_HC5N_9_8',
             region+'_HC5N_8_7',
             region+'_HC7N_19_18']
    window=['0', '9', '10', '12', 
            '13', '6', '2', '5', 
            '3', '4', '11', '7', '1']
    for i in range(len(folder)):
        file_list=glob.glob('{0}*window{1}*fits'.format(prefix,window[i]))
        if len(file_list) > 0:
            for file_i in file_list:
                os.rename( file_i, '{0}/{1}'.format( folder[i],
                           file_i.replace('.fits', '_sess{0}.fits'.format(i))))

def fillAll(overwrite=False):
    """
    Function to fill in all raw-data into the format needed for the 
    GBT-pipeline.
    
    fillAll(overwrite=False)

    overwrite : bool
        If True it will overwrite files.
    """

    RawDir = '/lustre/pipeline/scratch/KEYSTONE/rawdata/'
    try:
        os.chdir(RawDir)
    except OSError:
        warnings.warn("fillAll() must be run on GB machines with access to lustre")
        return

    catalogs.updateLogs(release=release)
    log = catalogs.parseLog()
    uniqSess = set(log['Session'].data.data)
    for session in uniqSess:
        if not overwrite:
            SessionName = 'AGBT16B_278_{0}'.format(session)
            OutputDir = SessionName+'.raw.vegas'
            if not os.access(OutputDir,os.W_OK):
                command = 'sdfits -backends=vegas AGBT16B_278_{0}'.format(session)
                subprocess.call(command,shell=True)
                groupchange = 'chgrp gas -R '+OutputDir
                subprocess.call(groupchange,shell=True)
                permissions = 'chmod g+rw -R '+OutputDir
                subprocess.call(permissions,shell=True)
        else:
            SessionName = 'AGBT16B_278_{0}'.format(session)
            OutputDir = SessionName+'.raw.vegas'
            subprocess.call('rm -rf '+OutputDir,shell=True)
            command = 'sdfits -backends=vegas AGBT16B_278_{0}'.format(session)
            subprocess.call(command,shell=True)
            groupchange = 'chgrp gas -R '+OutputDir
            subprocess.call(groupchange,shell=True)
            permissions = 'chmod g+rw -R '+OutputDir
            subprocess.call(permissions,shell=True)

def reduceSession(session = 1, overwrite=False, release = 'all'):
    """
    Function to reduce all data using the GBT-pipeline.
    
    reduceAll(overwrite=False, release='all')

    release : string
        Variable that selects which set of data is to be reduced. 
        Default value is 'all', while 'DR1' generates the Data Release 1, and 
        hopefully 'DR2' will be available in the near future.
    overwrite : bool
        If True it will overwrite files.
    """
    catalogs.updateLogs(release=release)
    catalogs.updateCatalog(release=release)
    RegionCatalog = catalogs.GenerateRegions()
    Log = catalogs.parseLog()
    SessionRows = Log['Session'] == session
    Log = Log[SessionRows]
    uniqSrc = RegionCatalog['Region name']
    cwd = os.getcwd()
    for region in uniqSrc:
        if region != 'none':
            try:
                os.chdir(cwd+'/'+region)
            except OSError:
                os.mkdir(cwd+'/'+region)
                os.chdir(cwd+'/'+region)
            LogRows = Log['Region name'] == region
            if np.any(LogRows):
                wrapper(region=region, overwrite = overwrite,
                        release=release, obslog = Log,
                        startdate=Log[LogRows][0]['Date'],
                        enddate=Log[LogRows][0]['Date'])

                os.chdir(cwd)



def reduceAll(overwrite=False, release = 'all'):
    """
    Function to reduce all data using the GBT-pipeline.
    
    reduceAll(overwrite=False, release='all')

    release : string
        Variable that selects which set of data is to be reduced. 
        Default value is 'all', while 'DR1' generates the Data Release 1, and 
        hopefully 'DR2' will be available in the near future.
    overwrite : bool
        If True it will overwrite files.
    """
    catalogs.updateLogs(release=release)
    catalogs.updateCatalog(release=release)
    RegionCatalog = catalogs.GenerateRegions()
    Log = catalogs.parseLog()
    uniqSrc = RegionCatalog['Region name']
    cwd = os.getcwd()
    for region in uniqSrc:
        if region != 'none':
            try:
                os.chdir(cwd+'/'+region)
            except OSError:
                os.mkdir(cwd+'/'+region)
                os.chdir(cwd+'/'+region)
            wrapper(region=region, overwrite = overwrite,
                    release=release, obslog = Log)
            os.chdir(cwd)

def wrapper(logfile='ObservationLog.csv',region='W3',
            window=['8', '9', '10', '12', 
                    '13', '6', '2', '5', 
                    '3', '4', '11', '7', '1'],
            overwrite=False,startdate = '2015-01-1',
            enddate='2020-12-31',release='all',obslog = None):
    """
    This is the KEYSTONE pipeline which chomps the observation logs and
    then batch calibrates the data.  It requires AstroPy because
    their tables are pretty nifty.

    wrapper(logfile='../ObservationLog.csv',region='NGC1333',window=['3'])

    region : string
        Region name as given in logs
    window : list of strings
        List of spectral windows to calibrate
    logfile : string
        Full path to CSV version of the logfile (optional)
    obslog : astropy.Table
        Table representing an already parsed observation log
    overwrite : bool
        If True, carries out calibration for files already present on disk.
    startdate : string
        representation of date in format YYYY-MM-DD for beginning calibration
    enddate : string
        date in format YYYY-MM-DD for ending calibration
    release : string
        name of column in the log file that is filled with boolean
        values indicating whether a given set of scans belongs to the data
        release.
    If a logfile or obslog isn't specified, logs will be retrieved from Google.
    """
    StartDate = Time(startdate)
    EndDate = Time(enddate)
    if not os.access(logfile,os.R_OK):
        catalogs.updateLogs(release=release)

    if obslog is None:
        t = catalogs.parseLog(logfile=logfile)
    else:
        t = obslog

    for observation in t:
        print(observation['Date'])
        ObsDate = Time(observation['Date'])
        if (region == observation['Region name']) & \
                (ObsDate >= StartDate) & (ObsDate <= EndDate) & \
                (observation[release] == 'TRUE'):
            for thisWindow in window:
                if str(observation['Beam Gains']) == '--':
                    Gains = '1,1,1,1,1,1,1,1,1,1,1,1,1,1'
                else:
                    Gains = observation['Beam Gains']
                if str(observation['Special RawDir']) == '--':
                    doPipeline(SessionNumber=observation['Session'],
                               StartScan=observation['Start Scan'],
                               EndScan=observation['End Scan'],
                               Source=observation['Source'],
                               Gains=Gains,
                               Region=region,
                               Window=str(thisWindow),
                               overwrite=overwrite)
                else :
                    doPipeline(SessionNumber=observation['Session'],
                               StartScan=observation['Start Scan'],
                               EndScan=observation['End Scan'],
                               Source=observation['Source'],
                               Gains=Gains,
                               Region=region,
                               RawDataDir=observation['Special RawDir'],
                               Window=str(thisWindow),overwrite=overwrite)

def doPipeline(SessionNumber=1,StartScan = 11, EndScan=58,
               Source='Perseus_map_NGC1333-A', Window='0',
               Region = 'NGC1333', OptionDict = None,
               RawDataDir = None,
               Gains=None,
               OutputRoot = None, overwrite=False):
    """
    This is the basic KEYSTONE pipeline which in turn uses the gbt pipeline.
    """
    if RawDataDir is None:
        RawDataDir = '/lustre/pipeline/scratch/KEYSTONE/rawdata/'
    if Gains is None:
        Gains = '1,1,1,1,1,1,1,1,1,1,1,1,1,1'
    SessionDir = 'AGBT16B_278_'+str(SessionNumber).zfill(2)+'.raw.vegas/'
    BankNames = ['A','B','C','D','E','F','G','H']
    print('Reducing '+SessionDir)

    WindowDict = {'8':'NH3_11',   
                  '9':'NH3_22',   
                  '10':'NH3_33',   
                  '12':'NH3_44',   
                  '13':'NH3_55',   
                  '6':'CH3OH_10_9',
                  '2':'CH3OH_12_11',
                  '5':'C2S_2_1',
                  '3':'HNCO_1_0', 
                  '4':'H2O', 
                  '11':'HC5N_9_8',
                  '7':'HC5N_8_7', 
                  '1':'HC7N_19_18'}
                  
    # Set default pipeline options as a dictionary
    if OptionDict is None:
        OptionDict = {'--window':Window,
                      '--imaging-off':'',
                      '--clobber':'',
                      '-v':'4',
                      '-m':'{0}:{1}'.format(StartScan,EndScan),
                      '--units':'tmb',
                      '--smoothing-kernel-size':'0',
                      '--keep-temporary-files':'',
                      '--beam-scaling':Gains}
    if OutputRoot is None:
        OutputRoot = os.getcwd()+'/'
    # Try to make the output directory
    print('Region {0}'.format(Region))
    OutputDirectory = OutputRoot+Region+'_'+WindowDict[Window]
    if not os.access(OutputDirectory,os.W_OK):
        try:
            os.mkdir(OutputDirectory)
            print('Made directory {0}'.format(OutputDirectory))
        except:
            warnings.warn('Unable to make output directory '+OutputDirectory)
            raise

    for bank in BankNames:
        # Loop over each feed and polarization
        # we check if a pipeline call is necessary.
        for feed in ['0','1','2','3','4','5','6']:
            for pol in ['0','1']:
                FilesIntact = True
                if not overwrite:
                    outputfile = Source+'_scan_{0}_{1}_window{2}_feed{3}_pol{4}_sess{5}.fits'.\
                        format(StartScan,EndScan,Window,feed,pol,SessionNumber)
                    FilesIntact = FilesIntact and os.path.exists(OutputDirectory+'/'+outputfile)
                    if FilesIntact:
                        print('Data for Polarization {0} of Feed {1} appear on disk... skipping'.format(pol,feed))
                #
                if (not FilesIntact) or (overwrite):
                    InputFile = RawDataDir+SessionDir+'AGBT16B_278_'+\
                        str(SessionNumber).zfill(2)+\
                        '.raw.vegas.{0}.fits'.format(bank)
                    command = 'gbtpipeline -i '+InputFile
                    for key in OptionDict:
                        command = command+' '+key+' '+OptionDict[key]
                    command = command+' --feed '+feed+' --pol '+pol
                    print(command)
                    subprocess.call(command,shell=True)

                    indexname    = Source+'_scan_{0}_{1}_window{2}_feed{3}_pol{4}.index'.\
                        format(StartScan,EndScan,Window,feed,pol)
                    outindexname = Source+'_scan_{0}_{1}_window{2}_feed{3}_pol{4}_sess{5}.index'.\
                        format(StartScan,EndScan,Window,feed,pol,SessionNumber)
                    try:
                        os.rename(indexname,OutputDirectory+'/'+outindexname)
                    except:
                        pass

                    filename   = Source+'_scan_{0}_{1}_window{2}_feed{3}_pol{4}.fits'.\
                        format(StartScan,EndScan,Window,feed,pol)
                    outputfile = Source+'_scan_{0}_{1}_window{2}_feed{3}_pol{4}_sess{5}.fits'.\
                        format(StartScan,EndScan,Window,feed,pol,SessionNumber)
                    try:
                        os.rename(filename,OutputDirectory+'/'+outputfile)
                        os.chown(OutputDirectory+'/'+outputfile,0774)
                    except:
                        pass
                    
