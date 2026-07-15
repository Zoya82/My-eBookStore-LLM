## 阶段 2A 用户认证规则（当前契约）

- 注册：`username` 必填，首尾空格会去除，长度 3-150 且唯一；`phone` 必须是唯一的 11 位数字；`password` 必填、长度 6-128，仅写入且使用 Django 哈希。重复数据和并发冲突均返回 HTTP 400，成功不自动登录。
- `GET/PUT /api/users/profile/`：可修改 `username`、`avatar`、`gender`、`email`；`gender` 仅 `M`、`F` 或空值，email 必须合法。`id`、`phone`、`is_active`、`is_staff`、`is_superuser` 只读；提交这些字段或 password 会明确返回 HTTP 400。
- 登录成功返回 7 天 JWT，payload 至少包含 `user_id`、`username`、`exp`。缺参返回 400，错误密码或停用用户返回 401。
- JWT 使用 `Authorization: Bearer <token>`，Bearer 大小写兼容。缺失 Authorization 返回未认证；格式错误、无效、过期、用户不存在或已停用均返回明确 HTTP 401。

📚 智能掌上书店 API 接口文档

版本：V1.0

最后更新：2026年7月14日



一、通用说明

1.1 基础信息

项目	内容

基础URL	http://127.0.0.1:8000/api

数据格式	请求与响应均为 JSON

字符编码	UTF-8

1.2 认证方式

需要登录的接口，在请求头中携带：



text

Authorization: Bearer <JWT\_Token>

Token 通过登录接口获取，有效期 7 天，过期后需重新登录。



1.3 统一响应格式

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "操作成功",

&#x20;   "data": { ... }

}

错误响应：



json

{

&#x20;   "code": 400,

&#x20;   "msg": "错误描述信息"

}

1.4 HTTP 状态码说明

状态码	含义	前端处理

200	操作成功	正常处理数据

400	参数错误或业务校验失败	展示 msg 中的错误信息

401	未登录或 Token 过期	跳转到登录页

403	权限不足	提示用户无权限

404	资源不存在	提示资源不存在

500	服务器内部错误	提示“系统繁忙，请稍后重试”

1.5 版本类型说明

值	说明	价格特点	购买后流程

digital	电子版	较便宜（约为纸质版60%）	支付即完成，自动加入书架，可阅读全文

physical	纸质版	较贵	支付后需管理员发货→用户确认收货

1.6 订单状态码说明

状态码	状态名	说明	可执行操作

1	待付款	订单已创建，等待支付	pay（支付）、cancel（取消）

2	已提交	已支付，等待发货	等待管理员发货

3	待收货	已发货，等待确认	confirm（确认收货）

4	已完成	交易完成	无

5	已取消	订单已取消	无

### 图书列表价格筛选

`GET /api/books/` 支持以下可选查询参数：

| 参数 | 说明 |
| --- | --- |
| `price_min` | 最低代表售价，使用 `representative_sale_price__gte` 过滤 |
| `price_max` | 最高代表售价，使用 `representative_sale_price__lte` 过滤 |

两个参数可同时传递组成闭区间。空字符串视为未传；非法数字、`NaN` 或 `Infinity` 返回 HTTP 400。没有在售版本且代表售价为 `null` 的图书不会出现在价格筛选结果中。

二、用户管理模块（/users）

2.1 用户注册

项目	说明

路径	POST /users/register/

认证	❌ 不需要

请求体：



json

{

&#x20;   "username": "testuser",

&#x20;   "phone": "13800138000",

&#x20;   "password": "123456"

}

参数	类型	必填	说明

username	string	✅	用户名，3\~150位

phone	string	✅	手机号，11位数字

password	string	✅	密码，6\~128位

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "注册成功",

&#x20;   "data": {

&#x20;       "id": 1,

&#x20;       "username": "testuser",

&#x20;       "phone": "13800138000",

&#x20;       "avatar": null,

&#x20;       "gender": null,

&#x20;       "email": ""

&#x20;   }

}

2.2 用户登录

项目	说明

路径	POST /users/login/

认证	❌ 不需要

请求体：



json

