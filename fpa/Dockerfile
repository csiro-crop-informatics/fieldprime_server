#
# Build docker image with the current app code in it.
#
#

FROM mod-wsgi-fp-pylibs
WORKDIR /app
COPY . /app/
RUN mkdir /app/fieldprime; \
  mkdir /app/fieldprime/wsessions; \
  chown whiskey /app/fieldprime/wsessions; \
  mkdir /app/fieldprime/fplog; \
  mkdir /app/fieldprime/photos; \
  mkdir /app/fieldprime/categoryImages; \
  mkdir /app/fieldprime/crashReports; \
  echo fpwserver:bar > /app/fieldprime/fppw

#chmod 777 /app/fieldprime/wsessions; 
# Should prob give permissions just to www-data, currently it seems wsgi script is run as user whiskey

ENV FP_ROOT /app/fieldprime/
EXPOSE 80
ENTRYPOINT [ "mod_wsgi-docker-start" ]
CMD [ "--working-directory", "/app", "wsgi_adm_entry.py" ]

