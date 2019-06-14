#!/bin/env python3

import os, sys, json, collections, getpass

try:
    # Installed by default on lxplus
    import requests
except:
    print("Please install the requests module,")
    print("the equivalent of one of the following:")
    print("  pip install requests")
    print("  yum install python-requests")
    sys.exit(1)

try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder
except ImportError:
    MultipartEncoder = None

# Shouldn't be used outside this module
_AUTH_URL = 'https://oidc.plus4u.net/uu-oidcg01-main/0-0/'
_SITE_URL = 'https://itkpd-test.unicorncollege.cz/'

# MJB -- Define an exception specific to this file so that we may catch them (if we wish)
class dbAccessError(Exception):
    def __init__(self, message):
        self.message = message

from pprint import PrettyPrinter
pp = PrettyPrinter(indent = 1, width = 200)

# Fix the str (python3) versus basestring (Python2) issue
# See: https://stackoverflow.com/questions/11301138/how-to-check-if-variable-is-string-with-python-2-and-3-compatibility
try:
    basestring
except NameError:
    basestring = str

import time
class ExpiredToken(Exception):
    def __init__(self, expired_at, current_time):
        self.expired_at     = expired_at
        self.current_time   = current_time
class NoToken(Exception):
    pass

# MJB -- Define a class for wrapping up authentication/doSomething commands but in a single requests session
class ITkPDSession(requests.Session):

    def __init__(self, enable_printing = True):
        super(ITkPDSession, self).__init__()
        self.enable_printing = enable_printing
        self.dbAccessString = '\033[1m' + '\033[97m' + 'dbAccess:' + '\033[0m' + ' '
        if sys.version_info >= (3, 0):
            self.__convertToUtf8 = self.__convertToUtf8__Python3
        else:
            self.__convertToUtf8 = self.__convertToUtf8__Python2
        self.accessCode1    = None
        self.accessCode2    = None
        self.token          = None
        # self.issued_at      = -1
        # self.expires_at     = -1
        # self.expires_in     = -1

    def __sessionPrinter(self, string, style = None):
        if self.enable_printing:
            if style in ['h', 'header']:
                print(self.dbAccessString + string)
            elif style in ['p', 'pretty']:
                pp.pprint(string)
            else:
                print(string)
        else:
            pass

    def __toBytes(self, data):
        try:
            return bytes(data, 'utf-8')
        except TypeError:
            return data

    def __convertToUtf8__Python2(self, data):
        if isinstance(data, basestring):
            return data.encode('utf-8')
        elif isinstance(data, collections.Mapping):
            return dict(map(self.__convertToUtf8__Python2, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self.__convertToUtf8__Python2, data))
        else:
            return data

    def __convertToUtf8__Python3(self, data):
        return data

    def authenticate(self, accessCode1 = None, accessCode2 = None, save_codes = False):
        self.__sessionPrinter('Getting token.', 'h')
        if os.getenv('ITK_DB_AUTH'):
            self.__sessionPrinter('Token already exists in shell environment.', 'h')
            self.token = os.getenv('ITK_DB_AUTH')
        else:
            data = {'grant_type': 'password'}
            if accessCode1 is None or accessCode2 is None:
                data['accessCode1'] = getpass.getpass(self.dbAccessString + 'Enter AccessCode 1:')
                data['accessCode2'] = getpass.getpass(self.dbAccessString + 'Enter AccessCode 2:')
                if save_codes:
                    self.accessCode1, self.accessCode2 = data['accessCode1'], data['accessCode2']
            else:
                data['accessCode1'] = accessCode1
                data['accessCode2'] = accessCode2
            data = self.__toBytes(json.dumps(data))
            self.__sessionPrinter('Sending credentials to get a token.', 'h')
            token = self.doSomething(action = 'grantToken', method = 'POST', data = data, url = _AUTH_URL)
            token = self.__toBytes(token)
            self.token, self.issued_at, self.expires_at, self.expires_in = token['id_token'], float(token['issued_at']), float(token['expires_at']), float(token['expires_in'])
        self.headers.update({'Authorization': 'Bearer ' + self.token})
        return self.token

    def refreshToken(self):
        if self.accessCode1 is None or self.accessCode2 is None:
            pass
        else:
            self.authenticate(self.accessCode1, self.accessCode2)

    def updateToken(self, token):
        self.token = token
        self.headers.update({'Authorization': 'Bearer ' + self.token})

    def doSomething(self, action, method, data = None, url = _SITE_URL):
        # if self.token is not None or action == 'grantToken':
        #     if time.time() < self.expires_at or action == 'grantToken':
                if data is not None:
                    if MultipartEncoder is not None and isinstance(data, MultipartEncoder):
                        self.headers.update({'Content-Type' : data.content_type})
                    else:
                        self.headers.update({'Content-Type' : 'application/json'})
                        if type(data) is bytes:
                            pass
                        else:
                            data = self.__toBytes(json.dumps(data))
                else:
                    data = {}
                if method == 'GET':
                    response = self.get(url = url + action, data = data)
                elif method == 'POST':
                    response = self.post(url = url + action, data = data)
                else:
                    self.__sessionPrinter('Unknown method \'{0}\' -- EXITING.'.format(method), 'h')
                    sys.exit(1)
                if response.status_code != 200:
                    self.__sessionPrinter('Bad status code.', 'h')
                    self.__sessionPrinter('requests status code: %s' % response.status_code, 'h')
                    self.__sessionPrinter('requests header:', 'h')
                    self.__sessionPrinter(response.headers, 'p')
                    try:
                        uuAppErrorMap = self.__convertToUtf8(response.json())['uuAppErrorMap']
                        self.__sessionPrinter('uAppErrorMap:', 'h')
                        self.__sessionPrinter(uuAppErrorMap, 'p')
                    except (KeyError, ValueError):
                        self.__sessionPrinter('No uuAppErrorMap available.', 'h')
                        self.__sessionPrinter('requests text:', 'h')
                        self.__sessionPrinter(response.text, 'h')
                    response.raise_for_status()
                try:
                    dataOut = self.__convertToUtf8(response.json())
                except ValueError:
                    self.__sessionPrinter('No json could be decoded.', 'h')
                    dataOut = response.text
                if 'pageItemList' in dataOut:
                    return dataOut['pageItemList']
                elif 'itemList' in dataOut:
                    return dataOut
                else:
                    return dataOut
        #     else:
        #         raise ExpiredToken(expired_at = self.expires_at, current_time = time.time())
        # else:
        #     raise NoToken