{

&#x20;   "username": "testuser",

&#x20;   "password": "123456"

}

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "登录成功",

&#x20;   "data": {

&#x20;       "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",

&#x20;       "user": {

&#x20;           "id": 1,

&#x20;           "username": "testuser",

&#x20;           "phone": "13800138000",

&#x20;           "avatar": null,

&#x20;           "gender": null,

&#x20;           "email": ""

&#x20;       }

&#x20;   }

}

失败响应：



json

{

&#x20;   "code": 401,

&#x20;   "msg": "用户名或密码错误"

}

2.3 获取个人信息

项目	说明

路径	GET /users/profile/

认证	✅ 需要登录

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": {

&#x20;       "id": 1,

&#x20;       "username": "testuser",

&#x20;       "phone": "13800138000",

&#x20;       "avatar": null,

&#x20;       "gender": null,

&#x20;       "email": "",

&#x20;       "is\_active": true,

&#x20;       "is\_staff": false,

&#x20;       "is\_superuser": false

&#x20;   }

}

2.4 修改个人信息

项目	说明

路径	PUT /users/profile/

认证	✅ 需要登录

说明	支持部分更新，只传需要修改的字段即可

请求体（示例，所有字段均选填）：



json

{

&#x20;   "username": "新名字",

&#x20;   "avatar": "https://example.com/avatar.jpg",

&#x20;   "gender": "M",

&#x20;   "email": "new@email.com"

}

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "更新成功",

&#x20;   "data": { ... }  // 完整用户信息

}

三、图书展示模块（/books）

3.1 图书列表（含搜索/筛选/排序）

项目	说明

路径	GET /books/

认证	❌ 不需要

请求参数（全部选填）：



参数	类型	说明	示例

page	int	页码，默认1	?page=2

page\_size	int	每页条数，默认10	?page\_size=20

search	string	关键词搜索（书名/作者/ISBN）	?search=三体

category	int	分类ID筛选	?category=1

publisher	string	出版社筛选	?publisher=中信出版社

price\_min	decimal	最低价格	?price\_min=10

price\_max	decimal	最高价格	?price\_max=50

is\_new	boolean	true=只显示7天内新书	?is\_new=true

ordering	string	排序字段	见下方说明

排序字段说明：



值	含义

sale\_price	按代表售价从低到高排序（优先纸质在售，其次电子版在售）

\-sale\_price	按代表售价从高到低排序（优先纸质在售，其次电子版在售）

sales\_count	销量从低到高

\-sales\_count	销量从高到低

rating	评分从低到高

\-rating	评分从高到低

publish\_date	出版日期从早到晚

\-publish\_date	出版日期从晚到早

请求示例：



text

GET /api/books/?search=三体\&category=1\&ordering=-sale\_price\&page=1\&page\_size=10

成功响应：



json

{

&#x20;   "count": 100,

&#x20;   "next": "http://127.0.0.1:8000/api/books/?page=2",

&#x20;   "previous": null,

&#x20;   "results": \[

&#x20;       {

&#x20;           "id": 1,

&#x20;           "title": "活着",

&#x20;           "author": "余华",

&#x20;           "cover\_image": "/media/covers/1.jpeg",

&#x20;           "sale\_price": "20.00",

&#x20;           "rating": 4.8,

&#x20;           "sales\_count": 1520,

&#x20;           "stock": 50,

&#x20;           "category\_name": "文学"

&#x20;       }

&#x20;   ]

}

3.2 图书详情

项目	说明

路径	GET /books/{id}/

认证	❌ 不需要

说明	已购买电子版的用户可查看已下架图书

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": {

&#x20;       "id": 1,

&#x20;       "title": "活着",

&#x20;       "author": "余华",

&#x20;       "isbn": "9787506365437",

&#x20;       "publisher": "作家出版社",

&#x20;       "publish\_date": "2012-08-01",

&#x20;       "cover\_image": "/media/covers/1.jpeg",

&#x20;       "description": "《活着》讲述了农村人福贵的悲惨人生遭遇...",

&#x20;       "catalog": "第一章 我家...",

&#x20;       "content\_file\_path": "books/content/1.txt",

