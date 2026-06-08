from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class DevPasswordBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if not username:
            return None
        try:
            user = UserModel.objects.get(username__iexact=username)
            if user.is_active:
                return user
        except UserModel.DoesNotExist:
            return None
        return None
