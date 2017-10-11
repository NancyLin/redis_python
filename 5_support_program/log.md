# 使用Redis记录系统日志 #
---------

在构建一个系统时，我们常常需要记录当前发生的事情，以及记录特定消息出现的频率，根据出现频率的高低来决定消息的排列信息，帮助我们找到重要的信息。

常见记录日志的方法有两种：
1. 将日志记录在文件中。随时时间流逝将日志行不断添加到文件里面，并在一段时间后创建新的日志文件。这种方式为每个不同的服务创建不同的日志，由于服务轮换日志的机制不同，也缺少一种能够方便地聚合所有日志并对其进行处理的常见方法。
2. syslog服务。这种服务几乎运行在Linux服务器和Unix服务器的514号TCP端口和UDP端口上。syslog接受其他程序发来的日志消息，并将这个消息路由至存储在硬盘上的各个日志文件，并且负责旧日志的轮换和删除工作。甚至还可以将日志消息转发给其他服务来做进一步的处理。

syslog的转发功能可以将不同的日志分别存储在同一台服务器的多个文件里面，对于长时间地记录日志非常有帮助。我们可以使用redis来存储与时间紧密相关的日志，从而在功能上替代那些需要在短期内被存储的syslog消息。

## 1. 最新日志 ##

我们需要使用 *“列表”* 来存储最新日志文件，使用LPUSH命令将日志消息推入到列表中。如果我们之后想要查看已有日志消息的话，可以使用LRANGE命令来拉取列表中的消息。

我们还要命名不同的日志消息队列，根据问题的严重性对日志进行分级。

```
import time
import logging
import unittest
import redis
from datetime import datetime

# 设置一个字典，将大部分日志的安全级别映射为字符串
SEVERITY = {
	logging.DEBUG: 'debug',
	logging.INFO: 'info',
	logging.WARNING: 'warning',
	logging.ERROR: 'error',
	logging.CRITICAL: 'critical',
}

SEVERITY.update((name, name) for name in SEVERITY.values())

"""
存储最新日志文件，命名不同的日志消息队列，根据问题的严重性对日志进行分级

@param {object}
@param {string} name    消息队列名称
@param {string} message 消息
@param {string} severity安全级别
@param {object} pip     pipline

"""
def logRecent(conn, name, message, severity=logging.INFO, pip=None):
	# 将日志的安全级别转换为简单的字符串
    severity = str(SEVERITY.get(severity, severity)).lower()
    # 创建要保存的redis列表key
    destination = 'recent:%s:%s'%(name, severity)
    # 将当前时间加到消息里面，用于记录消息的发送时间
    message = time.asctime() + ' ' + message
    # 使用流水线来将通信往返次数降低为一次
    pipe = pip or conn.pipeline()
    # 将消息添加到列表的最前面
    pipe.lpush(destination, message)
    # 修剪日志列表，让它只包含最新的100条消息
    pipe.ltrim(destination, 0, 99)
    pipe.execute()
```

## 2. 常见日志 ##

我们需要记录较高频率出现的日志，使用*“有序集合”*，将消息作为成员，消息出现的频率为成员的分值。

为了确保我们看到的常见消息都是最新的，需要以每小时一次的频率对消息进行轮换，并在轮换日志的时候保留上一个小时记录的常见消息，从而防止没有任何消息存储的情况出现。

```
"""
记录较高频率出现的日志，每小时一次的频率对消息进行轮换，并在轮换日志的时候保留上一个小时记录的常见消息

@param {object}
@param {string} name    消息队列名称
@param {string} message 消息
@param {string} severity安全级别
@param {int}    timeout 执行超时时间

"""
def logCommon(conn, name, message, severity=logging.INFO, timeout=5):
    # 设置日志安全级别
    severity = str(SEVERITY.get(severity, severity)).lower()
    # 负责存储近期的常见日志消息的键
    destination = 'common:%s:%s'%(name, severity)
    # 每小时需要轮换一次日志，需要记录当前的小时数
    start_key = destination + ':start'
    pipe = conn.pipeline()
    end = time.time() + timeout
    while time.time() < end:
    	try:
    		# 对记录当前小时数的键进行监听，确保轮换操作可以正常进行
            pipe.watch(start_key)
    		# 当前时间
            now = datetime.utcnow().timetuple()
    		# 取得当前所处的小时数
            hour_start = datetime(*now[:4]).isoformat()

            existing = pipe.get(start_key)
    		# 开始事务
            pipe.multi()
    		# 如果这个常见日志消息记录的是上个小时的日志
            if existing and existing < hour_start:
    			# 将这些旧的常见日志归档
                pipe.rename(destination, destination + ':last')
                pipe.rename(start_key, destination + ':pstart')
                # 更新当前所处的小时数
                pipe.set(start_key, hour_start)
            elif not existing:
                pipe.set(start_key, hour_start)

            # 记录日志出现次数
            pipe.zincrby(destination, message)
            # 将日志记录到日志列表中，调用excute
            logRecent(pipe, name, message, severity, pipe)
            return
        except redis.exceptions.WatchError:
            continue
```

** 测试 **
测试代码如下：

```
class TestLog(unittest.TestCase):
    def setUp(self):
        import redis
        self.conn = redis.Redis(db=15)
        self.conn.flushdb

    def tearDown(self):
        self.conn.flushdb()
        del self.conn
        print
        print

    def testLogRecent(self):
    	import pprint
    	conn = self.conn

        print "Let's write a few logs to the recent log"
        for msg in xrange(5):
            logRecent(conn, 'test', 'this is message %s'%msg)

        recent = conn.lrange('recent:test:info', 0, -1)
        print 'The current recent message log has this many message:', len(recent)
        print 'Those message include:'
        pprint.pprint(recent[:10])
        self.assertTrue(len(recent) >= 5)

    def testLogCommon(self):
        import pprint
        conn = self.conn

        print "Let's writ a few logs to the common log"
        for count in xrange(1, 6):
        	for i in xrange(count):
        		logCommon(conn, 'test', 'message-%s'%count)

        common = conn.zrevrange('common:test:info', 0, -1, withscores=True)
        print 'The current common message log has this many message:', len(common)
        print 'Those common message include:'
        pprint.pprint(common)
        self.assertTrue(len(common) >= 5)

if __name__ == '__main__':
    unittest.main()
```

