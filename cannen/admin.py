from models import SongFile
from models import UserSong
from models import GlobalSong
from models import SongVote
from models import SongFileScore
from models import UserProfile
from django.contrib import admin

class SongFileAdmin(admin.ModelAdmin):
    fields = ['owner', 'file']
    list_filter = ['owner']

admin.site.register(SongFile, SongFileAdmin)
admin.site.register(UserSong)
admin.site.register(GlobalSong)

class SongVoteAdmin(admin.ModelAdmin):
    list_filter = ['subject','voter']

admin.site.register(SongVote, SongVoteAdmin)

class UserAdmin(admin.ModelAdmin):
    fields = ['user', 'coins']

admin.site.register(SongFileScore)
admin.site.register(UserProfile)
