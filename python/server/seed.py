import os

from django.contrib.auth.hashers import make_password

PASSWORD = '123456'

SETTINGS = [
    ('app_env', os.getenv('APP_ENV', 'dev'), '当前环境，dev 或 prod'),
    ('h5_title', 'H5 基座', 'H5 标题'),
    ('app_version', '1.1.0', '对外版本号'),
    ('h5_slogan', '配置改完刷新即可生效', '首页标语'),
    ('h5_primary', '#1989fa', '主题色'),
    ('h5_theme', 'light', 'light 或 dark'),
    ('h5_watermark', 'no', '页面水印'),
    ('h5_locale', 'zh-CN', '默认语言'),
    ('feature_share', 'yes', '分享'),
    ('feature_pay', 'yes', '支付'),
    ('feature_dark', 'yes', '深色模式'),
    ('feature_pwa', 'yes', 'PWA'),
    ('privacy_version', '1', '隐私协议版本'),
    ('register_enabled', 'yes', '开放注册'),
    ('login_captcha', 'no', '登录验证码'),
    ('allow_multi_login', 'yes', '多端在线'),
    ('access_minutes', '120', '访问令牌分钟'),
    ('refresh_days', '7', '刷新令牌天数'),
    ('login_fail_limit', '5', '失败锁定次数'),
    ('login_lock_minutes', '10', '锁定分钟'),
    ('rate_limit_ip', '300', '每分钟 IP 限流'),
    ('api_sign', 'no', '接口签名'),
    ('sms_provider', 'console', 'console/aliyun/tencent'),
    ('pay_channel', 'mock', 'mock/wechat/alipay'),
    ('storage_provider', 'local', 'local/minio/aliyun/cos'),
    ('max_upload_mb', '20', '上传大小 MB'),
    ('log_keep_days', '30', '接口日志保留天数'),
    ('doc_password', '', '接口文档密码，空则不校验'),
    ('plugin_checkin', 'yes', '签到插件'),
    ('plugin_survey', 'yes', '问卷插件'),
    ('plugin_lottery', 'no', '抽奖插件'),
    ('plugin_vote', 'no', '投票插件'),
    ('plugin_points', 'no', '积分插件'),
    ('plugin_member', 'no', '会员插件'),
    ('plugin_comment', 'no', '评论插件'),
    ('plugin_map', 'no', '地图插件'),
    ('plugin_live', 'no', '直播插件'),
    ('plugin_ai', 'no', 'AI 插件'),
    ('plugin_contract', 'no', '电子合同插件'),
    ('plugin_ocr', 'no', 'OCR 插件'),
    ('plugin_saas', 'no', '多租户插件'),
    ('admin_login_captcha', 'yes', '管理端登录验证码'),
    ('module_order', 'yes', '订单模块'),
    ('module_track', 'yes', '埋点模块'),
    ('module_notice', 'yes', '公告模块'),
    ('module_banner', 'yes', '轮播模块'),
    ('module_pay', 'yes', '支付模块'),
]

GROUPS = [
    ('组织', 'dir:org', 30),
    ('内容', 'dir:content', 40),
    ('业务', 'dir:biz', 50),
    ('系统', 'dir:system', 60),
]

