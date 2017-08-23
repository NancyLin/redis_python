### 文章投票网站的redis相关实现
----------
### 需求: ###
要构建一个文章投票网站，文章需要在**一天**内至少获得200张票，才能优先显示在**当天**文章列表前列。

但是为了避免发布时间较久的文章由于累计的票数较多而一直停留在文章列表前列，我们需要有随着时间流逝而不断减分的评分机制。

于是具体的评分计算方法为:将文章得到的支持票数乘以一个常量432（由一天的秒数86400除以文章展示一天所需的支持票200得出），然后加上文章的发布时间，得出的结果就是文章的评分。

### Redis设计 ### 
（1）对于网站里的每篇文章，需要使用一个**散列**来存储文章的标题、指向文章的网址、发布文章的用户、文章的发布时间、文章得到的投票数量等信息。

![记录文章内容散列][1]

为了方便网站根据文章发布的先后顺序和文章的评分高低来展示文章，我们需要两个有序集合来存储文章：
（2）**有序集合**，成员为文章ID，分值为文章的发布时间。

![文章发布时间有序集合][2]

（3）**有序集合**，成员为文章ID，分值为文章的评分。

![文章评分有序集合][3]

（4）为了防止用户对同一篇文章进行多次投票，需要为每篇文章记录一个已投票用户名单。使用**集合**来存储已投票的用户ID。由于集合是不能存储多个相同的元素的，所以不会出现同个用户对同一篇文章多次投票的情况。

![用户投票集合][4]

（5）文章支持群组功能，可以让用户只看见与特定话题相关的文章，比如“python”有关或者介绍“redis”的文章等，这时，我们需要一个集合来记录群组文章。例如 programming群组

![群组文章集合][5]

*为了节约内存，当一篇文章发布期满一周之后，用户将不能对它进行投票，文章的评分将被固定下来，而记录文章已投票用户名单的集合也会被删除。*

### 代码设计 ### 
*1.当用户要发布文章时，*

（1）通过一个计数器counter执行INCR命令来创建一个新的文章ID。

（2）使用SADD将文章发布者ID添加到记录文章已投票用户名单的集合中，并用EXPIRE命令为这个集合设置一个过期时间，让Redis在文章发布期满一周后自动删除这个集合。

（3）使用HMSET命令来存储文章的相关信息，并执行两ZADD命令，将文章的初始评分和发布时间分别添加到两个相应的有序集合中。

```
import time

# 截止时间，一周
ONE_WEEK_IN_SECONDS = 7 * (24 * 60 * 60)
# 计分常量
VOTE_SCORE = 432

"""
发布文章

@param {object}
@param {string} 用户
@param {string} 文章title
@param

@return {string} 文章id
"""
def postArticle(conn, user, title, link):
    # 创建一个新的文章ID
    article_id = str(conn.incr('article:'))

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
```

*2.当用户尝试对一篇文章进行投票时，*
（1）用ZSCORE命令检查记录文章发布时间的有序集合(redis设计2)，判断文章的发布时间是否未超过一周。

（2）如果文章仍然处于可以投票的时间范畴，那么用SADD将用户添加到记录文章已投票用户名单的集合(redis设计4)中。

（3）如果上一步操作成功，那么说明用户是第一次对这篇文章进行投票，那么使用ZINCRBY命令为文章的评分增加432(ZINCRBY命令用于对有序集合成员的分值执行自增操作)；

并使用HINCRBY命令对散列记录的文章投票数量进行更新
```
"""
用户投票功能

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

```
*3.我们已经实现了文章投票功能和文章发布功能，接下来就要考虑如何取出评分最高的文章以及如何取出最新发布的文章*

（1）我们需要使用ZREVRANGE命令取出多个文章ID。（由于有序集合会根据成员的分值从小到大地排列元素，使用ZREVRANGE以分值从大到小的排序取出文章ID）

（2）对每个文章ID执行一次HGETALL命令来取出文章的详细信息。

这个方法既可以用于取出评分最高的文章，又可以用于取出最新发布的文章。

```
"""
取出评分最高的文章，或者最新发布的文章

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
```
*4. 对文章进行分组，用户可以只看自己感兴趣的相关主题的文章。*

群组功能主要有两个部分：一是负责记录文章属于哪个群组，二是负责取出群组中的文章。

为了记录各个群组都保存了哪些文章，需要为每个群组创建一个集合，并将所有同属一个群组的文章ID都记录到那个集合中。

```
"""
添加移除文章到指定的群组中

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
```
由于我们还需要根据评分或者发布时间对群组文章进行排序和分页，所以需要将同一个群组中的所有文章按照评分或者发布时间有序地存储到一个有序集合中。
但我们已经有所有文章根据评分和发布时间的有序集合，我们不需要再重新保存每个群组中相关有序集合，我们可以通过取出群组文章集合与相关有序集合的交集，就可以得到各个群组文章的评分和发布时间的有序集合。

