#!/bin/bash

# Downloaded 2014-Aug-13 from:
#   https_proxy=web-proxy:8080 wget -O futurelearn-dl.sh 'https://gist.githubusercontent.com/nonsleepr/11401542/raw/aed0845b3df52c728cd42659f84c69afb0182e7a/futurelearn_dl.sh'

TMP_DIR=$HOME/tmp/ED_FUTURELEARN
OP_DIR=/e/ED_FUTURELEARN

[ ! -d $TMP_DIR ] && mkdir -p $TMP_DIR
[ ! -d $OP_DIR ]  && mkdir -p $OP_DIR

COOKIES_TXT=$TMP_DIR/cookies.txt

USER_AGENT="--user-agent 'Mozilla/4.0'"
USER_AGENT="--user-agent 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36'"
USER_AGENT="--user-agent 'Mozilla/5.0 (X11; Linux x86_64)'"
#USER_AGENT=""
USER_AGENT="--user-agent 'Mozilla/5.0'"

SIGNIN_URL='https://www.futurelearn.com/sign-in'

#
# Usage:
#    > futurelearn_dl.sh login@email.com password course-name week-id
#
# Where *login@email.com* and *password* - your credentials
# ,*course-name* is the name from URL
# and *week-id* is the ID from the URL
#
# E.g. To download all videos from the page: https://www.futurelearn.com/courses/corpus-linguistics/todo/238
# Execute following command:
#    > futurelearn_dl.sh login@email.com password corpus-linguistics 238
#

VERBOSE=0
VERBOSE=1

PAUSE=0
#PAUSE=1

SETX=0

################################################################################
# Functions:

#############################
#
# Function: die
#
# - Yes I'm a Perl refugee ...
#
function die {
    echo "$0: die - $*" >&2
    exit 1
}

[ ! -d $OP_DIR ]  && die "Failed 'mkdir -p $OP_DIR'"
[ ! -d $TMP_DIR ] && die "Failed 'mkdir -p $TMP_DIR'"

#############################
#
# Function: pause
#
# - Prompt to press return
#
function pause {
    echo "Press <return> to continue"
    read _dummy
}

#############################
#
# Function: getToken
#
# - Get the authentication_token from the login page
#
function getToken {
    [ $VERBOSE -ne 0 ] && echo "Getting authentication_token from login page ... [with USER_AGENT='$USER_AGENT']"

    # Pulls the login page and strips out the auth token
    #authToken=$(curl $USER_AGENT -s -L -c $COOKIES_TXT $SIGNIN_URL | \

    TOKEN_HTML=$TMP_DIR/TOKEN_PAGE.html
    #curl --user-agent 'Mozilla/5.0' -s -L -c $COOKIES_TXT $SIGNIN_URL > $TOKEN_HTML
    curl $USER_AGENT -s -L -c $COOKIES_TXT $SIGNIN_URL > $TOKEN_HTML

    #authToken=$(curl --user-agent 'Mozilla/5.0' -s -L -c $COOKIES_TXT $SIGNIN_URL | \
        #grep authenticity_token | \
        #sed -e 's/.*<input//' -e 's/.*value="//' -e 's/".*//')
    authToken=$(grep authenticity_token $TOKEN_HTML | \
        sed -e 's/.*<input//' -e 's/.*value="//' -e 's/".*//')

    [ $VERBOSE -ne 0 ] && echo "got authToken <$authToken>"
    [ -z "$authToken" ] && die "Failed to get authToken"

    [ $PAUSE -ne 0 ] && pause
}
 
#############################
#
# Function: login
#
# - login
#
function login {
    [ $VERBOSE -ne 0 ] && echo "login ..."

    # Posts all the pre-URI-encoded stuff and appends the URI-encoded auth token

    LOGIN_OP=$TMP_DIR/LOGIN.html

    [ $SETX -ne 0 ] && set -x
    curl $USER_AGENT -X POST -s -L -e $SIGNIN_URL -c $COOKIES_TXT -b $COOKIES_TXT \
        --data-urlencode email=$email \
        --data-urlencode password=$password \
        --data-urlencode authenticity_token="$authToken" $SIGNIN_URL > $LOGIN_OP
    [ $SETX -ne 0 ] && set +x
    [ $VERBOSE -gt 1 ] && cat $LOGIN_OP

    grep "This page doesn.t exist" $LOGIN_OP && die "Failed to login as $email/mdp ['this page']"
    grep "sign you in" $LOGIN_OP && die "Failed to login as $email/mdp"

    [ $VERBOSE -ne 0 ] && echo "Logged in"
    [ $PAUSE -ne 0 ] && pause
}
 

