Install:
pip install numpy requests pyshp

Usage: GPSParse.py [-h] [-o OUT] [-v FOV] [-g NPOINTS] [-k KEY_FILE] [-e ELEV]
                   [-s] [-l LOG_FILE]
                   gps_file

Convert gps log textfile to shapefile

positional arguments:
  gps_file              Input file of tab-separated gps coordinates. File
                        Format: lon lat alt roll pitch yaw

optional arguments:
  -h, --help            show this help message and exit
  -o OUT, --out OUT     Name of shapefile to write (default out.shp)
  -v FOV, --fov FOV     Field of view of spectrometer being used (default 17
                        degrees)
  -g NPOINTS, --google-elev NPOINTS
                        Number of elevation points to request from the Google
                        API (default 1). Elevations are interpolated evenly
                        throughout the scan area. Note: Requires a google API
                        key (see --key-file)
  -k KEY_FILE, --key-file KEY_FILE
                        Location of file containing Google API key to use for
                        Google Maps elevation requests. If not specified,
                        program will try to read ./key.txt
  -e ELEV, --elev ELEV  Use a single elevation value (in meters) for the whole
                        reading instead of using the google elevation api
  -s, --smooth          Produce a shapefile with fewer jagged edges
  -l LOG_FILE, --log-meta LOG_FILE
                        Append metadata to a log file. Creates the log file if
                        it doesn't exist