Redis的ZINTERSTORE命令可以接受多个集合和多个有序集合作为输入，找出所有同时存在于集合和有序集合的成员，并以几种不同的方式来合并这些成员的分值（所有集合成员的分支都会视为1）。

对于文章投票网站来说，可以使用ZINTERSTORE命令选出相同成员中最大的那个分值来作为交集成员的分值：取决于所使用的排序选项，这些分值既可以是文章的评分，也可以是文章的发布时间。

如下的示例图，显示了执行ZINTERSTORE命令的过程：

![群组文章的有序集合过程][6]

对集合groups:programming和有序集合score:进行交集计算得出了新的有序集合score:programming，它包含了所有同时存在于集合groups:programming和有序集合score:的成员。因为集合groups:programming的所有成员分值都被视为1，而有序集合score:的所有成员分值都大于1，这次交集计算挑选出来的分值为相同成员中的最大分值，所以有序集合score:programming的成员分值实际上是由有序集合score:的成员的分值来决定的。

所以，我们的操作如下：

（1）通过群组文章集合和评分的有序集合或发布时间的有序集合执行ZINTERSTORE命令，而得到相关的群组文章有序集合。

（2）如果群组文章很多，那么执行ZINTERSTORE需要花费较多的时间，为了尽量减少redis的工作量，我们将查询出的有序集合进行缓存处理，尽量减少ZINTERSTORE命令的执行次数。

为了保持持续更新后我们能获取到最新的群组文章有序集合，我们只将结果缓存60秒。

（3）使用上一步的getArticles函数来分页并获取群组文章。
```
"""
根据评分或者发布时间对群组文章进行排序和分页

@param {object}
@param {int}   文章ID
@param {array} 添加的群组
@param {array} 移除的群组

"""
def getGroupArticles(conn, group, page, order = 'score:'):
    # 群组有序集合名
    key = order + group

    if not conn.exists(key):
        conn.zinterstore(key, ['group:' + group, order], aggregate = 'max')
        conn.expire(key, 60)

    return getArticles(conn, page, key)

```
以上就是一个文章投票网站的相关redis实现。

测试代码如下：

```
import unittest
class TestArticle(unittest.TestCase):
    """
    初始化redis连接
    """
    def setUp(self):
        import redis
        self.conn = redis.Redis(db=15)

    """
    删除redis连接
    """
    def tearDown(self):
        del self.conn
        print
        print

    """
    测试文章的投票过程
    """
    def testArticleFunctionality(self):
        conn = self.conn
        import pprint

        # 发布文章
        article_id = str(postArticle(conn, 'username', 'A titile', 'http://www.baidu.com'))
        print "我发布了一篇文章，id为：", article_id
        print
        self.assertTrue(article_id)
        
        article = 'article:' + article_id
        # 显示文章保存的散列格式
        print "文章保存的散列格式如下："
        article_hash = conn.hgetall(article)
        print article_hash
        print
        self.assertTrue(article)

        # 为文章投票
        voteArticle(conn, 'other_user', article)
        print '我们为该文章投票，目前该文章的票数：'
        votes = int(conn.hget(article, 'votes'))
        print votes
        print
        self.assertTrue(votes > 1)

        print '当前得分最高的文章是：'
        articles = getArticles(conn, 1)
        pprint.pprint(articles)
        print
        self.assertTrue(len(articles) >= 1)

        # 将文章推入到群组
        addRemoveGroups(conn, article_id, ['new-group'])
        print "我们将文章推到新的群组，其他文章包括："
        articles = getGroupArticles(conn, 'new-group', 1)
        pprint.pprint(articles)
        print
        self.assertTrue(len(articles) >= 1)

        测试结束，删除所有的数据结构
        to_del = (
            conn.keys('time:*') + conn.keys('voted:*') + conn.keys('score:*') + 
            conn.keys('articles:*') + conn.keys('group:*')
        )

        if to_del:
            conn.delete(*to_del)

if __name__ == '__main__':
	unittest.main()
```
### 代码地址 ###

[https://github.com/NancyLin/redis_python/tree/master/article_voted][7]

文章投票网站的相关redis实现设计，具体分析请看博客：https://segmentfault.com/a/1190000010741281

  [1]: https://segmentfault.com/img/bVS4cn?w=26&h=219
  [2]: https://segmentfault.com/img/bVS4de?w=26&h=219
  [3]: https://segmentfault.com/img/bVTeoa?w=266&h=147
  [4]: https://segmentfault.com/img/bVS9jg?w=263&h=149
  [5]: https://segmentfault.com/img/bVTeoA?w=269&h=150
  [6]: https://segmentfault.com/img/bVTerN?w=891&h=155
  [7]: https://github.com/NancyLin/redis_python/tree/master/article_voted
