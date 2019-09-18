from flask import Flask, request, render_template, redirect, url_for, flash, session, request, Markup
from flask import *
from geopy.geocoders import Nominatim
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from validate_email import validate_email
from wtforms import validators
import datetime
import random 
import os
import binascii
import re
from base64 import b64encode
from Crypto.Cipher import AES
import base64

app = Flask(__name__)
db = SQLAlchemy(app)

db_path = os.path.join(os.path.dirname(__file__), 'mydb.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SECRET_KEY'] = 'isasecret'




mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'xxxxxxx@gmail.com',
    "MAIL_PASSWORD": 'xxxxxxxxxxxx'
    
}


#initalize mail
mail = Mail(app)


class Student(db.Model):
	__tablename__ = 'students'
	name = db.Column(db.String(60))
	password  = db.Column(db.String)
	school_email = db.Column(db.String)
	school = db.Column(db.String)
	user_id = db.Column(db.Integer, primary_key = True)
	date_joined = db.Column(db.Date)
	verified = db.Column(db.Boolean)
	temp_token = db.Column(db.Integer)

class Listing(db.Model):
	__tablename__ = 'listings'
	listing_id = db.Column(db.Integer, primary_key = True)
	listing_title = db.Column(db.String)
	listing_description = db.Column(db.String)
	listing_photo_one = db.Column(db.String)
	listing_photo_two = db.Column(db.String)
	listing_photo_three = db.Column(db.String)
	listing_photo_four = db.Column(db.String)
	listing_photo_five = db.Column(db.String)
	listing_seller = db.Column(db.String)
	listing_phone = db.Column(db.Integer)
	listing_email = db.Column(db.String(64))
	listing_address = db.Column(db.String)
	listing_added = db.Column(db.Date)
	listing_price = db.Column(db.Numeric)
	listing_school = db.Column(db.String)
	listing_number = db.Column(db.String)
	listing_lat = db.Column(db.Numeric)
	listing_long = db.Column(db.Numeric)
	listing_city = db.Column(db.String)
	listing_state = db.Column(db.String)



@app.route("/dormhome")
def dormhome():

	return render_template("dormhome.html", name=session.get("name"), 
		latest_posts = Listing.query.order_by(Listing.listing_added.desc()).limit(10), now=datetime.date.today())


#register and login for the user
@app.route("/registerandlogin", methods=['GET', 'POST'])
def registerandlogin():
	registererrors = []
	if request.method == "POST":
		if request.form['button'] == "join":
			if request.form['password']!= "" and len(request.form['password']) < 6:
					registererrors.append("Your password is too short")
			if request.form['name'] == "" or request.form['password'] == "" or request.form['school_email'] == "":
					registererrors.append("At least one of the required fields is not filled out.")
			if len(Student.query.filter_by(school_email = request.form['school_email']).all()) > 0:
					registererrors.append("Your school email is already in use.")
			if registererrors:
				for error in registererrors:
					flash(error)
			else:
				user_token = binascii.hexlify(os.urandom(20)).decode() 
				new_student = Student(name = request.form['name'], password = request.form['password'], school_email = 
				request.form['school_email'], school = request.form['school'], date_joined = datetime.datetime.today(), verified = False, 
				temp_token = user_token)
				db.session.add(new_student)
				db.session.commit()
				msg = Message(subject="Your DormRoom Account",
                sender=app.config.get("MAIL_USERNAME"),
                recipients=[request.form['school_email']], # replace with your email for testing
                body="Click the link to confirm your account: http://127.0.0.1:5000/verify/" + user_token)
				mail.send(msg)
				flash("We have sent an email to your account to be verified.")
	if request.method == "POST":
		if request.form['button'] == "login":
			loginerrors = []
			if request.form['email'] == "" or request.form['loginpassword'] == "":
				loginerrors.append("At least one required field is not filled out")
			result = Student.query.filter_by(school_email = request.form['email'], password = request.form['loginpassword']).all()
			if len(result) is not 1 and request.form['email']!="" and request.form['loginpassword']!="":
				loginerrors.append("Your username and/or password is incorrect.")
			if len(result) is 1 and result[0].verified == False:
				loginerrors.append("You are not a verified user.")
			if loginerrors:
				for error in loginerrors:
					flash(error)
			else:
				session['name'] = result[0].name
				session['email'] = result[0].school_email
				session['user_id'] = result[0].user_id
				session['school'] = result[0].school
				return redirect(url_for("dormhome"))
		
	return render_template("registerandlogin.html")





#search all listings
@app.route("/search", methods=['GET'])
def search(): 
	query = request.args.get("query")
	page = int(request.args.get("page"))
	if session.get("email") == None:
		initial_post = Listing.query
	else:
		initial_post = Listing.query.filter_by(listing_school = session.get("school"))
	searched_posts = initial_post.filter(Listing.listing_title.contains(query) | Listing.listing_description.contains(query)) 

	return render_template("search.html", searched_posts = searched_posts.paginate(per_page = 1, page= page, error_out= True), query=query, page=request.args.get("page"), date=datetime.date.today())

