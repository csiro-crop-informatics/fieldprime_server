IMAGE_NAME = fp_adm
CONT_NAME = c_$(IMAGE_NAME)

run :
	docker run --name $(CONT_NAME) --link c_fp_mysql:mysql -d -p 8000:80 $(IMAGE_NAME)

shell :
	docker exec -it $(CONT_NAME) mod_wsgi-docker-shell

bash :
	docker run -it --entrypoint=/bin/bash $(IMAGE_NAME) -i

# Make image with needed python libraries installed :
build :
	docker build --tag $(IMAGE_NAME) .

stop :
	docker stop $(CONT_NAME)

kill :
	docker stop $(CONT_NAME)
	docker rm $(CONT_NAME)

zap :
	make kill
	make build
	make run
	make shell

clean :
	docker rm `docker ps -aq`
#	docker rmi $$(docker images -q --filter "dangling=true")
