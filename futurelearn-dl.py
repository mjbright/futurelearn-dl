#!/usr/bin/env python

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

DEBUG=True

# Download file types by extension (case insensitive):
#DOWNLOAD_TYPES = [ 'pdf', 'mp4', 'mp3', 'doc', 'docx', 'ppt', 'pptx', 'wmv' ]
#DOWNLOAD_TYPES = [ 'pdf', 'mp4' ]
#DOWNLOAD_TYPES = [ 'pdf' ]
#DOWNLOAD_TYPES = [ 'mp4' ]
#DOWNLOAD_TYPES = [ 'pdf', 'mp4', 'mp3', 'ppt', 'pptx', 'wmv' ]
DOWNLOAD_TYPES = [ 'pdf', 'mp4' ]
for d in range(len(DOWNLOAD_TYPES)):
    DOWNLOAD_TYPES[d] = DOWNLOAD_TYPES[d].lower()
    

TMP_DIR=os.getenv('HOME') + '/tmp/FUTURELEARN_DL'
OP_DIR=os.getenv('HOME') + '/FUTURELEARN_DL'

email = sys.argv[1]
password = sys.argv[2]
course_id = sys.argv[3]

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
        os.makedirs(path)
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
        fatal("No authenticity_token in response")
    print(apos)
    vpos = content[ apos: ].find("value=")
    # "authentication_token" in content:
    if vpos == -1:
        fatal("No value in authenticity_token in response")
    
    token_pos = apos + vpos + len("value=") + 1
    close_quote_pos = token_pos + content[token_pos:].find('"')
    
    print("authenticity_token at pos {} -> {} in response.content".format(token_pos, close_quote_pos))
    
    token=content[ token_pos: close_quote_pos ]
    print("TOKEN='{}'".format(token))
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

def getCourseWeekStepPage(course_id, week_id, step_id):
    '''
        get the specified step page

        RETURNS: list of downloadable urls
    '''

    course_step_url='https://www.futurelearn.com/courses/{}/2/steps/{}'.format(course_id, step_id)

    URLS = {}
    urls_seen = []

    response = session.get(course_step_url, headers=headers)
    #showResponse(response)
    content = response.content.decode('utf8', 'ignore')

    if DEBUG:
        ofile= TMP_DIR + '/course.' + course_id + '.s' + step_id + '.response.content'
        print("Writing 'course week step {} page' response to <{}>".format(step_id, ofile))
        writeFile(ofile, content)

    for DOWNLOAD_TYPE in DOWNLOAD_TYPES:
        #print("Searching for '{}' files in {}".format(DOWNLOAD_TYPE, ofile))
        URLS[DOWNLOAD_TYPE] = getDownloadableURLs(content, DOWNLOAD_TYPE)

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

def getDownloadableURLs(content, DOWNLOAD_TYPE):
    ## -- Now loop through identifying downloadable items:

    urls = []
    urls_seen = []

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

        if DOWNLOAD_TYPE == 'mp4':
            #if DEBUG: print("MATCHING URL=<<{}>>".format(url))
            urls.append( url )
        else:
            # With other types, check that the url ends with the type e.g. ".pdf"
            if lurl[-(1+len(DOWNLOAD_TYPE)):] == "." + DOWNLOAD_TYPE:
                #if DEBUG: print("MATCHING URL=<<{}>>".format(url))
                urls.append( url )

    return urls
        

def getCourseWeekPage(course_id, week_id):

    course_week_url='https://www.futurelearn.com/courses/{}/2/todo/{}'.format(course_id, week_id)

    response = session.get(course_week_url, headers=headers)
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

    course_url='https://www.futurelearn.com/courses/{}/2/todo'.format(course_id)
    response = session.get(course_url, headers=headers)
    #showResponse(response)
    content = response.content.decode('utf8')

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

weeks = getCoursePage(course_id)
for week_id in weeks:
    steps = getCourseWeekPage(course_id, week_id)
    for step_id in steps:
        getCourseWeekStepPage(course_id, week_id, step_id)

sys.exit(0)
################################################################################

# REQUEST methods:
#dir(request)=['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_cookies', '_encode_files', '_encode_params', 'body', 'copy', 'deregister_hook', 'headers', 'hooks', 'method', 'path_url', 'prepare', 'prepare_auth', 'prepare_body', 'prepare_content_length', 'prepare_cookies', 'prepare_headers', 'prepare_hooks', 'prepare_method', 'prepare_url', 'register_hook', 'url']

# RESPONSE methods:
#['__attrs__', '__bool__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__iter__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_content', '_content_consumed', 'apparent_encoding', 'close', 'connection', 'content', 'cookies', 'elapsed', 'encoding', 'headers', 'history', 'is_permanent_redirect', 'is_redirect', 'iter_content', 'iter_lines', 'json', 'links', 'ok', 'raise_for_status', 'raw', 'reason', 'request', 'status_code', 'text', 'url']



