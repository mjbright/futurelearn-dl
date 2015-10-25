# futurelearn-dl

An early Python3ic attempt at automating downloads from the FutureLearn website (for enrolled courses).

## futurelearn-dl.py:

First attempt at a Python3 version.

Currently succeeds to obtain authenticity_token and to login using this token.

It then 
- downloads the appropriate course page
- downloads each 'week' page for the course
- downloads each 'step' page for each week of the course
- finds downloadabls urls (pdf and mp4 for the moment) in each 'step' page

## TEST_futurelearn-dl.py.sh:

This is simply a template for calling futurelearn-dl.py.

Put your email, password and course_id as arguments within this file

## Usage:
'''
    futurelearn-dl.py  <course-id> <username> <password>

e.g.

    futurelearn-dl.py  data-to-insight user password
   
'''

## TODO:
- Actually download files!!
- Fix unicode errors
- Extend to more download types
- Lots more ...

