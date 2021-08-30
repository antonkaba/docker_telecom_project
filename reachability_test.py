# -*- coding: utf-8 -*-
import subprocess
import argparse

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Possible options for reachability test:')
  parser.add_argument('-ip', help='container ip address', dest='ip', required='true')
  args = parser.parse_args()
  
  try:
    subprocess.check_output("ping -c 1 "+args.ip,shell=True)
    print('True') 
  except subprocess.CalledProcessError:
    print('False')

