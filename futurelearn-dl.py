#!/usr/bin/env python3

import sys, os, errno
import requests
import json

'''
    Author: Michael Bright, @mjbright
    Created: 2015-Oct-24

    Attempt at auto-downloading videos and other materials from futurelearn.com

    TODO: Do proper argument handling and associated processing
    - specify e-mail, password, course_id, week, type
    - specify temp/output dirs, debug
    - only download new files
    - multiple debugging/verbosity levels
    - download SD or HD

'''

SIGNIN_URL = 'https://www.futurelearn.com/sign-in'

#DEBUG=True
DEBUG=False
#DEBUG = os.getenv('DOWNLOAD_DEBUG', default=False)
DOWNLOAD=True
OVERWRITE_NONEMPTY_FILES=False

WEEKS = []
WEEK_NUM = -1 # Select all weeks unless specified on command-line

# Download file types by extension (case insensitive):
#DOWNLOAD_TYPES = [ 'pdf', 'mp4', 'mp3', 'doc', 'docx', 'ppt', 'pptx', 'wmv' ]
#DOWNLOAD_TYPES = [ 'pdf', 'mp4' ]
#DOWNLOAD_TYPES = [ 'pdf' ]
#DOWNLOAD_TYPES = [ 'mp4' ]
#DOWNLOAD_TYPES = [ 'pdf', 'mp4', 'mp3', 'ppt', 'pptx', 'wmv' ]
DOWNLOAD_TYPES = [ 'pdf', 'mp4' ]
for d in range(len(DOWNLOAD_TYPES)):
    DOWNLOAD_TYPES[d] = DOWNLOAD_TYPES[d].lower()
    
TMP_DIR = os.getenv('TMP_DIR', default='/tmp/FUTURELEARN_DL')
OP_DIR  = os.getenv('OP_DIR',  default=os.getenv('HOME') + '/Education/FUTURELEARN')

print("Using temp   dir <{}>".format(TMP_DIR))
print("Using Output dir <{}>".format(OP_DIR))

email = sys.argv[1]
password = sys.argv[2]
course_id = sys.argv[3]
course_run = int(sys.argv[4])

COURSE_URL='https://www.futurelearn.com/courses/{}/{}/todo'.format(course_id, course_run)
COURSE_STEP_URL='https://www.futurelearn.com/courses/{}/{}/steps'.format(course_id, course_run)

if len(sys.argv) == 6:
    WEEK_NUM = int(sys.argv[5])

#print(len(sys.argv))
#sys.exit(0)
#if len(sys.argv

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36',
    'content-type': 'application/json',
}

## -- Functions: ---------------------------------------------------

def fatal(msg):
    ''' die brutally '''
    print("FATAL:" + msg)
    sys.exit(1)

def mkdir_p(path):
    '''
         Perform equivalent of 'mkdir -p path' to create a directory and any necessary
         parent directories
    '''
    try:
        if DEBUG: print("Creating dir <{}>".format(path))
        os.makedirs(path)
        if not os.path.isdir(path):
            fatal("Error creating dir <{}>".format(path))

    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def showResponse(response):
    '''
       Dump various fields of a http response
    '''
    print("url=" + response.url)
    print("request=" + str(response.request))
    print("request.method=" + str(response.request.method))
    print("REQUEST headers(request)=" + str(response.request.headers))
    print("RESPONSE cookies(response)=" + str(response.cookies))
    print("RESPONSE len(response.content)=" + str(len(response.content)))
    print("status_code=" + str(response.status_code))
    print(str(response))
    print("reason={}".format(str(response.reason)))
    print("status_code={}".format(str(response.status_code)))
    #print("content={}".format(str(response.content)))
    print("encoding={}".format(str(response.encoding)))
    print("headers={}".format(str(response.headers)))
    print("history={}".format(str(response.history)))
    print("is_redirect={}".format(str(response.is_redirect)))
    print("ok={}".format(str(response.ok)))
    print("links={}".format(str(response.links)))
    print("raise_for_status={}".format(str(response.raise_for_status)))
    print("raw={}".format(str(response.raw)))
    print("text={}".format(str(response.text)))
    print("url={}".format(str(response.url)))
    print("json={}".format(str(response.json)))

