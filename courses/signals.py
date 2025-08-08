from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import CourseMaterial


@receiver(post_delete, sender=CourseMaterial)
def delete_file_on_delete(sender, instance, **kwargs):
    if instance.upload:
        instance.upload.delete(save=False)


@receiver(pre_save, sender=CourseMaterial)
def delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = CourseMaterial.objects.get(pk=instance.pk)
    except CourseMaterial.DoesNotExist:
        return

    # if the file has changed, delete the old one
    if old.upload and old.upload != instance.upload:
        old.upload.delete(save=False)