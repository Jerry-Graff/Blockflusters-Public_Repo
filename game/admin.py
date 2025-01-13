from django.contrib import admin
from .models import FilmImage, GameSession
from django.utils.html import mark_safe


@admin.register(FilmImage)
class FilmImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'tier', 'frame', 'image_tag', 'hint_1', 'hint_2')
    list_filter = ('tier',)
    search_fields = ('title',)
    readonly_fields = ('image_tag',)

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "No Image"

    image_tag.short_description = 'Image Preview'


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'score', 'time_remaining', 'current_tier_shown', 'frame_mode', 'last_active')
    readonly_fields = ('session_id',)