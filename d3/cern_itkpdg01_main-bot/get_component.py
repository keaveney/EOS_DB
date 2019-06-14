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
CMD_GET_COMPONENT = '/cern-itkpd-test/' + TID + '-' + AWID + '/getComponent'
CMD_GET_BINARY_DATA = '/cern-itkpd-test/' + TID + '-' + AWID + '/uu-app-binarystore/getBinaryData'

INPUT_FILE = "./input/get_component.json"
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
  dto_out = get_component(token, dto_in)
  output_file = open(OUTPUT_FLD + "/get_component.json", "w")
  output_file.write(dto_out)
  output_file.close()
  dto_out_json = json.loads(dto_out)
  if dto_out_json['attachments']:
    download_attachments(token, dto_out_json['attachments'])

def download_attachments(token, attachments):
  for attachment in attachments:
    dto_in = {'code': attachment['code']}
    binary = get_binary_data(token, dto_in)
    with open(OUTPUT_FLD + "/" + attachment['filename'], "wb") as file:
      file.write(binary.content)

def get_binary_data(token, dto_in):
  headers = {'Authorization': 'Bearer ' + token,
             'Content-type': 'application/json'}

  url = CMD_GATEWAY + CMD_GET_BINARY_DATA

  response = requests.get(url, headers=headers, params=dto_in)
  return response

def get_component(token, dto_in):
  headers = {'Authorization':'Bearer '+ token,
             'Content-type':'application/json'}

  url = CMD_GATEWAY + CMD_GET_COMPONENT

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
#    access_code_1 = getpass.getpass("Access Code 1: ")
#    access_code_2 = getpass.getpass("Access Code 2: ")
    access_code_1 = "ucl001"
    access_code_2 = "mar123ek1"

    token = oidc_grant_token(access_code_1, access_code_2)
    token_json = json.loads(token)
    print("Welcome to the ITk Production Database! Retrieving component details is being processed ...")
    print("")
    process_input_file(token_json["id_token"])
except Exception as e:
    print('500,CLIENT_UNEXPECTED_ERROR,' + str(e))
    exit(1)
