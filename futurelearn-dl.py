#!/usr/bin/env python

import sys
import requests
import json

session = requests.Session()

SIGNIN_URL = 'https://www.futurelearn.com/sign-in'

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36',
    #'content-type': 'application/txt',
    'content-type': 'application/json',
}

email = sys.argv[1]
password = sys.argv[2]
course_id = sys.argv[3]

print("Using e-mail={} password=***** course_id={}".format(email, course_id))

def showResponse(response):
    print("url=" + response.url)
    print("request=" + str(response.request))
    print("request.method=" + str(response.request.method))
    print("REQUEST headers(request)=" + str(response.request.headers))
    print("RESPONSE cookies(response)=" + str(response.cookies))
    print("RESPONSE len(response.content)=" + str(len(response.content)))
    print("status_code=" + str(response.status_code))

def fatal(msg):
    print("FATAL:" + msg)
    sys.exit(1)

def writeFile(file, content):
    f = open(file, 'w')
    f.write(content)
    f.close()

def getToken(url):
    response = session.get(url, headers=headers)
    #showResponse(response)
    content = response.content.decode('utf8')
    writeFile('token.response.content', content)

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

def login(url, email, password, token, cookies):
    data=json.dumps({'email': email, 'password':password, 'authenticity_token':token})
    print("COOKIES={}".format( str(cookies) ))
    #data='''
#email={}
#password={}
#authenticity_token={}
#'''.format(email, password, token)
    response = session.post(url, headers=headers, cookies=cookies, data=data)
    content = response.content.decode('utf8')
    writeFile('login.response.content', content)
    return response

#--data-urlencode email=$email
#--data-urlencode password=$password
#--data-urlencode authenticity_token=$TOKEN $URL2"

#do the login
token, cookies = getToken(SIGNIN_URL)
response = login(SIGNIN_URL, email, password, token, cookies)

print(str(response))
#print(str(dir(response)))
#['__attrs__', '__bool__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__iter__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_content', '_content_consumed', 'apparent_encoding', 'close', 'connection', 'content', 'cookies', 'elapsed', 'encoding', 'headers', 'history', 'is_permanent_redirect', 'is_redirect', 'iter_content', 'iter_lines', 'json', 'links', 'ok', 'raise_for_status', 'raw', 'reason', 'request', 'status_code', 'text', 'url']
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

sys.exit(0)
################################################################################

# REQUEST methods:
#dir(request)=['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_cookies', '_encode_files', '_encode_params', 'body', 'copy', 'deregister_hook', 'headers', 'hooks', 'method', 'path_url', 'prepare', 'prepare_auth', 'prepare_body', 'prepare_content_length', 'prepare_cookies', 'prepare_headers', 'prepare_hooks', 'prepare_method', 'prepare_url', 'register_hook', 'url']

# RESPONSE methods:
#['__attrs__', '__bool__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__iter__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_content', '_content_consumed', 'apparent_encoding', 'close', 'connection', 'content', 'cookies', 'elapsed', 'encoding', 'headers', 'history', 'is_permanent_redirect', 'is_redirect', 'iter_content', 'iter_lines', 'json', 'links', 'ok', 'raise_for_status', 'raw', 'reason', 'request', 'status_code', 'text', 'url']


#response = conn.getresponse()
#print(response.status, response.reason)
#print( dir(r) )
#print("CONTENT=")
#content = r.content
#content = bytes(r.content, 'UTF-8')
#content = r.content.decode('utf-8', errors='replace')


#print(dir(response.content))
#f.write(response.content.decode('utf8'))

#content = response.content.encode('utf-8', errors='replace')
#print(content)

sys.exit(0)


print("R=")
print(r)
token = r['response']['user']['authentication_token']    #set token value
print("TOKEN=")
print(token)
response = r.json()
token = response['response']['user']['authentication_token']    #set token value
print(token)
sys.exit(0)

#r = session.post(SIGNIN_URL,
                    #data=json.dumps({'email': email, 'password':password}), 
                    #headers={'content-type': 'application/json'})
#response = r.json()

print(response) #check response
token = response['response']['user']['authentication_token']    #set token value

#Now you can do authorised calls
#r = session.get('http://localhost:5000/protected', 
r = session.get(SIGNIN_URL,
                headers={'Authentication-Token': token})
print(r.text)


