from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.auth import login_required, permission_required
from common.response import body, err, ok
from common.settings_store import clear_setting_cache
from plugins.models import Checkin, Survey, SurveyResponse
from plugins.registry import PLUGINS, plugin_state, require_plugin
from system.models import Setting


@csrf_exempt
@require_http_methods(['GET'])
def plugin_list(request):
    return ok({'items': [plugin_state(item['code']) for item in PLUGINS]})


@csrf_exempt
@permission_required('admin:plugin')
@require_http_methods(['POST'])
def plugin_toggle(request):
    data = body(request) or {}
    code = (data.get('code') or '').strip()
    state = plugin_state(code)
    if state is None:
        return err('插件不存在')
    enabled = 'yes' if data.get('enabled') else 'no'
    Setting.objects.update_or_create(key=f'plugin_{code}', defaults={'value': enabled, 'remark': state['name']})
    clear_setting_cache(f'plugin_{code}')
    return ok(plugin_state(code))


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def checkin_status(request):
    message = require_plugin('checkin')
    if message:
        return err(message)
    today = timezone.localdate()
    done = Checkin.objects.filter(account=request.account, day=today).exists()
    total = Checkin.objects.filter(account=request.account).count()
    return ok({'today': done, 'total': total, 'points': total})


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def checkin(request):
    message = require_plugin('checkin')
    if message:
        return err(message)
    today = timezone.localdate()
    row, created = Checkin.objects.get_or_create(account=request.account, day=today, defaults={'points': 1})
    if not created:
        return err('今天已经签到')
    return ok(row.public(), '签到成功')


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def surveys(request):
    message = require_plugin('survey')
    if message:
        return err(message)
    return ok({'items': [row.public() for row in Survey.objects.filter(enabled=True)]})


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def survey_detail(request, survey_id):
    message = require_plugin('survey')
    if message:
        return err(message)
    survey = Survey.objects.filter(id=survey_id, enabled=True).first()
    if survey is None:
        return err('问卷不存在', 404, 404)
    data = survey.public()
    data['questions'] = [row.public() for row in survey.questions.all()]
    data['submitted'] = SurveyResponse.objects.filter(survey=survey, account=request.account).exists()
    return ok(data)


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def survey_submit(request, survey_id):
    message = require_plugin('survey')
    if message:
        return err(message)
    survey = Survey.objects.filter(id=survey_id, enabled=True).first()
    if survey is None:
        return err('问卷不存在', 404, 404)
    if SurveyResponse.objects.filter(survey=survey, account=request.account).exists():
        return err('已经提交过')
    data = body(request) or {}
    SurveyResponse.objects.create(survey=survey, account=request.account, answers=data.get('answers') or {})
    return ok({'submitted': True})
