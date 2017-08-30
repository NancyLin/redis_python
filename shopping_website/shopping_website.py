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
        
        session_keys = []
        for token in tokens:
            session_keys.append('viewed:' + token)
        
        # 批量删除相应的用户最近浏览商品有序集合，登录令牌与用户映射关系的散列和记录最近登录用户的有序集合
        conn.delete(*session_key)
        conn.hdel('login:', *tokens)
        conn.zrem('recent:', *tokens)
    