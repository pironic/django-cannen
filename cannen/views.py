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

import backend
from .models import UserSong, GlobalSong, SongFile, add_song_and_file

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
        now_playing = GlobalSong.objects.filter(is_playing=True)[0]
        now_playing = CANNEN_BACKEND.get_info(now_playing)
    except IndexError:
        now_playing = None
    playlist = GlobalSong.objects.filter(is_playing=False)
    playlist = [CANNEN_BACKEND.get_info(m) for m in playlist]

    userqueue = UserSong.objects.filter(owner=request.user)
    userqueue = [CANNEN_BACKEND.get_info(m) for m in userqueue]

    #return the default values without library
    data = dict(current=now_playing, playlist=playlist, queue=userqueue, enable_library=enable_library)
    
    #if the library is enabled, then prepare the data and pass it to the template
    if enable_library:
        songfiles = SongFile.objects.filter(owner=request.user)
        userlibrary = [CANNEN_BACKEND.get_info(Song) for Song in songfiles]
        userlibrary.sort(key=lambda x: (x.artist.lower().lstrip('the ') if x.artist else x.artist, x.title))
        data = dict(current=now_playing, playlist=playlist, queue=userqueue, library=userlibrary, enable_library=enable_library)

    return render_to_response('cannen/info.html', data,
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
