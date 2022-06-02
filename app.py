#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from distutils.log import error
from email.policy import default
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import ForeignKey
from forms import *
from flask_migrate import Migrate
import psycopg2
import timestring
from models import db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
# app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI' ] = 'postgresql://postgres:1234@localhost:5432/fyyurdb'
#----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues_data = Venue.query.distinct(Venue.city, Venue.state).all()
  areas=[]

  for entry in venues_data:
    venues_area = Venue.query.filter_by(city=entry.city).all()
    venue = []

    for data in venues_area:
      venue_details = {
        'id': data.id,
        'name': data.name
      }
      venue.append(venue_details)

    area = {
      'city': entry.city,
      'state': entry.state,
      'venues': venue
    }
   
    areas.append(area)
  
  return render_template('pages/venues.html', areas=areas);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  all_venues = Venue.query.all()
  data =[]
  search_term = request.form.get('search_term').lower()
  for venue in all_venues:
    venue_name = venue.name.lower()
    if search_term in venue_name:
      data.append({
        'id': venue.id,
        'name': venue.name,
      })
    response = {'count': len(data),'data': data}

  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  venue_shows = Show.query.filter_by(venue_id=venue_id).all()
  
  genres = []
  past_shows = []
  upcoming_shows = []
  present_day = datetime.now()

  for genre in venue.genres:
    genres.append(genre)
  
  for show in venue_shows:
    artist = Artist.query.get(show.artist_id)
    show_time = timestring.Date(show.date)

    if show_time > present_day:
      upcoming_shows.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link,
        'start_time': show.date
      })
    else:
      past_shows.append({
        'artist_id': artist.id,
        'artist_name': artist.name,
        'artist_image_link': artist.image_link, 
        'start_time': show.date
      })  


  venue_data = {
    'id': venue.id,
    'name': venue.name,
    'address': venue.address,
    'city': venue.city,
    'genres': genres,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.need_talent,
    'seeking_description': venue.talent_description,
    'image_link': venue.image_link,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=venue_data)



