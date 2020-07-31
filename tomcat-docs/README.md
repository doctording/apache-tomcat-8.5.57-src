`apache-tomcat-8.5.57-src`源码阅读笔记

* Main Class

`org.apache.catalina.startup.Bootstrap`

* VM options

`-Dcatalina.home=./ -Dcatalina.base=./ -Djava.endorsed.dirs=./endorsed -Djava.io.tmpdir=./temp -Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager -Djava.util.logging.config.file=./conf/logging.properties -Dfile.encoding=UTF-8 -Duser.region=us -Duser.language=en`

idea启动运行