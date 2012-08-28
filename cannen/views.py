# This file is part of Cannen, a collaborative music player.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ValidationError
from django.template import RequestContext
from django.conf import settings
from django.db.models import F # https://docs.djangoproject.com/en/dev/ref/models/instances/?from=olddocs#how-django-knows-to-update-vs-insert
from django.core.cache import cache

import requests
from django.core import serializers

import backend
from .models import UserSong, GlobalSong, SongFile, SongFileScore, UserProfile, GlobalSongRate, add_song_and_file

@login_required
def index(request):
    title = getattr(settings, "CANNEN_TITLE", None)
    listen_urls = getattr(settings, "CANNEN_LISTEN_URLS", [])
    
    data = dict(title=title, listen_urls=listen_urls)
    return render_to_response('cannen/index.html', data,
                              context_instance=RequestContext(request))

@login_required
def info(request):
    CANNEN_BACKEND = backend.get()
    enable_library = getattr(settings, 'CANNEN_ENABLE_LIBRARY', False)
    try:
        globalSong = GlobalSong.objects.filter(is_playing=True)[0]
        now_playing = globalSong
        now_playing = CANNEN_BACKEND.get_info(now_playing)
    except IndexError:
        now_playing = None
    playlist = GlobalSong.objects.filter(is_playing=False)
    playlist = [CANNEN_BACKEND.get_info(m) for m in playlist]

    userqueue = UserSong.objects.filter(owner=request.user)
    userqueue = [CANNEN_BACKEND.get_info(m) for m in userqueue]
    
    #if we're playing, we need to populate the rating objects for the info page based on current song.
    if(now_playing != None):
        #populate the self rate info, in order to show the proper rating icons.
        try:
            rateSelf = GlobalSongRate.objects.filter(subject=globalSong,rater=request.user)[0]
        except IndexError:
            rateSelf = 0

        #try to load the history for the currently playing song...
        try:
            songScore = SongFileScore.objects.filter(url=globalSong.url)[0]
        except IndexError:
            #the song doesn't have a history, lets make a new one.
            songScore = SongFileScore(url=globalSong.url)
            
        #can't rate your own stuff, check that!
        if(globalSong.submitter == request.user):
            rateSelf = 'X'
        
    else:
        rateSelf = 'X'
        songScore = 0
        
        
    #return the default values without library
    data = dict(current=now_playing, playlist=playlist, queue=userqueue, rateSelf=rateSelf, songScore=songScore, enable_library=enable_library)
    
    #if the library is enabled, then prepare the data and pass it to the template
    if enable_library:
        songfiles = SongFile.objects.filter(owner=request.user)
        userlibrary = [CANNEN_BACKEND.get_info(Song) for Song in songfiles]
        userlibrary.sort(key=lambda x: (x.artist.lower().lstrip('the ') if x.artist else x.artist, x.title))
        data = dict(current=now_playing, playlist=playlist, queue=userqueue, rateSelf=rateSelf, songScore=songScore, library=userlibrary, enable_library=enable_library)

    return render_to_response('cannen/info.html', data,
                              context_instance=RequestContext(request))

@login_required
def navbarinfo(request):
    listeners = cache.get('rawr')
    statusUrl = getattr(settings, 'CANNEN_STATUS_URL', None)
    statusUser = getattr(settings, 'CANNEN_STATUS_USER', None)
    statusPass = getattr(settings, 'CANNEN_STATUS_PASS', None)
    statusMount = getattr(settings, 'CANNEN_STATUS_MOUNT', None)
    
    if not listeners and statusUrl:
        r = requests.get('http://' + statusUser + ':' + statusPass + '@' + statusUrl)
        #root = lxml.html.fromstring(r.content)
        # work in progress.

        cache.set('rawr',2,300)
        listeners = cache.get('rawr')
        
    if (listeners == 1):
        strCurrentListeners = "1 Current Listener"
    else:
        strCurrentListeners = "%s Current Listeners" % listeners
    
    # fetch the user coins or 'leaves'
    try:
        userProfile = UserProfile.objects.filter(user=request.user)[0]
        leaves = userProfile.coinsEarned - userProfile.coinsSpent
    except IndexError:
        leaves = 0
    
    if (leaves == 1):
        strLeaves = "1 Leaf"
    else:
        strLeaves = "%s Leaves" % leaves
    
    data = dict(currentListeners=strCurrentListeners, leaves=strLeaves)
    return render_to_response('cannen/navbarinfo.html', data,
                              context_instance=RequestContext(request))

@login_required
def library(request):
    title = getattr(settings, "CANNEN_TITLE", None)
    listen_urls = getattr(settings, "CANNEN_LISTEN_URLS", [])
    enable_library = getattr(settings, 'CANNEN_ENABLE_LIBRARY', False)
	
    CANNEN_BACKEND = backend.get()
    Songs = SongFile.objects.all()
	
    userqueue = UserSong.objects.filter(owner=request.user)
    userqueue = [CANNEN_BACKEND.get_info(m) for m in userqueue]
    
    #return data without library info in it... as default
    data = dict(title=title, listen_urls=listen_urls, queue=userqueue, enable_library=enable_library)

    #if the library is enabled, prepare and pass the data
    if enable_library:
        library = [CANNEN_BACKEND.get_info(Song) for Song in Songs]
        library.sort(key=lambda x: (x.artist.lower().lstrip('the ') if x.artist else x.artist, x.title))
        data = dict(title=title, listen_urls=listen_urls, queue=userqueue, library=library, enable_library=enable_library)
	
    return render_to_response('cannen/library.html', data,
                              context_instance=RequestContext(request))
							  							  
