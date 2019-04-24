from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from timeline.auth import login_required
from timeline.db import get_db

from datetime import datetime
import json

bp = Blueprint('blog', __name__)


@bp.route('/index')
def index():
    """Show all the posts"""
    all_tags = get_all_tags()
    print(all_tags)
    all_timeline_tags = get_all_timeline_tags()
    print(all_timeline_tags)
    tags_to_show = get_tags_to_show(all_tags, all_timeline_tags)
    timelines = sqlarray_to_json(get_all_from_all_timelines(), tags_to_show)
    print(timelines)
    return render_template('blog/index.html', tls=timelines, timelines = json.dumps(timelines))\

@bp.route('/')
def homePage():
    """Show all the posts"""
    timelines = sqlarray_to_json(get_all_from_all_timelines())
    print(timelines)
    return render_template('blog/homePage.html', tls=timelines, timelines = json.dumps(timelines))

def get_tags_to_show(all, tt):
    d = {}
    for tid in tt:
        arr = []
        for tagid in tt[tid]:
            arr.append(all[tagid])
        d[tid] = arr
    return d
    

def get_timeline(id):
    """Get a timeline by id.
    :param id: id of timeline to get
    """
    db = get_db()
    timeline = db.execute(
        'SELECT t.id, title, summary, background_image, created, author_id, username'
        ' FROM timeline t JOIN user u ON t.author_id = u.id'
        ' WHERE t.id = ?',
        (id,)
    ).fetchone()

    if timeline is None:
        abort(404, "Timeline id {0} doesn't exist.".format(id))
        
    tl = {'timeline': timeline, 'events': []}
    events = db.execute(
        'SELECT * FROM timeline_has th INNER JOIN event e ON th.event_id = e.id WHERE th.timeline_id = ' + str(timeline['id'])
    ).fetchall()
    tl['events'] = events

    return tl
    
def get_all_timelines():
    db = get_db()
    timelines = db.execute(
        'SELECT id, title, author_id FROM timeline'
    ).fetchall()
    return timelines
    
def get_all_from_all_timelines():
    db = get_db()
    timelines = db.execute(
        'SELECT id, title, summary, background_image, author_id FROM timeline'
    ).fetchall()
    return timelines
    
    
def sqlarray_to_json_event(array):
    json_array = []
    for object in array:
        entry = {'id': object['id'], 'title': object['title'], 'summary': object['summary'], 'startDate': str(object['startDate']), 'endDate': str(object['endDate']), 'image': object['image'], 'credit': object['credit']}
        if 'author_id' in object.keys():
            entry['author_id'] = object['author_id']
        json_array.append(entry)
    return json_array
    
def sqlarray_to_json(array, tags=None):
    json_array = []
    print(tags)
    for object in array:
        id = object['id']
        entry = {'id': id, 'title': object['title']}
        if 'author_id' in object.keys():
            entry['author_id'] = object['author_id']
        if 'background_image' in object.keys():
            entry['background_image'] = object['background_image'] or url_for('static', filename='default_background.jpg')
        if 'summary' in object.keys():
            entry['summary'] = object['summary']
        if tags and id in tags:
            entry['tags'] = tags[id]
        json_array.append(entry)
    return json_array
    
def get_formatted_date(date):
    if date: 
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        d = date.date()
        date_obj = {'year': d.year, 'month': d.month, 'day': d.day}
        return date_obj
    return None
    
    
def get_event(id):
    """Get an event by id.
    :param id: id of event to get
    """
    db = get_db()
    event = db.execute(
        'SELECT id, title, summary, startDate, endDate, image, credit'
        ' FROM event t WHERE id = ?',
        (id,)
    ).fetchone()
    return event
    
    
def get_all_events():
    db = get_db()
    events = db.execute(
        'SELECT id, title FROM event'
    ).fetchall()
    return events
	
def get_all_from_all_events():
    db = get_db()
    events = db.execute(
        'SELECT id, title, summary, startDate, endDate, image, credit'
        ' FROM event'
    ).fetchall()
    return events
    
def get_formatted_event(event):
    new_event = {'text': {'headline': event['title'], 'text': event['summary']}}
    start_date = get_formatted_date(event['startDate'])
    if start_date:
        new_event['start_date'] = start_date
    end_date = get_formatted_date(event['endDate'])
    if end_date:
        new_event['end_date'] = end_date
    if 'image' in event.keys():
        new_event['media'] = {'url': event['image'], 'thumbnail': event['image']}
        if 'credit' in event.keys():
            new_event['media']['credit'] = event['credit']
    return new_event

    
        
def make_timeline_json(tl):
    js = {'title': {
             'text': {
               'headline': tl['timeline']['title'],
               'text': tl['timeline']['summary']
             },
             'background': {
                'url': tl['timeline']['background_image'] or url_for('static', filename='default_background.jpg')
             }
           },
           'events': []
          };
    for event in tl['events']:
        js['events'].append(get_formatted_event(event))
    return js
    