#the user's info: change his/her school, delete account here
@app.route("/me", methods=['GET', 'POST'])
def me():
	if request.method == "POST":
		if request.form['button'] == 'delete account':
			user_to_delete = Student.query.filter_by(school_email = session.get("email")).first()
			all_posts_to_delete = Listing.query.filter_by(listing_email = session.get("email")).all()
			for post in all_posts_to_delete:
				db.session.delete(post)
			db.session.delete(user_to_delete)
			db.session.commit()
			session.clear()
			flash("your account has been deleted")
			return redirect(url_for("dormhome"))
		else:
			new_school = request.form['school']
			user_logged = Student.query.filter_by(school=session.get("school")).first()
			user_logged.school = request.form['school']
			db.session.commit()
			session['school'] = new_school
			return redirect(url_for('me'))

	return render_template("me.html", school=session.get("school"), days=(datetime.date.today() - Student.query.filter_by(school_email = session.get("email")).first().date_joined).days, num_posts =  Listing.query.filter_by(listing_email = session.get("email")).count())

#view a listing and contact the user
@app.route("/viewpost/<id>", methods=['POST', 'GET'])
def viewpost(id):
	if request.method == "POST":
		if request.form['button'] == "send":
			msg = Message(subject="interested in your listing",
            sender= request.form['from'],
            recipients=[request.form['to']],
            body=request.form['message'])
			mail.send(msg)
			flash("email sent")
	return render_template("viewpost.html", post = Listing.query.filter_by(listing_id=id).first(), email=session.get("email") if session.get("email")
		is not None else ' ')



#view all of the signed in user's listings
@app.route("/userlistings")
def userlistings():

    
	return render_template("userlistings.html",  userlistings = Listing.query.filter_by(listing_email = 
		session.get("email")).all())


@app.route("/editpost/<int:id>", methods=['POST', 'GET'])
def editpost(id):
	if request.method == "POST":
		photos = request.files.getlist("photos")
		errors = []
		pattern = re.compile("^[\dA-Z]{3}-[\dA-Z]{3}-[\dA-Z]{4}$", re.IGNORECASE)
		loc_string = request.form['address'] + ' ' + request.form['city']
		geolocator = Nominatim(user_agent="dormroom")
		location = geolocator.geocode(loc_string)
		list_photos = request.files.getlist("photos[]")
		if request.form['title'] == "" or request.form['description'] == "" or request.form['address'] == "" or request.form['phonenumber'] == "" or request.form['contactname'] == "" or request.form['contactemail'] == "" or request.form['price'] == "":
			errors.append("Not all fields filled out.")
		if validate_email(request.form['contactemail']) == False and request.form['contactemail']!= "":
				errors.append("Please use a valid email to advertise your post.")
		if len(list_photos) < 2:
				errors.append("Please upload at least two photos.")
		if pattern.match(request.form['phonenumber']) is None:
				errors.append("Please enter a valid phone number.")
		if request.form['price'].isdigit() == False:
				errors.append("Please enter a numeric price.")
		if errors:
			for error in errors:
				flash(error)
		else:
			listing_to_edit = Listing.query.filter_by(id = id).first()
			listing_to_edit.title = request.form['title']
			listing_to_edit.description = request.form['description']
			listing_to_edit.listing_photo_one = b64encode(photos[0].read())
			listing_to_edit.listing_photo_two = b64encode(photos[1].read())
			listing_to_edit.listing_photo_three = b64encode(photos[2].read()) if len(photos) > 2 else ''
			listing_to_edit.listing_photo_four = b64encode(photos[3].read()) if len(photos) > 3 else ''
			listing_to_edit.listing_photo_five = b64encode(photos[4].read()) if len(photos) > 4 else ''
			listing_to_edit.listing_seller = request.form['contactname']
			listing_to_edit.listing_photo = request.form['phonenumber']
			listing_to_edit.listing_email = request.form['contactemail']
			listing_to_edit.listing_address = request.form['address']
			listing_to_edit.listing_added = datetime.datetime.now()
			listing_to_edit.listing_price = request.form['price']
			listing_to_edit.listing_school = session.get("school")
			listing_to_edit.listing_number = request.form['aptnumber']
			listing_to_edit.listing_lat = location.latitude
			listing_to_edit.listing_long = location.longitude
			listing_to_edit.listing_city = request.form['city']
			listing_to_edit.listing_state = request.form['state']
			db.session.commit()
			flash("Your post has been updated.")
			return redirect(url_for('userlistings'))


			


	return render_template("editpost.html", listing_to_edit = Listing.query.filter_by(listing_id = id).first())





