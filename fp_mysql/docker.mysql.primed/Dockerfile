#
# Extend mysql image with FieldPrime databases and user.
#

FROM mysql:5.7.10

RUN mkdir /fieldprime
WORKDIR /fieldprime

# Create fpsys and fp_mk databases:
COPY fpsys.sql /docker-entrypoint-initdb.d
COPY fprime.sql /docker-entrypoint-initdb.d

