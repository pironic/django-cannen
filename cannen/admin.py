from models import GlobalSong
from models import GlobalSongRate
from models import SongFile
from models import SongFileScore
from models import UserSong
from models import UserProfile
from django.contrib import admin

class GlobalSongRateAdmin(admin.ModelAdmin):
    list_filter = ['subject','rater']
    list_display = ['rater','rate','subject']
admin.site.register(GlobalSongRate, GlobalSongRateAdmin)

class GlobalSongAdmin(admin.ModelAdmin):
    list_filter = ['submitter']
    list_display = ['is_playing','submitter','url']
    list_display_links = ['url']
admin.site.register(GlobalSong, GlobalSongAdmin)

class SongFileScoreAdmin(admin.ModelAdmin):
    ordering = ['url']
    fields = ['url','score']
    list_display = ['score','url']
    list_display_links = ['url']
admin.site.register(SongFileScore, SongFileScoreAdmin)

class SongFileAdmin(admin.ModelAdmin):
    ordering = ['file']
    fields = ['owner', 'file']
    list_display = ['owner','file']
    list_filter = ['owner']
    list_display_links = ['file']
admin.site.register(SongFile, SongFileAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    ordering = ['user']
    list_display = ['user','coinsEarned','coinsSpent']
admin.site.register(UserProfile, UserProfileAdmin)

class UserSongAdmin(admin.ModelAdmin):
    ordering = ['owner','orderable_position']
    list_display = ['orderable_position','owner','url']
    list_display_links = ['url']
admin.site.register(UserSong, UserSongAdmin)