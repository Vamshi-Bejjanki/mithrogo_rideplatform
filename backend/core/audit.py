from core.models import AuditLog


def record(actor, action, obj, changes=None):
    """Append an audit entry. Used by admin saves/actions and any admin-triggered business change."""
    AuditLog.objects.create(
        actor=actor if actor is not None and getattr(actor, "is_authenticated", False) else None,
        action=action,
        model=obj._meta.label_lower,
        object_id=str(obj.pk),
        changes=changes or {},
    )
