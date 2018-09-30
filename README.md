# Item Catalog

> Austin Talbot

## About

Project Overview
You will develop an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

## Some things you might need

- [Vagrant](https://www.vagrantup.com/)
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

## Skills used for this project

- Python
- HTML
- CSS
- Flask
- Bulma CSS
- Jinja2
- SQLAchemy
- OAuth
- Facebook / Google Login

## Getting Started

- Install Vagrant and VirtualBox
- Clone this repo into the `catlog/` directory found in the Vagrant directory
- Run `vagrant up` to run the virtual machine, then `vagrant ssh` to login to the VM
- from the main directory run `sudo pip install -r requirements`
- run application with `python3 views.py` from within its directory
- go to `http://localhost:8000/categories` to access the application
- \*if first time running, you must add a category before adding an item by using the `lotsOfCategories.py` script

#### --------------------------------------

#### CRUD for categories

#### --------------------------------------

`/sitemap` - quick list of all of the crud operations and a link to the JSON endpoints.

`/` or `/categories` - Returns catalog page with all categories and recently viewed items

`/categories/new` - Allows user to create new category (if the user is logged in).

`/categories/<int:category_id>/edit/` - Allows user to edit an existing category

`/categories/<int:category_id>/delete/` - Allows user to delete an existing category

#### CRUD for category items

`/categories/<int:category_id>/` or `/categories/<int:category_id>/items/` - diplays a category and a list of items in the catalog

`/categories/<int:category_id>/item/<int:catalog_item_id>/` - diplays an item in the catalog

`/categories/item/new` - Allows user to create a new item and associate it with any category that is created.

`/categories/<int:category_id>/item/<int:catalog_item_id>/edit` - Allows user to update an item (login required)

`/categories/<int:category_id>/item/<int:catalog_item_id>/delete` - Allows user to delete an item (login required)

#### --------------------------------------

#### Login

#### --------------------------------------

`/login` - login page

## Possible improvements

- Image Upload, possible future addition with file upload
