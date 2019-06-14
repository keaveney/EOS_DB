#!/usr/bin/env python
import os, sys
import argparse
import random
import itk_pdb.dbAccess as dbAccess

def assembleHybrid(hyb_id = None, abc_ids = []):
    pos = 0
    for a in abc_ids:
        dbAccess.doSomething("assembleComponent",
                             {"parent": hyb_id,
                              "child": a,
                              "properties": {"POSITION": pos}})
        pos += 1

def registerObject(p, sp, inst, ct, typ, props
):
    # Only particular institutes can register components?
    j = dbAccess.doSomething("registerComponent",
                    {"project": p, "subproject": sp,
                     "institution": inst, "componentType": ct,
                     "type": typ, "properties": props})
    print("Registered object (%s:%s)" % (ct,typ))
    # print(j)
    # extract reference (NB id is something different)

    code = j["component"]["code"]

    if dbAccess.verbose:
        print("Registered object: %s" % code)

    return code

def makeChips(chip_count):
    abc_ids = []

    for a in range(chip_count):
        myid = int(random.uniform(999999999, 1999999999))
        # Extract properties from list_component_types
        a_id = registerObject("S", "SG", "RL", "ABC", "ABC130",
                              {"ID": str(myid)})
        abc_ids.append(a_id)

    return abc_ids

def makeHybrid(test_flag):
    if test_flag:
        print("Test: not making anything")
        return

    hyb_id = registerObject("S", "SE", "RL", "HYBRID", "R0H0", {"RFID": "abcdef"})

    abc_ids = makeChips(20)

    assembleHybrid(hyb_id, abc_ids)

def makeWafer(test_flag):
    print("This doesn't work yet")
    return

known_things = ["hybrid", "wafer"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a test component in the production database")
    parser.add_argument("thing", help="Thing to be created (eg wafer, hybrid)")
    parser.add_argument("--test", action="store_true", help="Don't write to DB")
    parser.add_argument("--verbose", action="store_true",
                        help="Print what's being sent and received")

    args = parser.parse_args()

    print("Thing to create: %s" % args.thing)

    if args.thing not in known_things:
        print("Types of things:")
        for k in known_things:
            print("  %s" % k)
        sys.exit(1)

    if args.verbose:
        dbAccess.verbose = True

    if os.getenv("ITK_DB_AUTH"):
        dbAccess.token = os.getenv("ITK_DB_AUTH")

    try:
        if args.thing == "hybrid":
            makeHybrid(args.test)
        if args.thing == "wafer":
            makeWafer(args.test)
    except:
        if args.verbose:
            print("Request failed:")
            import traceback
            traceback.print_exc()
        else:
            print("Request(s) failed, use --verbose flag for more information")
