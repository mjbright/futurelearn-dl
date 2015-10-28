#!/bin/bash 

COURSE_ID="MyCourse"
COURSE_RUN=1
COURSEDIR=/e/Education/FUTURELEARN/$COURSE_ID

export TMP_DIR=~/tmp/FUTURELEARN_DL
export OP_DIR=~/Education/FutureLearn

export FL_DEBUG=False
export FL_VERBOSE=1

./futurelearn-dl.py YOUR_LOGIN YOUR_PASSWORD $COURSE_ID $COURSE_RUN [<WEEK_NUM>]

if [ $? -eq 0 ];then
    find $COURSEDIR -type f -exec ls -altr {} \;
else
    echo "Look for new files with - find $COURSEDIR -type f -exec ls -altr {} \\;"
fi




# e.g.
# for course run 1 of data-to-insight:
#
#    ./futurelearn-dl.py joe joespass data-to-insight 1
#
# or to download just week1:
#    ./futurelearn-dl.py joe joespass data-to-insight 1 1


