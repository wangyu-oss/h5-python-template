from django.db.models.signals import pre_save
from django.dispatch import receiver

from common.context import get_current_account
from common.models import TimeStampedModel


@receiver(pre_save)
def fill_operator(sender, instance, **kwargs):
    if not isinstance(instance, TimeStampedModel):
        return
    account = get_current_account()
    if account is None or not getattr(account, 'pk', None):
        return
    if instance._state.adding and not getattr(instance, 'created_by_id', None):
        instance.created_by = account
