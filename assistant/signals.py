import logging
import threading
from django.db import transaction
from django.dispatch import receiver
from django.db.models.signals import post_save

from courses.models import CourseMaterial  # adjust import path to your app
from .pipeline import process_material

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CourseMaterial)
def build_indexes_on_create(sender, instance: CourseMaterial, created, **kwargs):
    if not created:
        return
    if instance.material_type != CourseMaterial.PDF:
        return
    if not instance.upload:
        return

    def _run():
        try:
            process_material(instance)
            logger.info("Indexed material %s (id=%s)", instance.title, instance.id)
        except Exception as e:
            logger.exception("Indexing failed for material %s: %s", instance.id, e)

    # Ensure file is committed to storage before processing
    transaction.on_commit(lambda: threading.Thread(target=_run, daemon=True).start())
