# !/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import urlparse
import uuid
import threading
import unittest
import json

"""
获取并返回令牌对应的用户

@param {object}
@param {string} token

@return {string} 用户id
"""
def checkToken(conn, token):
	return conn.hget('login:', token)

"""
更新令牌时，需要更改用户令牌信息，将用户记录到最近登录用户的有序集合中，
如果用户浏览的是商品，则需要将浏览商品写入该用户浏览过商品的有序集合中，并保证该集合不超过25个

@param {object}
@param {string} token
@param {string} user
@param {string} item

"""
def updateToken(conn, token, user, item = None):
    timestamp = time.time()
    # 更新用户令牌登录对应的用户信息
    conn.hset('login:', token, user)
    # 增加最近访问的用户到有序集合
    conn.zadd('recent:', token, timestamp)

	# 如果浏览产品，记录该用户最近访问的25个产品
    if item:
        conn.zadd('viewed:' + token, item, timestamp)
        conn.zremrangebyrank('viewed:' + token, 0, -26)
        # 记录每个商品的浏览量
        conn.zincrby('viewed:', item, -1)

"""
定期清理会话数据，只保留最新的1000万个会话。

使用 *守护进程的方式来运行或者定义一个cron job每隔一段时间运行* ，
检查最近 “记录最近登录用户的有序集合” 大小是否超过了限制，超过限制每秒从集合中删除最旧的100个令牌，
并且移除相应的“登录令牌与用户映射关系的散列”的信息和对应的“记录各个用户最近浏览商品的有序集合”。

@param {object}
"""

# 循环判断，如果是cron job可以不用循环
QUIT = False
# 限制保留的最大会话数据
LIMIT = 10000000

def cleanFullSession(conn):
    # 循环判断，如果是cron job可以不用循环
    while not QUIT:
        # 查询最近登录用户会话数
        size = conn.zcard('recent:')
        # 没有超过限制，休眠1秒再继续执行
        if size <= LIMIT:
            time.sleep(1)
            continue
        
        # 查询最旧登录的最多100个令牌范围
        end_index = min(size - LIMIT, 100)
        tokens = conn.zrange('recent:', 0, end_index - 1)
        
        # 将要删除的key都推入到数组中，要时候一起删除
        session_keys = []
        for token in tokens:
            session_keys.append('viewed:' + token)
            session_keys.append('cart:' + token)
        
        # 批量删除相应的用户最近浏览商品有序集合，用户的购物车，登录令牌与用户映射关系的散列和记录最近登录用户的有序集合
        conn.delete(*session_keys)
        conn.hdel('login:', *tokens)
        conn.zrem('recent:', *tokens)

"""
对购物车进行更新，如果用户订购某件商品数量大于0，将商品信息添加到 “用户的购物车散列”中，如果购买商品已经存在，那么更新购买数量

@param {object}
@param {string} session
@param {string} item
@param {float}  count

"""
def addToCart(conn, session, item, count):
    if count <= 0:
    	# 从购物车移除指定商品
        conn.hrem('cart:' + session, item)
    else:
    	# 将指定商品添加到对应的购物车中
        conn.hset('cart:' + session, item, count)

"""
在用户请求页面时，对于不能被缓存的请求，直接生成并返回页面，
对于可以被缓存的请求，先从缓存取出缓存页面，如果缓存页面不存在，那么会生成页面并将其缓存在Redis，最后将页面返回给函数调用者。

@param {object} conn
@param {string} request
@param {callback}

@return 
"""
def cacheRequest(conn, request, callback):
    # 判断请求是否能被缓存，不能的话直接调用回调函数
    if not canCache(conn, request):
        return callback(request)
    
    # 将请求转换为一个简单的字符串健，方便之后进行查找
    page_key = 'cache:' + hashRequest(request)
    content = conn.get(page_key)
    
    # 没有缓存的页面，调用回调函数生成页面，并缓存到redis中
    if not content:
        content = callback(request)
        conn.setex(page_key, content, 300)

    return content

