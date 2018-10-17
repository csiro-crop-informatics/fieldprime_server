#
#
# Build docker image with the current app code in it.
#
#
FROM tiangolo/uwsgi-nginx-flask:python2.7

MAINTAINER Tim Erwin <tim.erwin@csiro.au>, Andrew Spriggs <andrew.spriggs.csiro.au>

# Application Directory
ENV FIELDPRIME_ROOT /app/
WORKDIR ${FIELDPRIME_ROOT}

#Environment variables that set application path and hostname
#These are used are global config variables defined in config.py

# Docker container hostname of mysql database
ENV FP_MYSQL_HOST fieldprime-mysql
ENV FP_MYSQL_PORT 3306

# Serve static /static/ directly from nginx
ENV STATIC_PATH /app/fp_web_admin/static/

# Install library deps
RUN apt-get update && apt-get install -y libmariadbclient-dev libldap2-dev libsasl2-dev
# Install python  deps
COPY requirements.txt ${FIELDPRIME_ROOT}
RUN pip install -r requirements.txt

# Logging
# TODO: pass this onto docker log handler
RUN mkdir ${FIELDPRIME_ROOT}fplog; \
    touch ${FIELDPRIME_ROOT}fplog/dolog; \
    chown -R www-data ${FIELDPRIME_ROOT}fplog;

#MySQL connection credentials, these needs to match details in init.sql
ARG FPWS_PW=fpwserver:bar

# Copy in app source and other necessaries:
COPY main.py ${FIELDPRIME_ROOT}
COPY conf/uwsgi.ini ${FIELDPRIME_ROOT}
COPY fp_web_admin ${FIELDPRIME_ROOT}/fp_web_admin
COPY fp_common ${FIELDPRIME_ROOT}/fp_common

#TODO permissions
RUN mkdir ${FIELDPRIME_ROOT}wsessions; \
    mkdir ${FIELDPRIME_ROOT}photos; \
    mkdir ${FIELDPRIME_ROOT}categoryImages; \
    mkdir ${FIELDPRIME_ROOT}crashReports; \
    echo $FPWS_PW > ${FIELDPRIME_ROOT}.fppw;
