#
#
# Build docker image with the current app code in it.
#
#
FROM fp_wsgi_pylibs
MAINTAINER Michael Kirk <michael.kirk@csiro.au>, Tim Erwin <tim.erwin@csiro.au>

#Environment variables that set application path and hostname
#These are used are global config variables defined in config.py
ENV FP_ROOT /app/
# Docker container hostname of mysql database
ENV FP_MYSQL_HOST fp_mysql
WORKDIR ${FP_ROOT}

#MySQL connection credentials, these needs to match details in init.sql
ARG FPWS_PW=fpwserver:bar

# Copy in app source and other necessaries:
COPY fp_admin_entry.wsgi ${FP_ROOT}
COPY fp_web_admin ${FP_ROOT}fp_web_admin
COPY fp_common ${FP_ROOT}fp_common

COPY sslCerts /app/sslCerts

# Argument to be applied to mod_wsgi-express start command:
COPY server_args ${FP_ROOT}.whiskey

RUN mkdir ${FP_ROOT}wsessions; \
    mkdir ${FP_ROOT}photos; \
    mkdir ${FP_ROOT}categoryImages; \
    mkdir ${FP_ROOT}crashReports; \
    mkdir ${FP_ROOT}fplog; \
    touch ${FP_ROOT}fplog/dolog; \
    echo $FPWS_PW > ${FP_ROOT}.fppw; \
    chown -R whiskey ${FP_ROOT};

#TODO: File permissions?
# /app/fieldprime/wsessions;
# Should prob give permissions just to www-data, currently it seems wsgi script is run as user whiskey

EXPOSE 80
ENTRYPOINT [ "mod_wsgi-docker-start" ]

#uid=whiskey,gid=root
USER $MOD_WSGI_USER:$MOD_WSGI_GROUP
CMD [ "fp_admin_entry.wsgi" ]
