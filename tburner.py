#!/usr/bin/env python

import sys
import os
import tfunctions


def runburn():
    loginurl = 'https://energy.vaisala.com/admin/login/'

    burnable = tfunctions.getBurnable(loginurl)
    tritons = tfunctions.tritonBuilder(burnable)
    donotburn = tfunctions.getDoNotBurn()

    tfunctions.issueBurn(tritons, donotburn)


if __name__ == '__main__':
    runburn()
    os.execv(__file__, sys.argv)
