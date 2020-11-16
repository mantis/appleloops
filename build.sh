#!/bin/sh

LOCAL_PYTHON=$(/usr/bin/which python3)

BUILD_DIR=dist/zipapp/usr/local/bin
BUILD_OUT=${BUILD_DIR}/appleloops

if [ ${LOCAL_PYTHON} == '' ]; then
    /bin/echo 'Python 3 is required. Exiting.'
    exit 1
fi

# To provide your own python path, just add '--python=/path/to/python' after './build'
# For example: ./build.sh --python="/usr/bin/env python3.7"
# or           ./build.sh --python="/usr/local/munki/python"
if [[ ! -z ${1} ]]; then
    DIST_CMD=$(echo /usr/local/bin/python3 -m zipapp src --compress --output ${BUILD_OUT} ${1})
else
    DIST_CMD=$(echo /usr/local/bin/python3 -m zipapp src --compress --output ${BUILD_OUT} --python=\"/usr/local/bin/python3\")
fi

# Clean up
/bin/rm ${BUILD_OUT} &> /dev/null

# Build
eval ${DIST_CMD}

# If the file exists, we can build the pkg
if [ -f ${BUILD_OUT} ]; then
    /bin/chmod +x ${BUILD_OUT}
    /bin/cp ${BUILD_OUT} .
    /usr/bin/make
fi
