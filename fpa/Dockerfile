FROM mod-wsgi-fp-pylibs
WORKDIR /app
COPY . /app/
RUN mkdir /app/fieldprime; \
  mkdir /app/fieldprime/wsessions; \
  chmod 777 /app/fieldprime/wsessions
# Should prob give permissions just to www-data

ENV FP_ROOT /app/fieldprime/
EXPOSE 80
ENTRYPOINT [ "mod_wsgi-docker-start" ]
CMD [ "--working-directory", "/app", "wsgi_adm_entry.py" ]
