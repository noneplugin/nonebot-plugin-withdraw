# nonebot-plugin-withdraw

基于 [nonebot2](https://github.com/nonebot/nonebot2) 的简单撤回插件，让机器人撤回 **自己发出的消息**

使用场景是如果机器人发出了不和谐的消息，群友可以帮忙及时撤回

### 使用

**以下命令需要加[命令前缀](https://v2.nonebot.dev/docs/api/config#Config-command_start) (默认为`/`)，可自行设置为空**

#### 方式1：

@机器人 撤回 [num]

`num` 指机器人发的倒数第几条消息，从 `0` 开始，默认为 `0`，如：

```
@机器人 撤回    # 撤回倒数第一条消息
@机器人 撤回 1    # 撤回倒数第二条消息
```

#### 方式2：

回复需要撤回的消息，回复“撤回”

### 支持的 adapter

- [x] OneBot v11
- [x] OneBot v12
- [x] Kaiheila
- [x] Telegram
- [x] Feishu
- [x] RedProtocol
- [x] Discord
- [x] QQ
- [x] Satori
- [x] DoDo