def writeBinaryFile(file, content):
    ''' Write binary content to the specified file '''

    f = open(file, 'wb')
    try:
        f.write(content)
    except UnicodeEncodeError as exc:
        print("EXC=" + str( exc ))
        pass
    f.close()

def writeFile(file, content):
    ''' Write content to the specified file '''
    f = open(file, 'w')
    try:
        f.write(content)
    except UnicodeEncodeError as exc:
        print("EXC=" + str( exc ))
        pass
    f.close()

def getToken(session, url):
    ''' Perform request to the specified signin url and extract the 'authenticity_token'
        RETURN: token and cookies
    '''
    response = session.get(url, headers=headers)
    #showResponse(response)
    content = response.content.decode('utf8')
    if DEBUG:
        ofile= TMP_DIR + '/token.response.content'
        print("Writing 'getToken' response to <{}>".format(ofile))
        writeFile(ofile, content)

    apos = content.find("authenticity_token")
    if apos == -1:
        fatal("getToken: No authenticity_token in response")
    #print(apos)
    vpos = content[ apos: ].find("value=")
    # "authentication_token" in content:
    if vpos == -1:
        fatal("getToken: No value in authenticity_token in response")
    
    token_pos = apos + vpos + len("value=") + 1
    close_quote_pos = token_pos + content[token_pos:].find('"')
    
    if DEBUG:
        print("authenticity_token at pos {} -> {} in response.content".format(token_pos, close_quote_pos))
    
    token=content[ token_pos: close_quote_pos ]
    #if DEBUG: print("Got authenticity_token '{}'".format(token))
    #print("Got token '{}'".format(token))
    #print("Got authenticity_token '{}'".format(len(token)))

    if len(token) < 88:
        fatal("getToken: Failed to get TOKEN")

    return token, response.cookies

def login(session, url, email, password, token, cookies):
    ''' Perform request to the specified signin url to perform site login
        RETURN: response
    '''
    data=json.dumps({'email': email, 'password':password, 'authenticity_token':token})
    #print("COOKIES={}".format( str(cookies) ))

    response = session.post(url, headers=headers, cookies=cookies, data=data)
    content = response.content.decode('utf8')
    if DEBUG:
        ofile= TMP_DIR + '/login.response.content'
        print("Writing 'login' response to <{}>".format(ofile))
        writeFile(ofile, content)

    return response

def getInteger(content, ipos):
    '''
       Return the integer value, if any, in content starting at position ipos
       RETURNS: the integers string
    '''
    # Build up integer:
    ivalue = ''
    while content[ipos].isdigit():
        ivalue  += content[ipos]
        ipos += 1

    return ivalue

def getCourseWeekStepPage(course_id, week_id, step_id, week_num):
    '''
        get the specified step page

        RETURNS: list of downloadable urls
    '''

    url = COURSE_STEP_URL + '/' + str(step_id)

    URLS = {}
    urls_seen = []

    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print("getCourseWeekStepPage: Failed to download url <{}>".format(url))
        return URLS
        #fatal("getCourseWeekStepPage: Failed to download url <{}>".format(url))

    #showResponse(response)
    content = response.content.decode('utf8', 'ignore')

    if DEBUG:
        ofile= TMP_DIR + '/course.' + course_id + '.s' + step_id + '.response.content'
        print("Writing 'course week step {} page' response to <{}>".format(step_id, ofile))
        writeFile(ofile, content)

    num_urls = 0
    for DOWNLOAD_TYPE in DOWNLOAD_TYPES:
        #print("Searching for '{}' files in {}".format(DOWNLOAD_TYPE, ofile))
        URLS[DOWNLOAD_TYPE] = \
            getDownloadableURLs(course_id, week_id, step_id, week_num, content, DOWNLOAD_TYPE)

        num_urls += len(URLS[DOWNLOAD_TYPE])

    if num_urls > 0:
        print()
        showDownloads(str(step_id), URLS)
    #print(str(URLS))

    return URLS

