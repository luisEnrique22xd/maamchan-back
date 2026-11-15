from django.contrib import admin
from .models import Campaign, TargetByTeam, LevelConfig

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active',)

admin.site.register(TargetByTeam)
admin.site.register(LevelConfig)