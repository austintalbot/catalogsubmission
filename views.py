from functools import wraps
from flask import (Flask, render_template, request, redirect, jsonify, url_for,
                   flash, make_response)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import relationship, sessionmaker
from collections import deque
from database_setup import Base, CategoryItem, Category, User
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import json
import httplib2
import requests
from flask_httpauth import HTTPBasicAuth
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

app = Flask(__name__)

# read client secrets from google
CLIENT_ID = json.loads(open('./static/client_secrets.json',
                            'r').read())['web']['client_id']
auth = HTTPBasicAuth()
APPLICATION_NAME = "Austin Talbot - Catalog APP"

# Connect to Database and create database session
engine = create_engine(
    'sqlite:///Catalog.db', connect_args={'check_same_thread': False})
auth = HTTPBasicAuth()
APPLICATION_NAME = "Austin Talbot - Catalog APP"

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

latestlist = []


class itemlist(object):
    def __init__(self, name, id, category_id, category, creator, *args,
                 **kwargs):
        self.name = name
        self.id = id
        self.category_id = category_id
        self.category = category
        self.creator = creator
        self.start = 0
        self.end = args

    def __hash__(self):
        return hash((self.name, self.id, self.category_id, self.creator))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.name == other.name and \
            self.id == other.id and \
            self.category_id == other.category_id and \
            self.creator == other.creator

    def __iter__(self):
        return self

    def __next__(self):
        if self.start >= len(self.end):
            raise StopIteration
        else:
            self.start += 1
            return self.end[self.start - 1]


# function to capture last five items viewed
def latest(items):
    if items not in latestlist:
        if len(latestlist) > 4:
            del latestlist[0]
            latestlist.append(items)
        else:
            latestlist.append(items)


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in login_session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# --------------------------------------
# JSON APIs to show Catalog information
# --------------------------------------
@app.route('/categories/api/')
def showAPI():
    categories = session.query(Category).all()
    items = session.query(CategoryItem).all()
    quantity = len(items)
    return render_template(
        'json.html', categories=categories, items=items, quantity=quantity)


@app.route('/categories/JSON')
def showCatalogJSON():
    """Returns JSON of all categories and items in the catalog"""
    categories = session.query(Category).all()
    return jsonify(Categories=[i.serialize for i in categories])


@app.route('/categories/<int:item_id>/JSON')
def showCatalogItemJSON(item_id):
    """Returns JSON of selected item in catalog"""
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    print(item.serialize)
    return jsonify(item=item.serialize)


@app.route('/categories/all/JSON')
def categoriesJSON():
    """Returns JSON of all categories and items in catalog"""
    items = session.query(CategoryItem).all()
    return jsonify(items=[r.serialize for r in items])


@app.route('/categories/Users/JSON')
def UsersJSON():
    """Returns JSON of all categories and items in catalog"""
    users = session.query(User).all()
    return jsonify(users=[r.serialize for r in users])


@app.route('/sitemap')
def showSitemap():
    categories = session.query(Category).all()
    items = session.query(CategoryItem).all()
    quantity = len(items)
    return render_template(
        'sitemap.html', categories=categories, items=items, quantity=quantity)


# --------------------------------------
# CRUD for categories
# --------------------------------------
# READ - home page, show latest items and categories
@app.route('/')
@app.route('/categories/')
def showCatalog():
    """Returns catalog page with all categories and recently added items"""
    categories = session.query(Category).all()
    items = session.query(CategoryItem).order_by(CategoryItem.id.desc()).all()
    quantity = len(items)
    print(quantity)
    if 'username' not in login_session:
        return render_template(
            'public_catalog.html',
            categories=categories,
            items=items,
            quantity=quantity)
    else:
        return render_template(
            'catalog.html',
            categories=categories,
            items=items,
            quantity=quantity,
            latest=latestlist)