def showDownloads(label, urls):
    print("-- " + label + ": Downloadable urls found: -----------")

    for type in urls:
        if len(urls[type]) != 0:
            print(type + ": ", end='')
            for url in urls[type]:
                print("-- " + url)

def pause(msg):
    print(msg)
    if DEBUG:
        print("Press <return> to continue")
        input()

def getDownloadableURLs(course_id, week_id, step_id, week_num, content, DOWNLOAD_TYPE):
    ## -- Now loop through identifying downloadable items:

    urls = []
    urls_seen = []
    num_urls = 0

    '''
         Generally we have an 'a href="URL"'
         POS_MATCH:   used to detect beginning of appropriate tag
         MEDIA_MATCH: used to if there is one type matching entry in whole 'content'
    '''
    POS_MATCH='<a href='
    MEDIA_MATCH=DOWNLOAD_TYPE

    # except for video
    if DOWNLOAD_TYPE == 'mp4':
        POS_MATCH='<video'
        MEDIA_MATCH='video/mp4'

    # If there's no mention of such media in the whole file, leave now:
    if not MEDIA_MATCH in content.lower():
        return urls
        #fatal("SHOULD MATCH")

    pos = content.lower().find(DOWNLOAD_TYPE)
    if DEBUG: print("Searching for {} in <<{}...>>".format(DOWNLOAD_TYPE, content[pos-20:pos+20]))

    # MP4:
    # <video poster="//view.vzaar.com/2088550/image" width="auto" height="auto" id="video-2088550" class="video-js vjs-futurelearn-skin" controls="controls" preload="none" data-hd-src="//view.vzaar.com/2088550/video/hd" data-sd-src="//view.vzaar.com/2088550/video"><source src="//view.vzaar.com/2088550/video" type="video/mp4" />

    #if DEBUG: print("getDownloadableURLs({}..., {})".format(content[:10], DOWNLOAD_TYPE))

    pos = 0
    while POS_MATCH in content.lower():
        mpos = content[pos:].lower().find(POS_MATCH)
        if mpos == -1:
            #if len(urls) != 0:
                #print(str(urls))
                #fatal("END")
            return urls
       
        #if DEBUG: print("FOUND {} at mpos={}".format(DOWNLOAD_TYPE, str(mpos)))
        pos += mpos

        # In video case, we also need to advance to the '<source src="XX"' tag
        if DOWNLOAD_TYPE == 'mp4':
            #if DEBUG: print("video in <<{}...>>".format(content[pos:pos+400]))
            pos += len(POS_MATCH)

            SRC_MATCH='<source src='
            mpos = content[pos:].lower().find(SRC_MATCH)

            # If there's no match, assume we reached the end of the content:
            if mpos == -1:
                return urls

            pos += mpos
            pos += len(SRC_MATCH)
            #if DEBUG: print("source src ==> <<{}...>>".format(content[pos:pos+400]))
        else:
            #if DEBUG: print("HREF ==> <<{}...>>".format(content[pos:pos+400]))
            pos += len(POS_MATCH)

        quote = content[pos]
        if quote != "'" and quote != '"':
            fatal("No quote(char={}) in <<{}...>>".format(quote, content[pos-10:pos+10]))
        #if DEBUG: print("Quote in <<{}...>>".format(content[pos-10:pos+10]))

        # step over start-quote:
        pos += 1

        # detect end-quote:
        eqpos = content[pos:].find(quote)
        if eqpos == -1:
            fatal("No end-quote in <<{}...>>".format(content[pos:pos+100]))
        eqpos += pos

        # Strip out the url, between the quotes:
        url=content[pos:eqpos]

        # Detect if just "//url" and insert http:
        if url[0:2] == "//":
            url = "https:" + url

        if DEBUG: print("content[{}:{}] => url={}".format(pos, eqpos, url))
        #pause("Got url <<{}>>".format(url))

        #if DEBUG: print("URL=<<{}>>".format(url))

        if url in urls_seen or url == '' or len(url) == 0:
            pass
        #if DEBUG: print("NEW URL=<<{}>>".format(url))

        urls_seen.append(url)
        lurl = url.lower()

        download_dir = OP_DIR + '/' + course_id + '/week' + str(week_num)

        if DOWNLOAD_TYPE == 'mp4':
            #if DEBUG: print("MATCHING URL=<<{}>>".format(url))
            urls.append( url )
            downloadFile(url, download_dir, DOWNLOAD_TYPE)
        else:
            # With other types, check that the url ends with the type e.g. ".pdf"
            if lurl[-(1+len(DOWNLOAD_TYPE)):] == "." + DOWNLOAD_TYPE:
                #if DEBUG: print("MATCHING URL=<<{}>>".format(url))
                urls.append( url )
                downloadFile(url, download_dir, DOWNLOAD_TYPE)

    return urls

