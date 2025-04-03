from flask import Blueprint, render_template
import json

admin = Blueprint('admin', __name__)

@admin.route('/')
def menu_page():
    return render_template('admin/menu.html')

@admin.route('/sneaker/list')
def sneaker_list_page():
    return render_template('admin/list-sneaker.html')

@admin.route('/sneaker/detail')
def sneaker_detail_page():
    from app import get_shoe_details
    sneaker_json = get_shoe_details()[0]
    sneaker = json.loads(sneaker_json)
    print(sneaker)
    return render_template('admin/detail-sneaker.html',sneaker=sneaker)

@admin.route('/sneaker/create')
def sneaker_create_page():
    return render_template('admin/create-sneaker.html')

@admin.route('/sneaker/scan-tag')
def scan_tag_page():
    return render_template('admin/scan-tag.html')