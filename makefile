fp_db_vol :
	docker volume create --name fp_db_vol

up :
	docker-compose up -d

build :
	docker-compose build


stop.all :
	docker stop `docker ps -q`

clean :
	rm fpsys.sql createProject.sh fprime.create.tables.sql
clean.con.all :
	docker rm `docker ps -aq`
clean.dangling.images :
	docker rmi $$(docker images -q --filter "dangling=true")
clean.volumes :
	docker volume rm $$(docker volume ls -qf dangling=true)

test.fp :
	curl https://***REMOVED***/fieldprime/

# Sample backup example from Docker docs, not tried yet..
backup :
	docker run --volumes-from fp_dbdata -v $(pwd):/backup ubuntu tar cvf /backup/backup.tar /dbdata

