import mimetypes
import secrets
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.audit import log_op
from common.auth import login_required, permission_required
from common.response import body, client_ip, err, ok, paginate
from common.security import sign_payload
from common.settings_store import setting_int
from files.models import FileAccessLog, FileRecord
from files.storage import StorageError, get_storage, scan_file

ALLOWED = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.mp3', '.pdf', '.txt', '.xlsx', '.xls', '.zip', '.csv'}


def _check_file(name, size):
    suffix = Path(name).suffix.lower()
    if suffix and suffix not in ALLOWED:
        return '不支持的文件类型'
    limit = setting_int('max_upload_mb', 20) * 1024 * 1024
    if size > limit:
        return '文件超过大小限制'
    return ''


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def upload(request):
    upload_file = request.FILES.get('file')
    if upload_file is None:
        return err('请选择文件')
    message = _check_file(upload_file.name, upload_file.size)
    if message:
        return err(message)
    data = upload_file.read()
    if not scan_file(data):
        return err('文件未通过安全检查')
    try:
        storage = get_storage()
        path = storage.save(upload_file.name, data)
    except StorageError as exc:
        return err(str(exc))
    from common.scope import current_tenant_id
    record = FileRecord.objects.create(
        owner=request.account,
        tenant_id=current_tenant_id(request),
        name=upload_file.name,
        path=path,
        size=len(data),
        content_type=upload_file.content_type or '',
        storage=storage.name,
        is_private=request.POST.get('private') == '1',
    )
    log_op(request, 'file_upload', record.name)
    return ok(record.public())


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def chunk(request):
    upload_id = (request.POST.get('upload_id') or '').strip()
    index = request.POST.get('index') or '0'
    part = request.FILES.get('file')
    if not upload_id or part is None:
        return err('分片参数不完整')
    folder = settings.DATA_DIR / 'uploads' / 'chunks' / upload_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / index).write_bytes(part.read())
    return ok({'upload_id': upload_id, 'index': int(index)})


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def chunk_complete(request):
    data = body(request) or {}
    upload_id = (data.get('upload_id') or '').strip()
    name = (data.get('name') or 'file.bin').strip()
    total = int(data.get('total') or 0)
    folder = settings.DATA_DIR / 'uploads' / 'chunks' / upload_id
    if not upload_id or not folder.exists() or total <= 0:
        return err('分片不存在')
    blob = b''.join((folder / str(index)).read_bytes() for index in range(total))
    message = _check_file(name, len(blob))
    if message:
        return err(message)
    try:
        storage = get_storage()
        path = storage.save(name, blob)
    except StorageError as exc:
        return err(str(exc))
    record = FileRecord.objects.create(
        owner=request.account,
        name=name,
        path=path,
        size=len(blob),
        content_type=mimetypes.guess_type(name)[0] or '',
        storage=storage.name,
        is_private=bool(data.get('private')),
    )
    for child in folder.iterdir():
        child.unlink()
    folder.rmdir()
    return ok(record.public())


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def file_list(request):
    qs = FileRecord.objects.filter(is_deleted=False)
    if not request.account.is_super:
        qs = qs.filter(owner=request.account)
    total, rows = paginate(request, qs)
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def file_delete(request):
    data = body(request) or {}
    row = FileRecord.objects.filter(id=data.get('id'), is_deleted=False).first()
    if row is None:
        return err('文件不存在')
    if row.owner_id != request.account.id and not request.account.is_super:
        return err('没有权限', 403, 403)
    try:
        get_storage().delete(row.path)
    except StorageError:
        pass
    row.is_deleted = True
    row.save(update_fields=['is_deleted', 'updated_at'])
    return ok({'deleted': True})


@csrf_exempt
@require_http_methods(['GET'])
def file_raw(request, file_id):
    row = FileRecord.objects.filter(id=file_id, is_deleted=False).first()
    if row is None:
        return err('文件不存在', 404, 404)
    if row.is_private:
        exp = request.GET.get('exp') or ''
        sign = request.GET.get('sign') or ''
        expected = sign_payload(settings.SECRET_KEY, f'{row.id}:{exp}')
        if not exp or sign != expected or int(exp) < int(timezone.now().timestamp()):
            if getattr(request, 'account', None) is None:
                return err('文件需要授权', 401, 401)
    try:
        content = get_storage().read(row.path) if row.storage == 'local' else _read_any(row)
    except Exception:
        return err('文件读取失败', 404, 404)
    FileAccessLog.objects.create(file=row, account=getattr(request, 'account', None), ip=client_ip(request)[:64])
    response = HttpResponse(content, content_type=row.content_type or 'application/octet-stream')
    response['Content-Disposition'] = f'inline; filename="{row.name}"'
    return response


def _read_any(row):
    from files.storage import LocalStorage, get_storage
    if row.storage == 'local':
        return LocalStorage().read(row.path)
    return get_storage().read(row.path)


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def file_sign(request):
    data = body(request) or {}
    row = FileRecord.objects.filter(id=data.get('id'), is_deleted=False).first()
    if row is None:
        return err('文件不存在')
    exp = int((timezone.now() + timedelta(minutes=10)).timestamp())
    sign = sign_payload(settings.SECRET_KEY, f'{row.id}:{exp}')
    return ok({'url': f'/api/v1/files/{row.id}/raw?exp={exp}&sign={sign}'})


@csrf_exempt
@permission_required('admin:file')
@require_http_methods(['GET'])
def admin_files(request):
    from common.scope import tenant_qs
    qs = tenant_qs(request, FileRecord.objects.filter(is_deleted=False))
    keyword = (request.GET.get('keyword') or '').strip()
    if keyword:
        qs = qs.filter(name__icontains=keyword)
    total, rows = paginate(request, qs)
    return ok({'items': [row.public() for row in rows], 'total': total})
