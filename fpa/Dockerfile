FROM mod-wsgi-fp-pylibs
WORKDIR /app
COPY . /app/
EXPOSE 80
ENTRYPOINT [ "mod_wsgi-docker-start" ]
CMD [ "--working-directory", "/app", "wsgi_adm_entry.py" ]
