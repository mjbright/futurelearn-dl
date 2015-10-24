# futurelearn-dl

An early attempt at automating downloads from the FutureLearn website (for enrolled courses).

There are currently 2 attempts:
- futurelearn_dl.sh: This script fails to login
- futurelearn_dl.py: This script successfully logs in ... more functionality to be implemented

## futurelearn-dl.py:

First attempt at a Python3 version.

Currently succeeds to obtain authenticity_token and to login using this token.

## TEST_futurelearn-dl.py.sh:

This is simply a template for calling futurelearn-dl.py.

Put your email, password and course_id as arguments within this file

## futurelearn-dl.sh:

**NOTE:** This does not work, it's a horrible hack,
I'm throwing this out there because people have requested it and because I need it myself
(but don't have the time to invest right now).

**NOTE:** I did not write the original script, I adapted a script which was posted as a Gist here:
  https://gist.github.com/nonsleepr/11401542

This is currently a bash script and even the initial login is failing - although we seem to obtain a valid token.

## Usage:
'''
    futurelearn-dl.sh  <course-id> <username> <password>

e.g.

    futurelearn-dl.sh  data-to-insight user password
   
'''

## TODO:
- Fix ;-)
- Rewrite in a real language such as Python3 ... now started ...
- Abandon bash script ... (but I leave the code here in case someone wants to run with it)

