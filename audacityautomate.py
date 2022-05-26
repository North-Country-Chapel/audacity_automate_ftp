import subprocess
import time


#opens Audacity and waits a few seconds so audcacitypipetest is happy.
#be sure to enable Preferences/Modules/mod-script-pipe in Audacity!

subprocess.Popen('C:\Program Files\Audacity\Audacity.exe')
time.sleep(5)




import audacitypipetest as pipe_test
import eyed3  #see: https://github.com/audacity/audacity/issues/1696 for why this is all necessary
import os
import shutil
import ftplib
from datetime import date


ftpServer = "ftp.server.com"
ftpUsername = "ftp_username"
ftpPassword = "ftp_password"

#Base path this all lives on
HomeDir = os.path.expanduser('~/Desktop')

# PATH is where downloaded files should go
PATH = HomeDir + '/FTP'
# Image location for ID3 tag
imagefile = HomeDir + '/ncmp3tag.png'
audacity_output_folder = HomeDir + '/macro-output'



# Open FTP server
ftp = ftplib.FTP(ftpServer)
ftp.login(ftpUsername, ftpPassword)

ftpDir = ftp.pwd()

#Get the latest file off FTP server
ftpFiles = list(ftp.mlsd())
ftpFiles.sort(key = lambda file: file[1]['modify'], reverse = True)
newestFile = ftpFiles[0][0]

#Download the file to PATH folder
os.chdir(PATH)

while not os.path.isfile(PATH + "/" + newestFile):
    ftp.retrbinary("RETR " + newestFile, open(newestFile, 'wb').write)

ftp.quit()    


# Audacity processing
def run_commands(INFILE):
    filename = ('"' + str(os.path.join(PATH, INFILE + '.mp3')) + '"')
    pipe_test.do_command(f"Import2: Filename={filename}") 
    pipe_test.do_command('Macro_cleanfileFTP:')


# Platform specific file name and file path.
while not os.path.isdir(PATH):
    PATH = os.path.realpath(input('Path to test folder: '))
    if not os.path.isdir(PATH):
        print('Invalid path. Try again.')


#Get files from folder
localFile = os.listdir(PATH)
for f in localFile:
    if f.endswith('mp3'):
        INFILE = f
        while not os.path.isfile(os.path.join(PATH, INFILE)):
            INFILE = input('Name of input mp3 file: ')
            INFILE = os.path.splitext(INFILE)[0] + '.mp3'
            if not os.path.isfile(os.path.join(PATH, INFILE)):
                print(f"{os.path.join(PATH, INFILE)} not found. Try again.")
            else:
                print(f"Input file: {os.path.join(PATH, INFILE)}")
        # Remove file extension.
        INFILE = os.path.splitext(INFILE)[0]
    
        # Get ID3 info
        audiofile = eyed3.load(os.path.join(PATH, INFILE + '.mp3'))
        if (audiofile.tag == None):
            audiofile.initTag()

        # Delete comments because they double up
        # https://github.com/nicfit/eyeD3/issues/111
        for comment in audiofile.tag.comments:

            audiofile.tag.comments.remove(comment.description)
    
        audiofile.tag.save()      

        year = audiofile.tag.recording_date
        comment = u"© Apply Within"
        albumartist = audiofile.tag.album_artist
        image = open(imagefile,"rb").read()

        # Apply the macro()
        run_commands(INFILE)  

        # Save ID3 tag info to the cleaned file 
        audiofile = eyed3.load(os.path.join(audacity_output_folder, INFILE + '.mp3'))
   
        audiofile.tag.recording_date = year
        audiofile.tag.comments.set(comment) 
        audiofile.tag.album_artist = albumartist
        audiofile.tag.images.set(3,image,"image/png",u"NCC logo") #https://tuxpool.blogspot.com/2013/02/how-to-store-images-in-mp3-files-using.html

        audiofile.tag.save()


# Close audacity
subprocess.call(["taskkill","/F","/IM","Audacity.exe"])
os.kill

#TODO: go to macro_output folder
#TODO: FTP upload and overwrite with new files