@app.route("/forgotpassword", methods=['GET', 'POST'])
def forgotpassword():
	if request.method == "POST":
		errors = []
		email = request.form['email']
		email_exists = Student.query.filter_by(school_email = email).first()
		if email_exists == None and email!="":
			errors.append("That email could not be found in our system.")
		if email == "":
			errors.append("Please enter an email.")
		if errors:
			for error in errors:
				flash(error)
		else:
			msg_text = email.rjust(32)
			secret_key = '1234567890123456' 
			cipher = AES.new(secret_key, AES.MODE_ECB) 
			encoded = base64.b64encode(cipher.encrypt(msg_text))
			encoded_email = str(encoded)
			msg = Message(subject="Reset your DormRoom password",
                sender=app.config.get("MAIL_USERNAME"),
                recipients=[request.form['email']],
                body="Click the link to reset your password: http://127.0.0.1:5000/resetpassword/" + encoded_email)
			mail.send(msg)
			flash("We have sent a link to your account to reset your password.")



	return render_template("forgotpassword.html")







#view all listings for the user's school on the map
@app.route("/map")
def map():
	school = session.get("school")
	if school == 'UCSD':
		longitude = -117.2340
		latitude = 32.8801
	elif school == "UCD":
		longitude = -121.7617
		latitude = 38.5382
	elif school == "UCSB":
		longitude = -119.8489
		latitude = 34.4140
	elif school == "UCLA":
		longitude = -118.4452
		latitude = 34.0689
	elif school == "UCSC":
		longitude = -122.0583
		latitude = 36.9916
	elif school == "UCI":
		longitude  = -117.8443
		latitude = 33.6405
	else:
		longitude = -122.2585
		latitude = 37.8719
	return render_template("map.html", locations = Listing.query.filter_by(listing_school = session.get("school")).all(), latitude = latitude, longitude = longitude)


#make a post
@app.route("/post", methods=['POST', 'GET'])
def post():
	if session.get("name") is None:
		return redirect(url_for('registerandlogin'))
	if request.method == "POST":
		if request.form['button'] == "addpost":
			posterrors = []
			pattern = re.compile("^[\dA-Z]{3}-[\dA-Z]{3}-[\dA-Z]{4}$", re.IGNORECASE)
			loc_string = request.form['address'] + ' ' + request.form['city']
			geolocator = Nominatim(user_agent="dormroom")
			location = geolocator.geocode(loc_string)
			list_photos = request.files.getlist("photos[]")
			if request.form['title'] == "" or request.form['description'] == "" or request.form['address'] == "" or request.form['phonenumber'] == "" or request.form['contactname'] == "" or request.form['contactemail'] == "" or request.form['price'] == "":
				posterrors.append("Not all fields filled out.")
			if validate_email(request.form['contactemail']) == False and request.form['contactemail']!= "":
				posterrors.append("Please use a valid email to advertise your post.")
			if len(list_photos) < 2:
				posterrors.append("Please upload at least two photos.")
			if pattern.match(request.form['phonenumber']) is None:
				posterrors.append("Please enter a valid phone number.")
			if request.form['price'].isdigit() == False:
				posterrors.append("Please enter a numeric price.")
			if posterrors:
				for error in posterrors:
					flash(error)
			else:
				new_listing = Listing(listing_id = random.randint(100000, 999999), listing_title = request.form['title'], listing_description = request.form['description'], listing_photo_one = b64encode(list_photos[0].read()), listing_photo_two = b64encode(list_photos[1].read()), listing_photo_three  = b64encode(list_photos[2].read()) if len(list_photos) > 2 else '', listing_photo_four = b64encode(list_photos[3].read()) if len(list_photos) > 3 else '', listing_photo_five = b64encode(list_photos[4].read()) if len(list_photos) > 4 else '', listing_seller = request.form['contactname'],listing_phone = request.form['phonenumber'], listing_email = request.form['contactemail'], listing_address = request.form['address'], listing_added = datetime.datetime.now(), listing_price = request.form['price'], listing_school = session.get("school"), listing_number = request.form['aptnumber'], listing_lat = location.latitude, listing_long = location.longitude, listing_city = request.form['city'], listing_state = request.form['state'])
				db.session.add(new_listing)
				db.session.commit()
				message = Markup("added your post.<a href='/userlistings'> view your listings</a>")
				flash(message)



	return render_template("post.html", name=session.get("name"), email=session.get("email"), school= session.get("school"))



#logout
@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("dormhome"))

#verify the user with a token added to the user's row
@app.route("/verify/<string:token>")
def verify(token):
	user_to_verify = Student.query.filter_by(temp_token = token).first()
	verified = user_to_verify.verified
	name = user_to_verify.name 
	if verified == True:
		flash("You are already verified")
		return redirect(url_for("dormhome"))
	else:
		user_to_verify.verified = True
		db.session.commit()
		session['name'] = name
		session['email'] = user_to_verify.school_email
		session['user_id'] = user_to_verify.user_id 
		session['school'] = user_to_verify.school
		flash("Your account is now verified.")
		return redirect(url_for("dormhome"))

	return render_template("redirect.html")


@app.errorhandler(404)
def no_page_so_sad(e):
    return render_template('404.html'), 404


if __name__ == "__main__":
	app.run(debug=True)


