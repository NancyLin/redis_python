# !/usr/bin/env python
# -*- coding: utf-8 -*-

import time

# 截止时间，一周
ONE_WEEK_IN_SECONDS = 7 * (24 * 60 * 60)
# 计分常量
VOTE_SCORE = 432

"""
发布文章
（1）通过计数器INCR创建一个新的文章ID
（2）将文章发布者ID添加到记录文章已投票用户名单的集合中，并用EXPIRE为这个集合设置过期时间，让redis在过期后自动删除这个集合
（3）用HMSET存储文章的相关信息，并执行两个ZADD，将文章的初始评分与发布时间添加到两个相应的有序集合中

@param {object}
@param {string} 用户
@param {string} 文章title
@param

@return {string} 文章id
"""
def postArticle(conn, user, title, link):
    # 创建一个新的文章ID
    article_id = str(conn.INCR('article:'))

    # 将文章发布者ID添加到记录文章已投票用户名单的集合中，并用EXPIRE为这个集合设置过期时间
    voted = 'voted:' + article_id
    conn.sadd(voted, user)
    conn.expire(voted, ONE_WEEK_IN_SECONDS)
    
    now = time.time()
    
    # 用HMSET存储文章的相关信息
    article = 'article:' + article_id
    conn.hmset(article, {
        'title': title,
        'link': link,
        'poster': user,
        'time': now,
        'votes': 1
    })
    
    # 执行两个ZADD，将文章的初始评分与发布时间添加到两个相应的有序集合中
    conn.zadd('time:', article, now)
    conn.zadd('score:', article, now + VOTE_SCORE)
    
    return article_id


"""
用户投票功能
（1）判断文章是否超过了投票截止时间
（2）从artcle:id标识符里面取出文章的ID
（3）如果用户是第一次为这篇文章投票，那么增加这篇文章的投票数量和评分

@param {object}
@param {string} 用户
@param {string} 文章


"""
def articleVote(conn, user, article):
	# 可投票的文章最早发布时间
    cutoff = time.time() - ONE_WEEK_IN_SECONDS
    if conn.zscore('time:', article) < cutoff:
        return
    
    article_id = article.partition(':')[-1]
    # 将用户添加到已投票用户名单的集合中
    if conn.sadd('voted:' + article_id, user):
        conn.zincrby('score:', article, VOTE_SCORE)
        conn.hincrby(article, 'votes', 1)





