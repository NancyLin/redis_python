### Redis常用命令 ###
----------

#### 1.字符串 ####

在redis里面，字符串可以存储以下3中类型的值

- 字符串。
- 整数。
- 浮点数。

用户可以对存储着整数或者浮点数的字符串执行自增或者自减的操作，在有需要的时候，Redis还会将整数转为浮点数。

整数的取值范围与系统的位数相关（32位或64位）。

浮点数的取值范围和精度则与双精度浮点数（double）相同，64位(11位阶码，1位符号位，剩下52位尾数)。

常用的命令如下：

1. 数据操作

- get 获取存储在指定键的值
- set 设置存储在指定键的值
- del 删除存储在指定键的值（这个命令用于所有类型）

2. 自增自减命令

- incr 将键存储的值加1，eg： incr key-name
- decr 将键存储的值减1，eg： decr key-name
- incrby 将键存储的值加上整数amount，eg：incrby key-name amount
- decrby 将键存储的值减去整数amount，eg：decrby key-name amount
- incrbyfloat 将键存储的值加上浮点数amount，这个命令在Redis2.6以上的版本可用，eg：incrbyfloat key-name amount

如果用户对一个不存在的键或者存储了空串的键执行自增或者自减操作，redis会将这个键值当做0来处理。

如果用户对一个无法解释为整数或浮点数的字符串进行自增或自减，redis会向用户返回一个错误。

3. 处理子串和二进制位的命令

- append 将value追加到指定键key-name当前存储的值的末尾，eg：append key-name value
- getrange 获取一个由偏移量start至偏移量end范围内所有字符组成的子串，包括start和end在内（由以前的substr改名而来），eg：getrange key-name start end
- setrange 将从offset偏移量开始的子串设置为给定值，eg：setrange key-name offset value
- getbit 将字节串看作是二进制位串，并返回位串中偏移量为offset的二进制位的值。eg：getbit key-name offset
- setbit 将字节串看作是二进制位串，并将位串中偏移量为offset的二进制的值设置为value。eg：setbit key-name offset value
- bitcount 统计二进制位串里面值为1的二进制位的数量，如果给定了可选的start偏移量和end偏移量，那么只对偏移量指定范围内的二进制位进行统计。eg：bitcount key-name [start end]
- bitop 对一个或多个二进制位串执行包括并（and）、或（or）、异或（xor）、非（not）在内的任意一种按位运算操作，并将计算得出的结果保存在dest-key键里面。eg：bitop operation dest-key key-name [key-name...]

在使用setrange或者setbit对字符串进行写入的时候，如果字符串当前的长度不能满足写入要求，redis会自动使用空字节（null）来将字符串扩展至所需的长度，然后才进行写入操作。

在使用getrange读取字符串时，超出字符串末尾的数据会被视为空串，而在使用getbit读取二进制位串的时候，超出字符串末尾的二进制位会被视为0。

#### 2.列表 ####

一个链表，链表上的每个节点都包含一个字符串，一个列表结构可以有序地存储多个字符串。

列表允许用户从序列的两端推入或者弹出元素，获取列表元素以及执行各种常见的列表操作。

1. 常用的列表命令

- rpush 将一个或多个值推入列表的右端，eg：rpush key-name value [value ...]
- lpush 将一个或多个值推入列表的左端，eg：lpush key-name value [value ...]
- rpop  移除或返回列表最右端的元素，rpop key-name
- lpop  移除或返回列表最左端的元素，lpop key-name
- lindex 返回列表中偏移量为offset的元素，lindex key-name offset
- lrange 返回列表从start偏移量到end偏移量范围内的所有元素，其中偏移量为start和偏移量为end的元素也会包含在被返回的元素之内，lrange key-name start end
- ltrim 对列表进行修剪，只保留从start偏移量到end偏移量范围内的元素，其中偏移量为start和偏移量为end的元素也会被保留。ltrim key-name start end

组合使用ltrim和lrange可以构建出一个在功能上类似于lpop和rpop，但是却能够一次返回并弹出多个元素的操作。

2. 阻塞式的列表弹出命令以及在列表之间移动元素的命令

- blpop 从第一个非空列表弹出最左端的元素，或者在timeout秒之内阻塞并等待可弹出的元素出现。blpop key-name [key-name...] timeout
- brpop 从第一个非空列表弹出最右端的元素，或者在timeout秒之内阻塞并等待可弹出的元素出现。brpop key-name [key-name...] timeout
- rpoplpush 从source-key列表中弹出位于最右端的元素，然后将这个元素推入dest-key列表的最左端，并向用户返回这个元素。rpoplpush source-key dest-key
- brpoplpush 从source-key列表中弹出位于最右端的元素，然后将这个元素推入dest-key列表中的最左端，并向用户返回这个元素；如果source-key为空，那么在timeout秒之内阻塞并等待可弹出的元素。brpoplpush source-key dest-key timeout

对于阻塞弹出命令和弹出并推入命令，最常见的用例就是消息传递（messageing）和任务队列（task queue）。


