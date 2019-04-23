-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS timeline;
DROP TABLE IF EXISTS event;
DROP TABLE IF EXISTS timeline_has;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE timeline (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  background_image TEXT,
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT,
    startDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    endDate TIMESTAMP,
    image TEXT,
    credit TEXT
);

CREATE TABLE timeline_has (
    timeline_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL
);



INSERT INTO user values(1, 'admin', 'admin');
INSERT INTO user values(2, 'sourabh', 'sourabh');

INSERT INTO timeline values(1, 1, '2019-03-06 13:23:44', 'War of Independence', 'A war was fought for Independence.', '');
INSERT INTO event values(1, "Declaration of Independence", "Independence was declared", '1776-07-04 12:00:00', '', '', 'Philadelphia');
INSERT INTO event values(2, "Siege of Yorktown", "Yorktown was under siege", '1781-09-28 12:00:00', '1781-10-19 12:00:00', 'https://upload.wikimedia.org/wikipedia/commons/7/77/Redbout-10.jpg', 'Yorktown');

INSERT INTO timeline_has values(1, 1);
INSERT INTO timeline_has values(1, 2);
