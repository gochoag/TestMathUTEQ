from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quizzes.models import UserProfile


class Command(BaseCommand):
    help = 'Crea perfiles de usuario para usuarios existentes que no los tengan'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        
        if not users_without_profile.exists():
            self.stdout.write(
                self.style.SUCCESS('Todos los usuarios ya tienen perfiles creados.')
            )
            return
        
        created_count = 0
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            created_count += 1
            self.stdout.write(f'Perfil creado para: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Se crearon {created_count} perfiles de usuario exitosamente.'
            )
        ) 