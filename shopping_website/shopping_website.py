# !/usr/bin/env python
# -*- coding: utf-8 -*-

import time

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

def clearSession(conn):
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
        conn.delete(*session_key)
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
    if not canCache(request):
        return callback(request)
    
    # 将请求转换为一个简单的字符串健，方便之后进行查找
    page_key = 'cache:' + hash_request(request)
    content = conn.get(page_key)
    
    # 没有缓存的页面，调用回调函数生成页面，并缓存到redis中
    if not content:
        content = callback(request)
        conn.setex(page_key, content, 300)

    return content

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
        if not next or nextp[0][1] > now:
            time.sleep(.05)
            continue
        
        row_id = nextp[0][0]
        # 取出延迟值
        delay = conn.szcore('delay:', row_id)
        # 如果延迟值小于等于0，则不再缓存该数据行
        if delay <= 0:
            conn.zrem('schedule:', row_id)
            conn.zrem('delay:', row_id)
            conn.delete('inv:' + row_id) 
            continue;

        # 需要缓存的，更新缓存调度的有序集合，并缓存该数据行
        row = Inventory.get(row_id)
        conn.zadd('schedule:', row_id, now + delay)
        conn.set('inv:' + row_id, json.dumps(row.to_dict()))