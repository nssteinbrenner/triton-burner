# triton-burner
Identifying information has been removed from this script. Strings containing 'redacted' indicate information that has been removed.

Written on Python 3.7.1

Purpose of each file:

    triton.py - Definition of Triton class representation.
    tconfig.py - Reads and defines values from a config file (api keys, login info).
    tfunctions.py - Defines functions needed to build the Triton objects.
    tburner.py - Calls functions from tfunctions.py to build/burn the Triton objects.
    requirements.txt - Required Python modules to run the script.

Config file format is as follows:

    [api]
    darksky={apikey}
    google={apikey}

    [login]
    username={username}
    password={password}

The [api] and [login] lines are optional. They have no meaning to the config reading script.

12/3/2018 -

    - Rewritten to use HTTP POST/GET requests. Web browser automation is slow and cumbersome comparatively.
    - Rewrote logging, consolidated all errors into a single file, and all burns are in a separate file.
    - Removed redundant parts of the script. For example, it previously checked 4 weather sources. Now checks the two most reliable.
    - Separated files according to their utility. While not a very large project, this makes editing the file a lot easier.
    - Used lxml instead of html.parser with BeautifulSoup, lxml is a lot faster.
    - Added a "donotburn" file. Tritons listed in this file will not be burned.
