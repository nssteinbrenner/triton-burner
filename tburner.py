#!/usr/bin/env python

import tfunctions

loginurl = 'https://energy.redacted.com/admin/login/'

burnable = tfunctions.getBurnable(loginurl)
tritons = tfunctions.tritonBuilder(burnable)
donotburn = tfunctions.getDoNotBurn()

tfunctions.issueBurn(tritons, donotburn)