def downloadURLToFile(url, file, DOWNLOAD_TYPE):
    if not(OVERWRITE_NONEMPTY_FILES) and os.path.exists(file):
        statinfo = os.stat(file)
        #print(dir(statinfo))
        if statinfo.st_size != 0:
            print("Skipping non-zero size file <{}> of {} bytes".format(file, statinfo.st_size))
            return

    print("Downloading url<{}> ...".format(url), end='')

    # No user-agent: had some failures in this case when specifying user-agent ...
    headers = {}
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print("downloadURLToFile: Failed to download url <{}> => {}".format(url, response.status_code))
        return

    #showResponse(response)
    print("type={}, content.len={}".format(DOWNLOAD_TYPE, len(response.content)))
    if "The request signature we calculated" in response.content.decode('utf8', 'ignore'):
        print("Skipping bad content for file <{}> - may not be available yet".format(file))
        return
        
    print("Writing content to <{}>".format(file))
    writeBinaryFile(file, response.content)
    #fatal("STOP")

def downloadFile(url, download_dir, DOWNLOAD_TYPE):
    if not DOWNLOAD:
        return

    mkdir_p(download_dir)
    

    if DOWNLOAD_TYPE == 'mp4':
        # We need to create an 'x.mp4' filename from the url of the form
        #    'https://view.vzaar.com/2088434/video':
        
        # Let's strip of the /video at the end:
        urlUptoNumber = url [ :url.rfind('/video') ]
        #print(urlUptoNumber)

        # Get the filename from the url after the last slash (where the number is):
        filename = course_id + '_' + urlUptoNumber[ urlUptoNumber.rfind('/') + 1: ] + ".mp4"

        ofile= download_dir + '/' + filename
        downloadURLToFile(url, ofile, DOWNLOAD_TYPE)
    else:
        # Get the filename from the url after the last slash (where the source filename is):
        filename = url[ url.rfind('/') + 1: ]

        # Replace any '%20' chars by underscore(_)
        filename = filename.replace('%20', '_')

        if '%' in filename:
            fatal("downloadFile: Unhandled escape sequence in filename <{}>".format(filename))

        ofile= download_dir + '/' + filename
        downloadURLToFile(url, ofile, DOWNLOAD_TYPE)


def getCourseWeekPage(course_id, week_id):

    url=COURSE_URL + '/{}'.format(week_id)

    response = session.get(url, headers=headers)
    if response.status_code != 200:
        fatal("getCourseWeekPage: Failed to download url <{}>".format(url))
    #showResponse(response)
    content = response.content.decode('utf8')

    if DEBUG:
        ofile= TMP_DIR + '/course.' + course_id + '.w' + week_id + '.response.content'
        print("Writing 'course week {} page' response to <{}>".format(week_id, ofile))
        writeFile(ofile, content)

    ## -- Now loop through identifying steps:

    ## TODO: Make this page parsing more robust: should be using regexes:
    ## TODO: Make this page parsing more robust: should be checking 'list steps' is part of the '<ol'
    pos = content.find('<ol class=')
    current = content[pos:]
    pos = current.find('list steps')
    current = current[pos:]

    steps_seen=[]

    pos=0
    MATCH='/steps/'
    while MATCH in current:
        pos += current[pos:].find(MATCH)
        info = current[ pos-10 : pos + 20 ]
    
        #if DEBUG:
            #print("INFO=" + info)

        ipos = pos + len(MATCH)
        stepid = getInteger(current, ipos)
        current = current[pos+6:]
   
        if not stepid in steps_seen and not stepid == '':
            steps_seen.append(stepid)
            #if DEBUG: print("STEPID=" + stepid)

        # Step over current '/steps/':
        pos += len(MATCH)

    return steps_seen

