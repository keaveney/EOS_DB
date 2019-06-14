#!/usr/bin/env python

import json, httplib2, sys, os, getpass, requests, argparse
from requests.exceptions import RequestException

UU_OIDC_GATEWAY = "https://oidc.plus4u.net"
UU_OIDC_TOKEN_URI = "/uu-oidcg01-main/0-0/grantToken"

CMD_GATEWAY = "https://itkpd-test.unicorncollege.cz"
CMD_REGISTER_COMPONENT = '/registerComponent'
CMD_UPLOAD_TESTRUN_RESULTS = '/uploadTestRunResults'
CMD_CREATE_TESTRUN_ATTACHMENT = '/createTestRunAttachment'

# INPUT_FLD = "./input"
# INPUT_FLD_FILES = "C:/Users/Martin/Desktop/SensorUpload/"
# PROCESSED_FLD = "./processed"

http = httplib2.Http(".cache", disable_ssl_certificate_validation=True)

class CommandError(Exception):
    """Error thrown when some problem occures in communication with uuOIDC server. """
    def __init__(self, status, code, message):
        super(CommandError, self).__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def __str__(self):
        return str(self.status) + "," + self.code + "," + self.message

def Get_Sensor_Data(f, data):
    mainlines = []
    infolines = []
    infolist = []
    ivlist = {}

    for line in f:
        if (line.strip() == "#IV"):
            switch = 1
        elif (line[0] == '#'):
            switch = 0
            # print(f.readlines())
        if (not switch):
            if (line[0] != '#'):
                if (line[0] == "%"):
                    if (len(mainlines) != 0):
                        infolist.append(infolines)
                    infolines = []
                    line = line.strip()
                    if (line.strip('%') in mainlines):
                        line += '2'
                    mainlines.append(line.strip('%'))
                elif ((line != "\t\n") and (line != "\n")):
                    # line = ' '.join(line.split())
                    infolines.append(line)
        else:
            if ((line[0] != '#') and (line[0] != '-') and (line[0] != '\t')):
                ivlist[line[:line.find('\t')].strip()] = line[(line.find('\t') + 1):line.find('\n')].strip()

    infolist.append(infolines)

    for i in range(len(mainlines)):
        parameters = {}
        for j in infolist[i]:
            parameters[j[:j.find('\t')].strip()] = j[(j.find('\t') + 1):j.find('\n')].strip()
        data[mainlines[i]] = parameters

    data["RAWDATA"]["IV Characteristics (A)"] = ivlist

    if (data["TEST"]["PASSED"].upper() == "YES"):
        data["TEST"]["PASSED"] = True
    elif (data["TEST"]["PASSED"].upper() == "NO"):
        data["TEST"]["PASSED"] = False

    if (data["TEST"]["PROBLEM"].upper() == "YES"):
        data["TEST"]["PROBLEM"] = True
    elif (data["TEST"]["PROBLEM"].upper() == "NO"):
        data["TEST"]["PROBLEM"] = False

    print(data)
    print("")

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
        raise CommandError(status, error_json["code"], error_json["message"])

def load_json_file(json_file_path):
    try:
        with open(json_file_path) as json_file:
            json_file_data = json.load(json_file)
        return json_file_data
    except IOError:
        return None

def create_testrun_attachment(token, dir, code, INPUT_FLD_FILES):
    headers = {'Authorization':'Bearer '+ token}

    url = CMD_GATEWAY + CMD_CREATE_TESTRUN_ATTACHMENT


    files = {'data': (dir, open(INPUT_FLD_FILES + dir, 'rb'))}
    data={
        "testRun": code,
        "title": "Manufacturer's data",
        "description": "General information and initial test results of the sensor.",
        "data": (dir, open(INPUT_FLD_FILES + dir, 'rb'))
    }

    response = requests.post(url, headers=headers, files=files, data=data)