&#x20;       "category": {

&#x20;           "id": 1,

&#x20;           "name": "文学",

&#x20;           "parent": null

&#x20;       },

&#x20;       "versions": \[

&#x20;           {

&#x20;               "id": 1,

&#x20;               "version\_type": "digital",

&#x20;               "type\_label": "电子版",

&#x20;               "price": "16.00",

&#x20;               "sale\_price": "12.00",

&#x20;               "stock": 99999,

&#x20;               "is\_on\_sale": true

&#x20;           },

&#x20;           {

&#x20;               "id": 2,

&#x20;               "version\_type": "physical",

&#x20;               "type\_label": "纸质版",

&#x20;               "price": "28.00",

&#x20;               "sale\_price": "20.00",

&#x20;               "stock": 50,

&#x20;               "is\_on\_sale": true

&#x20;           }

&#x20;       ],

&#x20;       "is\_on\_sale": true,

&#x20;       "rating": 4.8,

&#x20;       "sales\_count": 1520,

&#x20;       "on\_shelf\_date": "2026-07-07",

&#x20;       "has\_preview": true,     // 是否有试读内容

&#x20;       "has\_digital": true,     // 是否提供电子版

&#x20;       "has\_physical": true     // 是否提供纸质版

&#x20;   }

}

3.3 首页聚合数据

项目	说明

路径	GET /books/home/

认证	❌ 不需要

说明	一次请求获取首页所有数据，减少请求次数；new_books 按上架时间与创建时间倒序返回最近上架的图书，最多 10 本

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": {

&#x20;       "banners": \[],  // 预留，后续配置轮播图

&#x20;       "new\_books": \[

&#x20;           {

&#x20;               "id": 1,

&#x20;               "title": "活着",

&#x20;               "author": "余华",

&#x20;               "cover\_image": "/media/covers/1.jpeg",

&#x20;               "sale\_price": "20.00",

&#x20;               "rating": 4.8,

&#x20;               "sales\_count": 1520,

&#x20;               "category\_name": "文学"

&#x20;           }

&#x20;           // ... 最多10本

&#x20;       ],

&#x20;       "hot\_books": \[

&#x20;           {

&#x20;               "id": 1,

&#x20;               "title": "活着",

&#x20;               "author": "余华",

&#x20;               "cover\_image": "/media/covers/1.jpeg",

&#x20;               "sale\_price": "20.00",

&#x20;               "rating": 4.8,

&#x20;               "sales\_count": 1520,

&#x20;               "category\_name": "文学"

&#x20;           }

&#x20;           // ... 最多10本

&#x20;       ]

&#x20;   }

}

3.4 图书试读

项目	说明

路径	GET /books/{id}/preview/

认证	✅ 需要登录

说明	返回正文前10%内容，用于试读功能

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": {

&#x20;       "book\_id": 1,

&#x20;       "book\_title": "活着",

&#x20;       "content": "我比现在年轻十岁的时候，获得了一个游手好闲的职业...",

&#x20;       "total\_length": 11000,

&#x20;       "preview\_length": 1100,

&#x20;       "is\_complete": false

&#x20;   }

}

is\_complete: true 表示全文不足10%，已全部展示



content 为空时表示本书暂无试读内容



3.5 阅读全文

项目	说明

路径	GET /books/{id}/read/

认证	✅ 需要登录 + 已购买电子版

说明	已购买电子版的用户可阅读全书，不受图书下架影响

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": {

&#x20;       "book\_id": 1,

&#x20;       "title": "活着",

&#x20;       "author": "余华",

&#x20;       "content": "全文内容...",

&#x20;       "total\_length": 11000

&#x20;   }

}

失败响应：



json

{

&#x20;   "code": 403,

&#x20;   "msg": "您尚未购买该书的电子版，请先购买"

}

四、购物车模块（/cart）

4.1 购物车列表

项目	说明

路径	GET /cart/

认证	✅ 需要登录

成功响应：



json

