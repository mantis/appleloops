#!/bin/sh

# If you have python3, then you can run this
if [ -f /usr/local/bin/python3 ]; then
    /usr/local/bin/python3 -m zipapp src --compress --output dist/zipapp/usr/local/bin/appleloops --python='/usr/bin/env python'
    /usr/local/bin/python3 -m zipapp src --compress --output appleloops --python='/usr/bin/env python'
    /usr/bin/make
else
    echo "Python 3 is required to use zipapp. Exiting."
    exit 1
fi
