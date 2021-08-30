FROM centos:latest

#ENV DEBIAN_FRONTEND=noninteractive

# install http server
RUN yum -y install httpd

# install ssh server
RUN yum install openssh-server -y \
 && yum install -y openssh-clients
RUN /usr/bin/ssh-keygen -A

# move all scripts that will run services (http and ssh)
RUN  mkdir services
COPY run_http_server services/run_http_server
COPY run_ssh_server services/run_ssh_server
COPY run_services.sh services/run_services.sh
COPY index.html /var/www/html/
RUN  chmod -R a+x /services

EXPOSE 22
EXPOSE 80

CMD ./services/run_services.sh
