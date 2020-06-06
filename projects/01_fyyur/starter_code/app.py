# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String)
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    show = db.relationship("Show", backref="Venue", lazy='dynamic')


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    # genres = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String)
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    show = db.relationship("Show", backref="Artist", lazy='dynamic')


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime())
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
"""
Reference: https://knowledge.udacity.com/questions/66342
"""


@app.route('/venues')
def venues():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    city_and_state = ''
    data = []

    venue_query = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()
    for venue in venue_query:

        upcoming_shows = venue.show.filter(Show.start_time > current_time).all()

        if city_and_state == venue.city + venue.state:
            data[len(data) - 1]["venues"].append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(upcoming_shows)
            })
        else:
            city_and_state = venue.city + venue.state
            data.append({
                "city": venue.city,
                "state": venue.state,
                "venues": [{
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": len(upcoming_shows)
                }]
            })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    data = []
    count = 0
    search_term = request.form.get('search_term', '')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    venue_query = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()
    for venue in venue_query:
        upcoming_shows = venue.show.filter(Show.start_time > current_time).all()

        if (search_term.lower() in venue.name.lower()) or (search_term.lower() in venue.city.lower()):
            count += 1
            data.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(upcoming_shows)
            })

    response = {
        "count": count,
        "data": data
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue_list = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    venue_query = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()

    for venue in venue_query:
        upcoming_shows = venue.show.filter(Show.start_time > current_time).all()
        past_shows = venue.show.filter(Show.start_time <= current_time).all()

        upcoming_shows_list = []
        past_shows_list = []

        if len(upcoming_shows) > 0:
            for show in upcoming_shows:
                upcoming_shows_list.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter(Artist.id == show.artist_id).first().name,
                    "artist_image_link": Artist.query.filter(Artist.id == show.artist_id).first().image_link,
                    "start_time": str(show.start_time)
                })

        if len(past_shows) > 0:
            for show in past_shows:
                past_shows_list.append({
                    "artist_id": show.artist_id,
                    "artist_name": Artist.query.filter(Artist.id == show.artist_id).first().name,
                    "artist_image_link": Artist.query.filter(Artist.id == show.artist_id).first().image_link,
                    "start_time": str(show.start_time)
                })

        venue_list.append({
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows_list,
            "upcoming_shows": upcoming_shows_list,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows)
        })

    # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
    data = list(filter(lambda d: d['id'] == venue_id, venue_list))[0]
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


"""
https://knowledge.udacity.com/questions/130507
"""


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    new_venue = Venue()

    new_venue.name = request.form['name']
    new_venue.city = request.form['city']
    new_venue.state = request.form['state']
    new_venue.address = request.form['address']
    new_venue.phone = request.form['phone']
    new_venue.genres = request.form.getlist('genres')
    new_venue.facebook_link = request.form['facebook_link']

    try:
        db.session.add(new_venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        flash('An error occurred. Venue ' + new_venue.name + ' could not be listed.')
        db.session.rollback()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    try:
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue.name + ' was successfully removed.')
    except:
        flash('An error occurred. Venue ' + venue.name + ' could not be removed.')
        db.session.rollback()

    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    artist_query = Artist.query.all()
    for artist in artist_query:
        data.append({
            "id": artist.id,
            "name": artist.name
        })

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    data = []
    count = 0
    search_term = request.form.get('search_term', '')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    artist_query = Artist.query.all()
    for artist in artist_query:
        upcoming_shows = artist.show.filter(Show.start_time > current_time).all()

        if (search_term.lower() in artist.name.lower()) or (search_term.lower() in artist.city.lower()):
            count += 1
            data.append({
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": len(upcoming_shows)
            })

    response = {
        "count": count,
        "data": data
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist_list = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    artist_query = Artist.query.all()

    for artist in artist_query:
        upcoming_shows = artist.show.filter(Show.start_time > current_time).all()
        past_shows = artist.show.filter(Show.start_time <= current_time).all()

        upcoming_shows_list = []
        past_shows_list = []

        if len(upcoming_shows) > 0:
            for show in upcoming_shows:
                upcoming_shows_list.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter(Venue.id == show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter(Venue.id == show.venue_id).first().image_link,
                    "start_time": str(show.start_time)
                })

        if len(past_shows) > 0:
            for show in past_shows:
                past_shows_list.append({
                    "venue_id": show.venue_id,
                    "venue_name": Venue.query.filter(Venue.id == show.venue_id).first().name,
                    "venue_image_link": Venue.query.filter(Venue.id == show.venue_id).first().image_link,
                    "start_time": str(show.start_time)
                })

        artist_list.append({
            "id": artist.id,
            "name": artist.name,
            "genres": ''.join(list(filter(lambda x: x != '{' and x != '}', artist.genres))).split(','),
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": past_shows_list,
            "upcoming_shows": upcoming_shows_list,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows)
        })

    data = list(filter(lambda d: d['id'] == artist_id, artist_list))[0]
    # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    artist = Artist.query.get(artist_id)
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link
    }

    return render_template('forms/edit_artist.html', form=form, artist=data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']

    try:
        db.session.add(artist)
        db.session.commit()

        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except:
        flash('An error occurred. Artist ' + artist_id + ' could not be updated.')

        db.session.rollback()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue = Venue.query.get(venue_id)
    data = {
        "id": 1,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link
    }

    return render_template('forms/edit_venue.html', form=form, venue=data)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']

    try:
        db.session.add(venue)
        db.session.commit()

        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
        flash('An error occurred. Venue ' + venue_id + ' could not be updated.')

        db.session.rollback()

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    new_artist = Artist()

    new_artist.name = request.form['name']
    new_artist.city = request.form['city']
    new_artist.state = request.form['state']
    new_artist.phone = request.form['phone']
    new_artist.genres = request.form.getlist('genres')
    new_artist.facebook_link = request.form['facebook_link']

    try:
        db.session.add(new_artist)
        db.session.commit()

        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        flash('An error occurred. Artist ' + new_artist.name + ' could not be listed.')

        db.session.rollback()

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows

    data = []
    show_query = Show.query.all()

    for show in show_query:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": Venue.query.filter(Venue.id == show.venue_id).first().name,
            "artist_id": show.artist_id,
            "artist_name": Artist.query.filter(Artist.id == show.artist_id).first().name,
            "artist_image_link": Artist.query.filter(Artist.id == show.artist_id).first().image_link,
            "start_time": str(show.start_time)
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form

    new_show = Show()
    new_show.start_time = request.form['start_time']

    artist_id = request.form['artist_id']
    artist = Artist.query.filter(Artist.id == artist_id).first()

    venue_id = request.form['venue_id']
    venue = Venue.query.filter(Venue.id == venue_id).first()

    new_show.Artist = artist
    new_show.Venue = venue

    try:
        db.session.add(new_show)
        db.session.commit()
        flash('Show was successfully listed!')

    except:
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
