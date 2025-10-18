from django.shortcuts import render
from django.contrib.auth import login

def confirm_email(request, code):
    confirmation = get_object_or_404(EmailConfirmation, code=code)
    if confirmation.is_expired():
        return render(request, 'emails/confirmation_expired.html')
    user = confirmation.user
    user.is_active = True
    user.save()
    login(request, user)  # ✅ Автовход
    confirmation.delete()
    return render(request, 'emails/confirmation_success.html')

def profile(request):
    return render(request, 'accounts/profile.html')