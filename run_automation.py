import os
import subprocess
import platform
import distro
import sys
import logging

def check_requirements(pyth_ver,distr,ver):
    if sys.version_info[0] < pyth_ver:
       logging.info("Test automation was aborted due to the wrong version of python on the host machine. Please use version 3.")
       raise Exception("Please use the latest version of python.")

    if distro.linux_distribution()[0] != distr:
       logging.info("Test automation was aborted due to a wrong Linux distribution. Please use Ubuntu.")
       raise Exception("This is supported only on Ubuntu.")
    else:
       if distro.linux_distribution()[1] != ver:
          logging.info("Test automation was aborted due to a wrong Ubuntu version. Please use 20.04")
          raise Exception("This is supported only on Ubuntu 20.04.")

def add_to_logs(returnCode,refcode,text):
    if returnCode == refcode:
      logging.info(text+": Success.")
    else:
      logging.info(text+": Fail.")
      raise Exception(text+": Fail.")


def check_output(command):
    out = str(subprocess.Popen(command,
                shell=True,
                stdout=subprocess.PIPE,
                universal_newlines=True).communicate()[0].rstrip())
    return out


if __name__ == '__main__':

  http_port      = 80
  ssh_port_cont  = 22
  ssh_port_host  = 22022

  logging.basicConfig(filename="./automation_log.txt",
                      filemode='w',
                      format='%(asctime)s, %(message)s',
                      datefmt='%m/%d/%Y %I:%M:%S %p',
                      level=logging.DEBUG)

  logging.info("Test automation has started.")

  check_requirements(3,'Ubuntu','20.04')

  # Build container B image that sets up a webserver
  build_B = subprocess.run("docker build -t webserver:v1 ./Container_B/.",shell=True) 
  add_to_logs(int(build_B.returncode),0,"Building webserver container B")

  # Build container A image that will test container B
  build_A = subprocess.run("docker build -t test_machine:v1 ./Container_A/.",shell=True) 
  add_to_logs(int(build_A.returncode),0,"Building test machine container A")
 
  # Deploy container B
  if 'container_B' in check_output('docker container ls'):
     if 'running' in check_output('docker container inspect -f {{.State.Status}} container_B'):
         subprocess.run("docker kill container_B",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  deploy_B = subprocess.run("docker run -dit --rm -p "+str(ssh_port_host)+":"+str(ssh_port_cont)+" -p "+str(http_port)+":"+str(http_port)+" --name container_B webserver:v1" \
                            ,shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  add_to_logs(int(deploy_B.returncode),0,"Deploying webserver container B")

  # Deploy container A
  if 'container_A' in check_output('docker container ls'):
      if 'running' in check_output('docker container inspect -f {{.State.Status}} container_A'):
          subprocess.run("docker kill container_A",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  deploy_A = subprocess.run("docker run -dit --rm --name container_A test_machine:v1",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  add_to_logs(int(deploy_A.returncode),0,"Deploying test machine container A")


  # Get ids of both deployed containers
  b_id = check_output("docker ps -aqf 'name=container_B'")
  a_id = check_output("docker ps -aqf 'name=container_A'")

  # Create local network
  network_exists = subprocess.run("docker network inspect net2connect_A_B" ,shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  if network_exists.returncode != 0:
    subprocess.run("docker network rm net2connect_A_B" ,shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    loc_net = subprocess.run("docker network create net2connect_A_B", shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    add_to_logs(int(loc_net.returncode),int(0),str("Establishing local network"))
 
  # Connect containers to local network
  connect_B = subprocess.run("docker network connect net2connect_A_B " + str(b_id),shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  add_to_logs(int(connect_B.returncode),0,"Attaching webserver container B to the local network")

  connect_A = subprocess.run("docker network connect net2connect_A_B " + str(a_id),shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  add_to_logs(int(connect_A.returncode),0,"Attaching test machine container A to the local network")

  # Do tests

  # Machine ip address
  machine_ip = check_output("hostname -I | awk '{print $1}'")

  # Reachability test:
  #Copy reachability test script to the container A that will run it
  subprocess.run("docker cp reachability_test.py container_A:/reachability_test.py",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  subprocess.run("docker exec -it container_A chmod +x reachability_test.py",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  reach_test = check_output("docker exec -it container_A python3 reachability_test.py -ip "+b_id)
  if 'True' in reach_test: add_to_logs(1,1,"Reachability test")

  # SSH test
  # Copy ssh test script to container A that will run it
  subprocess.run("docker cp ssh_test.sh container_A:/ssh_test.sh",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  subprocess.run("docker exec -it container_A chmod +x ssh_test.sh",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  ssh_test = str(check_output("docker exec -it container_A ./ssh_test.sh "+machine_ip+" "+str(ssh_port_host)))
  if ssh_test == 'Server is not reachable':
      add_to_logs(1,0,"SSH test")
  else:
      add_to_logs(1,1,"SSH test")

  # HTTP test
  address =machine_ip.strip() + ":"+str(http_port)
  #Copy http script to the container A that will run it
  subprocess.run("docker cp check_webserver.py container_A:/check_webserver.py",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  subprocess.run("docker exec -it container_A chmod +x check_webserver.py",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  http_test = str(check_output("docker exec -it container_A python3 check_webserver.py -ip "+address))
  add_to_logs(http_test,'200',"HTTP test")


  # Kill containers
  subprocess.run("docker kill container_A container_B",shell=True,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
  add_to_logs(1,1,"Killing containers")
   
  logging.info("Test automation has finished.")

