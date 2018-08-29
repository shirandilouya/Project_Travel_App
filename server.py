"""TravelApp"""


##########flash messages not working


from jinja2 import StrictUndefined

from flask import Flask, request, jsonify, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Pinpoint, Trip, UserTrip, Tag, TripTag, Friend
# import model

import datetime

import os 

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# If you use an undefined variable in Jinja2 it raises an error
app.jinja_env.undefined = StrictUndefined



@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")



@app.route('/login', methods=["GET"])
def show_login_form():
    """Shows login form for users."""

    return render_template("login.html")



@app.route("/login", methods=["POST"])
def log_in_user():
    """Checks for email and password in database, then logs in if they match."""

    # gets email and password from form
    email = request.form.get("email")
    password = request.form.get("password")

    # query db for user email
    check_email = User.query.filter(User.email==email).first()

    # check if email is in db
    if check_email:
        check_email_and_pw = User.query.filter(User.email==email, User.password==password).first()

        if check_email_and_pw:
            #store user email, first name and id in session
            session["email"] = check_email_and_pw.email
            session["fname"] = check_email_and_pw.fname
            session["current_user_id"] = check_email_and_pw.user_id

            flash("Logged in as %s" % email)
            # return redirect("/users", check_email_and_pw.user_id)#############################
            return redirect("/users/{}".format(check_email_and_pw.user_id))
        else:
            flash("Email and password don't match! Try again.")
            return render_template("login.html")

    else:
        flash("Your email is not registered. Please register here!")
        return redirect("/register")