{

&#x20;   "items": \[

&#x20;       {

&#x20;           "id": 1,

&#x20;           "book": 1,

&#x20;           "book\_detail": {

&#x20;               "id": 1,

&#x20;               "title": "活着",

&#x20;               "author": "余华",

&#x20;               "cover\_image": "/media/covers/1.jpeg",

&#x20;               "sale\_price": "12.00"

&#x20;           },

&#x20;           "quantity": 2,

&#x20;           "is\_selected": true,

&#x20;           "version\_type": "digital",

&#x20;           "subtotal": "24.00",

&#x20;           "created\_at": "2026-07-14T10:00:00Z"

&#x20;       }

&#x20;   ],

&#x20;   "selected\_total": "24.00",   // 勾选商品总价

&#x20;   "invalid\_count": 1,           // 失效商品数量

&#x20;   "invalid\_items": \[            // 失效商品详情

&#x20;       {

&#x20;           "id": 2,

&#x20;           "book": 3,

&#x20;           "book\_detail": { ... },

&#x20;           "quantity": 1,

&#x20;           "is\_selected": false,

&#x20;           "version\_type": "physical",

&#x20;           "subtotal": "18.50"

&#x20;       }

&#x20;   ]

}

4.2 添加商品到购物车

项目	说明

路径	POST /cart/

认证	✅ 需要登录

请求体：



json

{

&#x20;   "book\_id": 1,

&#x20;   "version\_type": "digital",

&#x20;   "quantity": 1

}

参数	类型	必填	说明

book\_id	int	✅	图书ID

version\_type	string	❌	digital 或 physical，默认 physical

quantity	int	❌	数量，默认1

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "添加成功",

&#x20;   "data": { ... }  // 完整的购物车条目信息

}

失败响应：



json

{

&#x20;   "code": 400,

&#x20;   "msg": "库存不足，当前库存仅 5 本"

}

4.3 修改数量

项目	说明

路径	PUT /cart/{item\_id}/

认证	✅ 需要登录

请求体：



json

{

&#x20;   "quantity": 5

}

4.4 删除单个商品

项目	说明

路径	DELETE /cart/{item\_id}/

认证	✅ 需要登录

4.5 批量切换勾选状态

项目	说明

路径	POST /cart/batch/

认证	✅ 需要登录

请求体：



json

{

&#x20;   "item\_ids": \[1, 2, 3],

&#x20;   "is\_selected": false

}

4.6 批量删除

项目	说明

路径	DELETE /cart/batch/

认证	✅ 需要登录

请求体：



json

{

&#x20;   "item\_ids": \[1, 2, 3]

}

4.7 清理失效商品

项目	说明

路径	DELETE /cart/clear-invalid/

认证	✅ 需要登录

说明	删除所有已下架或缺货的商品

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "已清理 2 件失效商品"

}

五、订单模块（/orders）

5.1 创建订单

项目	说明

路径	POST /orders/

认证	✅ 需要登录

说明	基于购物车勾选商品创建订单，自动锁定库存

请求体：



json

{

&#x20;   "address": "北京市朝阳区建国路88号SOHO现代城A座1201室",

&#x20;   "receiver": "张三",

&#x20;   "phone": "13800138000",

&#x20;   "cart\_item\_ids": \[1, 2],

&#x20;   "remark": "请用顺丰发货"

}

参数	类型	必填	说明

address	string	✅	收货详细地址

receiver	string	✅	收货人姓名

phone	string	✅	收货人手机号，11位

cart\_item\_ids	array	✅	购物车条目ID列表（需为勾选状态）

remark	string	❌	订单备注

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "订单创建成功，请尽快支付",

&#x20;   "data": {

&#x20;       "id": 1,

&#x20;       "order\_no": "20260714A1B2C3D4",

&#x20;       "status": 1,

&#x20;       "status\_text": "待付款",

&#x20;       "total\_amount": "36.00",

&#x20;       "pay\_amount": "36.00",

&#x20;       "receiver": "张三",

&#x20;       "receiver\_phone": "13800138000",

&#x20;       "receiver\_address": "北京市朝阳区建国路88号SOHO现代城A座1201室",

&#x20;       "items": \[...],

&#x20;       "created\_at": "2026-07-14T10:00:00Z"

&#x20;   }

}

5.2 订单列表

