#!/usr/bin/env/ python

with open('config', 'r') as f:
    lines = f.readlines()
    for line in lines:
        if 'darksky' in line:
            line = line.strip().split('=')
            darkapi = line[1]
        if 'google' in line:
            line = line.strip().split('=')
            googleapi = line[1]
        if 'password' in line:
            line = line.strip().split('=')
            energypass = line[1]
        if 'username' in line:
            line = line.strip().split('=')
            energyuser = line[1]
