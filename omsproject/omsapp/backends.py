from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class PhoneOrUdiseBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try login with regn number for FPO
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            try:
                # Try login with phone for other usres
                user = UserModel.objects.get(phone=username)
            except UserModel.DoesNotExist:
                try:
                    # Try login with udise_code for the school
                    user = UserModel.objects.get(udise_code=username)
                except UserModel.DoesNotExist:
                    return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