项目	说明

路径	GET /orders/

认证	✅ 需要登录

请求参数：



参数	类型	必填	说明

status	int	❌	1=待付款，2=已提交，3=待收货，4=已完成，5=已取消

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": \[

&#x20;       {

&#x20;           "id": 1,

&#x20;           "order\_no": "20260714A1B2C3D4",

&#x20;           "status": 1,

&#x20;           "status\_text": "待付款",

&#x20;           "total\_amount": "36.00",

&#x20;           "receiver": "张三",

&#x20;           "receiver\_phone": "13800138000",

&#x20;           "created\_at": "2026-07-14T10:00:00Z",

&#x20;           "item\_count": 2

&#x20;       }

&#x20;   ]

}

5.3 订单详情

项目	说明

路径	GET /orders/{order\_id}/

认证	✅ 需要登录

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": {

&#x20;       "id": 1,

&#x20;       "order\_no": "20260714A1B2C3D4",

&#x20;       "status": 1,

&#x20;       "status\_text": "待付款",

&#x20;       "total\_amount": "36.00",

&#x20;       "pay\_amount": "36.00",

&#x20;       "receiver": "张三",

&#x20;       "receiver\_phone": "13800138000",

&#x20;       "receiver\_address": "北京市朝阳区建国路88号SOHO现代城A座1201室",

&#x20;       "express\_no": null,

&#x20;       "express\_company": null,

&#x20;       "remark": "请用顺丰发货",

&#x20;       "items": \[

&#x20;           {

&#x20;               "id": 1,

&#x20;               "book\_id": 1,

&#x20;               "book\_title": "活着",

&#x20;               "book\_cover": "/media/covers/1.jpeg",

&#x20;               "book\_author": "余华",

&#x20;               "sale\_price": "12.00",

&#x20;               "quantity": 1,

&#x20;               "subtotal": "12.00",

&#x20;               "version\_type": "digital"    // digital=电子版, physical=纸质版

&#x20;           }

&#x20;       ],

&#x20;       "created\_at": "2026-07-14T10:00:00Z",

&#x20;       "pay\_time": null,

&#x20;       "ship\_time": null,

&#x20;       "receive\_time": null

&#x20;   }

}

5.4 订单操作（支付/取消/确认收货）

项目	说明

路径	PUT /orders/{order\_id}/

认证	✅ 需要登录

请求体：



json

{

&#x20;   "action": "pay"

}

参数	类型	必填	说明

action	string	✅	pay（支付）、cancel（取消）、confirm（确认收货）

不同 action 的业务效果：



action	适用状态	效果

pay	待付款（1）	支付订单。全电子版→直接完成；含纸质版→等待发货

cancel	待付款（1）	取消订单，释放库存

confirm	待收货（3）	确认收货，订单完成

支付成功响应（全部为电子版）：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "支付成功，订单已完成",

&#x20;   "data": {

&#x20;       "id": 1,

&#x20;       "status": 4,

&#x20;       "status\_text": "已完成",

&#x20;       "pay\_time": "2026-07-14T10:05:00Z",

&#x20;       ...

&#x20;   }

}

支付成功响应（包含纸质版）：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "支付成功，等待发货",

&#x20;   "data": {

&#x20;       "id": 1,

&#x20;       "status": 2,

&#x20;       "status\_text": "已提交",

&#x20;       "pay\_time": "2026-07-14T10:05:00Z",

&#x20;       ...

&#x20;   }

}

5.5 我的书架

项目	说明

路径	GET /orders/bookshelf/

认证	✅ 需要登录

说明	查看已购买的电子书列表，已下架图书仍然显示

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": \[

&#x20;       {

&#x20;           "book\_id": 1,

&#x20;           "title": "活着",

&#x20;           "author": "余华",

&#x20;           "cover\_image": "/media/covers/1.jpeg",

&#x20;           "purchased\_at": "2026-07-14T10:05:00Z",

&#x20;           "can\_read": true,

&#x20;           "is\_on\_sale": true    // false 表示已下架，但用户仍可阅读

&#x20;       }

&#x20;   ]

}

六、用户互动模块（/interactions）

