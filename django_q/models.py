import importlib
import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from picklefield import PickledObjectField


class Task(models.Model):
    name = models.CharField(max_length=100, editable=False)
    func = models.CharField(max_length=256)
    hook = models.CharField(max_length=256, null=True)
    args = PickledObjectField()
    kwargs = PickledObjectField()
    result = PickledObjectField(null=True)
    started = models.DateTimeField(editable=False)
    stopped = models.DateTimeField(editable=False)
    success = models.BooleanField(default=True, editable=False)

    @staticmethod
    def get_result(name):
        if Task.objects.filter(name=name).exists():
            return Task.objects.get(name=name).result
        return None

    def time_taken(self):
        return (self.stopped - self.started).total_seconds()

    class Meta:
        app_label = 'django_q'


@receiver(pre_save, sender=Task)
def call_hook(sender, instance, **kwargs):
    if instance.hook:
        module, func = instance.hook.rsplit('.', 1)
        try:
            m = importlib.import_module(module)
            f = getattr(m, func)
            f(instance)
        except Exception as e:
            logger = logging.getLogger('django-q')
            logger.error(_('return hook failed on {}').format(instance.name))
            logger.exception(e)


class SuccessManager(models.Manager):
    def get_queryset(self):
        return super(SuccessManager, self).get_queryset().filter(
            success=True)


class Success(Task):
    objects = SuccessManager()

    class Meta:
        app_label = 'django_q'
        verbose_name = _('Successful task')
        proxy = True


class FailureManager(models.Manager):
    def get_queryset(self):
        return super(FailureManager, self).get_queryset().filter(
            success=False)


class Failure(Task):
    objects = FailureManager()

    class Meta:
        app_label = 'django_q'
        verbose_name = _('Failed task')
        proxy = True


class Schedule(models.Model):
    func = models.CharField(max_length=256)
    hook = models.CharField(max_length=256, null=True, blank=True)
    args = models.CharField(max_length=256, null=True, blank=True)
    kwargs = models.CharField(max_length=256, null=True, blank=True)
    ONCE = 'O'
    HOURLY = 'H'
    DAILY = 'D'
    WEEKLY = 'W'
    MONTHLY = 'M'
    QUARTERLY = 'Q'
    YEARLY = 'Y'
    TYPE = (
        (ONCE, _('Once')),
        (HOURLY, _('Hourly')),
        (DAILY, _('Daily')),
        (WEEKLY, _('Weekly')),
        (MONTHLY, _('Monthly')),
        (QUARTERLY, _('Quarterly')),
        (YEARLY, _('Yearly')),
    )
    schedule_type = models.CharField(max_length=1, choices=TYPE, default=TYPE[0][0], verbose_name=_('Schedule Type'))
    repeats = models.SmallIntegerField(default=-1, verbose_name=_('Repeats'))
    next_run = models.DateTimeField(verbose_name=_('Next Run'), default=timezone.now, null=True)
    task = models.CharField(max_length=100, editable=False, null=True)

    def result(self):
        if Task.objects.filter(name=self.task).exists():
            task = Task.objects.get(name=self.task)
            if task.success:
                url = reverse('admin:django_q_success_change', args=(task.id,))
            else:
                url = reverse('admin:django_q_failure_change', args=(task.id,))
            return '<a href="{}">[{}]</a>'.format(url, self.task)

        return None

    def success(self):
        if Task.objects.filter(name=self.task).exists():
            return Task.objects.get(name=self.task).success

    success.boolean = True
    result.allow_tags = True

    class Meta:
        app_label = 'django_q'
        verbose_name = _('Scheduled task')
        ordering = ['next_run']
