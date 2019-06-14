import os, sys

print("Encoding: %s" % sys.stdout.encoding)
sys.stdout.flush()

os.environ["ITK_DB_AUTH"] = "0123456789abcdef"
os.environ["TEST_OVERRIDE"] = "1"
os.system("python read_db.py list_institutes")