def register_component(token, info):
  headers = {'Authorization':'Bearer '+ token,
             'Content-type':'application/json'}

  url = CMD_GATEWAY + CMD_REGISTER_COMPONENT

  dto_in = {
      "project" : "S",
      "subproject" : info["ITEM"]["Identification Number"][3:5],
      "institution" : "CUNI",
      "componentType" : "SENSOR",
      "type" : info["ITEM"]["Identification Number"][5:7],
      "serialNumber" : info["ITEM"]["Identification Number"],
      "properties" : {
          "ID" : info["ITEM"]["Serial Number"]
      }
  }

  response, content = http.request(url, "POST", headers=headers, body=json.dumps(dto_in))

  if response.status >= 200 and response.status < 300:
    response_json = str(content.decode())
    return response_json
  else:
    status = response.status
    error_json = json.loads(str(content))
    raise CommandError(status, error_json["code"], error_json["message"])

def upload_manufacturer_testrun_results(token, info, comp_code):
    headers = {'Authorization': 'Bearer ' + token,
               'Content-type': 'application/json'}

    url = CMD_GATEWAY + CMD_UPLOAD_TESTRUN_RESULTS

    dto_in = {
        "component": comp_code,
        "testType": "MANUFACTURING",
        "institution": "CUNI",
        "runNumber": "1",
        "passed": info["TEST"]["PASSED"],
        "properties": {
            "DATE": info["TEST"]["Test Date (DD/MM/YYYY)"],
            "SUBSTRATE_TYPE" : info["DATA"]["Substrate Type"],
            "SUBSTRATE_LOT" : info["DATA"]["Substrate Lot No."],
            "SUBSTRATE_ORIENT" : int(info["DATA"]["Substrate Orient"]),
            "SUBSTRATE_R_UPPER" : float(info["DATA"]["Substrate R Upper (kOhm.cm)"]),
            "SUBSTRATE_R_LOWER" : float(info["DATA"]["Substrate R Lower (kOhm.cm)"]),
            "THICKNESS_A" : int(info["DATA"]["Thickness(A: top-left) (micron)"]),
            "THICKNESS_B": int(info["DATA"]["Thickness(B: top-right) (micron)"]),
            "THICKNESS_C": int(info["DATA"]["Thickness(C: center) (micron)"]),
            "THICKNESS_D": int(info["DATA"]["Thickness(D: bottom-left) (micron)"]),
            "THICKNESS_E": int(info["DATA"]["Thickness(E: bottom-right) (micron)"])
        },
        "results" : {
            "PROBLEM" : info["TEST"]["PROBLEM"],
            "IV_TEMPERATURE" : int(info["DATA"]["IV Temperature(C)"]),
            "DEPLETION_VOLTS" : int(info["DATA"]["Deplation Volts (V)"]),
            "LEAKAGE_CURRENT_200": -1,
            "LEAKAGE_CURRENT_600": -1,
            "LEAKAGE_CURRENT_VFD" : float(info["DATA"]["Leakage Current at Vfd + 50V (microA)"]),
            "LEAKAGE_CURRENT_700" : float(info["DATA"]["Leakage current at 700 V (microA)"]),
            "ACTIVE_THICKNESS" : int(info["DATA"]["Active thickness (nominal value)"]),
            "BIAS_RESISTANCE_U" : float(info["DATA"]["Polysilicon Bias Resistance Upper (MOhm)"]),
            "BIAS_RESISTANCE_L" : float(info["DATA"]["Polysilicon Bias Resistance Lower (MOhm)"]),
            "ONSET_VOLTAGE_MICRODISCHARGE" : info["DATA"]["Onset voltage of Microdischarge (V)"]
        },
        "defects" : [
            {
                "name" : "Oxide Pinholes",
                "description" : info["DEFECT"]["Oxide pinholes"]
            },
            {
                "name" : "Metal Shorts",
                "description" : info["DEFECT"]["Metal Shorts"]
            },
            {
                "name" : "Metal Opens",
                "description" : info["DEFECT"]["Metal Opens"]
            },
            {
                "name" : "Implant Shorts",
                "description" : info["DEFECT"]["Implant Shorts"]
            },
            {
                "name" : "Implant Opens",
                "description" : info["DEFECT"]["Implant Opens"]
            },
            {
                "name" : "Microdischarge Strips",
                "description" : info["DEFECT"]["Microdischarge strips"]
            },
            {
                "name" : "Percentage of NG Strips",
                "description" : info["DEFECT"]["Percentage of NG strips"]
            }
        ]
    }

    response, content = http.request(url, "POST", headers=headers, body=json.dumps(dto_in))

    if response.status >= 200 and response.status < 300:
        response_json = str(content.decode())
        return response_json
    else:
        status = response.status
        error_json = json.loads(str(content))
        raise CommandError(status, error_json["code"], error_json["message"])