"""
判断页面是否能被缓存，检查商品是否被缓存以及页面是否为商品页面，根据商品排名来判断是否需要缓存

@param {object} conn
@param {string} request

@return {boolean}
"""
def canCache(conn, request):
    # 根据请求的URL，得到商品ID
    item_id = extractItemId(request)
    # 检查这个页面能否被缓存以及这个页面是否为商品页面
    if not item_id or isDynamic(request):
        return False

    # 商品的浏览排名
    rank = conn.zrank('viewed:', item_id)
    return rank is not None and rank < 10000

"""
解析请求的URL,取得query中的item id

@param {string} request

@return {string}
"""
def extractItemId(request):
    parsed = urlparse.urlparse(request)
    # 返回query字典
    query  = urlparse.parse_qs(parsed.query)
    return (query.get('item') or [None])[0]

"""
判断请求的页面是否动态页面

@param {string} request

@return {boolean}
"""
def isDynamic(request):
    parsed = urlparse.urlparse(request)
    query = urlparse.parse_qs(parsed.query)
    return '_' in query

"""
将请求转换为一个简单的字符串健，方便之后进行查找
@param {string} request

@return {string}
"""
def hashRequest(request):
    return str(hash(request))

"""
设置数据行缓存的延迟值和调度时间

@param {object} conn
@param {int}    row id
@param {int}    delay

"""
def scheduleRowCache(conn, row_id, delay):
    conn.zadd('delay:', row_id, delay)
    conn.zadd('schedule:', row_id, time.time())

"""
守护进程，根据调度时间有序集合和延迟值缓存数据行

@param {object} conn

"""
def cacheRow(conn):
    while not QUIT:
        # 需要读取”数据行缓存调度有序集合“的第一个元素，如果没有包含任何元素，或者分值存储的时间戳所指定的时间尚未来临，那么函数先休眠50毫秒，然后再重新进行检查
        next = conn.zrange('schedule:', 0, 0, withscores=True)
        now = time.time()
        if not next or next[0][1] > now:
            time.sleep(.05)
            continue
        
        row_id = next[0][0]
        # 取出延迟值
        delay = conn.zscore('delay:', row_id)
        # 如果延迟值小于等于0，则不再缓存该数据行
        if delay <= 0:
            conn.zrem('schedule:', row_id)
            conn.zrem('delay:', row_id)
            conn.delete('inv:' + row_id) 
            continue;

        # 需要缓存的，更新缓存调度的有序集合，并缓存该数据行
        row = Inventory.get(row_id)
        conn.zadd('schedule:', row_id, now + delay)
        conn.set('inv:' + row_id, json.dumps(row.toDict()))

"""
守护进程，删除所有排名在20000名之后的商品，并将删除之后剩余的所有商品浏览次数减半，5分钟执行一次

@param {object} conn

"""
def rescaleViewed(conn):
    while not QUIT:
        conn.zremrangebyrank('viewed:', 20000, -1)
        conn.zinterstore('viewed:', {'viewed:', .5})
        time.sleep(300)

"""
库存类，库存的商品信息
"""
class Inventory(object):
    def __init__(self, id):
        self.id = id

    @classmethod
    def get(cls, id):
        return Inventory(id)
    
    def toDict(self):
        return {'id':self.id, 'data':'data to cache...','cached':time.time()}

