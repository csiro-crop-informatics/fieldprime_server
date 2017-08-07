#
# Extend Dumplton's mod-wsgi-docker:python-2.7 image to make
# an image that has the required libraries installed and the
# the required python imports. 
#
# This is done using the build script that's already in the
# mod-wsgi-docker image. This script (mod_wsgi-docker-build)
# references the /app directory for stuff to do, in particular
# it pip installs from any requirements.txt file, and runs 
# script /app/.whiskey/action_hooks/pre-build if present.
# For which we have a script to load some libraries required
# for some of the required python imports.
#
# Note this can be done with the image "onbuild" provided
# by Dumpleton (which will copy from the context directory
# to /app and run the build script). But we don't want to
# go through installing the libraries we need and the standard
# pip installs every time we make a change to the app code.
# Hence this intermediate image which has these things, but
# not the app code which we load when extending this image.
#

FROM grahamdumpleton/mod-wsgi-docker:python-2.7

# Copy in requirements.txt and set up script and run embedded build script:
COPY requirements.txt /app/
COPY .whiskey /app/.whiskey
RUN mod_wsgi-docker-build

