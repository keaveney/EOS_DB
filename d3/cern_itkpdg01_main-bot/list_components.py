#!/usr/bin/python
import json
import httplib2
import sys
import os
import getpass
from pathlib import Path
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

UU_OIDC_GATEWAY = "https://oidc.plus4u.net"
UU_OIDC_TOKEN_URI = "/uu-oidcg01-main/0-0/grantToken"

CMD_GATEWAY = "https://uuos9.plus4u.net"
TID = "98234766872260181"
AWID = "dcb3f6d1f130482581ba1e7bbe34413c"
CMD_LIST_COMPONENTS = '/cern-itkpd-test/' + TID + '-' + AWID + '/listComponents'

INPUT_FILE = "./input/list_components.json"
OUTPUT_FLD = "./output"

http = httplib2.Http()

class CommandError(Exception):
  def __init__(self, status, uu_app_error_map):
    super(CommandError, self).__init__(uu_app_error_map)
    self._status = status
    self._code = list(uu_app_error_map.keys())[0]
    self._message = uu_app_error_map[self._code]['message']

  def __str__(self):
    return str(self._status) + "," + self._code + "," + self._message

def oidc_grant_token(access_code_1, access_code_2):
    post_data = {"grant_type": "password",
                 "username": access_code_1,
                 "password": access_code_2
                }

    headers = {'Content-Type': 'application/json'}

    url = UU_OIDC_GATEWAY + UU_OIDC_TOKEN_URI

    response, content = http.request(url, "POST", headers=headers, body=json.dumps(post_data))

    if response.status >= 200 and response.status < 300:
        token_json = str(content.decode())
        return token_json
    else:
        status = response.status
        error_json = json.loads(str(content.decode()))
        raise CommandError(status, error_json['uuAppErrorMap'])

def load_json_file(json_file_path):
    try:
        with open(json_file_path) as json_file:
            json_file_data = json.load(json_file)
        return json_file_data
    except IOError:
        return None

def process_input_file(token):
  dto_in = load_json_file(INPUT_FILE)
  dto_out = list_components(token, dto_in)
  output_file = open(OUTPUT_FLD + "/list_components.json", "w")
  output_file.write(dto_out)
  output_file.close()

def list_components(token, dto_in):
  headers = {'Authorization':'Bearer '+ token,
             'Content-type':'application/json'}

  url = CMD_GATEWAY + CMD_LIST_COMPONENTS

  response, content = http.request(url, "GET", headers=headers, body=json.dumps(dto_in))

  if response.status >= 200 and response.status < 300:
    response_json = str(content.decode())
    return response_json
  else:
    status = response.status
    error_json = json.loads(str(content.decode()))
    raise CommandError(status, error_json['uuAppErrorMap'])

try:
    print("*** ITk Production Database Bot ***")
    print("Please, sign in to the ITk Production Database")
    print("")
    access_code_1 = getpass.getpass("Access Code 1: ")
    access_code_2 = getpass.getpass("Access Code 2: ")

    token = oidc_grant_token(access_code_1, access_code_2)
    token_json = json.loads(token)
    print("Welcome to the ITk Production Database! Retriving components is being processed ...")
    print("")
    process_input_file(token_json["id_token"])
except Exception as e:
    print('500,CLIENT_UNEXPECTED_ERROR,' + str(e))
    exit(1)