#############################
#
# Function: downloadVideosFromStepPage
#
# - parse the 'Step' page looking for downloadable video links
#
function downloadVideosFromStepPage {
    STEP_PAGE_URL=$1

    [ $VERBOSE -ne 0 ] && echo "downloadVideosFromStepPage $STEP_PAGE_URL ..."

    #curl $USER_AGENT -s -b $COOKIES_TXT $1 > STEP.file
    #vzid=`curl -L $USER_AGENT -s -b $COOKIES_TXT $1 | grep -o 'vzaar [0-9]*' | cut -c 7-14`

    STEP_FILE=$TMP_DIR/STEP.file

    curl -L $USER_AGENT -s -b $COOKIES_TXT $STEP_PAGE_URL > $STEP_FILE
    #vzid=`curl -L $USER_AGENT -s -b $COOKIES_TXT $1 | perl -ne 'if (/view.vzaar.com\/(\d+)\/video/) { print $1; }'`
    vzid=`perl -ne 'if (/view.vzaar.com\/(\d+)\/video/) { print $1; }' < $STEP_FILE`

    [ -z "$vzid" ] && {
        ID=$(echo $1 | perl -ne 'if (/\/(\d+)\//) { print $1; }');
        cp -a $STEP_FILE $TMP_DIR/${ID}.html;
        return 0;
    }

    #perl -ne 'if (/view.vzaar.com\/(\d+)\/video/) { print $1; }' < STEP.1 
    #wget http://view.vzaar.com/1691550/video

    vzurl=https://view.vzaar.com/${vzid}/download
    echo "wget --content-disposition $vzurl"
    wget --content-disposition $vzurl

    [ $VERBOSE -ne 0 ] && echo "Done downloadVideosFromStepPage"
}

#############################
#
# Function: readLoginSpec
#
# - Just encapsulates/reports variable setting
#
function readLoginSpec {
    email=$1; password=$2; course=$3; weekid=$4

    echo "Using login credentials: email=$email password=**** course=$course weekid=$weekid"
}

#############################
#
# Function: test
#
# - test ...
#
function test {
    getToken; login
    #https://www.futurelearn.com/courses/talk-the-talk/steps/12029/progress
    #url=https://www.futurelearn.com${line}/progress

    # Video:
    #url=https://www.futurelearn.com/courses/talk-the-talk/steps/12029/progress
    #COURSE=talk-the-talk; ID=12029; TYPE=Video

    # 12822 : Discussion
    # 12823 : Article
    # 12827 : Quiz

    COURSE=talk-the-talk; ID=12822; TYPE=Discussion
    url=https://www.futurelearn.com/courses/$COURSE/steps/$ID/progress
    echo "downloadVideosFromStepPage $url"; downloadVideosFromStepPage $url; mv STEP.file STEP.$ID.$TYPE

    COURSE=talk-the-talk; ID=12823; TYPE=Article
    url=https://www.futurelearn.com/courses/$COURSE/steps/$ID/progress
    echo "downloadVideosFromStepPage $url"; downloadVideosFromStepPage $url; mv STEP.file STEP.$ID.$TYPE

    COURSE=talk-the-talk; ID=12827; TYPE=Quiz
    url=https://www.futurelearn.com/courses/$COURSE/steps/$ID/progress
    echo "downloadVideosFromStepPage $url"; downloadVideosFromStepPage $url; mv STEP.file STEP.$ID.$TYPE

}

