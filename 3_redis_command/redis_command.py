# !/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
import unittest
"""
发布者
"""
def publisher(conn, n):
	# 在刚开始执行时先休眠，让订阅者有足够的时间来连接服务器并监听消息
    time.sleep(1)
    for i in xrange(n):
        conn.publish('channel', i)
        # 发布消息之后进行短暂的休眠，让消息可以一条一条地出现
        time.sleep(1)

"""
发布订阅模式
"""
def runPubsub(conn):
	# 启动发送者线程发送3条消息
    threading.Thread(target=publisher, args=(conn,3,)).start()
    # 创建发布与订阅对象，并让它订阅给定的频道
    pubsub = conn.pubsub()
    pubsub.subscribe(['channel'])
    count = 0
    # 通过遍历函数pubsub.listen()执行结果来监听订阅消息
    for item in pubsub.listen():
        print item
        count += 1
        if count == 4:
        	# 在接收到一条订阅反馈消息和三条发布者发送消息之后，执行退订操作，停止监听新消息
            pubsub.unsubscribe()
        # 客户端在接收到退订反馈消息之后就不再接收消息
        if count == 5:
        	break

"""
事务处理
"""
def trans(conn):
    # 创建一个事务型流水线对象
    pipeline = conn.pipeline()
    # 把计数器的自增操作放入队列
    pipeline.incr('trans:')
    time.sleep(.1)
    # 把计数器的自减操作放入队列
    pipeline.incr('trans:', -1)
    # 执行被事务包裹的命令，并打印自增操作的执行结果
    print pipeline.execute()[0]

"""
测试
"""
class TestRedisPubSub(unittest.TestCase):
    def setUp(self):
        import redis
        self.conn = redis.Redis(db=15)
    
    def tearDown(self):
        del self.conn
        print
        print

    def testRunPubsub(self):
        runPubsub(self.conn)

    def testTrans(self):
        for i in xrange(3):
            threading.Thread(target=trans, args=(self.conn,)).start()
        time.sleep(.5)

if __name__ == '__main__':
    unittest.main()
    


