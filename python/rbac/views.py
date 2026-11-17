from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.audit import log_op
from common.auth import permission_required
from common.response import body, err, ok
from rbac.models import Menu, Role
from rbac.tree import menu_tree


@csrf_exempt
@permission_required('admin:role')
@require_http_methods(['GET'])
def roles(request):
    from common.scope import tenant_qs
    return ok({'items': [row.public() for row in tenant_qs(request, Role.objects.filter(is_deleted=False))]} )


@csrf_exempt
@permission_required('admin:role')
@require_http_methods(['POST'])
def role_save(request):
    data = body(request) or {}
    if data.get('id'):
        from common.scope import tenant_qs
        role = tenant_qs(request, Role.objects.filter(id=data['id'], is_deleted=False)).first()
        if role is None:
            return err('角色不存在')
    else:
        code = (data.get('code') or '').strip()
        if not code:
            return err('请填写角色编码')
        from common.scope import current_tenant_id
        role = Role(code=code, tenant_id=current_tenant_id(request))
    role.name = (data.get('name') or role.name or role.code)[:64]
    if data.get('code'):
        role.code = data['code'][:64]
    role.data_scope = (data.get('data_scope') or role.data_scope or 'all')[:16]
    role.remark = (data.get('remark') or '')[:200]
    role.save()
    if 'menu_ids' in data:
        role.menus.set(data.get('menu_ids') or [])
    log_op(request, 'role_save', role.code)
    return ok(role.public())


@csrf_exempt
@permission_required('admin:role')
@require_http_methods(['POST'])
def role_delete(request):
    data = body(request) or {}
    role = Role.objects.filter(id=data.get('id'), is_deleted=False).first()
    if role is None:
        return err('角色不存在')
    role.soft_delete()
    log_op(request, 'role_delete', role.code)
    return ok({'deleted': True})


@csrf_exempt
@permission_required('admin:menu')
@require_http_methods(['GET'])
def menus(request):
    client = request.GET.get('client') or ''
    qs = Menu.objects.all()
    if client:
        qs = qs.filter(client=client)
    return ok({'items': [row.public() for row in qs], 'tree': menu_tree(qs)})


@csrf_exempt
@permission_required('admin:menu')
@require_http_methods(['POST'])
def menu_save(request):
    data = body(request) or {}
    if data.get('id'):
        menu = Menu.objects.filter(id=data['id']).first()
        if menu is None:
            return err('菜单不存在')
    else:
        menu = Menu()
    for field in ('name', 'name_en', 'name_tw', 'path', 'icon', 'component', 'menu_type', 'permission', 'client'):
        if field in data:
            setattr(menu, field, str(data.get(field) or '')[:128])
    if 'parent_id' in data:
        menu.parent_id = data.get('parent_id') or None
    if 'sort' in data:
        menu.sort = int(data.get('sort') or 0)
    if 'visible' in data:
        menu.visible = bool(data.get('visible'))
    if 'keep_alive' in data:
        menu.keep_alive = bool(data.get('keep_alive'))
    menu.save()
    log_op(request, 'menu_save', menu.name)
    return ok(menu.public())


@csrf_exempt
@permission_required('admin:menu')
@require_http_methods(['POST'])
def menu_delete(request):
    data = body(request) or {}
    menu = Menu.objects.filter(id=data.get('id')).first()
    if menu is None:
        return err('菜单不存在')
    menu.delete()
    log_op(request, 'menu_delete', data.get('id'))
    return ok({'deleted': True})
