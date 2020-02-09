#!/bin/sh

# To provide your own python path, just add '--python=/path/to/python' after './build'
# For example: ./build.sh --python="/usr/bin/env python3.7"
# or           ./build.sh --python="/usr/local/munki/python"
if [[ ! -z ${1} ]]; then
    DIST_CMD=$(echo /usr/local/bin/python3 -m zipapp src --compress --output dist/zipapp/usr/local/bin/appleloops ${1})
else
    DIST_CMD=$(echo /usr/local/bin/python3 -m zipapp src --compress --output dist/zipapp/usr/local/bin/appleloops --python=\"/usr/bin/env python\")
fi

# If you have python3, then you can run this
if [ -f /usr/local/bin/python3 ]; then
    # Clean up
    /bin/rm dist/zipapp/usr/local/bin/appleloops &> /dev/null

    # Try and build.
    eval $DIST_CMD

    # If the file exists, we should build the pkg
    if [ -f dist/zipapp/usr/local/bin/appleloops ]; then
        /bin/cp dist/zipapp/usr/local/bin/appleloops appleloops
        /bin/chmod +x dist/zipapp/usr/local/bin/appleloops
        /bin/chmod +x appleloops
        /usr/bin/make
    fi
else
    echo "Python 3 is required to use zipapp. Exiting."
    exit 1
fi
