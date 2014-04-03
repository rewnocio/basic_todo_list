from base import app_init
app_init()

from datafly.pages.models import Page

pages = Page.find()
for p in pages:
    p.save()