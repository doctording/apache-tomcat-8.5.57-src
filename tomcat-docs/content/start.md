# Tomcat启动流程&架构

## 源码启动流程分析

```java
Bootstrap main
    Catlina load

        // Start the new server
        try {
            getServer().init();
        } catch (LifecycleException e) {
            if (Boolean.getBoolean("org.apache.catalina.startup.EXIT_ON_INIT_FAILURE")) {
                throw new java.lang.Error(e);
            } else {
                log.error("Catalina.start", e);
            }
        }
    
        @Override
        public final synchronized void init() throws LifecycleException {
            if (!state.equals(LifecycleState.NEW)) {
                invalidTransition(Lifecycle.BEFORE_INIT_EVENT);
            }
    
            try {
                setStateInternal(LifecycleState.INITIALIZING, null, false);
                initInternal();
                setStateInternal(LifecycleState.INITIALIZED, null, false);
            } catch (Throwable t) {
                handleSubClassException(t, "lifecycleBase.initFail", toString());
            }
        }
    
    StandardServer initInternal
        service.init();
            StandardService initInternal
                engine.init();
                    StandardEngine initInternal
                        getRealm
                connector.init();
                    Connector initInternal
                        protocolHandler.init();
                            AbstractHttp11Protocol init // tomcat 8默认了NIO方式，控制台可以看到"http-nio-8080"
                                AbstractProtocol init
                                    AbstractEndpoint init
                                         bind();
                                            NioEndpoint bind // ServerSocketChannel
                                                // 默认设置：serverSock.configureBlocking(true);

    Catlina start
        StandardServer startInternal
            engine.start();
            executor.start();
            connector.start();
                Connector startInternal
                    AbstractProtocol start
                        endpoint.start();
                            NioEndpoint startInternal
                                Poller run
                                    selector.select // Selector处理事件
                                         processKey(sk, attachment); // 处理SelectionKey
                                            processSocket(attachment, SocketEvent.OPEN_READ, true) // 处理请求
                                                executor.execute(sc);
                                            processSocket(attachment, SocketEvent.OPEN_WRITE, true) // 响应返回
                                startAcceptorThreads // 默认一个acceptor线程
                                    NioEndpoint的内部类Acceptor run方法
                                        serverSock.accept();
                                            setSocketOptions(socket); // 处理请求，且会重新`socket.configureBlocking(false)`
                                                

```

* 下图所示debug到`NioEndpoint`的bind方法

![](../imgs/debug-1.png)

* 下图所示debug到`NioEndpoint`的创建 acceptor, poller threads

![](../imgs/debug-2.png)

相关源码见：`NioEndpoint`类的`startInternal`方法

```java
/**
 * Start the NIO endpoint, creating acceptor, poller threads.
 */
@Override
public void startInternal() throws Exception {

    if (!running) {
        running = true;
        paused = false;

        processorCache = new SynchronizedStack<>(SynchronizedStack.DEFAULT_SIZE,
                socketProperties.getProcessorCache());
        eventCache = new SynchronizedStack<>(SynchronizedStack.DEFAULT_SIZE,
                        socketProperties.getEventCache());
        nioChannels = new SynchronizedStack<>(SynchronizedStack.DEFAULT_SIZE,
                socketProperties.getBufferPool());

        // Create worker collection
        if ( getExecutor() == null ) {
            createExecutor();
        }

        initializeConnectionLatch();

        // Start poller threads
        pollers = new Poller[getPollerThreadCount()];
        for (int i=0; i<pollers.length; i++) {
            pollers[i] = new Poller();
            Thread pollerThread = new Thread(pollers[i], getName() + "-ClientPoller-"+i);
            pollerThread.setPriority(threadPriority);
            pollerThread.setDaemon(true);
            pollerThread.start();
        }

        startAcceptorThreads();
    }
}
```

### jvisualvm查看tomcat启动后的线程

* 默认的一个Acceptor线程
* 2个Poller线程

![](../imgs/debug-4.png)


同时看到了10个`http-nio-8080-exex-`线程,这是由于EndPoint默认设置的了`private int minSpareThreads = 10;`

#### 自己设置线程池

```java
<Executor name="tomcatThreadPool" namePrefix="catalina-exec-"
          maxThreads="150" minSpareThreads="4"/>
-->

<!-- A "Connector" represents an endpoint by which requests are received
     and responses are returned. Documentation at :
     Java HTTP Connector: /docs/config/http.html
     Java AJP  Connector: /docs/config/ajp.html
     APR (HTTP/AJP) Connector: /docs/apr.html
     Define a non-SSL/TLS HTTP/1.1 Connector on port 8080
-->
<Connector port="8080" protocol="HTTP/1.1" executor="tomcatThreadPool"
           connectionTimeout="20000"
           redirectPort="8443" />
```

![](../imgs/debug-5.png)

#### 附加：public abstract class LifecycleBase implements Lifecycle

* Lifecycle接口统一管理Tomcat生命周期

```java
public interface Lifecycle {
    // 13个状态常量值
    public static final String BEFORE_INIT_EVENT = "before_init";
    public static final String AFTER_INIT_EVENT = "after_init";
    public static final String START_EVENT = "start";
    public static final String BEFORE_START_EVENT = "before_start";
    public static final String AFTER_START_EVENT = "after_start";
    public static final String STOP_EVENT = "stop";
    public static final String BEFORE_STOP_EVENT = "before_stop";
    public static final String AFTER_STOP_EVENT = "after_stop";
    public static final String AFTER_DESTROY_EVENT = "after_destroy";
    public static final String BEFORE_DESTROY_EVENT = "before_destroy";
    public static final String PERIODIC_EVENT = "periodic";
    public static final String CONFIGURE_START_EVENT = "configure_start";
    public static final String CONFIGURE_STOP_EVENT = "configure_stop";
    // 3个监听器方法
    public void addLifecycleListener(LifecycleListener listener);
    public LifecycleListener[] findLifecycleListeners();
    public void removeLifecycleListener(LifecycleListener listener);
    // 4个生命周期方法
    public void init() throws LifecycleException;
    public void start() throws LifecycleException;
    public void stop() throws LifecycleException;
    public void destroy() throws LifecycleException;
    // 2个当前状态方法
    public LifecycleState getState();
    public String getStateName();
```

* ​LifecycleBase 类则是Lifecycle 接口的默认实现