def create_timeline(title, summary, background_image, db):
    t = db.execute(
        'INSERT INTO timeline (title, summary, background_image, author_id)'
        ' VALUES (?, ?, ?, ?)',
        (title, summary, background_image, g.user['id'])
    )
    return t


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['summary']
        background_image = request.form['background_image']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            t = create_timeline(title, summary, background_image, db)
            db.commit()
            process_hash_tags(t.lastrowid, summary)
            return redirect(url_for('blog.view', id=t.lastrowid))
            
    timelines = json.dumps(sqlarray_to_json(get_all_timelines()))
    return render_template('blog/create.html', timelines=timelines)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def updateTimeline(id):
    """Update a post if the current user is the author."""
    tl = get_timeline(id)

    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['body']
        background_image = request.form['background_image']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE timeline SET title = ?, summary = ?, background_image = ? WHERE id = ?',
                (title, summary, background_image, id)
            )
            db.commit()
            process_hash_tags(id, summary)
            return view(id)
    
    events = json.dumps(sqlarray_to_json_event(get_all_from_all_events()))
    print(events)
    event_ids = [event['id'] for event in tl['events']]
    timelines = json.dumps(sqlarray_to_json(get_all_timelines()))
    return render_template('blog/update.html', tl={'timeline': tl['timeline'], 'events': events, 'event_ids': event_ids}, timelines=timelines)

def get_all_tags():
    db = get_db()
    return get_tag_dict(db.execute('SELECT * FROM tags').fetchall())
    
def get_all_timeline_tags():
    db = get_db()
    d = {}
    tt = db.execute('SELECT * FROM timeline_tags').fetchall()
    for elem in tt:
        tid = elem['timeline_id']
        if tid in d:
            d[tid].append(elem['tag_id'])
        else:
            d[tid] = [elem['tag_id']]
    return d


def get_tag_dict(arr):
    d = {}
    for elem in arr:
        d[elem['tag']] = elem['id']
        d[elem['id']] = elem['tag']
    return d
    
def get_tag_set(arr):
    s = set()
    for elem in arr:
        s.add(elem['tag_id'])
    return s

def process_hash_tags(tid, s):
    new_tags = set(part[1:] for part in s.split() if part.startswith('#'))
    db = get_db()
    all_tags = get_all_tags()
    existing_tags = get_tag_set(db.execute('SELECT * FROM timeline_tags WHERE timeline_id = ?', (tid,)).fetchall())
    print(new_tags)
    print(existing_tags)
    print(all_tags)
    current_tags = set(all_tags[tag] for tag in existing_tags)
    removed_tags = current_tags - new_tags
    added_tags = new_tags - current_tags
    for tag in added_tags:
        if tag not in all_tags:
            t = db.execute(
                     'INSERT INTO tags (tag)'
                     ' VALUES (?)',
                     (tag,)
                 )
            all_tags[tag] = t.lastrowid
            all_tags[t.lastrowid] = tag
        t = db.execute(
                'INSERT INTO timeline_tags'
                ' VALUES (?, ?)',
                (tid, all_tags[tag])
            )
    for tag in removed_tags:
        db.execute('DELETE FROM timeline_tags WHERE timeline_id = ? AND tag_id = ?', (tid, all_tags[tag]))
    print(all_tags)
    db.commit()
        