@login_required
def delete(request, songid):
    song = get_object_or_404(UserSong, pk=songid)
    if song.owner.id != request.user.id:
        raise PermissionDenied()
    song.delete()
    return HttpResponseRedirect(reverse('cannen.views.index'))

@login_required
def move(request, songid, dest):
    dest = int(dest)
    song = get_object_or_404(UserSong, pk=songid)
    if song.owner.id != request.user.id:
        raise PermissionDenied()
    song.move_relative(dest)
    return HttpResponseRedirect(reverse('cannen.views.index'))

@login_required
def add_url(request):
    url = request.POST['url']
    if url == '':
        raise ValidationError("url must not be empty")
    UserSong(owner=request.user, url=url).save()
    return HttpResponseRedirect(reverse('cannen.views.index'))

@login_required
def add_file(request):
    if request.POST.get and 'file' in request.POST and request.POST['file'] == '':
        return HttpResponseRedirect(reverse('cannen.views.index'))
    add_song_and_file(request.user, request.FILES['file'])
    return HttpResponseRedirect(reverse('cannen.views.index'))

@login_required
def play(request, url):
    if url == '':
        raise ValidationError("invalid track")
    UserSong(owner=request.user, url=url).save()
    return HttpResponseRedirect(reverse('cannen.views.index'))
    
@login_required
def rate(request, action, songid):
    #data validation, even though this would liekly never ever be called.
    if action == '':
        action = request.GET['action']
    if songid == '':
        songid = request.GET['songid']
        
    removeRate = False #an internal variable to determine if we're adding or removing a rate
        
    #gonna need to have this to insert into new and existing records
    globalRate = GlobalSongRate.objects.filter(subject=songid, rater=request.user)
    globalSong = GlobalSong.objects.get(id=songid)
    
    try: #get the dj profile
        djProfile = UserProfile.objects.filter(user=globalSong.submitter)[0]
    except:
        djProfile = UserProfile(user=globalSong.submitter)
    
    if globalSong.submitter == request.user:
        raise ValidationError("Sorry, %s, You cannot rate on the tracks you queued." % request.user)
    
    #try to load the history for the currently playing song...
    try:
        songScore = SongFileScore.objects.filter(url=globalSong.url)[0]
    except:
        #the song doesn't have a history, lets make a new one.
        songScore = SongFileScore(url=globalSong.url)
    # raise ValidationError("debug value = %s" % songScore.score)

    if len(globalRate) > 0: #have we previously rated this globalSong?
        nowPlayingRate = globalRate[0]
        
        # rating fiture for songs (votes on left, results on right)
        # V1 V2|R1 R2
        # U  U |+1 -1
        # U  D |+1 -2
        # D  U |-1 +2
        # D  D |-1 +1
        # rating figure for dj's (votes on left, results on right, DownRates in third)
        # V1 V2|R1 R2|D1 D2
        # U  U |+1 -1| 0  0
        # U  D |+1 -1| 0 +1
        # D  U | 0 +1|+1 -1
        # D  D | 0  0|+1 -1
     
        if nowPlayingRate.rate == 1: #previously rated up
            if action == '+': # already rated up, toggle... to support unvoting
                removeRate = True
                action = 1
                songScore.score = int(songScore.score) - 1
                djProfile.coinsEarned = int(djProfile.coinsEarned) - 1
            else:
                action = -1 #change the rate to down
                songScore.score = int(songScore.score) - 2
                djProfile.coinsEarned = int(djProfile.coinsEarned) - 1
                djProfile.downRatesReceived = int(djProfile.downRatesReceived) + 1
        else: #previously rated down
            if action == '+':
                action = 1  #change the rate to up
                songScore.score = int(songScore.score) + 2
                djProfile.coinsEarned = int(djProfile.coinsEarned) + 1
                djProfile.downRatesReceived = int(djProfile.downRatesReceived) - 1
            else:
                removeRate = True
                action = -1 # already rated up, toggle... to support unvoting
                songScore.score = int(songScore.score) + 1
                djProfile.downRatesReceived = int(djProfile.downRatesReceived) - 1
        nowPlayingRate.rate = action
    else: # they havn't rated yet, lets make a new rate
        if action == '+':
            #this is voting the globalSong (to prevent double voting per play)
            nowPlayingRate = GlobalSongRate(rater=request.user, subject=globalSong, rate=1) 
            #change the now playing SongFile's score
            songScore.score = int(songScore.score) + 1
            djProfile.coinsEarned = int(djProfile.coinsEarned) + 1
        else:
            nowPlayingRate = GlobalSongRate(rater=request.user, subject=globalSong, rate=-1)
            songScore.score = int(songScore.score) - 1
            djProfile.downRatesReceived = int(djProfile.downRatesReceived) + 1
            
    #save the stuff we've updated.
    djProfile.save()
    songScore.save()
    if not(removeRate):
        nowPlayingRate.save()
    else:
        nowPlayingRate.delete()
    return HttpResponseRedirect(reverse('cannen.views.index'))
