drun :
	docker run -it --rm --name fpadm-running -p 8000:80 fpadm

dshell :
	docker exec -it fpadm-running mod_wsgi-docker-shell

# Make image with needed python libraries installed :
	docker build --tag fpadm .

