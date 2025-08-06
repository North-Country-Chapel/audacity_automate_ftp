import subprocess
import time
import os
import eyed3  #see: https://github.com/audacity/audacity/issues/1696 for why this is all necessary
import random
import ftplib
import logging
import logging.config
from logging_config import setup_logging
from datetime import datetime

ftpServer = os.environ.get('FTP_MP3_SERVER')
ftpUsername = os.environ.get('FTP_MP3_USERNAME')
ftpPassword = os.environ.get('FTP_MP3_PASSWORD')

#Base path this all lives on
HomeDir = os.path.expanduser('~/Documents')

# Configure logging
logger = setup_logging(
    config_path='logging_config.json',
    fluentd_host='10.10.0.81'
)

# Where downloaded files should go
PATH = HomeDir + '/FTP'
# Image location for ID3 tag
imagefile = HomeDir + '/ncmp3tag.png'
# Folder that processed files output to (was audacity_output_folder)
output_folder = HomeDir + '/FTP/macro-output'

logger.info("Starting audio processing script (Linux version)")

count = 0

# Open FTP server
logger.info("Connecting to FTP server...")
ftp = ftplib.FTP(ftpServer)
ftp.login(ftpUsername, ftpPassword)
logger.info("Successfully connected to FTP server")

ftpDir = ftp.pwd()

#Get the latest file off FTP server
logger.info("Retrieving file list from FTP server...")
ftpFiles = list(ftp.mlsd())
ftpFiles.sort(key = lambda file: file[1]['modify'], reverse = True)

newestFile = ftpFiles[count][0]

# Make sure newestFile is an mp3
while not newestFile.endswith('mp3') and count < len(ftpFiles):
    count += 1
    newestFile = ftpFiles[count][0]

logger.info(f"Found newest MP3 file: {newestFile}")

#Download the file to PATH folder
os.chdir(PATH)
logger.info(f"Downloading {newestFile}...")
ftp.retrbinary("RETR " + newestFile, open(newestFile, 'wb').write)
logger.info(f"Successfully downloaded {newestFile}")

# FFmpeg processing function (replaces Audacity)
def process_audio_ffmpeg(input_file, output_file):
    """Process audio file with FFmpeg: normalize and convert to 64k MP3"""
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-filter:a', 'loudnorm=I=-16:TP=-1.5:LRA=7',
        '-codec:a', 'libmp3lame',
        '-b:a', '64k',
        '-y',  # Overwrite output file if it exists
        output_file
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg processing failed: {e}")
        return False

#Get files from folder and process them
logger.info("Processing downloaded files...")
localFile = os.listdir(PATH)
for f in localFile:
    if f.endswith('mp3'):
        INFILE = f
        INFILE_NO_EXT = os.path.splitext(INFILE)[0]
        
        input_path = os.path.join(PATH, INFILE)
        output_path = os.path.join(output_folder, INFILE)  # Keep same filename
        
        logger.info(f"Processing file: {INFILE}")
    
        # Get ID3 info from original file
        audiofile = eyed3.load(input_path)
        if (audiofile.tag == None):
            audiofile.initTag()

        # Delete comments because they double up
        # https://github.com/nicfit/eyeD3/issues/111
        for comment in audiofile.tag.comments:
            audiofile.tag.comments.remove(comment.description)
    
        audiofile.tag.save()      
        
        # Store metadata for later
        year = audiofile.tag.recording_date
        comment = u"© Apply Within"
        albumartist = audiofile.tag.album_artist
        image = open(imagefile,"rb").read()

        # Process with FFmpeg instead of Audacity
        logger.info(f"Starting FFmpeg processing for {INFILE}...")
        success = process_audio_ffmpeg(input_path, output_path)
        
        if success:
            logger.info(f"Successfully processed {INFILE}")
            
            # Apply ID3 tag info to the processed file 
            processed_audiofile = eyed3.load(output_path)
            if processed_audiofile.tag is None:
                processed_audiofile.initTag()
       
            processed_audiofile.tag.recording_date = year
            processed_audiofile.tag.comments.set(comment) 
            processed_audiofile.tag.album_artist = albumartist
            processed_audiofile.tag.images.set(3, image, "image/png", u"NCC logo")

            processed_audiofile.tag.save()
            logger.info(f"Applied metadata to {INFILE}")
        else:
            logger.error(f"Failed to process {INFILE}")

# Go to output folder
os.chdir(output_folder)

# Upload any mp3s in that folder. If no errors are thrown, delete files so they don't get processed next time.
logger.info("Uploading processed files to FTP server...")
for f in os.listdir(output_folder):
    if f.endswith(".mp3"):
        processed_file = f
        logger.info(f"Uploading {processed_file}...")
        try:
            with open(os.path.join(output_folder, processed_file), "rb") as file:
                ftp.storbinary("STOR " + processed_file, file)
            logger.info(f"Successfully uploaded {processed_file}")
        except Exception as e: 
            logger.error(f"FTP upload failed for {processed_file}: {e}")   
        else:    
            # Clean up files after successful upload
            os.remove(os.path.join(output_folder, processed_file))
            os.remove(os.path.join(PATH, processed_file))
            logger.info(f"Cleaned up local files for {processed_file}")
    
ftp.quit()
logger.info("Audio processing script completed successfully")