6.1 评价列表

项目	说明

路径	GET /interactions/reviews/

认证	❌ 不需要

请求参数：



参数	类型	必填	说明

book\_id	int	❌	筛选指定图书的评价。不传则返回当前用户的评价

示例请求：



text

GET /api/interactions/reviews/?book\_id=1

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": \[

&#x20;       {

&#x20;           "id": 1,

&#x20;           "user": 2,

&#x20;           "username": "testuser1",

&#x20;           "book": 1,

&#x20;           "book\_title": "活着",

&#x20;           "rating": 5,

&#x20;           "comment": "非常好看，强烈推荐！",

&#x20;           "created\_at": "2026-07-14T10:00:00Z",

&#x20;           "updated\_at": "2026-07-14T10:00:00Z"

&#x20;       }

&#x20;   ]

}

6.2 创建评价

项目	说明

路径	POST /interactions/reviews/

认证	✅ 需要登录

说明	用户必须已购买该书且订单状态为“已完成”

请求体：



json

{

&#x20;   "book\_id": 1,

&#x20;   "rating": 5,

&#x20;   "comment": "非常好看，强烈推荐！"

}

参数	类型	必填	说明

book\_id	int	✅	图书ID

rating	int	✅	1\~5星

comment	string	❌	评价内容，可选

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "评价成功",

&#x20;   "data": {

&#x20;       "id": 1,

&#x20;       "rating": 5,

&#x20;       "comment": "非常好看，强烈推荐！",

&#x20;       "created\_at": "2026-07-14T10:00:00Z"

&#x20;   }

}

失败响应：



json

{

&#x20;   "code": 400,

&#x20;   "msg": "您尚未购买该书或订单未完成，无法评价"

}

6.3 我的评价

项目	说明

路径	GET /interactions/reviews/me/

认证	✅ 需要登录

功能	获取当前用户的所有评价

6.4 收藏切换

项目	说明

路径	POST /interactions/favorites/toggle/

认证	✅ 需要登录

说明	已收藏则取消收藏，未收藏则添加收藏

请求体：



json

{

&#x20;   "book\_id": 1

}

成功响应（首次收藏）：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "added成功",

&#x20;   "data": {

&#x20;       "action": "added",

&#x20;       "book\_id": 1

&#x20;   }

}

成功响应（取消收藏）：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "removed成功",

&#x20;   "data": {

&#x20;       "action": "removed",

&#x20;       "book\_id": 1

&#x20;   }

}

6.5 我的收藏

项目	说明

路径	GET /interactions/favorites/

认证	✅ 需要登录

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": \[

&#x20;       {

&#x20;           "id": 1,

&#x20;           "book": 1,

&#x20;           "book\_detail": {

&#x20;               "id": 1,

&#x20;               "title": "活着",

&#x20;               "author": "余华",

&#x20;               "cover\_image": "/media/covers/1.jpeg",

&#x20;               "sale\_price": "20.00",

&#x20;               "rating": 4.8,

&#x20;               "sales\_count": 1520,

&#x20;               "category\_name": "文学"

&#x20;           },

&#x20;           "created\_at": "2026-07-14T10:00:00Z"

&#x20;       }

&#x20;   ]

}

6.6 记录浏览历史

项目	说明

路径	POST /interactions/histories/

认证	✅ 需要登录

说明	用户进入图书详情页时调用，系统自动保留最近20条

请求体：



json

{

&#x20;   "book\_id": 1

}

6.7 浏览历史列表

项目	说明

路径	GET /interactions/histories/

认证	✅ 需要登录

说明	返回最近20条浏览记录

6.8 清空浏览历史

项目	说明

路径	DELETE /interactions/histories/

认证	✅ 需要登录

七、后台管理模块（/admin）

⚠️ 权限说明：以下所有接口仅限 is\_staff=True 或 is\_superuser=True 的管理员访问。普通用户访问返回 403。



7.1 管理员订单列表

项目	说明

路径	GET /admin/orders/

认证	✅ 需要登录 + 管理员权限

请求参数（全部选填）：



参数	类型	说明

