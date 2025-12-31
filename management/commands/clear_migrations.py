import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Deletes all migration files from all apps, keeping __init__.py'

    def handle(self, *args, **options):
        base_dir = settings.BASE_DIR
        
        # Walk through all directories
        for root, dirs, files in os.walk(base_dir):
            if 'migrations' in dirs:
                migrations_dir = os.path.join(root, 'migrations')
                
                # Check if it's a valid migrations directory (has __init__.py)
                if '__init__.py' in os.listdir(migrations_dir):
                    self.stdout.write(f'Cleaning {migrations_dir}...')
                    
                    for filename in os.listdir(migrations_dir):
                        if filename != '__init__.py' and filename.endswith('.py'):
                            file_path = os.path.join(migrations_dir, filename)
                            try:
                                os.remove(file_path)
                                self.stdout.write(f'  Deleted {filename}')
                            except Exception as e:
                                self.stderr.write(f'  Failed to delete {filename}: {e}')
                        
                        # Also remove compiled python files
                        if filename.endswith('.pyc'):
                             file_path = os.path.join(migrations_dir, filename)
                             try:
                                os.remove(file_path)
                             except Exception:
                                 pass

                    # Remove __pycache__ if it exists
                    pycache_dir = os.path.join(migrations_dir, '__pycache__')
                    if os.path.exists(pycache_dir):
                        try:
                            shutil.rmtree(pycache_dir)
                            self.stdout.write('  Removed __pycache__')
                        except Exception as e:
                            self.stderr.write(f'  Failed to remove __pycache__: {e}')

        self.stdout.write(self.style.SUCCESS('Successfully cleared all migration files.'))
