# -*- coding: utf-8 -*-
import urllib.request
import argparse

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Possible options for VECTIS VTest2 system:')
  parser.add_argument('-ip', help='machine ip address', dest='ip', required='true')
  args = parser.parse_args()
  print(urllib.request.urlopen("http://"+args.ip).getcode())
