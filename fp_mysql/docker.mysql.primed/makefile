TAG = :v1
IMAGE_NAME = fp_mysql
IMAGE_W_VER = $(IMAGE_NAME)$(TAG)
RUN_NAME = c_$(IMAGE_NAME)


run :
	docker run -it --rm --name $(RUN_NAME) -e MYSQL_ROOT_PASSWORD=foo $(IMAGE_W_VER)

shell :
	docker exec -it $(RUN_NAME) /bin/bash

bash :
	docker run -it --entrypoint=/bin/bash $(IMAGE_W_VER) -i

fpsys.sql : ../fpsys.sql
	cp $< $@
fprime.sql : ../fprime.create.tables.sql
	echo 'create database fp_mk;' > $@
	echo 'use fp_mk;' >> $@
	cat $< >> $@
build : fprime.sql fpsys.sql
	docker build --tag $(IMAGE_W_VER) .

stop :
	docker stop $(RUN_NAME)

clean :
	rm fprime.sql fpsys.sql
#	docker rm `docker ps -aq`
#	docker rmi $$(docker images -q --filter "dangling=true")
#

sql :
	docker run --name cmysql -e MYSQL_ROOT_PASSWORD=foo -d mysql:latest

runs :
	docker run --name fpadm-running --link cmysql:mysql -d -p 8000:80 fpadm

#	docker run --rm --name fpadm-running --link cmysql:mysql -d -p 8000:80 fpadm
