# Python + Vue3 H5 基座

Django 接口、Vue3 H5、Vue3 管理后台。本地默认 SQLite、本地文件和内存缓存，双击 `start.bat` 即可启动。

## 环境

- Python 3.10 或更高版本
- Node.js 18 或更高版本

## 启动

Windows 双击仓库根目录的 `start.bat`。停止双击 `stop.bat`。

| 说明 | 值 |
| --- | --- |
| H5 | http://localhost:5173 |
| 管理后台 | http://localhost:5174 |
| 后端 | http://localhost:8010 |
| 健康检查 | http://localhost:8010/api/v1/health |
| 接口说明 | http://localhost:8010/api/docs |
| 管理员 | `admin` / `123456` |
| 租户管理员 | `tenant` / `123456` |
| 普通用户 | `zhangsan` / `123456` |

## 给新客户开租户

1. 用平台超管 `admin` 登录管理后台。管理端第一次登录不显示验证码，密码错误后再出现算术验证码。
2. 打开「客户」，填写名称和编码并保存。编码在整个平台内唯一。
3. 在顶栏切换到该客户，再到「用户」和「角色」里为本租户创建管理员。保存时会写入当前租户，不能改到别的客户。
4. 把租户管理员账号交给客户。客户只能看到本租户的用户、订单、内容和日志。
5. 支付和短信密钥放在服务端环境变量，不要写进系统配置。生产环境用 `APP_ENV=prod`，顶栏会显示环境和版本。

旧数据会归到种子租户 `default`。平台超管的 `tenant` 为空，不传 `X-Tenant-Id` 时看全部客户。

数据库文件是 `data/app.sqlite3`。上传文件在 `data/uploads`。日志在 `data/logs/app.log`。

## 已接通的能力

- 账号密码、短信验证码、游客、注册、找回密码、注销。开发环境发送验证码时，响应里带 `debug_code`
- 微信公众号 / 小程序登录和小程序外的 JSSDK 签名。没有密钥时走本地模拟，非微信环境前端降级
- Access Token 放内存，Refresh Token 使用 HttpOnly Cookie。退出后会话立即失效，可用系统配置切换单设备登录
- 用户、角色、菜单、按钮权限、数据范围。H5 和后台按权限码控制
- 系统配置、轮播、公告、字典、省市区。H5 启动时拉取配置，后台保存后刷新即可生效
- 本地上传、分片合并、私有文件签名。存储可切到 MinIO；阿里云 OSS / 腾讯 COS 在缺少密钥时返回未配置
- 站内信、短信和邮件。默认写日志，配置 SMTP 或云短信密钥后走对应渠道
- 模拟支付、订单超时关闭。微信支付、支付宝在缺少商户参数时不会假装成功
- 埋点批量上报、前端异常、IP 黑名单
- 签到和问卷插件。其余插件只保留开关，未实现的不能打开
- 深色主题、中文简繁和英文、安全区、水印、草稿、海报、Excel、PDF

运营商一键登录、实名厂商、病毒扫描、百度统计 / 友盟 / 神策只保留钩子。直播、OCR、电子合同不在本模板范围内。多租户按客户隔离数据，平台超管可在顶栏切换客户。

没有 Redis 时，站内信用轮询。设置 `REDIS_URL` 后缓存改为 Redis。`USE_CELERY=1` 时可以用 `python -m celery -A jobs.celery_app worker` 跑同一套清理任务，默认仍是进程内定时任务。

## 切换真实渠道

复制 `python/.env.example` 为 `python/.env`，填入对应密钥，再在后台「配置」里把 `sms_provider`、`pay_channel`、`storage_provider` 改成目标值。使用 PostgreSQL 时再执行 `pip install -r python/requirements-postgres.txt`。

| 变量 | 用途 |
| --- | --- |
| `WECHAT_APP_ID` / `WECHAT_APP_SECRET` | 公众号登录和 JSSDK |
| `WECHAT_MINI_APP_ID` / `WECHAT_MINI_SECRET` | 小程序登录 |
| `WECHAT_MCH_ID` / `WECHAT_API_V3_KEY` | 微信支付 |
| `ALIPAY_APP_ID` / `ALIPAY_PRIVATE_KEY` | 支付宝 |
| `ALIYUN_SMS_*` / `TENCENT_SMS_*` | 短信 |
| `SMTP_*` | 邮件 |
| `MINIO_*` | MinIO |
| `ALIYUN_OSS_*` / `TENCENT_COS_*` | 对象存储占位，识别到密钥后仍需补齐官方 SDK 上传 |

## 目录

| 路径 | 内容 |
| --- | --- |
| `python/` | Django 接口。虚拟环境放在 `python/myenv`，不提交 |
| `h5/` | Vue3 H5，开发端口 5173 |
| `admin/` | Vue3 管理后台，开发端口 5174 |
| `data/` | 本地数据库、上传文件和日志。只提交 `data/.gitkeep` |
| `start.bat` / `stop.bat` | Windows 下启动和停止 8010、5173、5174 |

接口统一返回 `{ code, msg, data }`，`code` 为 0 表示成功。演示账号密码是 `123456`。注册、找回和修改密码仍要求至少 8 位，并且同时包含字母和数字。

## 手动启动

```bat
cd python
python -m venv myenv
myenv\Scripts\python -m pip install -r requirements.txt
myenv\Scripts\python manage.py migrate
myenv\Scripts\python seed_demo.py
myenv\Scripts\python manage.py runserver 0.0.0.0:8010
```

另开终端：

```bat
cd h5
npm install
npm run dev
```

```bat
cd admin
npm install
npm run dev
```

## 检查

```bat
cd python
myenv\Scripts\python manage.py test common.tests
```

```bat
cd h5
npm test
npm run lint
```

```bat
cd admin
npm run lint
```

仓库根目录执行一次 `npm install` 后，Git 提交前会跑 H5 和管理台的 `eslint`。持续集成在 `.github/workflows/ci.yml`：后端跑 `common.tests`，H5 跑 `vitest`。
