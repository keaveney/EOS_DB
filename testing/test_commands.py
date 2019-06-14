import os, sys

# Don't do real connection to DB
os.environ["ITK_DB_AUTH"] = "0123456789abcdef"
os.environ["TEST_OVERRIDE"] = "1"

def runScriptTest(cl):
    print("Running command %s" % cl)
    py = sys.executable

    assert os.system("%s %s" % (py, cl)) == 0

def runScriptWithArgs(cl, args):
    for a in args:
        cmd = cl + " " + a
        runScriptTest(cmd)

def test_list_institutes(capsys):
    runScriptTest("read_db.py list_institutes")

def test_get_inventory(capsys):
    for invTest in ["listInstitutions", "listComponentTypes",
                    "listInventory", "trashUnassembled"]:
        args = [""]
        if invTest == "listInventory":
            args.append("--institution INST")

        runScriptWithArgs("getInventory.py %s" % invTest, args)
