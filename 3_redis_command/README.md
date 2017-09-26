# 3.Redis常用命令 #
----------

## 3.1 字符串 ##

在redis里面，字符串可以存储以下3中类型的值

- 字符串。
- 整数。
- 浮点数。

用户可以对存储着整数或者浮点数的字符串执行自增或者自减的操作，在有需要的时候，Redis还会将整数转为浮点数。

整数的取值范围与系统的位数相关（32位或64位）。

浮点数的取值范围和精度则与双精度浮点数（double）相同，64位(11位阶码，1位符号位，剩下52位尾数)。

常用的命令如下：

**1. 数据操作**

- get 获取存储在指定键的值
- set 设置存储在指定键的值
- del 删除存储在指定键的值（这个命令用于所有类型）

**2. 自增自减命令**

- incr 

incr key-name
将键存储的值加1。

- decr 

decr key-name
将键存储的值减1。

- incrby

incrby key-name amount
将键存储的值加上整数amount

- decrby 

decrby key-name amount
将键存储的值减去整数amount。

- incrbyfloat 

incrbyfloat key-name amount
将键存储的值加上浮点数amount，这个命令在Redis2.6以上的版本可用

如果用户对一个不存在的键或者存储了空串的键执行自增或者自减操作，redis会将这个键值当做0来处理。

如果用户对一个无法解释为整数或浮点数的字符串进行自增或自减，redis会向用户返回一个错误。

**3. 处理子串和二进制位的命令**

- append 

append key-name value
将value追加到指定键key-name当前存储的值的末尾

- getrange 

getrange key-name start end
获取一个由偏移量start至偏移量end范围内所有字符组成的子串，包括start和end在内（由以前的substr改名而来）

- setrange

setrange key-name offset value 
将从offset偏移量开始的子串设置为给定值

- getbit 

getbit key-name offset
将字节串看作是二进制位串，并返回位串中偏移量为offset的二进制位的值。

- setbit 

setbit key-name offset value
将字节串看作是二进制位串，并将位串中偏移量为offset的二进制的值设置为value

- bitcount 

bitcount key-name [start end]
统计二进制位串里面值为1的二进制位的数量，如果给定了可选的start偏移量和end偏移量，那么只对偏移量指定范围内的二进制位进行统计。

- bitop

bitop operation dest-key key-name [key-name...]
对一个或多个二进制位串执行包括并（and）、或（or）、异或（xor）、非（not）在内的任意一种按位运算操作，并将计算得出的结果保存在dest-key键里面。

在使用setrange或者setbit对字符串进行写入的时候，如果字符串当前的长度不能满足写入要求，redis会自动使用空字节（null）来将字符串扩展至所需的长度，然后才进行写入操作。

在使用getrange读取字符串时，超出字符串末尾的数据会被视为空串，而在使用getbit读取二进制位串的时候，超出字符串末尾的二进制位会被视为0。

## 3.2 列表 ##

一个链表，链表上的每个节点都包含一个字符串，一个列表结构可以有序地存储多个字符串。

列表允许用户从序列的两端推入或者弹出元素，获取列表元素以及执行各种常见的列表操作。

**1. 常用的列表命令**

- rpush 

rpush key-name value [value ...]
将一个或多个值推入列表的右端。

- lpush 

lpush key-name value [value ...]
将一个或多个值推入列表的左端。

- rpop

rpop key-name  
移除或返回列表最右端的元素。

- lpop 

lpop key-name 
移除或返回列表最左端的元素。

- lindex 

lindex key-name offset
返回列表中偏移量为offset的元素。

- lrange 

lrange key-name start end
返回列表从start偏移量到end偏移量范围内的所有元素，其中偏移量为start和偏移量为end的元素也会包含在被返回的元素之内。

- ltrim

ltrim key-name start end 
对列表进行修剪，只保留从start偏移量到end偏移量范围内的元素，其中偏移量为start和偏移量为end的元素也会被保留。

组合使用ltrim和lrange可以构建出一个在功能上类似于lpop和rpop，但是却能够一次返回并弹出多个元素的操作。

**2. 阻塞式的列表弹出命令以及在列表之间移动元素的命令**

- blpop 

blpop key-name [key-name...] timeout
从第一个非空列表弹出最左端的元素，或者在timeout秒之内阻塞并等待可弹出的元素出现。

- brpop 

brpop key-name [key-name...] timeout
从第一个非空列表弹出最右端的元素，或者在timeout秒之内阻塞并等待可弹出的元素出现。

