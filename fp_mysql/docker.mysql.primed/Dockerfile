#
# Extend mysql image with FieldPrime databases and user.
# NB - only fpsys db created. Shell into containter and use
# createProject.sh to create user project database.
#

FROM mysql:5.7.10

RUN mkdir /fieldprime
WORKDIR /fieldprime

COPY fpsys.sql /fieldprime
COPY fprime.create.tables.sql /fieldprime
COPY createProject.sh /fieldprime

# Setup script to run on container creation:
COPY init.sql /docker-entrypoint-initdb.d

# Create fieldprime server user, with password.  NOT VERY SECURE
ENV MYSQL_USER=fpwserver MYSQL_PASSWORD=bar

