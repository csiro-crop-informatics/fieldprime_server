#
# Extend mysql image with FieldPrime databases creation.
# Does not create any database user connection details
# or fieldprime users.
#

FROM mysql:5.7.10

RUN mkdir /fieldprime
WORKDIR /fieldprime


# Database creation
COPY sql/001_fpsys.sql /docker-entrypoint-initdb.d
COPY sql/002_fieldprime.sql /docker-entrypoint-initdb.d

# Database scripts/sql
COPY sql/fpsys.sql /fieldprime
COPY sql/fprime.create.tables.sql /fieldprime
COPY scripts/createProject.sh /fieldprime

# Create fieldprime server user, with password.  NOT VERY SECURE - And I think this now done in init.sql
#ENV MYSQL_USER=fpwserver MYSQL_PASSWORD=bar
#ENV MYSQL_USER=$FP_DB_USER MYSQL_PASSWORD=$FP_DB_PASS