verbose = False

token = None

import os
testing = False
if os.getenv("TEST_OVERRIDE"):
    testing = True

def setupConnection():
    global token

    print("Setup connection")

    token = authenticate()

def to_bytes(s):
    try:
        return bytes(s, 'utf-8')
    except TypeError:
        # Python 2, already OK
        return s

# DB has unicode, but console might be something else
# If eg ASCII, replace unicode chars
# If directed to file, force utf-8
def fix_encoding(s): 
    enc = sys.stdout.encoding

    # Default to utf-8 if redirected
    if enc is None:
        enc = "utf-8"

    if sys.version_info[0] == 2:
        return s.encode(enc, "replace")
    else:
        # Encode string into bytes
        s = s.encode(enc, "replace")
        s = s.decode(enc, "replace")
    return s

def myprint(s):
    print(fix_encoding(s))

def authenticate(accessCode1 = None, accessCode2 = None):
    print("Getting token")
    # post
    # Everything is json header

    a = {"grant_type": "password"}

    if accessCode1 is not None and accessCode2 is not None:
        a["accessCode1"] = accessCode1
        a["accessCode2"] = accessCode2
    else:
        import getpass

        a["accessCode1"] = getpass.getpass("AccessCode1: ")
        a["accessCode2"] = getpass.getpass("AccessCode2: ")

    a = to_bytes(json.dumps(a))

    print("Sending credentials to get a token")

    result = doSomething("grantToken", a, url = _AUTH_URL)

    # print("Authenticate result:", result)

    j = to_bytes(result)
    id_token = j["id_token"]

    return id_token

def listComponentTypes():
    printGetList("listComponentTypes?project=S",
                 output = "{name} ({code})")

def doMultiSomething(url, paramdata = None, method = None,
                     headers = None,
                     attachments = None):

    if verbose:
        print("Multi-part request to %s" % url)
        print("Send data: %s" % paramdata)
        print("Send headers: %s" % headers)
        print("method: POST")

    # print paramdata
    r = requests.post(url, data = paramdata, headers = headers,
                      files = attachments)

    if r.status_code in [500, 401]:
        print("Presumed auth failure")
        print(r.json())
        return None

    if r.status_code != 200:
        print(r)
        print(r.status_code)
        print(r.headers)
        print(r.text)
        r.raise_for_status()

    try:
        return r.json()
    except Exception as e:
        print("No json? ", e)
        return r.text

