# audacity_automate_ftp

Using an existing Audacity macro, this script downloads the newest file on a FTP site, opens it in Audacity, reads in the mp3, runs the macro, fixes the mangled ID3 tags, and uploads/overwrites the original file on the FTP site.

In Audacity, be sure to enable Preferences/Modules/mod-script-pipe and set an output directory in Preferences/Directories/Macro Output.

You must have the audacitypipetest.py file so it can be imported.

Relies heavily on work by:

The Audacity Pipe-Test: https://github.com/audacity/audacity/blob/master/scripts/piped-work/pipe_test.py

And this one: https://github.com/audacity/audacity/blob/master/scripts/piped-work/recording_test.py

And redditor /u/ColossalThrust: https://www.reddit.com/r/audacity/comments/rrecu7/audiobook_piping_script/
