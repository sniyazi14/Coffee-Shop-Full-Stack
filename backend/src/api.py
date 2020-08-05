import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

# ROUTES


@app.route('/drinks', methods=['GET'])
def fetch_drinks():
    drinks = Drink.query.all()
    if len(drinks) == 0:
        abort(404)
    drinks_short = [d.short() for d in drinks]
    result = {
        "success": True,
        "drinks": drinks_short
    }
    return jsonify(result)


# gets drink details for users that have 'get:drink-details' permission
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def fetch_drink_details(jwt):
    drinks = Drink.query.all()
    if len(drinks) == 0:
        abort(404)
    drinks_long = [d.long() for d in drinks]
    result = {
        "success": True,
        "drinks": drinks_long
    }
    return jsonify(result)


# creates new drink
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drink(jwt):
    try:
        body = request.get_json()
        title = body.get('title', None)
        recipe = body.get('recipe', None)
        if title is None or recipe is None:
            abort(422)
        drink = Drink(title=title,
                      recipe=json.dumps(recipe))
        drink.insert()
        result = {
            "success": True,
            "drinks": drink.long()
        }
        return jsonify(result)
    except Exception:
        abort(422)


# updates a selected drink
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    try:
        body = request.get_json()
        title = body.get('title', None)
        recipe = body.get('recipe', None)
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            return json.dumps({
                'success': False,
                'error': 'Drink #' + id + ' not found'
            }), 404
        if title:
            drink.title = title
        if recipe:
            drink.recipe = json.dumps(recipe)
        drink.update()
        result = {
            "success": True,
            "drinks": [drink.long()]
        }
        return jsonify(result)
    except Exception:
        abort(422)


# Deletes a drink by its id
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(404)
        drink.delete()
        return jsonify({
            'success': True,
            'delete': id
        })
    except Exception:
        abort(422)


# Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
                    "success": False,
                    "error": 500,
                    "message": "internal server error"
                }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