# Passed the uuAppErrorMap part of the message response
def decodeError(message, code):
    if "uu-app-server/internalServerError" in message:
        # Eg authentication problem "Signature verification raised"
        message = message["uu-app-server/internalServerError"]
        message = message["message"]
        print("Server responded with error message (code %d):" % code)
        myprint("\t%s" % message)
        return

    found = False

    for k in message.keys():
        if "cern-itkpd-main" in k:
            if "componentTypeDaoGetByCodeFailed" in k:
                found = True
                print("Either component type is invalid, or nothing found")
                continue
            elif "invalidDtoIn" in k:
                print("Decoding error message in %s" % k)
                found = True
        else:
            continue

        info = message[k]

        if "paramMap" in info:
            paramInfo = info["paramMap"]
            if "missingKeyMap" in paramInfo:
                for (k, v) in paramInfo["missingKeyMap"].items():
                    if len(v.keys()) == 1:
                        reason = v[list(v.keys())[0]]
                    else:
                        myprint("%s" % v.keys())
                        reason = v

                    if "$" in k:
                        # Seem to have $. in front
                        param_name = k[2:]
                    else:
                        param_name = k
                    myprint("Key '%s' missing: %s" % (param_name, reason))
            # There's probably also a invalidValueKeyMap which might be useful
        else:
            myprint(str(info))

    if not found:
        myprint("Unknown message: %s" % str(message))

def doRequest(url, data = None, headers = None, method = None):
    if method == "post" or method == "POST" or (method is None and data is not None):
        method = "POST"
    else:
        method = "GET"

    if verbose:
        print("Request to %s" % url)
        print("Send data %s" % data)
        print("Send headers %s" % headers)
        print("method %s" % method)

    if method == "POST":
        # print("Sending post")
        r = requests.post(url, data = data,
                          headers = headers)
    else:
        # print("Sending get")
        r = requests.get(url, data = data,
                         headers = headers)

    if r.status_code == 401:
        j = r.json()
        if "uuAppErrorMap" in j and len(j["uuAppErrorMap"]) > 0:
            if "uu-oidc/invalidToken" in j["uuAppErrorMap"]:
                global token
                print("Auth failure, need a new token!")
                token = None
                raise dbAccessError("Auth failure, token out of date")

    if r.status_code != 200:
        try:
            message = r.json()["uuAppErrorMap"]

            if verbose:
                print(r.status_code)
                print(r.headers)
                myprint("errormap: %s" % str(message))
            decodeError(message, r.status_code)
            raise dbAccessError("Error")
        except KeyError as a:
            myprint("Failed to decode error: %s" % str(a))
            # print(r)
            print(r.status_code)
            print(r.headers)
            print(r.text)
            raise dbAccessError("Bad status code")

    if "content-type" in r.headers:
        # Expect "application/json; charset=UTF-8"
        ct = r.headers["content-type"]
        if ct.split("; ")[0] != "application/json":
            myprint("Received unexpected content type: %s" % ct)
    else:
        print(r.headers)

    try:
        return r.json()
    except Exception as e:
        print("No json? ", e)
        return r.text

def doSomething(action, data = None, url = None, method = None,
                attachments = None):
    if testing:
        return doSomethingTesting(action, data, url, method, attachments)

    if token is None and url is None:
        setupConnection()
        if token is None:
            print("Authenticate failed")
            return

    if url is None:
        baseName = _SITE_URL
    else:
        baseName = url

    baseName += action

    if attachments is not None:
        # No encoding of data, as this is passed as k,v pairs
        headers = {"Authorization": "Bearer %s" % token}
        return doMultiSomething(baseName, paramdata = data,
                                headers = headers,
                                method = method, attachments = attachments)

    if data is not None:
        if type(data) is bytes:
            reqData = data
        else:
            reqData = to_bytes(json.dumps(data))
        if url is None: # Default
            pass # print("data is: ", reqData)
    else:
        reqData = None

    headers = {'Content-Type' : 'application/json'}
    # Header, token
    if token is not None:
        headers["Authorization"] = "Bearer %s" % token

    result = doRequest(baseName, data = reqData,
                       headers = headers, method = method)

    return result

def extractList(*args, **kw):
    "Extract data for a list of things (as json)"
    output = None
    if "output" in kw:
        output = kw["output"]
        del kw["output"]

    data = doSomething(*args, **kw)

    try:
        j = json.loads(data.decode("utf-8"))
    except ValueError:
        myprint("Response not json: %s" % str(data))
        return
    except AttributeError:
        # Already decoded to json (by requests)
        j = data
    if "pageItemList" not in j:
        if "itemList" in j:
            # Complete list
            l = j["itemList"]
        else:
            myprint(str(j))
            return
    else:
        # Sublist
        l = j["pageItemList"]

    if output is None:
        # All data
        return l
    else:
        # Just one piece
        if type(output) is list:
            result = []
            for i in l:
                result.append(list(i[o] for o in output))
            return result
        else:
            return [i[output] for i in l]

