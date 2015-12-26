#
# Extend Dumplton's image with his callback function
# that's already in the image, this references the context
# directory for scripts to run. For which we have a script
# to load some libraries required for some of the required
# python imports.
# The called function should prime python with the
# requirements.txt function in this dir if there is one.
#

FROM grahamdumpleton/mod-wsgi-docker:python-2.7

# Run script embedded in base
COPY requirements.txt /app/
COPY .whiskey /app/.whiskey
RUN mod_wsgi-docker-build

