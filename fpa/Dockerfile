FROM grahamdumpleton/mod-wsgi-docker:python-2.7-onbuild
WORKDIR /app
ONBUILD COPY . /app
EXPOSE 80
ENTRYPOINT [ "mod_wsgi-docker-start" ]
CMD [ "--working-directory", "/app", "wsgi_adm_entry.py" ]
