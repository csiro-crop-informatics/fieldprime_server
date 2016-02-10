#
# Build docker image with the current app code in it.
#
#

FROM fp_wsgi_pylibs
MAINTAINER Michael Kirk <***REMOVED***>

WORKDIR /app
ARG FPWS_PW=fpwserver:bar

# Copy in app source and other necessaries:
#COPY . /app/
COPY wsgi_adm_entry.py  /app/
COPY wsgi_app_entry.py  /app/
COPY fp_web_admin /app/fp_web_admin
COPY fp_common /app/fp_common
COPY fp_app_api /app/fp_app_api

# Argument to be applied to mod_wsgi-express start command:
COPY server_args /app/.whiskey
COPY sslStuff /app/sslStuff


RUN mkdir /app/fieldprime; \
  cd /app/fieldprime; \
  mkdir wsessions; \
  mkdir fplog; \
  touch fplog/dolog; \
  mkdir photos; \
  mkdir categoryImages; \
  mkdir crashReports; \
  echo $FPWS_PW > fppw; \
  chown -R whiskey /app/fieldprime /app/fp_web_admin /app/fp_common;


#chmod 777 /app/fieldprime/wsessions;
# Should prob give permissions just to www-data, currently it seems wsgi script is run as user whiskey

ENV FP_RUNTIME docker
ENV FP_ROOT /app/fieldprime/
EXPOSE 80
ENTRYPOINT [ "mod_wsgi-docker-start" ]
CMD [ "--working-directory", "/app", "wsgi_adm_entry.py" ]

