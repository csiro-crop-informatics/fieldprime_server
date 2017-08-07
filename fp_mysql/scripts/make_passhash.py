#!/usr/bin/python
import sys
from passlib.apps import custom_app_context as pwd_context
if len(sys.argv) != 2:
    print "Usage: python {0} <password>".format(sys.argv[0])
    exit()
password = sys.argv[1]
print pwd_context.encrypt(password)