- rpoplpush 

rpoplpush source-key dest-key
从source-key列表中弹出位于最右端的元素，然后将这个元素推入dest-key列表的最左端，并向用户返回这个元素。

- brpoplpush 

brpoplpush source-key dest-key timeout
从source-key列表中弹出位于最右端的元素，然后将这个元素推入dest-key列表中的最左端，并向用户返回这个元素；如果source-key为空，那么在timeout秒之内阻塞并等待可弹出的元素。

对于阻塞弹出命令和弹出并推入命令，最常见的用例就是消息传递（messageing）和任务队列（task queue）。

## 3.3 集合 ##

Redis的集合以无序的方式来存储多个各不相同的元素，用户可以快速地对集合执行添加元素的操作，移除元素以及检查一个元素是否存在于集合中。

**1. 常用的集合命令**

- sadd

sadd key-name item [item ...]
将一个或多个元素添加到集合中，并返回被添加元素当中原本并不存在于集合里面的元素数量。

- srem

srem key-name item [item ...]
从集合中移除一个或多个元素，并返回被移除元素的数量

- sismember

sismember key-name item
检查元素item是否存在于集合key-name里面，

- scard

scard key-name
返回集合包含的元素的数量。

- smembers

smembers key-name
返回集合所包含的所有元素。

- srandmember

srandmember key-name [count]
从集合里面随机地返回一个或多个元素。当count为正数，命令返回的随机元素不会重复，当count为负数，命令返回的随机元素可能会出现重复。


- spop

spop key-name
随机地移除集合中的一个元素，并返回被移除的元素

- smove

smove source-key dest-key item
如果集合source-key包含元素item，那么从集合source-key里面移除元素item，并将元素item添加到集合dest-key里面。如果item被成功移除，那么命令返回1，否则命令返回0。

**2. 用于组合和处理多个集合的命令**

- sdiff

sdiff key-name [key-name ...]
返回存在于第一个集合但不存在与其他集合中的元素（数学上的差集运算）

- sdiffstore

sdiffstore dest-key key-name [key-name ...]
将那些存在于第一个集合但并不存在于其他集合中的元素（数学上的差集运算）存储到dest-key键里面。

- sinter

sinter key-name [key-name ...]
返回那些同时存在于所有集合中的元素（数学上的交集运算）

- sinterstore

sinterstore dest-key key-name [key-name ...]
将那些同时存在于所有集合的元素（数学上的交集运算）存储到dest-key键里面

- sunion

sunion key-name [key-name ...]
返回那些至少存在于一个集合中的元素（数学上的并集计算）

- sunionstore

sunionstore dest-key key-name [key-name ...]
将那些至少存在于一个集合中的元素（数学上的并集计算）存储到dest-key键里面

## 4.4 散列 ##

Redis的散列是允许用户将多个键值对存储到一个Redis键中，适合将一些相关的数据存储在一起，可以将数据聚集看作是关系型数据库中的行，或者文档数据库中的文档。

**1. 用于添加删除键值对的散列操作**

- hget

hget key-name key
从散列里面获取一个键的值

- hmget

hmget key-name key [key ...]
从散列里面获取一个或多个键的值

- hset

hset key-name key value
为散列里面的一个键设置值

- hmset

hmset key-name key value [key vaule ...]
为散列里面的一个或多个键设置值

- hdel

hdel key-name key [key ..]
删除散列里面一个或多个键值对，返回成功找到并删除的键值对数量

- hlen

hlen key-name
返回散列包含的键值对数量

hmget和hmset批量处理多个键值既给用户带来方便又减少了命令的调用次数以及客户端与redis之间的通信往返次数来提升redis的性能。

**2. redis散列的高级特性**

- hexists

hexists key-name key
检查给定键是否存在于散列中

- hkeys

hkeys key-name
获取散列包含的所有键

- hvals

hvals key-name
获取散列包含的所有值

- hgetall

hgetall key-name
获取散列包含的所有键值对

- hincrby

hincrby key-name key increment
将键key存储的值加上整数increment，对散列中一个尚未存在的键执行自增操作时，redis会将键的值当做0来处理。

- hincrbyfloat

hincrbyfloat key-name key increment
将键key存储的值加上浮点数increment

尽管有hgetall存在，但hkeys和hvals也是非常有用的：如果散列包含的值非常大，那么可以先使用hkeys取出散列包含的所有键，然后再使用HGET一个接一个地取出键的值，从而避免因为一次获取多个大体积的值而导致服务器阻塞。