# name, path, permission, client, menu_type, sort, parent_permission, visible
MENUS = [
    ('概览', '/dashboard', 'admin:log', 'admin', 'menu', 10, '', True),
    ('客户', '/tenants', 'admin:tenant', 'admin', 'menu', 20, '', True),
    ('用户', '/users', 'admin:user:list', 'admin', 'menu', 31, 'dir:org', True),
    ('保存用户', '', 'admin:user:save', 'admin', 'button', 32, 'dir:org', False),
    ('角色', '/roles', 'admin:role', 'admin', 'menu', 33, 'dir:org', True),
    ('菜单', '/menus', 'admin:menu', 'admin', 'menu', 34, 'dir:org', True),
    ('轮播', '/banners', 'admin:banner', 'admin', 'menu', 41, 'dir:content', True),
    ('公告', '/announcements', 'admin:notice', 'admin', 'menu', 42, 'dir:content', True),
    ('订单', '/orders', 'admin:pay', 'admin', 'menu', 51, 'dir:biz', True),
    ('消息模板', '/templates', 'admin:sms', 'admin', 'menu', 52, 'dir:biz', True),
    ('配置', '/settings', 'admin:setting', 'admin', 'menu', 61, 'dir:system', True),
    ('数据字典', '/dicts', 'admin:dict', 'admin', 'menu', 62, 'dir:system', True),
    ('文件', '/files', 'admin:file', 'admin', 'menu', 63, 'dir:system', True),
    ('日志', '/logs', 'admin:log', 'admin', 'menu', 64, 'dir:system', True),
    ('埋点', '/track', 'admin:track', 'admin', 'menu', 65, 'dir:system', True),
    ('插件', '/plugins', 'admin:plugin', 'admin', 'menu', 90, '', False),
    ('导出', '', 'admin:export', 'admin', 'button', 91, '', False),
    ('支付', '/demo/tools', 'h5:pay', 'h5', 'button', 20, '', False),
]


