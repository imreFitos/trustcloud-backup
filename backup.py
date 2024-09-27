#!/usr/bin/env python3
#
# Copyright (C) 2024 Imre Fitos
# Licensed under the terms of the MIT license
#
# Download all Policy, Control and Evidence history from TrustCloud
# 
# Usage: ./backup.py [directory to save TrustCloud data into]
#

import json
import os
import pprint
import re
import requests
import sys

api_key = os.environ.get("TRUSTCLOUD_API_KEY", "")
if not api_key:
    sys.exit("Please export your TrustCloud API key in the TRUSTCLOUD_API_KEY environment variable!")

if len(sys.argv) != 2:
    sys.exit("specify directory to download TrustCloud data to.")

os.mkdir(sys.argv[1])

destdir = sys.argv[1] + '/'

headers = {
    'Authorization': f'Bearer {api_key}',
    'x-trustcloud-api-version': '1'
}

# save policies - currently API does not allow exporting actual policy! bug filed
print("Saving policies:")
response = requests.get('https://backend.trustcloud.ai/policies', headers=headers)
response.raise_for_status()

policies = response.json()

os.mkdir(destdir + 'policies')
for p in policies:
    print(p["shortName"])
    with open(destdir + 'policies/' + p["shortName"], "w") as f:
        f.write(p["template"])

print("Finished saving policies")
print()

# save controls
print("Saving controls and evidences:")
controlurl = 'https://api.trustcloud.ai/controls?limit=50'
controls = []
while True:
    response = requests.get(controlurl, headers=headers)
    for i in response.json():
        controls.append(i)
    link_header = response.headers.get('link')
    if link_header == 'null':
        break
    controlurl = re.search('<(.+)>', link_header).group(1)

os.mkdir(destdir + 'controls')

for c in controls:
    print(c["controlId"])
    os.mkdir(destdir + 'controls/' + c["controlId"])
    with open(destdir + 'controls/' + c["controlId"] + '/metadata' , "w") as f:
        pprint.pp(c, stream=f)

    # get all tests for this control
    response = requests.get('https://api.trustcloud.ai/controls/' + c["id"] + '/tests?limit=50', headers=headers)
    tests = response.json()
    for t in tests:
        print(t["id"])
        response = requests.get('https://api.trustcloud.ai/tests/' + t["id"] + '/evidence?limit=50', headers=headers)
        evidences = response.json()
        for e in evidences:
            with open(destdir + 'controls/' + c["controlId"] + '/' + e["id"] , "w") as f:
                pprint.pp(e, stream=f)

print("Finished controls and evidences")