status	int	1=待付款，2=已提交，3=待收货，4=已完成，5=已取消

order\_no	string	订单号搜索（模糊匹配）

receiver	string	收货人搜索（模糊匹配）

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": \[

&#x20;       {

&#x20;           "id": 1,

&#x20;           "order\_no": "20260714A1B2C3D4",

&#x20;           "status": 2,

&#x20;           "status\_text": "已提交",

&#x20;           "total\_amount": "36.00",

&#x20;           "receiver": "张三",

&#x20;           "receiver\_phone": "13800138000",

&#x20;           "created\_at": "2026-07-14T10:00:00Z",

&#x20;           "item\_count": 2

&#x20;       }

&#x20;   ]

}

7.2 管理员订单详情

项目	说明

路径	GET /admin/orders/{order\_id}/

认证	✅ 需要登录 + 管理员权限

7.3 管理员订单操作

项目	说明

路径	PUT /admin/orders/{order\_id}/action/

认证	✅ 需要登录 + 管理员权限

请求体（发货）：



json

{

&#x20;   "action": "ship",

&#x20;   "express\_no": "SF1234567890",

&#x20;   "express\_company": "顺丰速运"

}

请求体（强制取消）：



json

{

&#x20;   "action": "cancel"

}

参数	类型	必填	说明

action	string	✅	ship（发货）或 cancel（强制取消）

express\_no	string	❌	快递单号（发货时推荐填写）

express\_company	string	❌	快递公司（发货时可选，默认“顺丰速运”）

操作规则：



当前状态	ship（发货）	cancel（取消）

待付款（1）	❌	✅

已提交（2）	✅	✅

待收货（3）	❌	✅

已完成（4）	❌	❌

已取消（5）	❌	❌

7.4 管理员用户列表

项目	说明

路径	GET /admin/users/

认证	✅ 需要登录 + 管理员权限

请求参数（全部选填）：



参数	类型	说明

keyword	string	用户名/手机号搜索（模糊匹配）

page	int	页码，默认1

page\_size	int	每页条数，默认20

成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "success",

&#x20;   "data": {

&#x20;       "total": 10,

&#x20;       "page": 1,

&#x20;       "page\_size": 20,

&#x20;       "items": \[

&#x20;           {

&#x20;               "id": 1,

&#x20;               "username": "admin",

&#x20;               "phone": "",

&#x20;               "avatar": null,

&#x20;               "gender": null,

&#x20;               "email": "",

&#x20;               "is\_active": true,

&#x20;               "is\_staff": true,

&#x20;               "is\_superuser": true

&#x20;           }

&#x20;       ]

&#x20;   }

}

7.5 管理员用户详情

项目	说明

路径	GET /admin/users/{user\_id}/

认证	✅ 需要登录 + 管理员权限

7.6 管理员禁用/启用用户

项目	说明

路径	PUT /admin/users/{user\_id}/toggle/

认证	✅ 需要登录 + 管理员权限

请求体：



json

{

&#x20;   "is\_active": false

}

参数	类型	必填	说明

is\_active	boolean	✅	true=启用，false=禁用

限制：



不能禁用或启用自己



不能操作超级管理员账号



成功响应：



json

{

&#x20;   "code": 200,

&#x20;   "msg": "用户已禁用",

&#x20;   "data": {

&#x20;       "user\_id": 2,

&#x20;       "username": "testuser",

&#x20;       "is\_active": false

&#x20;   }

}

八、接口速查表

公开接口（无需登录）

方法	路径	功能

POST	/users/register/	用户注册

POST	/users/login/	用户登录

GET	/books/	图书列表（含搜索/筛选/排序）

GET	/books/{id}/	图书详情

GET	/books/home/	首页聚合数据

GET	/interactions/reviews/	评价列表

需登录接口（普通用户）

方法	路径	功能

GET	/users/profile/	获取个人信息

PUT	/users/profile/	修改个人信息

GET	/books/{id}/preview/	试读

GET	/books/{id}/read/	阅读全文

GET	/cart/	购物车列表

POST	/cart/	添加商品到购物车

PUT	/cart/{item\_id}/	修改数量