@bp.route('/<int:id>/view', methods=('GET',))
def view(id):
    """Update a post if the current user is the author."""
    tl = get_timeline(id)
    timeline_json = json.dumps(make_timeline_json(tl))
    timelines = json.dumps(sqlarray_to_json(get_all_timelines()))
    events = json.dumps(sqlarray_to_json(get_all_from_all_events()))
    event_ids = [event['id'] for event in tl['events']]
    return render_template('blog/view.html', tl={'timeline': tl['timeline'], 'timeline_json': timeline_json, 'events': events, 'event_ids': event_ids}, timelines=timelines)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_timeline(id)
    db = get_db()
    db.execute('DELETE FROM timeline WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
    
    

@bp.route('/<int:tid>/deleteevent/<int:eid>', methods=('GET',))
@login_required
def delete_event(tid, eid):
    """Delete an event."""
    try:
        db = get_db()
        db.execute('DELETE FROM timeline_has WHERE timeline_id = ? AND event_id = ?', (tid, eid))
        found = db.execute('SELECT count(*) FROM timeline_has WHERE event_id = ?', (eid,)).fetchone()[0]
        if found == 0:
            db.execute('DELETE FROM event WHERE id = ?', (eid,))
        db.commit()
    except Exception as e:
        return "FAILED"
    return "SUCCESS"

@bp.route('/<int:id>/create', methods=('POST',))
@login_required
def create_event(id):
    if request.method == 'POST':
        try:
            title = request.form['title']
            summary = request.form['summary']
            start_date = request.form['startDate'] + ' 12:00:00'
            end_date = request.form['endDate'] + ' 12:00:00' if request.form['endDate'] else ''
            image_url = request.form['image']
            credit = request.form['credit']
            error = None
    
            if error is not None:
                flash(error)
                return "Adding event failed"
            else:
                db = get_db()
                t = db.execute(
                    'INSERT INTO event (title, summary, startDate, endDate, image, credit)'
                    ' VALUES (?, ?, ?, ?, ?, ?)',
                    (title, summary, start_date, end_date, image_url, credit)
                )
                t = add_event_to_timeline(id, t.lastrowid, db)
                db.commit()
                event_json = get_formatted_event(request.form)
                return "SUCCESS" + json.dumps(event_json)
        except Exception as e:
            return e
    return "Only POST requests supported"
    

@bp.route('/<int:eid>/updateevent', methods=('POST',))
@login_required
def update_event(eid):
    try:
        title = request.form['title']
        summary = request.form['summary']
        start_date = request.form['startDate'] + ' 12:00:00'
        end_date = request.form['endDate'] + ' 12:00:00' if request.form['endDate'] else ''
        image_url = request.form['image']
        credit = request.form['credit']
        error = None
    
        db = get_db()
        db.execute(
            'UPDATE event SET title = ?, summary = ?, startDate = ?, endDate = ?, image = ?, credit = ? WHERE id = ?',
            (title, summary, start_date, end_date, image_url, credit, eid)
        )
        db.commit()
        return "SUCCESS"
    except Exception as e:
        print(e)
        return "FAILURE"
    
    
@bp.route('/<int:tid>/addevent/<int:eid>', methods=('GET',))
@login_required
def add_event(tid, eid):
    event = get_event(eid)
    db = get_db()
    add_event_to_timeline(tid, eid, db)
    db.commit()
    event_json = get_formatted_event(event)
    return "SUCCESS" + json.dumps(event_json)
    
    
    
def add_event_to_timeline(timeline_id, event_id, db):
    t = db.execute(
        'INSERT INTO timeline_has (timeline_id, event_id)'
        ' VALUES (?, ?)',
        (timeline_id, event_id)
    )
    return t
    

@bp.route('/<int:id1>/merge/<int:id2>', methods=('GET',))
@login_required
def merge_timelines(id1, id2):
    timeline1 = get_timeline(id1)
    timeline2 = get_timeline(id2)
    new_title = "Merge of " + timeline1['timeline']['title'] + " and " + timeline2['timeline']['title']
    new_background_image = timeline1['timeline']['background_image'] or timeline2['timeline']['background_image'] or ''
    db = get_db()
    t = create_timeline(new_title, new_title, new_background_image, db)
    new_timeline_id = t.lastrowid
    events_to_add = set()
    for event in timeline1['events']:
        events_to_add.add(event['id'])
    for event in timeline2['events']:
        events_to_add.add(event['id'])
    for event_id in events_to_add:
        add_event_to_timeline(new_timeline_id, event_id, db)
    db.commit()
    return "SUCCESS" + url_for('blog.view', id=new_timeline_id)
	
@bp.route('/<int:id1>/compare/<int:id2>', methods=('GET',))
@login_required
def compare_timelines(id1, id2):
    timeline1 = get_timeline(id1)
    timeline2 = get_timeline(id2)
    new_title = "Comparison of " + timeline1['timeline']['title'] + " and " + timeline2['timeline']['title']
    new_background_image = timeline1['timeline']['background_image'] or timeline2['timeline']['background_image'] or ''
    db = get_db()
    t = create_timeline(new_title, new_title, new_background_image, db)
    new_timeline_id = t.lastrowid
    events_to_add = set()
    for event in timeline1['events']:
        for event2 in timeline2['events']:
            if event['id'] == event2['id']:
                events_to_add.add(event['id'])
    for event_id in events_to_add:
        add_event_to_timeline(new_timeline_id, event_id, db)
    db.commit()
    return "SUCCESS" + url_for('blog.view', id=new_timeline_id)
	
@bp.route('/<int:id1>/contrast/<int:id2>', methods=('GET',))
@login_required
def contrast_timelines(id1, id2):
    timeline1 = get_timeline(id1)
    timeline2 = get_timeline(id2)
    new_title = "Contrast of " + timeline1['timeline']['title'] + " and " + timeline2['timeline']['title']
    new_background_image = timeline1['timeline']['background_image'] or timeline2['timeline']['background_image'] or ''
    db = get_db()
    t = create_timeline(new_title, new_title, new_background_image, db)
    new_timeline_id = t.lastrowid
    events_to_add = set()

    for event in timeline1['events']:
        found = 0;
        for event2 in timeline2['events']:
            if event['id'] == event2['id']:
                found = 1
        if found == 0:
            events_to_add.add(event['id'])
    for event in timeline2['events']:
        found = 0;
        for event2 in timeline1['events']:
            if event['id'] == event2['id']:
                found = 1
        if found == 0:
            events_to_add.add(event['id'])

    for event_id in events_to_add:
        add_event_to_timeline(new_timeline_id, event_id, db)
    db.commit()
    return "SUCCESS" + url_for('blog.view', id=new_timeline_id)
    
