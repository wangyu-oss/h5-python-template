PLUGINS = [
    {'code': 'checkin', 'name': '签到', 'implemented': True},
    {'code': 'survey', 'name': '问卷', 'implemented': True},
    {'code': 'lottery', 'name': '抽奖', 'implemented': False},
    {'code': 'vote', 'name': '投票', 'implemented': False},
    {'code': 'points', 'name': '积分任务', 'implemented': False},
    {'code': 'member', 'name': '会员优惠券', 'implemented': False},
    {'code': 'comment', 'name': '评论点赞收藏', 'implemented': False},
    {'code': 'map', 'name': '地图定位', 'implemented': False},
    {'code': 'live', 'name': '直播点播', 'implemented': False},
    {'code': 'ai', 'name': 'AI 对话', 'implemented': False},
    {'code': 'contract', 'name': '电子合同', 'implemented': False},
    {'code': 'ocr', 'name': 'OCR', 'implemented': False},
    {'code': 'saas', 'name': '多租户', 'implemented': False},
]


def plugin_state(code):
    from common.settings_store import setting
    item = next((row for row in PLUGINS if row['code'] == code), None)
    if item is None:
        return None
    enabled = setting(f'plugin_{code}', 'yes' if item['implemented'] else 'no') == 'yes'
    return {**item, 'enabled': enabled and item['implemented'], 'switch': setting(f'plugin_{code}', 'no')}


def require_plugin(code):
    state = plugin_state(code)
    if state is None or not state['implemented']:
        return '插件未实现'
    if state['switch'] != 'yes':
        return '插件未启用'
    return ''
