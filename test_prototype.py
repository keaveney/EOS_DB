#!/usr/bin/env python
import os, sys
import argparse
import json

import itk_pdb.dbAccess as dbAccess

class StandardCommand(object):
    def __init__(self, *args):
        self.action = args[0]
        self.allowed = args[1]
        self.required = list(self.allowed)
        if len(args) > 2:
            for o in args[2]:
                self.required.remove(o)

    def run(self, **kwargs):
        actionData = kwargs

        try:
            data = dbAccess.doSomething(self.action,
                                        method = "GET",
                                        data = actionData)
            if dbAccess.verbose:
                print(data)

            try:
                j = json.loads(data.decode("utf-8"))
            except AttributeError:
                j = data

            count = 0

            for d in j["pageItemList"]:
                code = d["code"]
                if self.test_type is not None and code != self.test_type:
                    continue

                count += 1
                p = build_prototype(d, j["componentType"])

                out = json.dumps(p, indent=4) # sort_keys=True
                fname = "prototype_%s.json" % code
                print("Saving %s" % fname)
                f = open(fname, 'w')
                f.write(out)
                f.close()

            if self.test_type is not None and count == 0:
                print("Test type %s not found in" % self.test_type)
                for d in j["pageItemList"]:
                    print("\t%s" % d["code"])
        except Exception as e:
            if not dbAccess.verbose:
                print("Request failed, use --verbose flag for more information")
            else:
                print("Request failed:")
                import traceback
                traceback.print_exc()

def type_proto(s, rep=None):
    if s["valueType"] == "array" and rep == None:
        return [type_proto(s, 1)]

    if rep == None and s["valueType"] != "single":
        return "unknown type %s %s" % (s["valueType"], s["dataType"])


    dt = s["dataType"]
    # valueType could indicate array?
    try:
        if dt == "compound":
            return dict([(d["code"], type_proto(d)) for d in s["children"]])
        return {
            "float": 0.0,
            "integer": 0,
            "boolean": False,
            "string": "some_string",
            }[s["dataType"]]
    except KeyError:
        return "unknown type %s" % s["dataType"]

def build_prototype(info, c):
    proto = {}
    proto["component"] = None
    proto["testType"] = info["code"]
    proto["institution"] = None
    proto["runNumber"] = "0-0"
    proto["passed"] = False
    proto["problem"] = False

    proto["properties"] = {}

    for v in info["properties"]:
        proto["properties"][v["code"]] = type_proto(v)

    proto["results"] = {}

    for v in info["parameters"]:
        proto["results"][v["code"]] = type_proto(v)

    if dbAccess.verbose:
        proto["raw_desc"] = info
        proto["raw_comp"] = c

    return proto

command = StandardCommand("listTestTypes", ["project", "componentType"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build prototype for test from production database")
    parser.add_argument("--component-type", help="Code for the type of component to query")
    parser.add_argument("--project", help="Code for the project, defaults to 'S' for Strips")
    parser.add_argument("--test-type", help="Code for the test type (default to all)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print what's being sent and received")

    args = parser.parse_args()

    if args.verbose:
        dbAccess.verbose = True

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    extraData = {}
    if args.component_type is not None:
        extraData["componentType"] = args.component_type

    if args.project is not None:
        extraData["project"] = args.project

    command.test_type = args.test_type

    data = command

    if "project" in data.allowed and "project" not in extraData:
        extraData["project"] = "S"

    for k in extraData.keys():
        if k not in data.allowed:
            print("Arg for %s not allowed" % (k))
            print(" need (%s)" % ', '.join(data.allowed))
            sys.exit(1)

    for k in data.required:
        if k not in extraData.keys():
            print("Arg for %s is required" % k)
            print(" need (%s)" % ', '.join(data.required))
            sys.exit(1)

    data.run(**extraData)