"""
测试
"""
class TestShoppingWebsite(unittest.TestCase):
    def setUp(self):
        import redis
        self.conn = redis.Redis(db=15)
    
    def tearDown(self):
        conn = self.conn
        to_del = (
            conn.keys('login:*') + conn.keys('recent:*') + conn.keys('viewed:*') +
            conn.keys('cart:*') + conn.keys('cache:*') + conn.keys('delay:*') + 
            conn.keys('schedule:*') + conn.keys('inv:*'))

        if to_del:
            conn.delete(*to_del)

        del self.conn

        global QUIT, LIMIT
        QUIT = False
        LIMIT = 10000000
        print
        print

    def testLoginCookies(self):
        conn = self.conn
        global LIMIT, QUIT
        token = str(uuid.uuid4())

        updateToken(conn, token, 'username', 'itemX')
        print "We just logged-in/updated token:", token
        print "For user:", 'username'
        print

        print "What username do we get when we look-up that tokan?"
        r = checkToken(conn, token)
        print r
        print
        self.assertTrue(r)

        print "Let's drop the maximun number of cookies to 0 to clear them out"
        print "We will start a thread to do the cleaning, while we stop it later"

        LIMIT = 0
        t = threading.Thread(target = cleanFullSession, args = (conn,))
        t.setDaemon(1)
        t.start()
        time.sleep(1)
        QUIT = True
        time.sleep(2)
        if t.isAlive():
            raise Exception("The clean sessions thread is still slive?!?")

        s = conn.hlen('login:')
        print "The current number of session still available is:", s
        self.assertFalse(s)

    def testShoppingCartCookies(self):
        conn = self.conn
        global LIMIT, QUIT
        token = str(uuid.uuid4())

        print "We'll refresh our session..."
        updateToken(conn, token, 'username', 'itemX')
        print "And add an item to the shopping cart"
        addToCart(conn, token, "itemY", 3)
        r = conn.hgetall('cart:' + token)
        print "Our Shopping cart currently has:", r
        print

        self.assertTrue(len(r) >= 1)

        print "Let's clean out our sessions an carts"
        LIMIT = 0
        t = threading.Thread(target=cleanFullSession, args=(conn,))
        t.setDaemon(1)
        t.start()
        time.sleep(1)
        QUIT = True
        time.sleep(2)
        if t.isAlive():
            raise Exception("The clean sessions thread is still alive?!?")

        r = conn.hgetall('cart:' + token)
        print "Our shopping cart now contains:", r

        self.assertFalse(r)

    def testCacheRequest(self):
        conn = self.conn
        token = str(uuid.uuid4())

        def callback(request):
            return "content for " + request

        updateToken(conn, token, 'username', 'itemX')
        url = 'http://test.com/?item=itemX'
        print "We are going to cache a simple request against", url
        result = cacheRequest(conn, url, callback)
        print "We got initial content:", repr(result)
        print

        self.assertTrue(result)

        print "To test that we've cached the request, we'll pass a bad callback"
        result2 = cacheRequest(conn, url, None)
        print "We ended up getting the same response!", repr(result2)

        self.assertEquals(result, result2)

        self.assertFalse(canCache(conn, 'http://test.com/'))
        self.assertFalse(canCache(conn, 'http://test.com/?item=itemX&_=1234567'))

    def testCacheRows(self):
        import pprint
        conn = self.conn
        global  QUIT

        print "First, let's schedule caching of itemX every 5 seconds"
        scheduleRowCache(conn, 'itemX', 5)
        print "Our schedule looks like:"
        s = conn.zrange('schedule:', 0, -1, withscores = True)
        pprint.pprint(s)
        self.assertTrue(s)

        print "We'll start a caching thread that will cache the data..."
        t = threading.Thread(target=cacheRow, args=(conn,))
        t.setDaemon(1)
        t.start()
        time.sleep(1)
        print "Our cached data looks like:"
        r = conn.get('inv:itemX')
        print repr(r)
        self.assertTrue(r)
        print
        print "We'll check again in 5 seconds..."
        time.sleep(5)
        print "Notice that the data has changed..."
        r2 = conn.get('inv:itemX')
        print repr(r2)
        print
        self.assertTrue(r2)
        self.assertTrue(r != r2)

        print "Let's force un-caching"
        scheduleRowCache(conn, 'itemX', -1)
        time.sleep(1)
        r = conn.get('inv:itemX')
        print "The cache was cleared?", not r
        print
        self.assertFalse(r)

        QUIT = True
        time.sleep(2)
        if t.isAlive():
            raise Exception("The database caching thread is still alive?!?")


if __name__ == '__main__':
    unittest.main()










