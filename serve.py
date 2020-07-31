#-*- coding:utf-8 -*-
import os
from sys import argv

def gitbook_operation():
    os.system("gitbook build ./tomcat-docs")
    os.system('gitbook serve ./tomcat-docs')

if __name__ == '__main__':
    gitbook_operation()