"""Dictionary of common cURL errors."""
# Sourced from https://curl.haxx.se/libcurl/c/libcurl-errors.html

CURL_ERRORS = {
    6: 'Could not resolve host',
    7: 'Failed to connect to host',
    9: 'Remote Access Denied',
    16: 'Problem with HTTP2 framing layer',
    18: 'File transfer shorter than expected',
    23: 'An error occurred writing to file',
    36: 'Download not resumed because offset was out of file boundary',
    47: 'Too many redirects',
    52: 'Nothing returned by the server',
    53: 'Specified crypto engine not found',
    54: 'Failed setting the selected SSL crypto engine as default',
    58: 'Problem with the local client certificate',
    59: 'Could not use specified cipher',
    60: 'Remote server SSL certificate or fingerprint not ok'
}
