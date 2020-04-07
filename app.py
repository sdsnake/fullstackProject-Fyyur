#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from extensions import csrf
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
csrf.init_app(app)
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    venue_list = Venue.query.distinct('state', 'city').all()
    for venue in venue_list:
        venue_data = {
            "city": venue.city,
            "state": venue.state,
            "venues": Venue.query.filter_by(city=venue.city).all()
        }
        data.append(venue_data)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    searched_term = request.form.get('search_term', '')

    result_venues = Venue.query.filter(
        Venue.name.ilike("%" + searched_term + "%")).all()
    count_venues = len(result_venues)

    response = {
        "count": count_venues,
        "data": result_venues
    }
    return render_template('pages/search_venues.html', results=response, search_term=searched_term.lower())


@app.route('/venues/<int:venue_id>', methods=['GET'])
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.filter_by(id=venue_id).first()

    old_shows = Artist.query.with_entities(Artist.id, Artist.name, Artist.image_link, Show.start_time).\
        join(Show, Artist.id == Show.artist_id).\
        join(Venue, Venue.id == Show.venue_id).\
        filter(Venue.id == venue_id).\
        filter(Show.start_time < datetime.utcnow()).\
        all()

    old_shows_todisplay = []
    for old_show in old_shows:
        previous_show = {
            "artist_id": old_show.id,
            "artist_name": old_show.name,
            "artist_image_link": old_show.image_link,
            "start_time": old_show.start_time.strftime("%d %b %Y %H:%M:%S.%f")
        }
        old_shows_todisplay.append(previous_show)

    future_shows = Artist.query.with_entities(Artist.id, Artist.name, Artist.image_link, Show.start_time).\
        join(Show, Artist.id == Show.artist_id).\
        join(Venue, Venue.id == Show.venue_id).\
        filter(Venue.id == venue_id).\
        filter(Show.start_time >= datetime.utcnow()).\
        all()

    futur_shows_todisplay = []
    for futur_show in future_shows:
        previous_show = {
            "artist_id": futur_show.id,
            "artist_name": futur_show.name,
            "artist_image_link": futur_show.image_link,
            "start_time": futur_show.start_time.strftime("%d %b %Y %H:%M:%S.%f")
        }
        futur_shows_todisplay.append(previous_show)

    # count upcoming shows
    upcoming_shows_count = Show.query.filter(
        Show.venue_id == venue_id, Show.start_time > datetime.utcnow()).count()

    data = {
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
        "past_shows": old_shows_todisplay,
        "upcoming_shows": futur_shows_todisplay,
        "past_shows_count": len(old_shows_todisplay),
        "upcoming_shows_count": upcoming_shows_count
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Creating venue by get requests data and validate before committing
    error = False
    form = VenueForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            name = form.name.data
            city = form.city.data
            state = form.state.data
            address = form.address.data
            phone = form.phone.data
            website = form.website.data
            image_link = form.image_link.data
            genres = form.genres.data
            facebook_link = request.form.get('facebook_link')
            venue = Venue(name=name,
                          city=city,
                          state=state,
                          address=address,
                          phone=phone,
                          website=website,
                          image_link=image_link,
                          genres=genres,
                          facebook_link=facebook_link
                          )
            db.session.add(venue)
            db.session.commit()
            # on successful db insert, flash success
            flash('Venue ' + request.form['name'] +
                  ' was successfully listed!')
        except:
            flash('An error occurred. Venue ' +
                  data.name + ' could not be listed.')
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
    else:
        flash(form.errors)  # Flashes reason, why form is unsuccessful
    return render_template('pages/home.html')

    @app.route('/venues/<venue_id>', methods=['DELETE'])
    def delete_venue(venue_id):
        # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
        try:
            Venue = Venue.query.get(venue_id)
            db.session.delete(Venue)
            db.session.commit()
            flash('Venue ' + venue_id + ' was deleted')
        except:
            db.session.rollback()
        finally:
            db.session.close()
    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    searched_term = request.form.get('search_term', '')

    result_artists = Artist.query.filter(
        Artist.name.ilike("%" + searched_term + "%")).all()
    count_artists = len(result_artists)

    response = {
        "count": count_artists,
        "data": result_artists
    }
    return render_template('pages/search_artists.html', results=response, search_term=searched_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # get the past and futur show to display. get the count show to
    artist = Artist.query.filter_by(id=artist_id).first()

    old_shows = Venue.query.with_entities(Venue.id, Venue.name, Venue.image_link, Show.start_time).\
        join(Show, Venue.id == Show.venue_id).\
        join(Artist, Artist.id == Show.artist_id).\
        filter(Artist.id == artist_id).\
        filter(Show.start_time < datetime.utcnow()).all()

    old_shows_todisplay = []

    for old_show in old_shows:
        old_show_todisplay = {
            "venue_id": old_show.id,
            "venue_name": old_show.name,
            "venue_image_link": old_show.image_link,
            "start_time": old_show.start_time.strftime("%d %b %Y %H:%M:%S.%f")
        }
        old_shows_todisplay.append(old_show_todisplay)

    future_shows = Venue.query.with_entities(Venue.id, Venue.name, Venue.image_link, Show.start_time).\
        join(Show, Venue.id == Show.venue_id).\
        join(Artist, Artist.id == Show.artist_id).\
        filter(Artist.id == artist_id).\
        filter(Show.start_time >= datetime.utcnow()).all()

    futur_shows_todisplay = []

    for futur_show in future_shows:
        futur_show_todisplay = {
            "venue_id": futur_show.id,
            "venue_name": futur_show.name,
            "venue_image_link": futur_show.image_link,
            "start_time": futur_show.start_time.strftime("%d %b %Y %H:%M:%S.%f")
        }
        futur_shows_todisplay.append(futur_show_todisplay)

    count_upcoming_shows = Show.query.filter(
        Show.artist_id == artist_id, Show.start_time > datetime.utcnow()).count()

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
        "image_link": artist.image_link,
        "past_shows": old_shows_todisplay,
        "upcoming_shows": futur_shows_todisplay,
        "past_shows_count": len(old_shows_todisplay),
        "upcoming_shows_count": count_upcoming_shows

    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    error = False
    artist = Artist.query.get(artist_id)
    try:
        artist.name = request.form.get('name')
        artist.city = request.form.get('city')
        artist.state = request.form.get('state')
        artist.phone = request.form.get('phone')
        artist.website = request.form.get('website')
        artist.image_link = request.form.get('image_link')
        artist.genres = request.form.get('genres')
        artist.facebook_link = request.form.get('facebook_link')
        db.session.commit()
    except:
        flash('An error occurred. Artist ' +
              artist.name + ' could not be listed.')
        error = True
        db.session.rollback()
        print(sys.exc_info())
    # on successful db insert, flash success
    finally:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully edited!')
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # venue record with ID <venue_id> using the new attributes
    error = False
    venue = Venue.query.get(venue_id)
    try:
        venue.name = request.form.get('name')
        venue.city = request.form.get('city')
        venue.state = request.form.get('state')
        venue.address = request.form.get('address')
        venue.phone = request.form.get('phone')
        venue.website = request.form.get('website')
        venue.image_link = request.form.get('image_link')
        venue.genres = request.form.get('genres')
        venue.facebook_link = request.form.get('facebook_link')
        db.session.commit()
    except:
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
        error = True
        db.session.rollback()
        print(sys.exc_info())
    # on successful db insert, flash success
    finally:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully edited!')
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # create a new artist and validate data before commiting
    error = False
    form = ArtistForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            name = form.name.data
            city = form.city.data
            state = form.state.data
            phone = form.phone.data
            website = form.website.data
            image_link = form.name.data
            genres = form.genres.data
            facebook_link = form.facebook_link.data
            artist = Artist(name=name,
                            city=city,
                            state=state,
                            phone=phone,
                            website=website,
                            image_link=image_link,
                            genres=genres,
                            facebook_link=facebook_link
                            )
            db.session.add(artist)
            db.session.commit()
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')
        except:
            flash('An error occurred. Artist ' +
                  request.form['name'] + ' could not be listed.')
            error = True
            db.session.rollback()
            print(sys.exc_info())
        # on successful db insert, flash success
        finally:
            # on successful db insert, flash success
            db.session.close()
    else:
        flash(form.errors)  # Flashes reason, why form is unsuccessful
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    shows = Show.query.all()
    data = []
    for show in shows:
        dataTmp = {
            "venue_id": Venue.query.filter_by(id=show.venue_id).first().id,
            "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
            "artist_id": Artist.query.filter_by(id=show.artist_id).first().id,
            "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
            "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        }
        data.append(dataTmp)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    error = False
    form = ShowForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            artist_id = form.artist_id.data
            venue_id = form.venue_id.data
            start_time = form.start_time.data
            show = Show(artist_id=artist_id,
                        venue_id=venue_id,
                        start_time=start_time,
                        )
            db.session.add(show)
            db.session.commit()
            # on successful db insert, flash success
            flash('Show was successfully listed!')
        except:
            flash('An error occurred. Show could not be listed.')
            error = True
            db.session.rollback()
            print(sys.exc_info())
        # on successful db insert, flash success
        finally:
            db.session.close()
    else:
        flash(form.errors)  # Flashes reason, why form is unsuccessful
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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
