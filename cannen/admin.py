from models import SongFile
from models import UserSong
from models import GlobalSong
from models import VoteMessage
from models import Vote
from django.contrib import admin

class SongFileAdmin(admin.ModelAdmin):
    fields = ['owner', 'file']
    list_filter = ['owner']

admin.site.register(SongFile, SongFileAdmin)
admin.site.register(UserSong)
admin.site.register(GlobalSong)
class VoteMessageAdmin(admin.ModelAdmin):
    fields = ['action', 'owner', 'coinCostOwner', 'coinCostAgree', 'coinCostDisagree', 'globalSong']
    list_filter = ['action']
admin.site.register(VoteMessage, VoteMessageAdmin)
class VoteAdmin(admin.ModelAdmin):
    fields = ['vote_message', 'voter', 'vote']
    list_filter = ['vote_message']
admin.site.register(Vote, VoteAdmin)