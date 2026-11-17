import os
import secrets
from pathlib import Path

from django.conf import settings

from common.settings_store import setting


class StorageError(Exception):
    pass


def scan_file(data):
    return True


class LocalStorage:
    name = 'local'

    def save(self, filename, data):
        safe = Path(filename).name or 'file'
        target_dir = settings.DATA_DIR / 'uploads'
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f'{secrets.token_hex(8)}_{safe}'
        target.write_bytes(data)
        return str(target.relative_to(settings.DATA_DIR)).replace('\\', '/')

    def read(self, path):
        return (settings.DATA_DIR / path).read_bytes()

    def delete(self, path):
        file = settings.DATA_DIR / path
        if file.exists():
            file.unlink()

    def signed_url(self, file_id, exp):
        return f'/api/v1/files/{file_id}/raw?exp={exp}'


class MinioStorage:
    name = 'minio'

    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', '').strip()
        self.access = os.getenv('MINIO_ACCESS_KEY', '').strip()
        self.secret = os.getenv('MINIO_SECRET_KEY', '').strip()
        self.bucket = os.getenv('MINIO_BUCKET', 'h5')
        if not self.endpoint or not self.access or not self.secret:
            raise StorageError('未配置 MinIO')

    def _client(self):
        from minio import Minio
        return Minio(self.endpoint, access_key=self.access, secret_key=self.secret, secure=os.getenv('MINIO_SECURE', '0') == '1')

    def save(self, filename, data):
        from io import BytesIO
        key = f'{secrets.token_hex(8)}_{Path(filename).name}'
        client = self._client()
        if not client.bucket_exists(self.bucket):
            client.make_bucket(self.bucket)
        client.put_object(self.bucket, key, BytesIO(data), len(data))
        return key

    def read(self, path):
        client = self._client()
        response = client.get_object(self.bucket, path)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, path):
        self._client().remove_object(self.bucket, path)

    def signed_url(self, file_id, exp):
        return f'/api/v1/files/{file_id}/raw?exp={exp}'


class AliyunStorage:
    name = 'aliyun'

    def __init__(self):
        if not os.getenv('ALIYUN_OSS_KEY') or not os.getenv('ALIYUN_OSS_SECRET') or not os.getenv('ALIYUN_OSS_BUCKET'):
            raise StorageError('未配置阿里云 OSS')

    def save(self, filename, data):
        raise StorageError('已识别阿里云 OSS 配置，请安装 oss2 后在此适配器补齐上传')

    def read(self, path):
        raise StorageError('阿里云 OSS 读取未启用')

    def delete(self, path):
        raise StorageError('阿里云 OSS 删除未启用')

    def signed_url(self, file_id, exp):
        return f'/api/v1/files/{file_id}/raw?exp={exp}'


class CosStorage(AliyunStorage):
    name = 'cos'

    def __init__(self):
        if not os.getenv('TENCENT_COS_SECRET_ID') or not os.getenv('TENCENT_COS_BUCKET'):
            raise StorageError('未配置腾讯云 COS')


def get_storage():
    provider = setting('storage_provider', os.getenv('STORAGE_PROVIDER', 'local') or 'local')
    if provider == 'minio':
        return MinioStorage()
    if provider == 'aliyun':
        return AliyunStorage()
    if provider == 'cos':
        return CosStorage()
    return LocalStorage()
