TAG = :v1
IMAGE_NAME = fp_mysql
IMAGE_W_VER = $(IMAGE_NAME)$(TAG)
RUN_NAME = c_$(IMAGE_NAME)

# Data container. Will use docker generated folder in /var/lib/docker/volumes, but you could use a dedicated non docker dir also.
volumeImage :
	docker run -v /var/lib/mysql --name c_fp_dbdata $(IMAGE_W_VER) echo "Data-only container for fpmysql"

run :
	docker run -d -it --name $(RUN_NAME) --volumes-from c_fp_dbdata -e MYSQL_ROOT_PASSWORD=foo $(IMAGE_W_VER)

shell :
	docker exec -it $(RUN_NAME) /bin/bash

bash :
	docker run -it --entrypoint=/bin/bash $(IMAGE_W_VER) -i

setup.sql :
	echo source fpsys.sql > $@
	echo source fprime.sql >> $@
	echo 'grant all on fpsys.* to fpwserver;' >> $@
	echo "CREATE USER fpwserver@localhost IDENTIFIED BY 'bar';" >> $@
	echo 'grant all on fpsys.* to fpwserver@localhost;' >> $@
fprime.create.tables.sql :
	cp ../$@ $@
createProject.sh :
	cp ../$@ $@
fpsys.sql : ../fpsys.sql
	cp $< $@
fprime.sql : ../fprime.create.tables.sql
	echo 'create database fp_mk;' > $@
	echo 'use fp_mk;' >> $@
	cat $< >> $@
build : fprime.sql fpsys.sql setup.sql createProject.sh fprime.create.tables.sql
	docker build --tag $(IMAGE_W_VER) .

stop :
	docker stop $(RUN_NAME)

clean :
	rm fprime.sql fpsys.sql setup.sql fprime.create.tables.sql

clean.con :
	docker rm $(RUN_NAME)
#	docker rm `docker ps -aq`

clean.dangling.images :
	docker rmi $$(docker images -q --filter "dangling=true")

########################################################################

sql :
	docker run --name cmysql -e MYSQL_ROOT_PASSWORD=foo -d mysql:latest

runs :
	docker run --name fpadm-running --link cmysql:mysql -d -p 8000:80 fpadm

#	docker run --rm --name fpadm-running --link cmysql:mysql -d -p 8000:80 fpadm
