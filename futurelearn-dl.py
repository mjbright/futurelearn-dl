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

'''

SIGNIN_URL = 'https://www.futurelearn.com/sign-in'

DEBUG=True

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
    f.write(content)
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

def getCourseWeekPage(course_id, week_id):

    course_week_url='https://www.futurelearn.com/courses/{}/2/todo/{}'.format(course_id, week_id)

    response = session.get(course_week_url, headers=headers)
    #showResponse(response)
    content = response.content.decode('utf8')

    if DEBUG:
        ofile= TMP_DIR + '/course.' + course_id + '.w' + week_id + '.response.content'
        print("Writing 'course week {} page' response to <{}>".format(week_id, ofile))
        writeFile(ofile, content)


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

    ## -- Now loop through identifying weekids: ../todo/<WEEKID>
    pos=0
    while '/todo/' in content[pos:]:
        pos += content[pos:].find('/todo/')
        info = content[ pos : pos + 20 ]
        # integer weekid starts here:
        ipos = pos + 6

        # Build up weekid:
        weekid = ''
        while content[ipos].isdigit():
            weekid  += content[ipos]
            ipos += 1

        if not weekid in weeks_seen:
            weeks_seen.append(weekid)
            if DEBUG:
                print("WEEKID=" + weekid)

        # Step over current '/todo/':
        pos += 6

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
    getCourseWeekPage(course_id, week_id)

sys.exit(0)
################################################################################

# REQUEST methods:
#dir(request)=['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_cookies', '_encode_files', '_encode_params', 'body', 'copy', 'deregister_hook', 'headers', 'hooks', 'method', 'path_url', 'prepare', 'prepare_auth', 'prepare_body', 'prepare_content_length', 'prepare_cookies', 'prepare_headers', 'prepare_hooks', 'prepare_method', 'prepare_url', 'register_hook', 'url']

# RESPONSE methods:
#['__attrs__', '__bool__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__iter__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_content', '_content_consumed', 'apparent_encoding', 'close', 'connection', 'content', 'cookies', 'elapsed', 'encoding', 'headers', 'history', 'is_permanent_redirect', 'is_redirect', 'iter_content', 'iter_lines', 'json', 'links', 'ok', 'raise_for_status', 'raw', 'reason', 'request', 'status_code', 'text', 'url']



