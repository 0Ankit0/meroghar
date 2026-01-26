import os
from django.core.management.commands.runserver import Command as RunserverCommand
from django.core.management import call_command

class Command(RunserverCommand):
    def handle(self, *args, **options):
        # We want to run the build only once, when the server starts,
        # not when the reloader restarts it, unless we want to rebuild on every change.
        # However, checking for runserver reloader logic is tricky.
        # A simple check is to look at os.environ.get('RUN_MAIN') which is set by the auto-reloader.
        
        # If we are NOT in the reloader process (i.e. this is the main process starting up)
        # OR if --noreload is passed.
        # Actually, usually 'RUN_MAIN' is set to 'true' in the *child* process.
        # So if we want to run it before the server *actually* starts serving, we might want to do it in the child process?
        # But if we do it in the child process, it will run every time the code changes.
        # Use case: "build the tailwind at the start".
        # Let's do it in the outer process to avoid repeated builds on code changes if not desired,
        # OR do it in the inner process if we want to ensure it's fresh.
        # Given "at the start", maybe just once is enough?
        # But if I edit tailwind config, I probably want it to rebuild.
        # However, django-tailwind usually runs a separate process for 'start' (watch mode).
        # The user asked to "build ... at the start".
        
        # Let's run it if we are in the main process (before reloader spawns child) or if usage doesn't use reloader.
        # AND let's also run it if we are in the child process? 
        # If I run it in the main process, it happens once.
        # If I run it in the child process, it happens every reload.
        # Let's just run it unconditionally at the start of handle, but checking if we are about to run the server.
        
        # Safe approach: Run it. If it takes time, it takes time.
        # But `tailwind build` is a one-off command. `tailwind start` is the watcher.
        # If the user wants "build at start", they likely mean compile the CSS once so it's ready.
        
        if not os.environ.get('RUN_MAIN') or options.get('use_reloader') is False:
             self.stdout.write(self.style.SUCCESS('Building Tailwind CSS...'))
             try:
                 call_command('tailwind', 'build')
             except Exception as e:
                 self.stdout.write(self.style.WARNING(f'Failed to build Tailwind CSS: {e}'))
        
        super().handle(*args, **options)