# CREATE - New category
@app.route('/categories/new', methods=['GET', 'POST'])
@login_required
def newCategory():
    """Allows user to create new category"""
    if 'user_id' not in login_session and 'email' in login_session:
        login_session['user_id'] = getUserID(login_session['email'])
    if request.method == 'POST':
        print(login_session)
        newCategory = Category(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash("New category created!", 'success')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('new_category.html')


# EDIT a category
@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    """Allows user to edit an existing category"""
    editedCategory = session.query(Category).filter_by(id=category_id).one()
    if editedCategory.user_id != login_session['user_id']:
        return """<script>
                    function myFunction() {
                        alert('You are not authorized!')
                        }
                </script>
                <body onload='myFunction()'>"""
    if request.method == 'POST':
        if request.form['name']:
            editedCategory.name = request.form['name']
            flash('Category Successfully Edited %s' % editedCategory.name,
                  'success')
            return redirect(url_for('showCatalog'))
    else:
        return render_template('edit_category.html', category=editedCategory)


# DELETE a category
@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    """Allows user to delete an existing category"""
    categoryToDelete = session.query(Category).filter_by(id=category_id).one()
    if categoryToDelete.user_id != login_session['user_id']:
        return """<script>
                         function myFunction() {
                            alert('You are not authorized!')
                        }
                    </script>
                <body onload='myFunction()'>"""
    if request.method == 'POST':
        session.delete(categoryToDelete)
        flash('%s Successfully Deleted' % categoryToDelete.name, 'success')
        session.commit()
        return redirect(url_for('showCatalog', category_id=category_id))
    else:
        return render_template(
            'delete_category.html', category=categoryToDelete)


# --------------------------------------
# CRUD for category items
# --------------------------------------
# READ - show category items
@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showCategoryItems(category_id):
    """returns items in category"""
    category = session.query(Category).filter_by(id=category_id).one()
    categories = session.query(Category).all()
    creator = getUserInfo(category.user_id)
    items = session.query(CategoryItem).filter_by(
        category_id=category_id).order_by(CategoryItem.id.desc())
    quantity = items.count()
    return render_template(
        'catalog_menu.html',
        categories=categories,
        category=category,
        items=items,
        quantity=quantity,
        creator=creator)


# READ ITEM - selecting specific item show specific information about that item
@app.route('/categories/<int:category_id>/item/<int:item_id>/')
def showCatalogItem(category_id, item_id):
    """returns category item"""
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(CategoryItem).filter_by(id=item_id).one()
    creator = getUserInfo(category.user_id)
    i = itemlist(item.name, item.id, category_id, category.name, creator)
    print(i.name)
    print(i.id)
    print(i.category_id)
    print(i.category)
    latest(i)
    return render_template(
        'catalog_menu_item.html',
        category=category,
        item=item,
        creator=creator)


# CREATE ITEM
@app.route('/categories/item/new', methods=['GET', 'POST'])
@login_required
def newCatalogItem():
    """return "This page will be for making a new catalog item" """
    categories = session.query(Category).all()
    if request.method == 'POST':
        addNewItem = CategoryItem(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            category_id=request.form['category'],
            user_id=login_session['user_id'])
        session.add(addNewItem)
        session.commit()
        flash("New catalog item created!", 'success')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('new_catalog_item.html', categories=categories)


# UPDATE ITEM
@app.route(
    '/categories/<int:category_id>/item/<int:item_id>/edit',
    methods=['GET', 'POST'])
@login_required
def editCatalogItem(category_id, item_id):
    """return "This page will be for making a updating catalog item" """
    editedItem = session.query(CategoryItem).filter_by(id=item_id).one()
    if editedItem.user_id != login_session['user_id']:
        return """<script>
                    function myFunction() {
                    alert('You are not authorized!')
                }
            </script>
        <body onload='myFunction()'>"""
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['category']:
            editedItem.category_id = request.form['category']
        session.add(editedItem)
        session.commit()
        flash("Catalog item updated!", 'success')
        return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Category).all()
        return render_template(
            'edit_catalog_item.html', categories=categories, item=editedItem)


# DELETE ITEM
@app.route(
    '/categories/<int:category_id>/item/<int:item_id>/delete',
    methods=['GET', 'POST'])
@login_required
def deleteCatalogItem(category_id, item_id):
    """return "This page will be for deleting a catalog item" """
    itemToDelete = session.query(CategoryItem).filter_by(id=item_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        return """<script>
                         function myFunction() {
                            alert('You are not authorized!')
                        }
                    </script>
                <body onload='myFunction()'>"""
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Catalog Item Successfully Deleted', 'success')
        return redirect(url_for('showCatalog'))
    else:
        return render_template(
            'delete_catalog_item.html', CatalogItem=itemToDelete)


# --------------------------------------
# Login Handling
# --------------------------------------


# Login route, create anit-forgery state token
@app.route('/login')
def login():
    # Create anti-forgery state token
    state = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in list(range(32)))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Connect FB login
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Gets acces token
    access_token = request.data
    print("access token received %s " % access_token)
    access_token = access_token.decode().split("'")[0]

    # Gets info from fb clients secrets
    app_id = json.loads(open('./static/facebook_secret.json',
                             'r').read())['web']['app_id']
    app_secret = json.loads(open('./static/facebook_secret.json',
                                 'r').read())['web']['app_secret']

    url = """https://graph.facebook.com/v3.1/oauth/
            access_token?client_id=%s
            &redirect_uri=%s&client_secret=%s&code=%s""" % (
        app_id, 'https://localhost:5000', app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    url = """https://graph.facebook.com/
            v2.8/me?access_token=%s&fields=name,id,email""" % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    result = result.decode().split("'")[0]
    result = str(result)

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session
    # in order to properly logout
    login_session['access_token'] = access_token

    # Get user picture
    url = """https://graph.facebook.com/v3.1/
             %s/picture?access_token=%s&redirect=0&height=200&width=200""" % (
        data["id"], login_session['access_token'])

    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    result = result.decode().split("'")[0]
    result = str(result)
    data = json.loads(result)
    login_session['picture'] = data["data"]["url"]

    # See if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "Login Successful!"


# disconnect FB login
@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must be included to successfully logout
    access_token = login_session['access_token']

    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    print(result)
    return "you have been logged out"


# CONNECT - Google login get token
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate anti-forgery state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(
            './static/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    print('Picture: %s' % login_session['picture'])

    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # See if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "Login Successful"


# Disconnect - revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = """https://accounts.google.com/o/oauth2/
    revoke?token=%s""" % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash("Successfully disconnected.")
        return redirect(url_for('showCatalog'))
    else:
        flash("Failed to revoke token for given user.")
        return redirect(url_for('showCatalog'))


# User Helper Functions
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    print(login_session)
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            if 'gplus_id' in login_session:
                del login_session['gplus_id']
            if 'credentials' in login_session:
                del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        if 'username' in login_session:
            del login_session['username']
        if 'email' in login_session:
            del login_session['email']
        if 'picture' in login_session:
            del login_session['picture']
        if 'user_id' in login_session:
            del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.", 'success')
        latestlist.clear()
        return redirect(url_for('showCatalog'))
    else:
        latestlist.clear()
        flash("You were not logged in", 'danger')
    return redirect(url_for('showCatalog'))


if __name__ == '__main__':
    app.config['SECRET_KEY'] = ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for x in list(range(32)))
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