def getCoursePage(course_id):
    '''
       GET the specified week page for this course based on it's course_id and week_id
       Then parse the page looking for steps (a step corresponds to a page with one or more videos)

       RETURNS: the list of steps in order
    '''

    weeks_seen=[]

    response = session.get(COURSE_URL, headers=headers)
    #showResponse(response)
    content = response.content.decode('utf8')

    DEBUG=True
    if DEBUG:
        ofile= TMP_DIR + '/course.' + course_id + '.response.content'
        print("Writing 'course page' response to <{}>".format(ofile))
        writeFile(ofile, content)

    ## TODO: Make this page parsing more robust: should be checking /todo/ is part of an "<a href"
    ## -- Now loop through identifying weekids: ../todo/<WEEKID>
    pos=0
    MATCH='/todo/'
    while MATCH in content[pos:]:
        pos += content[pos:].find(MATCH)
        info = content[ pos : pos + 20 ]
        # integer weekid starts here:
        ipos = pos + len(MATCH)

        weekid = getInteger(content, ipos)

        if not weekid in weeks_seen and not weekid == '':
            weeks_seen.append(weekid)
            if DEBUG:
                print("WEEKID=" + weekid)

        # Step over current '/todo/':
        pos += len(MATCH)

    if (len(weeks_seen) <= 0):
        fatal("getCoursePage: No week entries found - check your courseid and the courserun")

    return weeks_seen


## -- Main: --------------------------------------------------------

session = requests.Session()

mkdir_p(TMP_DIR)
if not os.path.isdir(TMP_DIR):
    fatal("Failed to create tmp dir <{}>".format(TMP_DIR))

print("Using e-mail={} password=***** course_id={}".format(email, course_id))

## -- do the login:
token, cookies = getToken(session, SIGNIN_URL)
response = login(session, SIGNIN_URL, email, password, token, cookies)

WEEKS = getCoursePage(course_id)

print("Course seems to comprise of {} weeks".format(len(WEEKS)))
#print(str(WEEKS))

if WEEK_NUM == -1: # All
    print("Downloading all weeks - if available")
    week_num=0
    for week_id in WEEKS:
        week_num += 1
        print("Downloading available week{} material".format(week_num))
        steps = getCourseWeekPage(course_id, week_id)
        print("STEPS=" + str(steps))
        for step_id in steps:
            getCourseWeekStepPage(course_id, week_id, step_id, week_num)
else:
    print("Downloading week " + str(WEEK_NUM))
    if WEEK_NUM > len(WEEKS) or WEEK_NUM < 1:
        fatal("No such week as " + str(WEEK_NUM))

    week_num = WEEK_NUM
    week_id = WEEKS[week_num-1]
    print("Downloading available week{} material".format(week_num))
    steps = getCourseWeekPage(course_id, week_id)
    for step_id in steps:
        getCourseWeekStepPage(course_id, week_id, step_id, week_num)

sys.exit(0)
################################################################################

# REQUEST methods:
#dir(request)=['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_cookies', '_encode_files', '_encode_params', 'body', 'copy', 'deregister_hook', 'headers', 'hooks', 'method', 'path_url', 'prepare', 'prepare_auth', 'prepare_body', 'prepare_content_length', 'prepare_cookies', 'prepare_headers', 'prepare_hooks', 'prepare_method', 'prepare_url', 'register_hook', 'url']

# RESPONSE methods:
#['__attrs__', '__bool__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__iter__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_content', '_content_consumed', 'apparent_encoding', 'close', 'connection', 'content', 'cookies', 'elapsed', 'encoding', 'headers', 'history', 'is_permanent_redirect', 'is_redirect', 'iter_content', 'iter_lines', 'json', 'links', 'ok', 'raise_for_status', 'raw', 'reason', 'request', 'status_code', 'text', 'url']



