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
def voteArticle(conn, user, article):
	# 判断文章是否超过了投票截止时间，如果超过，则不允许投票
    outoff = time.time() - ONE_WEEK_IN_SECONDS
    if conn.zscore('time:', article) < outoff:
        return
    
    article_id = article.partition(':')[-1]
    # 将用户添加到记录已投票用户名单的集合中
    if conn.sadd('voted:' + article_id, user):
    	# 增加该文章的评分和投票数量
    	conn.zincrby('score:', article, VOTE_SCORE)
    	conn.hincrby(article, 'votes', 1)

"""
取出评分最高的文章，或者最新发布的文章
（1）我们需要使用ZREVRANGE命令取出多个文章ID。（由于有序集合会根据成员的分值从小到大地排列元素，使用ZREVRANGE以分值从大到小的排序取出文章ID）
（2）对每个文章ID执行一次HGETALL命令来取出文章的详细信息。

@param {object}
@param {int}    页码
@param {string} 有序集合名称，可以是score:,time:

@return array
"""
# 每页的文章数
ARTICLES_PER_PAGE = 25

def getArticles(conn, page, order = 'score:'):
    # 获取指定页码文章的起始索引和结束索引
    start = (page - 1) * ARTICLES_PER_PAGE
    end   = start + ARTICLES_PER_PAGE - 1

    # 取出指定位置的文章id
    article_ids = conn.zrevrange(order, start, end)

    articles = []
    for id in article_ids:
        article_data = conn.hgetall(id)
        article_data['id'] = id

        articles.append(article_data)

    return articles

"""
添加移除文章到指定的群组中
为了记录各个群组都保存了哪些文章，需要为每个群组创建一个集合，并将所有同属一个群组的文章ID都记录到那个集合中。

@param {object}
@param {int}   文章ID
@param {array} 添加的群组
@param {array} 移除的群组

"""
def addRemoveGroups(conn, article_id, to_add = [], to_remove = []):
    article = 'article:' + article_id
    
    # 添加文章到群组中
    for group in to_add:
        conn.sadd('group:' + group, article)
    
    # 从群组中移除文章
    for group in to_remove:
        conn.srem('group:' + group, article)

"""
根据评分或者发布时间对群组文章进行排序和分页
（1）通过群组文章集合和评分的有序集合或发布时间的有序集合执行ZINTERSTORE命令，而得到相关的群组文章有序集合。
（2）如果群组文章很多，那么执行ZINTERSTORE需要花费较多的时间，为了尽量减少redis的工作量，我们将查询出的有序集合进行缓存处理，尽量减少ZINTERSTORE命令的执行次数。
为了保持持续更新后我们能获取到最新的群组文章有序集合，我们只将结果缓存60秒。
（3）使用上一步的getArticles函数来分页并获取群组文章。

@param {object}
@param {int}   文章ID
@param {array} 添加的群组
@param {array} 移除的群组

"""
def getGroupArticles(conn, group, page, order = 'score:'):
    # 群组有序集合名
    key = order + group

    if not conn.exists(key):
        conn.zinterstore(key, ['group:' + group, order], agregate = 'max')
        conn.expire(key, 60)

    return getArticles(conn, page, key)

    