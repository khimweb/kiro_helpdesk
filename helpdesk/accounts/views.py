from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator

from .forms import UserRegisterForm, LoginForm, ProfileUpdateForm, UserUpdateForm
from .models import User
from tickets.utils import role_required


def register_view(request):
    """Handle new user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            try:
                from tickets.notifications import send_auth_alert
                ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
                send_auth_alert(
                    username=user.username,
                    action='signup',
                    success=True,
                    ip_address=ip_address,
                    details=f'Email: {user.email}, Role: {user.get_role_display()}'
                )
            except Exception:
                pass

            request.session['ios_notification'] = {
                'type': 'success',
                'title': 'Registration Successful',
                'message': f'Account created successfully. Welcome {user.username}!',
                'icon': '✅',
                'auto_hide': True,
                'duration': 4000
            }

            messages.success(request, 'Account created successfully. Welcome!')
            return redirect('dashboard')
        else:
            try:
                from tickets.notifications import send_auth_alert
                username = form.data.get('username', 'Unknown')
                ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
                send_auth_alert(
                    username=username,
                    action='signup',
                    success=False,
                    ip_address=ip_address,
                    details='Form validation failed'
                )
            except Exception:
                pass

            request.session['ios_notification'] = {
                'type': 'error',
                'title': 'Registration Failed',
                'message': 'Please check the form for errors',
                'icon': '❌',
                'auto_hide': True,
                'duration': 4000
            }
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Send Telegram notification — never let it crash the request
            try:
                from tickets.notifications import send_auth_alert
                ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
                send_auth_alert(
                    username=user.username,
                    action='login',
                    success=True,
                    ip_address=ip_address,
                    details=f'Role: {user.get_role_display()}'
                )
            except Exception:
                pass

            request.session['ios_notification'] = {
                'type': 'success',
                'title': 'Login Successful',
                'message': f'Welcome back, {user.username}!',
                'icon': '✅',
                'auto_hide': True,
                'duration': 4000
            }

            messages.success(request, f'Welcome back, {user.username}!')
            # next must be a safe relative URL — fall back to dashboard name
            next_url = request.GET.get('next', '').strip()
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('dashboard')
        else:
            # Send Telegram notification — never let it crash the request
            try:
                from tickets.notifications import send_auth_alert
                username = form.data.get('username', 'Unknown')
                ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
                send_auth_alert(
                    username=username,
                    action='login',
                    success=False,
                    ip_address=ip_address,
                    details='Invalid credentials'
                )
            except Exception:
                pass

            request.session['ios_notification'] = {
                'type': 'error',
                'title': 'Login Failed',
                'message': 'Invalid username or password',
                'icon': '❌',
                'auto_hide': True,
                'duration': 4000
            }
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    try:
        from tickets.notifications import send_auth_alert
        ip_address = request.META.get('REMOTE_ADDR', 'Unknown')
        send_auth_alert(
            username=request.user.username,
            action='logout',
            success=True,
            ip_address=ip_address,
            details='User logged out successfully'
        )
    except Exception:
        pass

    logout(request)

    request.session['ios_notification'] = {
        'type': 'info',
        'title': 'Logged Out',
        'message': 'You have been logged out successfully',
        'icon': 'ℹ️',
        'auto_hide': True,
        'duration': 4000
    }

    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile_view(request):
    """View and update the logged-in user's profile."""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            
            # Send Telegram notification for profile update
            from tickets.notifications import send_change_alert
            send_change_alert(
                user=request.user,
                action='update',
                object_type='profile',
                object_info=f'User: {request.user.username}',
                details='Profile information updated'
            )
            
            # Add iOS-style notification data to session
            request.session['ios_notification'] = {
                'type': 'success',
                'title': 'Profile Updated',
                'message': 'Your profile has been updated successfully',
                'icon': '✅',
                'auto_hide': True,
                'duration': 4000
            }
            
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


# ── Admin user management ──────────────────────────────────────────────────────

@login_required
@role_required('admin')
def user_list_view(request):
    users = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'accounts/user_list.html', {'page_obj': page})


@login_required
@role_required('admin')
def user_edit_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    old_role = user.get_role_display()
    old_email = user.email
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            
            # Send Telegram notification for user update
            from tickets.notifications import send_change_alert
            new_role = user.get_role_display()
            new_email = user.email
            
            details = []
            if old_role != new_role:
                details.append(f'Role changed from {old_role} to {new_role}')
            if old_email != new_email:
                details.append(f'Email changed from {old_email} to {new_email}')
            
            send_change_alert(
                user=request.user,
                action='update',
                object_type='user',
                object_info=f'User: {user.username}',
                details=', '.join(details) if details else 'Profile updated'
            )
            
            # Add iOS-style notification data to session
            request.session['ios_notification'] = {
                'type': 'success',
                'title': 'User Updated',
                'message': f'User "{user.username}" updated successfully',
                'icon': '✅',
                'auto_hide': True,
                'duration': 4000
            }
            
            messages.success(request, 'User updated.')
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'target_user': user})


@login_required
@role_required('admin')
def user_delete_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, 'You cannot delete your own account.')
        else:
            # Send Telegram notification for user deletion
            from tickets.notifications import send_change_alert
            send_change_alert(
                user=request.user,
                action='delete',
                object_type='user',
                object_info=f'User: {user.username}',
                details=f'Email: {user.email}, Role: {user.get_role_display()}'
            )
            
            user.delete()
            
            # Add iOS-style notification data to session
            request.session['ios_notification'] = {
                'type': 'success',
                'title': 'User Deleted',
                'message': f'User "{user.username}" deleted successfully',
                'icon': '✅',
                'auto_hide': True,
                'duration': 4000
            }
            
            messages.success(request, 'User deleted.')
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'target_user': user})
