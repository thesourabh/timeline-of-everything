from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from timeline.auth import login_required
from timeline.db import get_db

from datetime import datetime

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    timelines = db.execute(
        'SELECT * FROM timeline t'
    ).fetchall()
    return render_template('blog/index.html', timelines=timelines)


def get_timeline(id, check_author=True):
    """Get a timeline and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of timeline to get
    :param check_author: require the current user to be the author
    :return: the timeline with author information
    :raise 404: if a timeline with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    db = get_db()
    timeline = db.execute(
        'SELECT t.id, title, summary, created, author_id, username'
        ' FROM timeline t JOIN user u ON t.author_id = u.id'
        ' WHERE t.id = ?',
        (id,)
    ).fetchone()

    if timeline is None:
        abort(404, "Timeline id {0} doesn't exist.".format(id))

    # if check_author and timeline['author_id'] != g.user['id']:
    #    abort(403)
        
    tl = {'timeline': timeline, 'events': []}
    events = db.execute(
        'SELECT * FROM timeline_has th INNER JOIN event e ON th.event_id = e.id WHERE th.timeline_id = ' + str(timeline['id'])
    ).fetchall()
    tl['events'] = events

    return tl


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == 'POST':
        title = request.form['title']
        summary = request.form['summary']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            t = db.execute(
                'INSERT INTO timeline (title, summary, author_id)'
                ' VALUES (?, ?, ?)',
                (title, summary, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.view', id=t.lastrowid))
            
    return render_template('blog/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_timeline(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ? WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)


@bp.route('/<int:id>/view', methods=('GET',))
def view(id):
    """Update a post if the current user is the author."""
    timeline = get_timeline(id)
    return render_template('blog/view.html', tl=timeline)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_timeline(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/create', methods=('POST',))
@login_required
def create_event(id):
    if request.method == 'POST':
        try:
            title = request.form['title']
            summary = request.form['summary']
            start_date = request.form['start-date'] + ' 12:00:00'
            end_date = request.form['end-date'] + ' 12:00:00'
            print(start_date)
            error = None
    
            if error is not None:
                flash(error)
                return "Adding event failed"
            else:
                db = get_db()
                t = db.execute(
                    'INSERT INTO event (title, summary, startDate, endDate)'
                    ' VALUES (?, ?, ?, ?)',
                    (title, summary, start_date, end_date)
                )
                print(t.lastrowid)
                t = db.execute(
                    'INSERT INTO timeline_has (timeline_id, event_id)'
                    ' VALUES (?, ?)',
                    (id, t.lastrowid)
                )
                db.commit()
                return "SUCCESS"
        except Exception as e:
            return e
    return "Only POST requests supported"
