run :
	docker run -it --rm --name fpadm-running -p 8000:80 fpadm

shell :
	docker exec -it fpadm-running mod_wsgi-docker-shell

bash :
	docker run -it --entrypoint=/bin/bash fpadm -i

# Make image with needed python libraries installed :
build :
	docker build --tag fpadm .

