from django.contrib.auth.backends import ModelBackend


class VerifiedUserModelBackend(ModelBackend):
    def user_can_authenticate(self, user):
        base_allowed = super().user_can_authenticate(user)
        if not base_allowed:
            return False

        if user.is_superuser:
            return True

        if hasattr(user, 'is_verified'):
            return user.is_verified

        return True