DELETE	/cart/{item\_id}/	删除单个商品

POST	/cart/batch/	批量切换勾选

DELETE	/cart/batch/	批量删除

DELETE	/cart/clear-invalid/	清理失效商品

POST	/orders/	创建订单

GET	/orders/	订单列表

GET	/orders/{id}/	订单详情

PUT	/orders/{id}/	订单操作

GET	/orders/bookshelf/	我的书架

POST	/interactions/reviews/	创建评价

GET	/interactions/reviews/me/	我的评价

POST	/interactions/favorites/toggle/	收藏切换

GET	/interactions/favorites/	我的收藏

POST	/interactions/histories/	记录浏览历史

GET	/interactions/histories/	浏览历史列表

DELETE	/interactions/histories/	清空浏览历史

需管理员权限接口

方法	路径	功能

GET	/admin/orders/	管理员订单列表

GET	/admin/orders/{id}/	管理员订单详情

PUT	/admin/orders/{id}/action/	管理员订单操作

GET	/admin/users/	管理员用户列表

GET	/admin/users/{id}/	管理员用户详情

PUT	/admin/users/{id}/toggle/	管理员禁用/启用用户

九、常见业务场景接口调用流程

场景 1：用户完整购书流程（纸质版）

text

1\. 注册 → POST /users/register/

2\. 登录 → POST /users/login/（获取 token）

3\. 浏览图书 → GET /books/

4\. 查看详情 → GET /books/{id}/

5\. 加入购物车 → POST /cart/（version\_type: "physical"）

6\. 查看购物车 → GET /cart/

7\. 创建订单 → POST /orders/

8\. 支付 → PUT /orders/{id}/（action: "pay"）

&#x20;  → 状态变为“已提交（2）”

9\. 等待管理员发货（管理员操作）

10\. 确认收货 → PUT /orders/{id}/（action: "confirm"）

&#x20;   → 状态变为“已完成（4）”

11\. 评价 → POST /interactions/reviews/

场景 2：用户完整购书流程（电子版）

text

1-7. 同上（加入购物车时 version\_type: "digital"）

8\. 支付 → PUT /orders/{id}/（action: "pay"）

&#x20;  → 状态直接变为“已完成（4）”，自动加入书架

9\. 阅读全文 → GET /books/{id}/read/

10\. 查看书架 → GET /orders/bookshelf/

场景 3：试读 + 购买决策

text

1\. 登录 → POST /users/login/

2\. 查看图书详情 → GET /books/{id}/

3\. 试读 → GET /books/{id}/preview/

4\. 决定购买 → 加入购物车 + 下单

场景 4：管理员发货流程

text

1\. 登录（管理员账号）

2\. 查看待发货订单 → GET /admin/orders/?status=2

3\. 查看订单详情 → GET /admin/orders/{id}/

4\. 发货 → PUT /admin/orders/{id}/action/（action: "ship"）

&#x20;  → 状态变为“待收货（3）”

5\. 用户确认后，订单变为“已完成（4）”

场景 5：管理员取消订单

text

1\. 查看待处理订单 → GET /admin/orders/?status=1

2\. 强制取消 → PUT /admin/orders/{id}/action/（action: "cancel"）

&#x20;  → 状态变为“已取消（5）”，库存自动释放

十、常见问题

Q1：电子版和纸质版如何区分？

在以下接口中通过 version\_type 字段区分：



接口	字段位置

加入购物车	请求参数 version\_type

购物车列表	响应中每个商品包含 version\_type

图书详情	响应中 versions 数组列出所有版本

订单详情	响应中每个商品包含 version\_type

Q2：为什么电子版支付后直接完成了？

电子版是虚拟商品，不需要物流发货，支付即交付。纸质版需要走完整的物流流程。



Q3：图书下架了，我还能阅读已购买的电子版吗？

能。 已购买的电子版不受下架影响，书架和阅读全文接口仍然可用。



Q4：为什么我不能评价某本书？

评价需要同时满足两个条件：



已购买该书



订单状态为“已完成”



Q5：Token 过期了怎么办？

调用登录接口重新获取 Token，前端需在收到 401 时跳转到登录页。





