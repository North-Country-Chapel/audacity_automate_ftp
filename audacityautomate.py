import subprocess
import time
import os


#opens Audacity and waits a few seconds so audcacitypipetest is happy.
#be sure to enable Preferences/Modules/mod-script-pipe in Audacity!

subprocess.Popen('C:\Program Files\Audacity\Audacity.exe')
time.sleep(5)



import pipeclient
#import audacitypipetest as pipe_test
import eyed3  #see: https://github.com/audacity/audacity/issues/1696 for why this is all necessary
import os
import random
import ftplib



ftpServer = os.environ.get('FTP_MP3_SERVER')
ftpUsername = os.environ.get('FTP_MP3_USERNAME')
ftpPassword = os.environ.get('FTP_MP3_PASSWORD')

#Base path this all lives on
HomeDir = os.path.expanduser('~/Documents')

# Where downloaded files should go
PATH = HomeDir + '/FTP'
# Image location for ID3 tag
imagefile = HomeDir + '/ncmp3tag.png'
# Folder that audacity macros output to
audacity_output_folder = HomeDir + '/macro-output'
client = pipeclient.PipeClient()

# Create a random filename for the Exit2 workaround
rnum = random.randint(1000, 9999)
savename = PATH + "/" + str(rnum) + '.aup3'
count = 0


# Open FTP server
ftp = ftplib.FTP(ftpServer)
ftp.login(ftpUsername, ftpPassword)

ftpDir = ftp.pwd()

#Get the latest file off FTP server
ftpFiles = list(ftp.mlsd())
ftpFiles.sort(key = lambda file: file[1]['modify'], reverse = True)

newestFile = ftpFiles[count][0]

# Make sure newestFile is an mp3
while not newestFile.endswith('mp3') and count < len(ftpFiles):
    count += 1
    newestFile = ftpFiles[count][0]

#Download the file to PATH folder
os.chdir(PATH)

ftp.retrbinary("RETR " + newestFile, open(newestFile, 'wb').write)


# Audacity processing
def run_commands(INFILE):
    filename = ('"' + str(os.path.join(PATH, INFILE + '.mp3')) + '"')
    
    client.write(f"Import2: Filename={filename}", timer=True)
    client.write("Macro_cleanfile:")

    # This is a workaround until Exit2 is added to Audacity. 
    # See https://forum.audacityteam.org/viewtopic.php?p=440395#p440395
    client.write("NewMonoTrack:")
    client.write("Macro_exitworkaround:")
    client.write(f'SaveProject2:AddToHistory="0" Filename="{savename}"')
    client.write("Exit:")


#Get files from folder
localFile = os.listdir(PATH)
for f in localFile:
    if f.endswith('mp3'):
        INFILE = f
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

        # Workaround python moving on before Audacity finishes processing
        # TODO: loop to check on macro-output file creation
        time.sleep(300)

        # Save ID3 tag info to the cleaned file 
        audiofile = eyed3.load(os.path.join(audacity_output_folder, INFILE + '.mp3'))
   
        audiofile.tag.recording_date = year
        audiofile.tag.comments.set(comment) 
        audiofile.tag.album_artist = albumartist
        audiofile.tag.images.set(3,image,"image/png",u"NCC logo") #https://tuxpool.blogspot.com/2013/02/how-to-store-images-in-mp3-files-using.html

        audiofile.tag.save()

# It all moves too fast for os.remove if you don't wait
time.sleep(10)
os.remove(savename)


# Go to Audacity output folder
os.chdir(audacity_output_folder)

# Upload any mp3s in that folder. If no errors are thrown, delete files so they don't get processed next time.
for f in os.listdir(audacity_output_folder):
    if f.endswith(".mp3"):
        newestFile = f
        try:
            open(audacity_output_folder + "/" + newestFile, "rb")
            ftp.storbinary("STOR " + newestFile, open(newestFile, "rb", 1024))
        except: 
            print("FTP failed")   
        else:    
            os.remove(audacity_output_folder + "/" + newestFile)
            os.remove(PATH + "/" + newestFile)
    

ftp.quit()    
