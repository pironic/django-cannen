from models import SongFile
from models import UserSong
from models import GlobalSong
from models import GlobalSongRate
from models import SongFileScore
from models import UserProfile
from django.contrib import admin

class SongFileAdmin(admin.ModelAdmin):
    fields = ['owner', 'file']
    list_filter = ['owner']

admin.site.register(SongFile, SongFileAdmin)
admin.site.register(UserSong)
admin.site.register(GlobalSong)

class GlobalSongRateAdmin(admin.ModelAdmin):
    list_filter = ['subject','rater']

admin.site.register(GlobalSongRate, GlobalSongRateAdmin)

class UserAdmin(admin.ModelAdmin):
    fields = ['user', 'coins']

admin.site.register(SongFileScore)
admin.site.register(UserProfile)