#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    form = VenueForm()
    
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    genres = form.genres.data
    facebook = form.facebook_link.data
    image = form.image_link.data
    website = form.website_link.data
    talent = form.seeking_talent.data
    desc = form.seeking_description.data
    # TODO: modify data to be the data object returned from db insertion
    new_venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook, image_link=image, website_link=website, need_talent=talent, talent_description=desc)

    db.session.add(new_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


@app.route('/venues/<venue_id>/delete', methods=['GET','POST','DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)

    if Show.query.get(venue_id):
      show = Show.query.filter_by(venue_id).all()
      db.session.delete(show)
      db.session.delete(venue)
      db.session.commit()
    else:
      db.session.delete(venue)
      db.session.commit()
    flash('Venue has been deleted successfully!')
  except:
    db.session.rollback()
    flash('Something went wrong, venue could not be deleted.')
  finally:
    db.session.close()


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')
  




#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  all_artists = Artist.query.distinct(Artist.id, Artist.name).order_by(Artist.id).all()

  return render_template('pages/artists.html', artists=all_artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  all_artists = Artist.query.all()
  data =[]
  search_term = request.form.get('search_term').lower()
  for artist in all_artists:
    artist_name = artist.name.lower()
    if search_term in artist_name:
      data.append({
        'id': artist.id,
        'name': artist.name,
      })

    response = {'count': len(data),'data': data}

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)
  artist_shows = Show.query.filter_by(artist_id=artist_id).all()
  
  genres = []
  past_shows = []
  upcoming_shows = []
  present_day = datetime.now()

  for genre in artist.genres:
    genres.append(genre)

  for show in artist_shows:
    venue = Venue.query.get(show.venue_id)
    show_time = timestring.Date(show.date)

    if show_time > present_day:
      upcoming_shows.append({
        'venue_id': venue.id,
        'venue_name': venue.name,
        'venue_image_link': venue.image_link,
        'start_time': show.date
      })
    else:
      past_shows.append({
        'venue_id': venue.id,
        'venue_name': venue.name,
        'venue_image_link': venue.image_link, 
        'start_time': show.date
      })  

  artist_data = {
    'id': artist.id,
    'name': artist.name,
    'city': artist.city,
    'genres': genres,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website_link,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.need_venue,
    'seeking_description': artist.venue_description,
    'image_link': artist.image_link,
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  current_artist = {
    'id': artist.id,
    'name': artist.name,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website_link,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.need_venue,
    'seeking_description': artist.venue_description,
    'image_link': artist.image_link
  }
 
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=current_artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm()
  try:
    artist = Artist.query.get(artist_id)  
  
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.genres = form.genres.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data
    artist.website_link = form.website_link.data
    artist.need_venue = form.seeking_venue.data
    artist.venue_description = form.seeking_description.data
    
    db.session.commit()

    flash("Artist " + request.form['name'] + ' was updated successfully!' )
  except:
    db.session.rollback()
    flash("An error occured. Artist could not be updated.")
  finally:
    db.session.close()  


  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  current_venue = {
    'id': venue.id,
    'name': venue.name,
    'city': venue.city,
    'address': venue.address,
    'state': venue.state,
    'phone': venue.phone,
    'website': venue.website_link,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.need_talent,
    'seeking_description': venue.talent_description,
    'image_link': venue.image_link
  }

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=current_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()
  try:
    venue = Venue.query.get(venue_id)  
  
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.address = form.address.data
    venue.genres = form.genres.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.website_link = form.website_link.data
    venue.need_venue = form.seeking_talent.data
    venue.venue_description = form.seeking_description.data
    
    db.session.commit()

    flash("Venue " + request.form['name'] + ' was updated successfully!' )
  except:
    db.session.rollback()
    flash("An error occured. Venue could not be updated.")
  finally:
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
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    form = ArtistForm()
   
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    genres = form.genres.data
    facebook = form.facebook_link.data
    image = form.image_link.data
    website = form.website_link.data
    venue = form.seeking_venue.data
    desc = form.seeking_description.data
    
    new_artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook, image_link=image, website_link=website, need_venue=venue, venue_description=desc)
  
    db.session.add(new_artist)
    db.session.commit()
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
    flash('Artist  was successfully listed!')
  
  except:
  # TODO: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Artist could not be listed.')
  
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/artists/<artist_id>/delete', methods=['GET', 'POST'])
def delete_artists(artist_id):
  try:
    artist = Artist.query.get(artist_id)

    if Show.query.get(artist.id):
      show = Show.query.filter_by(artist.id).all()
      db.session.delete(show)
    else:
      db.session.delete(artist)
      db.session.commit()
    flash('Artist has been deleted successfully!')
  except:
    db.session.rollback()
    flash('Something went wrong, artist could not be deleted.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.all()
  shows_data = []
  for show in shows:
    shows_data.append({
      'venue_id': Venue.query.get(show.venue_id).id,
      'venue_name': Venue.query.get(show.venue_id).name,
      'artist_id': Artist.query.get(show.artist_id).id,
      'artist_name': Artist.query.get(show.artist_id).name,
      'artist_image_link': Artist.query.get(show.artist_id).image_link,
      'start_time': show.date
    })

  return render_template('pages/shows.html', shows=shows_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    form = ShowForm()

    artist_id = int(form.artist_id.data)
    venue_id = int(form.venue_id.data)
    start_time = str( form.start_time.data)
    date = format_datetime(start_time, 'full')

    new_show = Show(artist_id=artist_id, venue_id=venue_id, date=date)

    db.session.add(new_show)
    db.session.commit()
  # on successful db insert, flash success
    flash('Show was successfully listed!')
  
  except:

  # TODO: on unsuccessful db insert, flash an error instead.
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')

  finally:
    db.session.close()
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