@app.route('/register', methods=["GET"])
def show_regestration_form():
    """Show registration form for new users"""
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def process_new_user():
    fname = request.form.get("fname")
    lname = request.form.get("lname")
    email = request.form.get("email")
    password = request.form.get("password")

    # query the db for user email
    check_email = User.query.filter(User.email==email).first()
    # check_email = True when user is in the database. 

    # if user is not in the database- regester them with name, email and password
    if not check_email:
        new_user = User(fname=fname, lname=lname, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session["email"] = new_user.email
        session["fname"] = new_user.fname
        session["current_user_id"] = new_user.user_id

        flash("You're now registered!")
        return redirect("/users/{}".format(new_user.user_id))


    else:
        flash("You've already registered, please login")


    return redirect("/login")



@app.route("/logout", methods=["GET"])
def log_out_user():
    """Logs out user."""

    session.clear()
    flash("You have been logged out!")

    return redirect("/")



@app.route("/trip/<trip_name>")
def get_trip_details(trip_name):
    """gets and shows trip details """
    ####################################################
    # going to work if there's only one unique trip name
    user_id=session['current_user_id']
    print("in trip route. user_id is:")
    print(user_id)
    # need to filter for trip name AND user id, which is already in the session
    # current_trip = Trip.query.filter(Trip.trip_name==trip_name, User.user_id==user_id).first()
    current_trip = Trip.query.filter(Trip.trip_name==trip_name).first()

    #updateing current trip in session - by id and name
    session["current_trip_name"] = current_trip.trip_name
    session["current_trip_id"] = current_trip.trip_id
    return render_template("trip-details.html", trip=current_trip)




# @app.route("/friend-trip/<trip_name>")
# def get_friend_trip_details(trip_name):
#     """gets and shows friend's trip details """
#     ####################################################
#     # going to work if there's only one unique trip name
#     # need to filter for trip name AND user id, which is already in the session
#     current_trip = Trip.query.filter(Trip.trip_name==trip_name).first()
#     #updateing current trip in session - by id and name
#     session["current_trip_name"] = current_trip.trip_name
#     session["current_trip_id"] = current_trip.trip_id
#     return render_template("friend-trip-details.html", trip=current_trip)



@app.route("/users/<user_id>")
# get here from login or register form
def get_user_details(user_id):
    """Gets and shows details about user."""
    # one way to get list of user trips based on user id
    # current_user = User.query.filter(User.user_id==user_id).first()
    # trips_list=current_user.trips
    user_id = session["current_user_id"]
    # get list of trips for this user based on user id
    current_user = User.query.filter(User.user_id==user_id).first()
    # or:
    # current_user = User.query.filter(User.user_id==session["user_id"]).first() 
    # session["fname"]=current_user.fname
    # session["lname"]=current_user.lname
    
    #getting list of friend ids for this user
    friends_id_list = Friend.query.filter(Friend.user_id == user_id).all()
    friends_list = []
    for friend in friends_id_list:
        user_id_2 = friend.friend_id
        # getting list of trips of current friend
        current_friend = User.query.filter(User.user_id==user_id_2).first()
        # friends list is a lis of friends' trips
        friends_list.append(current_friend)

    # session["friends_list"] = friends_list


    return render_template("user_profile.html", user=current_user, friends_list=friends_list)
 


@app.route("/following")
def friends_trips():
    """ render a template with list of users and their trips"""
    
    friends_list = get_friends_list(session["current_user_id"])
    
    return render_template("following.html", friends_list=friends_list)



def get_friends_list(user_id):
    """ return list of friend id's based on user id"""
    friends_id_list = Friend.query.filter(Friend.user_id == user_id).all()
    friends_list = []
    for friend in friends_id_list:
        user_id_2 = friend.friend_id
        # getting list of trips of current friend
        current_friend = User.query.filter(User.user_id==user_id_2).first()
        # friends list is a lis of friends' trips
        friends_list.append(current_friend)

    return friends_list




@app.route('/search')
def index2():
    """Map with search box"""

    return render_template("search_box.html", key=os.environ['GOOGLE_API_KEY'])


#################################################################
# calendar view
@app.route("/calendar-view")
def show_calendar():
    """ Show pinpoints of current trip on calendar"""

    return render_template("/calendar-view.html")



@app.route('/calendar-view-pinpoints')
def show_calendar_pinpoints():
    print("in function of route calendar view pinpoints")

    current_trip_name, pinpoint_dict_list = get_pinpoints()
    
    if not pinpoint_dict_list:
        flash("no pinpoints added to trip yet")
        return redirect("/search")

    # make a list of pinpoints such that each pinpoint will be a dictionary
    # of key value pairs, the keys are all columns of the pinpoint table
    # keys we need: name, start, end, lat, lng, rating, description
    
    return jsonify({"current_trip_name":[current_trip_name], "pinpoint_list":pinpoint_dict_list})


@app.route("/calendar-view-no-edit")
def show_calendar_no_edit():
    """ Show pinpoints of current trip on calendar without edit option"""

    return render_template("/calendar-view-no-edit.html")
####################################################################



@app.route('/map-view')
def show_map():
    """ show pinpoints of the current trip on map """


    # current_trip_id = session["current_trip_id"]
    # current_trip = Trip.query.filter(Trip.trip_id==current_trip_id).first()
    # pinpoint_list = Pinpoint.query.filter(Trip.trip_id==current_trip_id).all()
    
########comment out to put in function get_pinpoints
    # current_trip_id = session["current_trip_id"]
    # current_trip = Trip.query.filter(Trip.trip_id==current_trip_id).first()
    # pinpoint_list = current_trip.pinpoints 
    # pinpoint_list = get_pinpoints()

    # if there are no pinpoints to this trip yet
    # if not pinpoint_list:
    #     flash("no pinpoints added to trip yet")
    #     return redirect("/search")
 
    # return render_template("map-view.html", key=os.environ['GOOGLE_API_KEY'], current_trip=current_trip, pinpoint_list=pinpoint_list)
    return render_template("map-view.html", key=os.environ['GOOGLE_API_KEY'])



@app.route('/map-view-pinpoints')
def show_map_pinpoints():

    # current_trip_id = session["current_trip_id"]
    # print("got current trip id:")
    # print(current_trip_id)
    # #get the trip with our stored trip id
    # current_trip = Trip.query.filter(Trip.trip_id==current_trip_id).first()
    # print("got current trip query:")
    # print(current_trip.trip_name)
    # # get list of pinpoints for current trip
    # pinpoint_list = current_trip.pinpoints 

    # # pinpoint_list = Pinpoint.query.filter(Trip.trip_id==current_trip_id).all()

    # print("got pinpoint list")
    current_trip_name, pinpoint_dict_list = get_pinpoints()
    
    if not pinpoint_dict_list:
        flash("no pinpoints added to trip yet")
        return redirect("/search")

    # current_trip_name=current_trip.trip_name


    # make a list of pinpoints such that each pinpoint will be a dictionary
    # of key value pairs, the keys are all columns of the pinpoint table
    # keys we need: name, start, end, lat, lng, rating, description
    # pinpoint_dict_list = []
    # for pinpoint in pinpoint_list:
    #     pinpoint_dict = {"name": pinpoint.name,
    #                     "start": pinpoint.start,
    #                     "end": pinpoint.end,
    #                     "lat": pinpoint.lat,
    #                     "lng": pinpoint.lng,
    #                     "rating": pinpoint.rating,
    #                     "description": pinpoint.description}
    #     pinpoint_dict_list.append(pinpoint_dict)


    return jsonify({"current_trip_name":[current_trip_name], "pinpoint_list":pinpoint_dict_list})



@app.route("/friend-trip-map-view/<trip_name>")
def get_friend_trip_details(trip_name):
    """gets and shows friend's trip details """
    ####################################################
    # going to work if there's only one unique trip name
    # need to filter for trip name AND user id, which is already in the session
    current_trip = Trip.query.filter(Trip.trip_name==trip_name).first()
    #updateing current trip in session - by id and name
    session["current_trip_name"] = current_trip.trip_name
    session["current_trip_id"] = current_trip.trip_id
    return render_template("map-view-no-edit.html", trip = current_trip, key=os.environ['GOOGLE_API_KEY'])






#commented out  @app.route('/map-view-no-edit') and @app.route("/friend-trip/<trip_name>")
########################################################
# @app.route('/map-view-no-edit')
# def show_map_no_edit():
#     """ show pinpoints of the current trip on map """


#     # current_trip_id = session["current_trip_id"]
#     # current_trip = Trip.query.filter(Trip.trip_id==current_trip_id).first()
#     # pinpoint_list = Pinpoint.query.filter(Trip.trip_id==current_trip_id).all()
    
# ########comment out to put in function get_pinpoints
#     # current_trip_id = session["current_trip_id"]
#     # current_trip = Trip.query.filter(Trip.trip_id==current_trip_id).first()
#     # pinpoint_list = current_trip.pinpoints 
#     # pinpoint_list = get_pinpoints()

#     # if there are no pinpoints to this trip yet
#     # if not pinpoint_list:
#     #     flash("no pinpoints added to trip yet")
#     #     return redirect("/search")
 
#     # return render_template("map-view.html", key=os.environ['GOOGLE_API_KEY'], current_trip=current_trip, pinpoint_list=pinpoint_list)
#     return render_template("map-view.html", key=os.environ['GOOGLE_API_KEY'])






def get_pinpoints():
    """ returns name of trip & list of pinpoints for trip in session""" 
    
    current_trip_id = session["current_trip_id"]

    current_trip = Trip.query.filter(Trip.trip_id==current_trip_id).first()
    pinpoint_list = current_trip.pinpoints 
    current_trip_name = current_trip.trip_name
    # make a list of pinpoints where every pinpoint is a dictionary
    # with keys: name, start, end, etc
    pinpoint_dict_list = []

    for pinpoint in pinpoint_list:
        pinpoint_dict = {"name": pinpoint.name,
                        "start": pinpoint.start,
                        "end": pinpoint.end,
                        "lat": pinpoint.lat,
                        "lng": pinpoint.lng,
                        "rating": pinpoint.rating,
                        "description": pinpoint.description}
        pinpoint_dict_list.append(pinpoint_dict)

    return (current_trip_name, pinpoint_dict_list)



@app.route('/add-trip', methods=["GET"])
def add_trip_form():
    """form to add trip details"""

    return render_template("add-trip.html")




@app.route('/add-trip', methods=["POST"])
def add_trip():
    """add trip details to database"""
    trip_name = request.form.get("trip_name")
    start_trip = request.form.get("start_trip")
    end_trip = request.form.get("end_trip")
    is_public = request.form.get("is_public")
    if (is_public=='True'):
        is_public = True
    else:
        is_public = False
    new_trip=Trip(trip_name=trip_name, start_trip=start_trip, end_trip=end_trip, is_public=is_public)
    db.session.add(new_trip)
    db.session.commit()
    session["current_trip_id"]=new_trip.trip_id
    session["current_trip_name"]=new_trip.trip_name
    
    # connecting the new trip to the cuerrent user through user_trip tableS
    new_user_trip = UserTrip(user_id=session["current_user_id"], trip_id=session["current_trip_id"])
    db.session.add(new_user_trip)
    db.session.commit()



    # return redirect("/search/{}".format(trip_name))
    return redirect("/search")



@app.route("/add-pinpoint")
def go_to_add_pinpoint():

    return redirect("/search")




# @app.route("/add-pinpoint", methods=['POST'])
# def add_latlng():
#     """add pinpoint info to database"""

#     name = request.form.get("name")
#     latlng = request.form.get("latlng")
#     # getting lat lng positions as floats
#     latlng = latlng.strip(" ")
#     latlng = latlng.strip("(")
#     latlng = latlng.strip(")")
#     latlng = latlng.split(",")
#     lat = float(latlng[0])
#     lng = float(latlng[1])

#     start = request.form.get("start")
#     # print("this is start:")
#     # print(start)
#     end = request.form.get("end")
#     rating = request.form.get("rating")
#     description = request.form.get("description")

#     trip_id = session["current_trip_id"]
    


# #query to see if a pinpoint with the same position exists in the db
#     find_pinpoint = Pinpoint.query.filter_by(lat=lat, lng=lng, trip_id=trip_id).first()
    
    
  
#     if not find_pinpoint:
#         # new_pinpoint=Pinpoint(name=name, lat=lat, lng=lng)

#         new_pinpoint=Pinpoint(name=name, trip_id=trip_id, start=start, end=end, lat=lat, lng=lng, rating=rating, description=description)

#         db.session.add(new_pinpoint)
#         db.session.commit()
#     else:
#         #overwriting existing pinpoint


#         # # flash message not working
#         # flash("pinpoint already exists")


#     return "have pinpoint"


@app.route("/add-pinpoint", methods=['POST'])
def add_latlng():
    """add pinpoint info to database"""

    name = request.form.get("name")
    start = request.form.get("start")
    end = request.form.get("end")
    rating = request.form.get("rating")
    description = request.form.get("description")
    # this is true if the pinpoint exists in the database and we are just editing it
    # false if this is a new pinpoint to add to db
    if_exists = request.form.get("if_exists")

    trip_id = session["current_trip_id"]
    # print("this is if_exists")
    # print(if_exists)
    # query to find pinpoint in database by pinpoint name and trip id
    find_pinpoint = Pinpoint.query.filter_by(name=name, trip_id=trip_id).first()

    if if_exists==True: # we are editing an existing pinpoint
        #overwriting existing pinpoint
        # find_pinpoint = Pinpoint.query.filter_by(name=name, trip_id=trip_id).first()
        # print("find pinpoint is:")
        # print(find_pinpoint)
        # overwrite data in database for this pinpoint
        find_pinpoint.start = start
        find_pinpoint.end = end
        find_pinpoint.rating = rating
        find_pinpoint.description = description
        # db.session.commit()
    else:
        # find_pinpoint = Pinpoint.query.filter_by(name=name, trip_id=trip_id).first()

        if find_pinpoint==None: # If pinpoint is not in database, make new pinpoint
            latlng = request.form.get("latlng")
            # getting lat lng positions as floats
            latlng = latlng.strip(" ")
            latlng = latlng.strip("(")
            latlng = latlng.strip(")")
            latlng = latlng.split(",")
            lat = float(latlng[0])
            lng = float(latlng[1])

            new_pinpoint=Pinpoint(name=name, trip_id=trip_id, start=start, end=end, lat=lat, lng=lng, rating=rating, description=description)

            db.session.add(new_pinpoint)
            # db.session.commit()
        else: # pinpoint is in database, but we are still in the search page
            # this is still saving pinpoint twice in defferent pp-id's

            find_pinpoint.start = start
            find_pinpoint.end = end
            find_pinpoint.rating = rating
            find_pinpoint.description = description
            
    db.session.commit()

    return "have pinpoint"


@app.route("/explore")
def explore_trips():
    """ render a template with list of users and their trips"""
    # get list of users with public profiles
    all_users_list = User.query.filter().group_by(User.user_id).all()
    print("got users list")
    print (all_users_list[0])
    return render_template("explore.html", all_users_list=all_users_list)






if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    # app.debug = True
    app.debug = False

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0", port="5001")