def printItem(item, format):
    print(format.format(**item))

def printGetList(*args, **kw):
    output = None
    if "output" in kw:
        output = kw["output"]
        del kw["output"]
    data = doSomething(*args, **kw)

    try:
        j = json.loads(data.decode("utf-8"))
    except ValueError:
        myprint("Response not json: %s" % data)
        return
    except AttributeError:
        # Already decoded to json (by requests)
        j = data
    if "pageItemList" not in j:
        if "itemList" in j:
            # Complete list
            l = j["itemList"]
        else:
            # print(str(j))
            l = [j]
    else:
        # Returned sublist
        l = j["pageItemList"]

    if verbose:
        myprint("%s" % l)

    if output is not None:
        for i in l:
            printItem(i, output)
    else:
        printList(l, "print_first" in kw)

# If output is short enough, can print on one line
def isShortDict(d):
    keys = d.keys()

    if "*" in keys: # Threshold bounds
        return True
    if "children" in keys and len(d["children"]) > 0:
        return False
    if "code" in keys and "name" in keys:
        return True
    if "properties" in keys and d["properties"] is not None:
        return False
    if "userIdentity" in keys:
        return True
    return False

simple_type_list = [bool, int, float, str]
if sys.version_info[0] == 2:
    simple_type_list.append(unicode)

def printDict(d, indentation=''):
    # First match common dicts
    keys = list(d.keys())

    if "*" in keys:
        # Threshold: {'*': {'max': None, 'nominal': None, 'min': None}
        print("%s\t*..." % indentation)
        return

    try:
        if "value" in keys:
            # Most things have these parameters
            out = ("%s%s (%s) = %s"
                   % (indentation, d["name"], d["code"], d["value"]))
            out = fix_encoding(out)
            print(out)
            keys.remove("code")
            keys.remove("name")
            keys.remove("value")
        elif "userIdentity" in keys:
            out = ("%s%s %s (%s)" % (indentation,
                                     d["firstName"], d["lastName"],
                                     d["userIdentity"]))
            out = fix_encoding(out)
            print(out)
            keys.remove("lastName")
            keys.remove("firstName")
            keys.remove("userIdentity")

            # NB We intentionally ignore middleName
        elif "componentType" in keys and "user" not in keys:
            # eg Children of component
            comp = d["componentType"]["code"]
            subtype = d["type"]["code"]
            comp_id = d["id"]
            out = ("%s%s/%s (%s)" % (indentation, comp, subtype, comp_id))
            out = fix_encoding(out)
            print(out)

            keys.remove("componentType")
            keys.remove("type")
            keys.remove("id")

            # For brevity, we ignore state, component, properties
        elif "comment" in keys:
            # Ignore datetime/user here
            myprint("%s%s" % (indentation, d["comment"]))
            keys.remove("comment")
        elif "filename" in keys:
            # Ignore datetime/user here
            myprint("%s%s" % (indentation, d["filename"]))
            keys.remove("filename")
        else:
            # Most else have these parameters
            out = ("%s%s (%s)"
                  % (indentation, d["name"], d["code"]))
            out = fix_encoding(out)
            print(out)
            keys.remove("code")
            keys.remove("name")

        # test-type schema
        if "valueType" in keys and d["dataType"] != "compound":
            myprint("%s  %s %s" % (indentation, d["valueType"], d["dataType"]))
            keys.remove("valueType")
            keys.remove("dataType")
        if "children" in keys:
            keys.remove("children")
            subdict = d["children"]
            if subdict != None:
                printList(subdict, False, indentation)

        if "properties" in keys:
            p = d["properties"]
            if p is None:
                pass
            else:
                # print("%sProperties:" % indentation)
                printList(p, False, indentation)
                keys.remove("properties")

        if "parameters" in keys:
            print("%sParameters:" % indentation)
            printList(d["parameters"], False, indentation)
            keys.remove("parameters")

        if "testTypes" in keys and d["testTypes"] is not None:
            print("%sTest types:" % indentation)
            printList(d["testTypes"], False, indentation)
            keys.remove("testTypes")

        if verbose:
            if len(keys) > 0:
                myprint("%s\t\t Skipped keys: %s" % (indentation, keys))

        return
    except TypeError:
        # eg attempt to index list with string
        if len(indentation) > 1:
            print("%s...Printing unknown dict" % indentation)
    except KeyError:
        # Mostly the lower-level dicts match above patterns
        if len(indentation) > 1:
            print(fix_encoding("%s...Printing unknown dict" % indentation))

            if verbose:
                print(fix_encoding("%s\t\t (all names: %s)" % (indentation, list(d.keys()))))

    indentation += "\t"

    # Generic
    for k, v in d.items():
        if v is None:
            print(fix_encoding("%s%s: null" % (indentation, k)))
        elif type(v) is str or (sys.version_info[0] == 2 and type(v) is unicode):
            print(fix_encoding("%s%s: %s" % (indentation, k,v)))
        elif type(v) in [bool, int, float]:
            print(fix_encoding("%s%s: %s" % (indentation, k,v)))
        elif type(v) is list:
            print(fix_encoding("%s%s (%d)" % (indentation, k, len(v))))
            printList(v, False, indentation)
        elif type(v) is dict:
            subdict = v
            # Sometimes short enough for one line
            if isShortDict(v):
                # No-new line difficult with Python 2 and 3
                sys.stdout.write("%s%s:" % (indentation, k))
                printDict(v, " ")
            else:
                print(fix_encoding("%s%s:" % (indentation, k)))
                printDict(v, indentation+"\t")
        else:
            myprint("%s?Type: %s: %s" % (indentation, k, v))

