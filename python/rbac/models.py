from django.db import models

from common.models import SoftDeleteModel


class Menu(models.Model):
    name = models.CharField(max_length=64)
    name_en = models.CharField(max_length=64, blank=True, default='')
    name_tw = models.CharField(max_length=64, blank=True, default='')
    path = models.CharField(max_length=128, blank=True, default='')
    icon = models.CharField(max_length=64, blank=True, default='')
    component = models.CharField(max_length=64, blank=True, default='')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    sort = models.IntegerField(default=0)
    menu_type = models.CharField(max_length=16, default='menu')
    permission = models.CharField(max_length=64, blank=True, default='')
    visible = models.BooleanField(default=True)
    keep_alive = models.BooleanField(default=False)
    client = models.CharField(max_length=16, default='admin')

    class Meta:
        ordering = ['sort', 'id']

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'name_en': self.name_en or self.name,
            'name_tw': self.name_tw or self.name,
            'path': self.path,
            'icon': self.icon,
            'component': self.component,
            'parent_id': self.parent_id,
            'sort': self.sort,
            'menu_type': self.menu_type,
            'permission': self.permission,
            'visible': self.visible,
            'keep_alive': self.keep_alive,
            'client': self.client,
        }


class Role(SoftDeleteModel):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64)
    data_scope = models.CharField(max_length=16, default='all')
    remark = models.CharField(max_length=200, blank=True, default='')
    menus = models.ManyToManyField(Menu, blank=True, related_name='roles')

    class Meta:
        ordering = ['id']

    def public(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'code': self.code,
            'data_scope': self.data_scope,
            'remark': self.remark,
            'menu_ids': list(self.menus.values_list('id', flat=True)),
        }
