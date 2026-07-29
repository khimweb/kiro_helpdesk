"""Create or update the configured Django administrator at container startup."""

import os

import django


def main():
    django.setup()

    username = os.getenv("DJANGO_SUPERUSER_USERNAME")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
    email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")

    if not username or not password:
        print("Admin bootstrap skipped: administrator credentials are not configured.")
        return

    from django.contrib.auth import get_user_model

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": True,
            "is_superuser": True,
            "role": "admin",
        },
    )

    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.role = "admin"
    user.set_password(password)
    user.save()

    action = "created" if created else "updated"
    print(f"Admin bootstrap: {action} administrator '{username}'.")


if __name__ == "__main__":
    main()
