Cannen Collaborative Music Player
=================================

Cannen is a collaborative music player written to use [Django][] and
[MPD][]. It is designed to have a very simple interface: users upload
music files from their own computer, or submit song URLs, and Cannen
will play them. Cannen adds submitted songs to the main playlist in a
round-robin style from all the users that have submitted songs, to be
as fair as possible.

  [Django]: https://www.djangoproject.com/
  [MPD]: http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki

Requirements
------------
 * Python
 * Django
 * MPD
 * python-mpd (>= 0.3.0)
 
### Optional

 * Icecast (for streaming your radio station)
 * pyftpdlib (>= 0.7.0, for the FTP upload server)

Demo Project
------------

Cannen comes with a demonstration Django project in `demo/` that you
can use to quickly see Cannen in action. Inside that directory, run

~~~~
python manage.py syncdb
python manage.py runserver
~~~~

to create a test database and start up a Django test server at
`localhost:8000`. To run a demo player that "plays" each song for 10
seconds, run `python manage.py runcannen` in another terminal.

Installation
------------

Cannen requires a running instance of MPD, and setting this up is
simple but beyond the scope of this README. See the [Configuration][]
article on the [MPD wiki][MPD]. Cannen will require write access to
the MPD music directory, since it will store uploaded songs in
`$MPD_MUSIC_DIR/uploaded`. The easiest way to do this is to run MPD on
the same machine running Cannen, but you can get away with a network
share.

  [Configuration]: http://mpd.wikia.com/wiki/Configuration

If you want other people to listen to the music, you'll likely want to
stream it out through Icecast, which will involve setting up an
Icecast server. Again, this is outside the scope of this
README. Cannen doesn't care what MPD does with the music once it gets
it.

Once MPD is set up, you will need to install Cannen on your Django
site. Copy the `cannen` directory into your site directory, and add
`cannen` to your `INSTALLED_APPS` in `settings.py`. While you're
there, add the following line:

~~~~{.py}
CANNEN_BACKEND = ('cannen.backends.mpd.MPDBackend', 'localhost', 6600, '/path/to/mpd/music')
~~~~

Replace the last 3 parts with your MPD host, port, and the path to the
MPD music directory. If you have an MPD password, add it at the end
like so:

~~~~{.py}
CANNEN_BACKEND = ('cannen.backends.mpd.MPDBackend', 'localhost', 6600, '/path/to/mpd/music', 'password')
~~~~

Finally, you need to add Cannen to your URL router. You can do this by
adding the following line to your `urlpatterns` in `urls.py`:

~~~~{.py}
    url(r'^radio/', include('cannen.urls')),
~~~~

This will put Cannen at the URL `http://yourdomain.com/radio/`. Feel
free to put it wherever you want it. Finally, remember to run
`python manage.py syncdb` to install the Cannen tables, and if needed,
`python manage.py collectstatic` to install Cannen's static files.

### Running the Playlist Manager

Cannen needs a secondary process to run in the background to manage
the playlist, apart from the main Django process that serves the
website. In order to run this process, run
`python ./manage.py runcannen` inside your site directory.

### Running the FTP Upload Server

Cannen has an FTP server that you can run in the background to allow
your users to easily upload a lot of songs at once. This server
requires pyftpdlib version 0.7.0 or later, and it also requires that
your Django authentication backend supports password-based
logins. This means that the FTP server will *not* work for OAuth-based
backends, however, some OAuth backends also allow each user to have a
local password.

To run the FTP upload server, run `python ./manage.py runcannenftp`
inside your site directory.

### Extra Considerations

By default, Cannen is only available to logged-in users. This means
you need to give people a way to log in at all, so if you're setting
this up yourself you might want to create a few simple log in and
registration pages for people to use. Check out the Django
documentation for more details.

### Other Settings

#### CANNEN_GARBAGE_COLLECT

By default, Cannen will delete uploaded files as soon as they are
played. If you do not wish for this to happen, set
`CANNEN_GARBAGE_COLLECT` to `False` in your settings file.

#### CANNEN_ENABLE_LIBRARY

Cannen also has a library feature which, by default, is disabled. To
enable this feature, set `CANNEN_ENABLE_LIBRARY` to `True` in your
settings file. To get the most out of your Library experience, you'll
likely want to disable the garbage collector as well, as listed
directly above.

#### CANNEN_UPLOAD_DIR

If you want to store your uploaded songs somewhere other than
`uploaded/`, you can change this by setting `CANNEN_UPLOAD_DIR`.

#### CANNEN_LISTEN_URLS

If you are running an Icecast stream, you can set the
`CANNEN_LISTEN_URLS` setting to a list of `(name, url)` tuples to show
on the default template. For example,

 ~~~~{.py}
CANNEN_LISTEN_URLS = [
    ('MP3', '/streams/radio.mp3'),
    ('Vorbis', '/streams/radio.ogg'),
]
~~~~

#### CANNEN_TITLE

You can also set the title on the default template with
`CANNEN_TITLE`.