## 3.5 有序集合 ##

有序集合存储着成员与分值之间的映射，并且提供了分值处理命令，以及根据分值大小有序地获取或扫描成员和分值的命令。

**1. 有序集合常用命令**

- zadd

zadd key-name score member [score member ...]
将带有给定分值的成员添加到有序集合里面，注意这里是先输入分值再输入成员，而python客户端执行zadd命令是先输入成员后输入分值。

- zrem

zrem key-name member [member ...]
从有序集合里面移除给定的成员，并返回被移除成员的数量

- zcard

zcard key-name
返回有序集合包含的成员数量

- zincrby

zincrby key-name increment member
将member成员的分值加上increment

- zcount

zcount key-name min max
返回分值介于min和max之间的成员数量

- zrank

zrank key-name member
返回成员member在有序集合中的排名，排名以0开始

- zscore

zscore key-name member
返回成员member的分值

- zrange

zrange key-name start stop [withscores]
返回有序集合中排名介于start和stop之间的成员，如果给定了可选的withscores选项，那么命令会将成员的分值也一并返回

**2. 有序集合的范围型数据获取命令和范围型数据删除命令，以及并集命令和交集命令**

- zrevrank

zrevrank key-name member
返回有序集合成员member的排名，成员按照分值从大到小排列

- zrevrange

zrevrange key-name start stop [withscores]
返回有序集合给定排名范围内的集合，成员按照分值从大到小排列

- zrangebyscore

zrangebyscore key min max [withscores] [limit offset count]
返回有序集合中分值介于min和max之间的所有成员

- zrevrangebyscore

zrevrangebyscore key max min [withscores] [limit offset count]
获取有序集合中分值介于min和max之间的所有成员，并按照分值从大到小的顺序来返回它们

- zremrangebyrank

zremrangebyrank key-name start stop
移除有序集合中排名介于start和stop之间的所有成员

- zremrangebyscore

zremrangebyscore key-name min max
移除有序集合中分值介于min和max之间的所有成员

- zinterscore

zinterscore dest-key key-count key [key ...] [weights weight [weight ...]] [aggregate sum|min|max]
对给定的有序集合执行类似于集合的交集运算，并将结果保存在dest-key中。默认使用的聚集函数是sum，可以根据aggregate的参数修改聚集函数。

- zunionscore

zunionscore dest-key key-count key [key ...] [weights weight [weight ...]] [aggregate sum|min|max]
对给定的有序集合执行类似于集合的并集运算，并将结果保存在dest-key中。默认使用的聚集函数是sum，可以根据aggregate的参数修改聚集函数。

对于，用户可以将集合作为输入传给zinterscore和zunionscore，命令会将集合看作是成员分值全为1的有序集合来处理。

## 6. 发布与订阅 ##

发布与订阅（又称pub/sub）的特点是订阅者（listener）负责订阅频道（channel），发送者（publisher）负责向频道发送二进制字符串消息（binary string message）。每当有消息被发送至给定频道时，频道的所有订阅者都会接收到消息。

也可以把频道看作是电台，其中订阅者可以同时收听多个电台，而发送者则可以在任何电台发送消息。

1.发布与订阅命令

- subscribe

subscribe channel [channel ...]
订阅给定的一个或多个频道

- unsubscribe

unsubscribe [channel [channel ...]]
退订给定的一个或多个频道，如果执行时没有给定任何频道，那么退订所有频道

- publish

publish channel message
向给定频道发送消息

- psubcribe

psubcribe pattern [pattern ...]
订阅与给定模式相匹配的所有频道

- punsubcribe

punsubcribe [pattern [pattern ...]]
退订给定的模式，如果执行时没有给定任何模式，那么退订所有模式

示例代码如下：
```
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

if __name__ == '__main__':
    unittest.main()
```

虽然redis的发布订阅模式很有用，但我们比较少用，主要原因有以下：

（1）与redis的稳定性有关。对于旧版redis来说，如果客户端订阅了某个或某些频道，读取的消息速度不够快，不断积压的消息会使redis输出缓冲区的体积变得越来越大，导致redis速度变慢甚至直接崩溃，也可能导致操作系统强制杀死进程，或者操作系统直接不可用。

新版的redis会自动断开不符合client-output-buffer-limit pubsub配置选项要求的订阅客户端。

（2）和数据传输的可靠性有关。任何网络系统在执行操作时都有可能会遇到断线情况，如果客户端在执行订阅操作的过程中断线，那么客户端将丢失在断线期间发送的所有消息。

