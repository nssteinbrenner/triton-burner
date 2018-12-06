# triton-burner
Written on Python 3.7.1

Purpose of each file:

    triton.py - Definition of Triton class representation.
    tconfig.py - Defines values from a file called 'config' in the local directory (api keys, login info).
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

Changelog:

12/6/2018-

    - Changed tburner.py so that it is able to be daemonized (previously ran using timer)
    - Changed triton.py logWriter function to check for/create burned and log directories depending on if they exist.
    - Added WUnderground as a weather source.
    - Minor syntax changes/removed some redundant code

12/3/2018 -

    - Rewritten to use HTTP POST/GET requests. Web browser automation is slow and cumbersome comparatively.
    - Rewrote logging, consolidated all errors into a single file, and all burns are in a separate file.
    - Removed some of the redundant parts of the script. Example: Triton.setWeather() function.
    - Separated files according to their utility. While not a very large project, this makes editing the file a lot easier.
    - Used lxml instead of html.parser with BeautifulSoup, lxml is a lot faster.
    - Added a "donotburn" file. Tritons listed in this file will not be burned.
