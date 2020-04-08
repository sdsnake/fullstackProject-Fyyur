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

Show = db.Table('Show', db.Model.metadata,
                db.Column('Venue_id', db.Integer, db.ForeignKey('Venue.id')),
                db.Column('Artist_id', db.Integer, db.ForeignKey('Artist.id')),
                db.Column('start_time', db.DateTime)
                )


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
    venues = db.relationship('Artist', secondary=Show,
                             backref=db.backref('shows', lazy='joined'))


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

    old_shows = db.session.query(
        Artist.id.label("artist_id"),
        Artist.name.label("artist_name"),
        Artist.image_link.label("artist_image_link"),
        Show).\
        filter(Show.c.Venue_id == venue_id).\
        filter(Show.c.Artist_id == Artist.id).\
        filter(Show.c.start_time <= datetime.now()).\
        all()
    old_shows_todisplay = []
    for old_show in old_shows:
        previous_show = {
            "artist_id": old_show[0],
            "artist_name": old_show[1],
            "artist_image_link": old_show[2],
            "start_time": old_show.start_time.strftime("%d %b %Y %H:%M:%S.%f")
        }
        old_shows_todisplay.append(previous_show)

    future_shows = db.session.query(
        Artist.id.label("artist_id"),
        Artist.name.label("artist_name"),
        Artist.image_link.label("artist_image_link"),
        Show).\
        filter(Show.c.Venue_id == venue_id).\
        filter(Show.c.Artist_id == Artist.id).\
        filter(Show.c.start_time > datetime.now()).\
        all()

    futur_shows_todisplay = []
    for futur_show in future_shows:
        previous_show = {
            "artist_id": futur_show[0],
            "artist_name": futur_show[1],
            "artist_image_link": futur_show[2],
            "start_time": futur_show.start_time.strftime("%d %b %Y %H:%M:%S.%f")
        }
        futur_shows_todisplay.append(previous_show)

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
        "upcoming_shows_count": len(futur_shows_todisplay)
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
            genres = ','.join(form.genres.data)
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
    # get the past and futur show to display. get the count show too
    artist = Artist.query.filter_by(id=artist_id).first()

    old_shows = db.session.query(
        Venue.id.label("venue_id"),
        Venue.name.label("venue_name"),
        Venue.image_link.label("venue_image_link"),
        Show).\
        filter(Show.c.Artist_id == artist_id).\
        filter(Show.c.Venue_id == Venue.id).\
        filter(Show.c.start_time <= datetime.now()).\
        all()

    old_shows_todisplay = []

    for old_show in old_shows:
        old_show_todisplay = {
            "venue_id": old_show[0],
            "venue_name": old_show[1],
            "venue_image_link": old_show[2],
            "start_time": old_show.start_time.strftime("%d %b %Y %H:%M:%S.%f")
        }
        old_shows_todisplay.append(old_show_todisplay)

    future_shows = db.session.query(
        Artist.id.label("artist_id"),
        Artist.name.label("artist_name"),
        Artist.image_link.label("artist_image_link"),
        Show).\
        filter(Show.c.Venue_id == Venue.id).\
        filter(Show.c.Artist_id == Artist.id).\
        filter(Show.c.start_time > datetime.now()).\
        all()

    futur_shows_todisplay = []

    for futur_show in future_shows:
        futur_show_todisplay = {
            "venue_id": futur_show[0],
            "venue_name": futur_show[1],
            "venue_image_link": futur_show[2],
            "start_time": futur_show.start_time.strftime("%d %b %Y %H:%M:%S.%f")
        }
        futur_shows_todisplay.append(futur_show_todisplay)

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
        "upcoming_shows_count": len(futur_shows_todisplay)

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
    # get past, futur and count show to display on client
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
            genres = ','.join(form.genres.data)
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
    shows = db.session.query(Show).all()
    data = []
    for show in shows:
        dataTmp = {
            "venue_id": Venue.query.filter_by(id=Show.c.Venue_id).first().id,
            "venue_name": Venue.query.filter_by(id=Show.c.Venue_id).first().name,
            "artist_id": Artist.query.filter_by(id=Show.c.Artist_id).first().id,
            "artist_name": Artist.query.filter_by(id=Show.c.Artist_id).first().name,
            "artist_image_link": Artist.query.filter_by(id=Show.c.Artist_id).first().image_link,
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
    if request.method == 'POST':
        try:
            show = Show.insert().values(
                Venue_id=request.form.get('venue_id'),
                Artist_id=request.form.get('artist_id'),
                start_time=request.form.get('start_time')
            )
            db.session.execute(show)
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