def run():
    from accounts.models import Account, Department, Tenant, UserGroup
    from notify.models import InboxMessage, MessageTemplate
    from plugins.models import Survey, SurveyQuestion
    from rbac.models import Menu, Role
    from system.models import Announcement, Banner, DictItem, DictType, Region, Setting

    tenant, _ = Tenant.objects.get_or_create(code='default', defaults={'name': '默认客户', 'status': 'active'})
    for key, value, remark in SETTINGS:
        category = 'basic'
        if key.startswith(('h5_', 'feature_')):
            category = 'h5'
        elif key.startswith('pay_') or key == 'module_pay' or key == 'module_order':
            category = 'pay'
        elif key.startswith(('sms_', 'plugin_')) or key.startswith('module_notice'):
            category = 'message'
        elif key.startswith(('login_', 'register_', 'admin_login', 'allow_', 'access_', 'refresh_', 'rate_', 'api_')):
            category = 'security'
        Setting.objects.update_or_create(key=key, tenant=None, defaults={'value': value, 'remark': remark, 'category': category})

    parents = {}
    menu_rows = []
    for name, permission, sort in GROUPS:
        parent, _ = Menu.objects.update_or_create(
            permission=permission,
            client='admin',
            defaults={'name': name, 'path': '', 'menu_type': 'directory', 'sort': sort, 'visible': True, 'parent': None},
        )
        parents[permission] = parent
        menu_rows.append(parent)
    for name, path, permission, client, menu_type, sort, parent_permission, visible in MENUS:
        lookup = {'client': client, 'path': path} if path else {'client': client, 'permission': permission, 'menu_type': menu_type}
        menu, _ = Menu.objects.update_or_create(
            **lookup,
            defaults={
                'name': name,
                'path': path,
                'permission': permission,
                'menu_type': menu_type,
                'sort': sort,
                'visible': visible,
                'parent': parents.get(parent_permission),
            },
        )
        menu_rows.append(menu)

    admin_role, _ = Role.objects.update_or_create(code='admin', defaults={'name': '管理员', 'data_scope': 'all'})
    user_role, _ = Role.objects.update_or_create(code='user', defaults={'name': '用户', 'data_scope': 'self'})
    guest_role, _ = Role.objects.update_or_create(code='guest', defaults={'name': '游客', 'data_scope': 'self'})
    admin_role.menus.set(menu_rows)
    user_role.menus.set([row for row in menu_rows if row.permission == 'h5:pay'])
    guest_role.menus.clear()

    dept, _ = Department.objects.get_or_create(name='默认部门', defaults={'sort': 1})
    group, _ = UserGroup.objects.get_or_create(code='normal', defaults={'name': '普通用户'})

    password = make_password(PASSWORD)
    admin, _ = Account.objects.update_or_create(
        username='admin',
        defaults={
            'password': password,
            'display_name': '管理员',
            'phone': '13800000000',
            'status': 'active',
            'is_super': True,
            'is_guest': False,
            'is_deleted': False,
            'dept': dept,
        },
    )
    user, _ = Account.objects.update_or_create(
        username='zhangsan',
        defaults={
            'password': password,
            'display_name': '张三',
            'phone': '13800138000',
            'status': 'active',
            'is_super': False,
            'is_guest': False,
            'is_deleted': False,
            'dept': dept,
        },
    )
    tenant_role, _ = Role.objects.update_or_create(code='tenant_admin', defaults={'name': '租户管理员', 'data_scope': 'all', 'tenant': tenant})
    tenant_role.menus.set([row for row in menu_rows if row.permission not in ('admin:tenant', 'admin:menu')])
    admin.roles.set([admin_role])
    user.tenant = tenant
    user.save(update_fields=['tenant'])
    user.roles.set([user_role])
    user.groups.set([group])
    tenant_admin, _ = Account.objects.update_or_create(
        username='tenant',
        defaults={
            'password': password,
            'display_name': '租户管理员',
            'phone': '13900000000',
            'status': 'active',
            'is_super': False,
            'is_guest': False,
            'is_deleted': False,
            'dept': dept,
            'tenant': tenant,
        },
    )
    tenant_admin.roles.set([tenant_role])

    Banner.objects.get_or_create(title='欢迎使用 H5 基座', defaults={'color': '#1989fa', 'sort': 1, 'link': '/mine'})
    Banner.objects.get_or_create(title='配置、支付、消息都已接通', defaults={'color': '#07c160', 'sort': 2, 'link': '/demo/tools'})
    notice, _ = Announcement.objects.get_or_create(
        title='系统公告',
        defaults={'content': '<p>这是一条来自后台的富文本公告，修改后刷新 H5 即可看到。</p>', 'enabled': True, 'tenant': tenant},
    )
    if notice.tenant_id is None:
        notice.tenant = tenant
        notice.save(update_fields=['tenant'])

    gender, _ = DictType.objects.get_or_create(code='gender', defaults={'name': '性别'})
    for sort, (label, value) in enumerate([('男', 'male'), ('女', 'female'), ('保密', 'unknown')]):
        DictItem.objects.get_or_create(dict_type=gender, value=value, defaults={'label': label, 'sort': sort})

    beijing, _ = Region.objects.get_or_create(code='110000', defaults={'name': '北京市'})
    city, _ = Region.objects.get_or_create(code='110100', defaults={'name': '北京市', 'parent': beijing})
    Region.objects.get_or_create(code='110101', defaults={'name': '东城区', 'parent': city})
    guangdong, _ = Region.objects.get_or_create(code='440000', defaults={'name': '广东省'})
    guangzhou, _ = Region.objects.get_or_create(code='440100', defaults={'name': '广州市', 'parent': guangdong})
    Region.objects.get_or_create(code='440106', defaults={'name': '天河区', 'parent': guangzhou})

    MessageTemplate.objects.get_or_create(
        code='login_code',
        defaults={'channel': 'sms', 'title': '登录验证码', 'content': '验证码 {code}，5 分钟内有效'},
    )
    MessageTemplate.objects.get_or_create(
        code='pay_ok',
        defaults={'channel': 'inbox', 'title': '支付成功', 'content': '{subject} 已支付'},
    )
    InboxMessage.objects.get_or_create(account=user, title='欢迎', defaults={'content': '这是一条站内信，未读时底部会显示红点。'})

    survey, _ = Survey.objects.get_or_create(title='体验问卷', defaults={'enabled': True})
    SurveyQuestion.objects.get_or_create(survey=survey, title='你从哪里打开这个页面？', defaults={'qtype': 'single', 'options': ['微信', '浏览器', '其他'], 'sort': 1})
    SurveyQuestion.objects.get_or_create(survey=survey, title='还希望模板补充什么？', defaults={'qtype': 'text', 'options': [], 'sort': 2})
    Banner.objects.filter(tenant__isnull=True).update(tenant=tenant)
    Announcement.objects.filter(tenant__isnull=True).update(tenant=tenant)
    return {'admin': admin.username, 'user': user.username, 'tenant': tenant_admin.username}