def printList(l, print_first, indentation='', location=''):
    first = True

    startLine = indentation + "\t"

    for i in l:
        if len(indentation) == 0:
            print("%sitem" % indentation)
        elif verbose:
            print("%sList item" % indentation)
        if len(indentation) > 0 and verbose:
            print(fix_encoding(str(i)))
        if first:
            if print_first:
                myprint("%sFirst: %s" % (startLine, i))
            first = False

        if type(i) is dict:
            printDict(i, startLine)
        elif type(i) in simple_type_list:
            print(fix_encoding("%s%s" % (startLine, i)))
        else:
            myprint("%s Unexpected type in list %s" % (indentation, type(i)))
            if verbose:
                print(i)

# listComponentTypes()

def summary(project="S"):
    print(" ===== Institutes =====")
    inst_output = "{name} ({code})"
    if sys.version_info[0] == 2:
        inst_output = u"{name} ({code})"

    printGetList("listInstitutions", method = "GET", output = inst_output)

    print(" ==== Strip component types =====")
    printGetList("listComponentTypes?project=%s" % project, method = "GET",
                 output = "{name} ({code})")
    # ({subprojects}) ({stages}) ({types})")

    # name, code
    #  Arrays: subprojects, stages, types

    type_codes = extractList("listComponentTypes", {"project": project}, method = "GET",
                             output = "code")

    print(" ==== Test types by component =====")
    type_codes = extractList("listComponentTypes", {"project": project}, method = "GET",
                             output = "code")
    for tc in type_codes:
        myprint("Test types for %s" % tc)
        printGetList("listTestTypes", {"project": project,
                                       "componentType": tc},
                     method = "GET", output = "  {name} ({code}) {state}")

# Produce some response without talking to DB
def doSomethingTesting(action, data = None, url = None, method = None,
                       attachments = None):
    if verbose:
        print("Testing request: %s" % action)
        print(" URL: %s" % url)
        print(" data: %s" % data)
        print(" method: %s" % method)
        print(" attachments: %s" % attachments)

    def encode(s):
        j = to_bytes(json.dumps(s))
        j = json.loads(j.decode("utf-8"))
        return j

    if action == "grantToken":
        return {'id_token': "1234567890abcdf"}
    if action == "listInstitutions":
        # Make sure there's some unicode in here
        return encode({"pageItemList": [
                {'code': 'UNIA', 'supervisor': u'First Second With\xe4t\xeda Last', 'name': u'Universit\xe4t A'}, {u'code': u'UNIB', u'supervisor': 'Other Name', 'name': 'University B'}
            ]})
    elif action == "listComponentTypes":
        # Make sure there's some unicode in here
        return encode({"pageItemList": [
                {'code': 'COMPA', 'name': u'Hybrid Type A'}, {u'code': u'COMPB', 'name': 'Module Type B'}
            ]})
    elif action == "listComponents":
        # Make sure there's some unicode in here
        return encode({"pageItemList": [
            {'code': 'HYBA', 'name': u'Hybrid A', 'trashed': False, 'institution': {'code': 'UNIA'}},
            {u'code': u'MODB', 'name': 'Module B', 'trashed': True, 'institution': {'code': 'UNIA'}}
            ]})

    raise dbAccessError("Action %s not known for testing" % action)
