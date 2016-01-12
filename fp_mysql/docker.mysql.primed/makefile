TAG = :v1
IMAGE = fp_mysql
IMAGE_W_VER = $(IMAGE)$(TAG)
RUN_NAME = c_$(IMAGE)

#
# Data container. Will use docker generated folder in /var/lib/docker/volumes, but you could also use
# a dedicated non docker dir.
# Having a separate container Somewhat reduces the chance of accidentally deleting the database files.
# NB, this will exit immediately, having created the persistent volume.
#
volumeImage :
	docker run -v /var/lib/mysql --name c_fp_dbdata $(IMAGE) echo "Data-only container for fpmysql"

dataVol :
	docker volume create --name fp_dbdata

#
# Mysql server container. This has to be running for access to the database.
#
run :
	docker run -d -it --name $(RUN_NAME) --volumes-from c_fp_dbdata -e MYSQL_ROOT_PASSWORD=foo $(IMAGE)

# Attempt to try with host db directory, not tested, and probably not advisable if you use /var/lib/mysql independently.
# When I tried, file ownerships were changed and a reinstall of mysql was required.
#runHostDb :
#	docker run -d -it --name c_fp_mysql -e MYSQL_ROOT_PASSWORD=foo -v /var/lib/mysql:/var/lib/mysql fp_mysql:v1

shell :
	docker exec -it $(RUN_NAME) /bin/bash

bash :
	docker run -it --entrypoint=/bin/bash $(IMAGE) -i

fprime.create.tables.sql :
	cp ../$@ $@
createProject.sh :
	cp ../$@ $@
fpsys.sql : ../fpsys.sql
	cp $< $@
build : fpsys.sql createProject.sh fprime.create.tables.sql
	docker build --tag $(IMAGE) .

stop :
	docker stop $(RUN_NAME)

stop.all :
	docker stop `docker ps -q`

clean :
	rm fpsys.sql createProject.sh fprime.create.tables.sql
clean.con :
	docker rm $(RUN_NAME)
clean.con.all :
	docker rm `docker ps -aq`
clean.dangling.images :
	docker rmi $$(docker images -q --filter "dangling=true")

########################################################################