#############################
#
# Function: parseCourseWeekFile
#
# - read input file extracting 'steps'
#
function parseCourseWeekFile {
    file=$1;
    echo "parseCourseWeekFile $file"

    getToken; login

    STEPS=$(perl -ne '
           BEGIN { $OL_STEPS=0; };
           if (/<ol class=.*list steps/) { $OL_STEPS=1; };
           if ($OL_STEPS && /a href=\"(.+\/steps\/\d+)\"/) { print $1,"\n"; }' < $file)

    echo "------- STEPS=<<$STEPS>>"

    grep "You must be enrolled to view this course" $file && die "Not enrolled (or not connected\!)"

    [ -z "$STEPS" ] && die "No steps detected in page $file"

    for line in $STEPS;do
        url=https://www.futurelearn.com${line}/progress
        echo "downloadVideosFromStepPage $url"
        downloadVideosFromStepPage $url
    done


        #<ol class='list steps'>
        #  <li class='media media-small media-sectioned clearfix step'>
        #    <a href="/courses/talk-the-talk/steps/12854"><span>
        #      <div class="stepnumber media_icon stepnumber-current" title="Next">1.1</div>
        #    </span>
        #    <div class='media_body'>
        #      <div class='header header-double'>
        #        <h5 class='headline headline-primary'>
        #          Before you start...
        #        </h5>
        #        <span class='headline headline-secondary type'>article</span>
        #      </div>
        #    </div>
        #    </a>
        #  </li>
        #  <li class='media media-small media-sectioned clearfix step'>
        #    <a href="/courses/talk-the-talk/steps/12029"><span>
        #      <div class="stepnumber media_icon " title="Not Started">1.2</div>
        #    </span>
        #    <div class='media_body'>
        #      <div class='header header-double'>
        #        <h5 class='headline headline-primary'>
        #          Leaving an impression
        #        </h5>
        #        <span class='headline headline-secondary type'>video</span>
        #      </div>
        #    </div>
        #    </a>
        #  </li>

    echo "Done ... parseCourseWeekFile $file"
}

#############################
#
# Function: getWeekIdsFromCourseWeek1Page
#
# - By requesting the course page we obtain the week1 view
# - We parse this to get the URL of each week page
#
function getWeekIdsFromCourseWeek1Page {
    # Download Course page

    COURSE_PAGE=$TMP_DIR/course_page.html

    BASE_URL=https://www.futurelearn.com/courses/${course}/2/todo

    curl $USER_AGENT -s -L -b $COOKIES_TXT $BASE_URL > $COURSE_PAGE
    ls -al $COURSE_PAGE

    grep todonav_itembox-index $COURSE_PAGE > $TMP_DIR/WEEK_PAGES.html
    while read LINE;do
        #echo "LINE: $LINE"
        WEEK_ID=$(echo $LINE | sed -e 's/.*<a href="//' -e 's/".*//' -e 's/.*todo\///')
        #echo "WEEK_ID: $WEEK_ID"

        WEEKPAGE=$TMP_DIR/WEEK${WEEK_ID}.html
        curl $USER_AGENT -s -L -b $COOKIES_TXT https://www.futurelearn.com/courses/${course}/todo/${WEEK_ID} > $WEEKPAGE
        #downloadVideosFromStepPage $BASE_URL/$WEEK_ID
        parseCourseWeekFile $WEEKPAGE
    done < $TMP_DIR/WEEK_PAGES.html
}

################################################################################
# Treat cmd-line args:


while [ ! -z "$1" ];do
    case $1 in
        -x) SETX=1;;
        -X) set -x;;
        -v) let VERBOSE=VERBOSE+1;;
        -p) PAUSE=1;;

        -f) 
            shift; INPUT_FILE=$1; shift; readLoginSpec $*; parseCourseWeekFile $INPUT_FILE; exit $?;;

        -c)
            #<a href="/courses/talk-the-talk/todo/893"><h3 class='todonav_itembox todonav_itembox-index'>

            shift; readLoginSpec $*;
            getToken; login
            #echo "email=$email"
            #die "HERE"

            WEEKS=$(perl -ne 'if (/a href=.*\/todo\/(\d+)/) { print $1,"\n"; }' < COURSE.html)

            DIR=$PWD
            for WEEK in $WEEKS;do
                echo "[$PWD] Treating week '$WEEK'"

                [ ! -d WEEK$WEEK ] && {
                    echo "mkdir WEEK$WEEK";
                    mkdir WEEK$WEEK;
                    cd WEEK$WEEK;
                        weekid=$WEEK;
                        echo "[$PWD] $0 $email $password $course $weekid";
                        $0 $email $password $course $weekid;
                    cd $DIR;
                    rmdir WEEK$WEEK 2>/dev/null; 
                }
            done
            find WEEK*/ -type f

            die "TO COMPLETE"
            ;;

        -course)
            shift; readLoginSpec $*;
            getToken; login;

            # Download Front-Course page (to get list of weeks)
            curl $USER_AGENT -s -L -b $COOKIES_TXT https://www.futurelearn.com/courses/${course}/todo > COURSE.html
            die "TO COMPLETE";
            ;;

        -test)
            shift; readLoginSpec $*; test; exit $?;;

        *)
            readLoginSpec $*; set --;;
    esac
    shift
done

################################################################################
# Main:

getToken; login

getWeekIdsFromCourseWeek1Page


exit 0

curl $USER_AGENT -s -L -b $COOKIES_TXT https://www.futurelearn.com/courses/${course}/todo/${weekid} | \
    grep -B1 'headline.*video' | grep -o '/courses[^"]*' | \
    while read -r line; do
        url=https://www.futurelearn.com${line}/progress
        downloadVideosFromStepPage $url
    done


