from datetime import datetime
from bottle import Bottle, redirect, response, request, abort, TemplateError
from bson.objectid import ObjectId

from datafly.core import template
from datafly.models.page import Page

from config import db

public_app = Bottle()

@public_app.get('/sitemap.xml')
def sitemap():   
    urlset = []
    pages = db.pages.find({ 'current': True, 'meta.hide': { '$ne': True } })
    for page in pages:
        if page['id'] == 'home':
            continue
        urlset.append(dict(
            location = page['id'],
            lastmod = page['published'].strftime('%Y-%m-%dT%H:%M:%S'),
            changefreq = 'weekly'
        ))    
    response.headers['Content-Type'] = 'application/xml'
    return template('sitemap.html', urlset=urlset)

@public_app.get('/:page')
@public_app.get('/<section:re:(news)>/:page')
def simple_page(page=None, section=None):
    page_id = request.path.strip('/') if page else 'home'
    page = Page.get_latest(page_id)    
    try:
        return template('%s.html' % page_id, page=page)        
    except TemplateError:
        if not page:
            return abort(404, "Page not found")        
        return template('default.html', page=page, page_id=page_id)

@public_app.get('/')
def home():
    # getting tasks list and changing date format (date -> str)
    tasks_list = list(db.tasks_list.find().sort([("date", 1)]))

    for task in tasks_list:
        try:
            task["date"] = task["date"].strftime("%Y-%m-%d")
        except:
            pass
    
    template_context = dict(
        tasks_list = tasks_list,
        page = Page.get_latest('home')
    )
    return template('home.html', **template_context)

@public_app.post('/save_tasks/')
def save_tasks():
    # getting form data (new task)
    task_date = request.forms.get("new_date")
    task_description = request.forms.get("new_description")

    # handling new task case
    if len(task_date) != 0 and len(task_description) != 0:
        # changing date format
        try:
            task_date = datetime.strptime(task_date, "%Y-%m-%d")
        except:
            redirect("/")
    
        # saving obtained information inside mongo db
        db.tasks_list.insert({"date": task_date, "description": task_description})

    # handling changes to the existing cases
    for element in request.forms:
        if element.find("old") != -1:
            # getting task id
            task_id = element.split("_")[-1]

            # updating task date
            if element.find("date") != -1:
                try:
                    new_date = datetime.strptime(request.forms[element], "%Y-%m-%d")
                    db.tasks_list.update({"_id": ObjectId(task_id)}, {"$set": {"date": new_date}})
                except Exception, e:
                    print e
                    pass

            # updating task description
            else:
                db.tasks_list.update({"_id": ObjectId(task_id)}, {"$set": {"description": request.forms[element]}})

    # redirecting to the home page
    redirect("/")

@public_app.get('/delete/<task_id>/')
def delete_task(task_id):
    # saving obtained information inside mongo db
    db.tasks_list.remove({"_id": ObjectId(task_id)})

    # redirecting to the home page
    redirect("/")
