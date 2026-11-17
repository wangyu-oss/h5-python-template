from django.db import models

from common.models import TimeStampedModel
from system.models import fmt


class Checkin(models.Model):
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='checkins')
    day = models.DateField()
    points = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('account', 'day')]
        ordering = ['-day']

    def public(self):
        return {'day': self.day.isoformat(), 'points': self.points, 'created_at': fmt(self.created_at)}


class Survey(TimeStampedModel):
    title = models.CharField(max_length=120)
    enabled = models.BooleanField(default=True)

    def public(self):
        return {'id': self.id, 'title': self.title, 'enabled': self.enabled}


class SurveyQuestion(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=200)
    qtype = models.CharField(max_length=16, default='text')
    options = models.JSONField(default=list, blank=True)
    sort = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort', 'id']

    def public(self):
        return {'id': self.id, 'title': self.title, 'qtype': self.qtype, 'options': self.options or [], 'sort': self.sort}


class SurveyResponse(TimeStampedModel):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    answers = models.JSONField(default=dict)

    class Meta:
        unique_together = [('survey', 'account')]
