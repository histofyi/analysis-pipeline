from flask import Blueprint, current_app, request, redirect

from functions.template import templated


allele_views = Blueprint('allele_views', __name__)




@allele_views.get('')
@templated('alleles/home')
def allele_home_handler():
    return {}