def upload_iv_results(token, info, comp_code):
    headers = {'Authorization': 'Bearer ' + token,
               'Content-type': 'application/json'}

    url = CMD_GATEWAY + CMD_UPLOAD_TESTRUN_RESULTS

    voltage_list = []
    current_list = []
    for j in info["RAWDATA"]["IV Characteristics (A)"]:
        try:
          current_list.append(float(info["RAWDATA"]["IV Characteristics (A)"][j]))
          voltage_list.append(int(j))
        except:
            pass

    dto_in = {
        "component": comp_code,
        "testType": "IV",
        "institution": "CUNI",
        "runNumber": "1",
        "passed": info["TEST"]["PASSED"],
        "properties" : {
            "TEMPERATURE" : int(info["RAWDATA"]["IV Temperature(C)"]),
            "HUMIDITY" : int(info["RAWDATA"]["Humidity (%)"]),
            "VOLTAGE_STEP" : int(info["RAWDATA"]["Voltage step (V)"]),
            "DELAY" : int(info["RAWDATA"]["Delay time (second)"]),
            "VOLTAGE_START" : voltage_list[0],
            "VOLTAGE_END" : voltage_list[-1]
        },
        "results" : {
            "VOLTAGE" : voltage_list,
            "CURRENT" : current_list
        }
    }

    response, content = http.request(url, "POST", headers=headers, body=json.dumps(dto_in))

    if response.status >= 200 and response.status < 300:
        response_json = str(content.decode())
        return response_json
    else:
        status = response.status
        error_json = json.loads(str(content))
        raise CommandError(status, error_json["code"], error_json["message"])

def process_files_in_folder(token, INPUT_FLD_FILES):
    txt_files = list(filter(lambda x: x[-4:] == '.txt', os.listdir(INPUT_FLD_FILES)))
    for dir in txt_files:
        file = open(INPUT_FLD_FILES + dir, "r")
        data = {}
        Get_Sensor_Data(file, data)
        file.close()
        response_json = register_component(token, data)
        sensor_code = json.loads(response_json)["component"]["code"]
        resp = upload_manufacturer_testrun_results(token, data, sensor_code)
        print(resp)
        print("")
        testrun_code = json.loads(resp)["testRun"]["id"]
        create_testrun_attachment(token, dir, testrun_code, INPUT_FLD_FILES)
        resp_iv = upload_iv_results(token, data, sensor_code)
        print(resp_iv)
        print("")

def main(args):
    try:
        INPUT_FLD_FILES = args.INPUT_FLD_FILES
        print("")
        print("*** ITk Production Database Bot ***")
        print("Please, sign in to the ITk Production Database")
        print("")
        access_code_1 = getpass.getpass("Access Code 1: ")
        access_code_2 = getpass.getpass("Access Code 2: ")
        token = oidc_grant_token(access_code_1, access_code_2)
        token_json = json.loads(token)
        print("Welcome to the ITk Production Database! Your requirement is being processing ...")
        print("")
        process_files_in_folder(token_json["id_token"], INPUT_FLD_FILES)
    except RequestException as e:
        print('Request exception: ' + str(e))
        exit(1)
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Batch register/upload sensor data to the ITkPD', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    required = parser.add_argument_group('required arguments')
    required.add_argument('-i', '--INPUT-FLD-FILES', dest = 'INPUT_FLD_FILES', type = str, required = True, help = 'Location of manufacturer test results files')

    args = parser.parse_args()
    sys.exit(main(args))
