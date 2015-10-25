# futurelearn-dl

An early Python3ic attempt at automating downloads from the FutureLearn website (for enrolled courses).

There are no doubt problems with this, but it seems to work on my initial tests

**TESTED**: Tested on Windows 8 under Cygwin, using Anaconda Python3.  Should work for other installations ... YMMV

## futurelearn-dl.py:

First attempt at a Python3 version.

Currently succeeds to obtain authenticity_token and to login using this token.

It then 
- downloads the appropriate course page
- downloads each 'week' page for the course
- downloads each 'step' page for each week of the course
- finds downloadabls urls (pdf and mp4 for the moment) in each 'step' page
- it chooses a filename (not a meaningful one for mp4) and downloads to that file
  - skips already downloaded files
  - it skips the file if it contains "request signature": seems to indicate a video file which isn't available yet

## TEST_futurelearn-dl.py.sh:

This is simply a template for calling futurelearn-dl.py.

Put your email, password and course_id as arguments within this file

## Usage:
'''
    futurelearn-dl.py <username> <password> <course_id> <course_run>[<week_num>]

e.g.

for run 1 of data-to-insight

    futurelearn-dl.py  user password data-to-insight 1

or to get just week1:

    futurelearn-dl.py  user password data-to-insight 1 1
   
'''

**Note**: To override the temp file directory
    export TMP_DIR=/tmp

**Note**: To override the output file root directory
    export OP_DIR=/e/Education/FUTURELEARN

**Note**: Under cygwin, Anaconda I needed to set in the form <DRIVE:/path> e.g.
    export OP_DIR=e:/Education/FUTURELEARN

## TODO:
- Fix unicode errors
- Extend to more download types
- Lots more ...

