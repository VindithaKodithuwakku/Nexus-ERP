from django.contrib import admin
from .models import Worker, Project, ProjectItem

# Registering our new models so they appear in the Admin Panel

admin.site.register(Worker)
admin.site.register(Project)
admin.site.register(ProjectItem)