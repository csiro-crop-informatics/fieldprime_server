TAG = :v1
IMAGE_NAME = fp_mysql
IMAGE_W_VER = $(IMAGE_NAME)$(TAG)
RUN_NAME = c_$(IMAGE_NAME)

#
# Data container. Will use docker generated folder in /var/lib/docker/volumes, but you could use a dedicated non docker dir also.
# Having a separate container Somewhat reduces the chance of accidentally deleting the database files.
# NB, this will exit immediately, having created the persistent volume.
#
volumeImage :
	docker run -v /var/lib/mysql --name c_fp_dbdata $(IMAGE_W_VER) echo "Data-only container for fpmysql"

#
# Mysql server container. This has to be running for access to the database.
#
run :
	docker run -d -it --name $(RUN_NAME) --volumes-from c_fp_dbdata -e MYSQL_ROOT_PASSWORD=foo $(IMAGE_W_VER)

# Attempt to try with host db directory, not tested, and probably not advisable if you use /var/lib/mysql independently.
# When I tried, file ownerships were changed and a reinstall of mysql was required.
#runHostDb :
#	docker run -d -it --name c_fp_mysql -e MYSQL_ROOT_PASSWORD=foo -v /var/lib/mysql:/var/lib/mysql fp_mysql:v1

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
clean.con.all :
	docker rm `docker ps -aq`
clean.dangling.images :
	docker rmi $$(docker images -q --filter "dangling=true")

########################################################################
