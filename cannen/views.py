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
from django.db.models import Count

import backend
import cannen.backend
from .models import UserSong, GlobalSong, SongFile, add_song_and_file, VoteMessage, Vote

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
    
    vote_messages = VoteMessage.objects.exclude(vote__voter=request.user, vote__subscribed=False)#.annotate(myVote='vote__vote')
    pollData = []
    for vote_message in vote_messages:
        try: #existing vote?
            user_vote = Vote.objects.filter(voter=request.user, vote_message=vote_message)[0]
        except IndexError: #nope, lets make a new instance to save it.
            user_vote = Vote(voter=request.user, vote_message=vote_message, vote=None)
        requiredVotes = getattr(settings, 'CANNEN_VOTES_REQUIRED', 5)
        requiredVotesYes = int(round(requiredVotes * getattr(settings, 'CANNEN_VOTES_SUCCESS_RATIO', 0.6),0))
        totalVotes = Vote.objects.filter(vote_message=vote_message).exclude(vote=None).count()
        stats = dict(required=requiredVotes,requiredYes=requiredVotesYes,total=totalVotes)
        pollData.append(dict(poll=vote_message,vote=user_vote,stats=stats))
    

    #if the library is enabled, then prepare the data and pass it to the template
    if enable_library:
        songfiles = SongFile.objects.filter(owner=request.user)
        userlibrary = [CANNEN_BACKEND.get_info(Song) for Song in songfiles]
        userlibrary.sort(key=lambda x: (x.artist.lower().lstrip('the ') if x.artist else x.artist, x.title))
        data = dict(current=now_playing, playlist=playlist, queue=userqueue, library=userlibrary, enable_library=enable_library, polls=pollData)
    else: #return the default values without library
        data = dict(current=now_playing, playlist=playlist, queue=userqueue, enable_library=enable_library, polls=pollData)

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
    
@login_required
def poll(request, action, songid=None):
    
    if songid and action == 'skip':
        try:#try to load the globalSong that is referenced for skipping
            globalSong = GlobalSong.objects.get(id=songid)
        except IndexError: 
            raise ValidationError("Invalid song speicfied to skip.")
            
        try: #existing poll?
            vote_message = VoteMessage.objects.filter(owner=request.user, action=action, globalSong=globalSong)[0]
        except IndexError: #nope, lets make a new instance to save it.
            vote_message = VoteMessage(owner=request.user, action=action,globalSong=globalSong)
            
        if (getattr(settings, 'CANNEN_SHUFFLE_ENABLE', False) and globalSong.Submitter.id == getattr(settings, 'CANNEN_SHUFFLE_USER_ID', 0)):
            vote_message.CoinCostOwner = 0
            vote_message.CoinCostAgree = 0
            vote_message.CoinCostDisagree = 0
        else:
            vote_message.CoinCostOwner = 2
        
        vote_message.save()
        Vote(voter=request.user, vote_message=vote_message, user_vote.vote = 't').save()
    #else:
        
    return HttpResponseRedirect(reverse('cannen.views.index'))


@login_required
def vote(request, action, pollid):
    try: #get the poll from the id
        vote_message = VoteMessage.objects.get(id=pollid)
    except:
        raise ValidationError("Invalid PollID Specified.")
        
    try: #existing vote?
        user_vote = Vote.objects.filter(voter=request.user, vote_message=vote_message)[0]
    except IndexError: #nope, lets make a new instance to save it.
        user_vote = Vote(voter=request.user, vote_message=vote_message)
    
    if (action == 'n'): # provide option to opt-out or dismiss, all in one!
        user_vote.subscribed = False
    else: 
        user_vote.vote = {
            'n' : lambda: None,
            't' : lambda: True,
            'f' : lambda: False
        }[action]()
    
    user_vote.save()
        
    requiredVotes = getattr(settings, 'CANNEN_VOTES_REQUIRED', 5)
    totalVotes = Vote.objects.filter(vote_message=vote_message).exclude(vote=None).count()
    votesFor = Vote.objects.filter(vote_message=vote_message,vote=True).count()
    votesNeededYes = int(round(requiredVotes * getattr(settings, 'CANNEN_VOTES_SUCCESS_RATIO', 0.6),0))
    if votesFor >= votesNeededYes: #success, pass the poll, then remove it.
        if(vote_message.action == 'skip'): #skip method
            if not vote_message.globalSong:
                raise ValidationError("Invalid song speicfied to skip.")
            else: #its a valid song, lets skip it.
                backend = cannen.backend.get()
                backend.stop()
                #charge the people's for the poll
                
                #charge the owner, for starting it.
                poll_creator = UserProfile.objects.filter(user=vote_message.owner)[0]
                poll_creator.coinsSpent = poll_creator.coinsSpent + vote_message.coinCostOwner
                poll_creator.save()
                #charge the people who agree
                votersAgree = Vote.objects.filter(vote_message=vote_message,vote=True)
                for voter in votersAgree:
                    voter_profile = UserProfile.objects.filter(user=voter)[0]
                    voter_profile.coinsSpent = voter_profile.coinsSpent + vote_message.coinCostAgree
                    voter_profile.save()
        else:
            raise ValidationError("Poll complete but no method built for this action<br/>votesFor: "+str(votesFor)+"<br/>votesAgainst:"+str(totalVotes-votesFor)+"<br/>")
    elif totalVotes >= requiredVotes: #failure on the poll. remove it.
        #charge the owner, for starting it.
        #voter_profile = UserProfile.objects.filter(user=voter)[0]
        #voter_profile.coinsSpent = voter_profile.coinsSpent + vote_message.coinCostOwner

        #charge the people who disagree
        votersDisagree = Vote.objects.filter(vote_message=vote_message,vote=False)
        for voter in votersDisagree:
            voter_profile = UserProfile.objects.filter(user=voter)[0]
            voter_profile.coinsSpent = voter_profile.coinsSpent + vote_message.coinCostDisagree
            voter_profile.save()
        vote_message.delete()
    
    #raise ValidationError("not built yet. rawr.")
    return HttpResponseRedirect(reverse('cannen.views.index'))
