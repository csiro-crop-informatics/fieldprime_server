#
# Extend mysql image with FieldPrime databases and user.
# NB - only fpsys db created. Shell into container and use
# createProject.sh to create user project database.
#

FROM mysql:5.7.10

#
# Optional build args to set mysql fp user name and password.
# Note these should be reset at run time for the data-only container:
#
# Sql syntax for changing password:
# ALTER USER user IDENTIFIED BY 'auth_string';
#
ARG FP_DB_USER=fpwserver
ARG FP_DB_PASS=barDef

RUN mkdir /fieldprime
WORKDIR /fieldprime

#
# Setup script to run on container creation, and files needed by it:
#
COPY sql/init.sql /docker-entrypoint-initdb.d
COPY sql/fpsys.sql /fieldprime
COPY sql/fprime.create.tables.sql /fieldprime
COPY scripts/createProject.sh /fieldprime

# Create fieldprime server user, with password.  NOT VERY SECURE - And I think this now done in init.sql
#ENV MYSQL_USER=fpwserver MYSQL_PASSWORD=bar
#ENV MYSQL_USER=$FP_DB_USER MYSQL_PASSWORD=$FP_DB_PASS