如果喜欢简单易用的pushlish命令和subscribe命令，并且可以承担可能会丢失一部分数据的风险，那么也可以继续使用redis提供的发布和订阅特性。

## 3.7 其他命令 ##

这节的命令可以用于处理多种类型的数据。

### 3.7.1 排序 ###

- sort

sort source-key [by pattern][limit offset count][get pattern [get pattern...]][asc|desc][alpha][store dest-key]
根据给定的选项，对输入的列表，集合或者有序集合进行排序，然后返回或者存储排序的结果

sort命令可以根据降序而不是默认的升序来排序元素，将元素看做是数字来排序，或者将元素看做是二进制字符串来排序；使用被排序元素之外的其他值作为权重来进行排序，甚至可以从输入的列表，集合，有序集合以外的其他地方进行取值。

如以下代码演示了通过sort将散列存储的数据作为权重进行排序，以及怎样获取并返回散列存储的数据：
```
# 首先将一些元素添加到列表里面
>>> conn.rpush('sort-input', 23, 15, 110, 7)
4

# 根据数字大小对元素进行排序
>>> conn.sort('sort-input')
['7','15','23','110']

# 根据字母表顺序对元素进行排序
>>> conn.sort('sort-input', alpha=True)
['110','15','23','7']

# 添加一些用于执行排序操作和获取操作的附加数据
>>> conn.hset('d-7', 'field', 5)
>>> conn.hset('d-15', 'field', 1)
>>> conn.hset('d-23', 'field', 9)
>>> conn.hset('d-110', 'field', 3)

# 将散列的域field用作权重，对sort-input列表进行排序
>>> conn.sort('sort-input', by='d-*->field')
['15','110','7','23']

# 获取外部数据，并将它们用作命令的返回值，而不是返回被排序的数据
>>> conn.sort('sort-input', by='d-*->field', get='d-*->field')
['1','3','5','9']
```

### 3.7.2 基本的Redis事务 ###

Redis的基本事务需要用到multi命令和exec命令，这种事务可以让一个客户端在不被其他客户端打断的情况下执行多个命令。

被multi和exec命令包围的所有命令会一个接一个地执行，直到所有命令都执行完毕为止。当一个事务执行完毕后，redis才会处理其他客户端的命令。

当redis从一个客户端那里接收到multi命令时，Redis会将这个客户端之后发送的所有命令都放在一个队列里面，直到这个客户端发送exec命令为止，然后redis就会在不被打断的情况下，一个接一个地执行存储在队列里面的命令。

redis事务在python客户端上面是由pipeline实现的，对连接对象调用pipeline方法创建一个事务，在一切正常的情况下，客户端会自动地使用multi和exec包裹起用户输入的多个命令，此外，为了减少redis与客户端之间的通信往返次数，提升执行多个命令时的性能，python的redis客户端会存储起事务包含的多个命令，然后在事务执行时一次性将所有命令都发送给redis。

注意，redis要在接收到exec命令之后，才会执行那些位于multi和exec之间的入队命令。

示例代码如下：
```
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

# 测试
for i in xrange(3):
    threading.Thread(target=trans, args=(self.conn,)).start()
time.sleep(.5)

```

### 3.7.3 键的过期时间 ###

在使用Redis存储数据的时候，有些数据在某个时间点之后就不再有用，用户可以使用DEL命令显示地删除那些无用数据，也可以通过redis的过期时间特性来让一个键在给定的时限之后自动被删除。

键过期命令只能为整个键设置过期时间，而没办法为键里面的单个元素设置过期时间，为了解决这个问题，可以使用存储时间戳的有序集合来实现针对单个元素的过期操作。

- persist

persist key-name
移除键的过期时间

- ttl

ttl key-name
查看给定键距离过期还有多少秒

- expire

expire key-name seconds
让给定键在指定的秒数之后过期

- expireat

expireat key-name timestamp
将给定键的过期时间设置为给定的unix时间戳

- pttl

pttl key-name
查看给定键距离过期时间还有多少毫秒，这个命令在redis2.6或以上版本可用

- pexpire

pexpire key-name milliseconds
让给定键在指定的豪秒数之后过期，这个命令在redis2.6或以上版本可用

- pexpireat

pexpireat key-name timestamp-milliseconds
将一个毫秒级精度的unix时间戳设置为给定键的过期时间，这个命令在redis2.6或以上版本

