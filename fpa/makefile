run :
	docker run -it --rm --name fpadm-running -p 8000:80 fpadm

shell :
	docker exec -it fpadm-running mod_wsgi-docker-shell

bash :
	docker run -it --entrypoint=/bin/bash fpadm -i

# Make image with needed python libraries installed :
build :
	docker build --tag fpadm .

stop :
	docker stop fpadm-running

clean :
	docker rm `docker ps -aq`
#	docker rmi $$(docker images -q --filter "dangling=true")
#

sql :
	docker run --name cmysql -e MYSQL_ROOT_PASSWORD=foo -d mysql:latest

runs :
	docker run --name fpadm-running --link cmysql:mysql -d -p 8000:80 fpadm

#	docker run --rm --name fpadm-running --link cmysql:mysql -d -p 8000:80 fpadm
