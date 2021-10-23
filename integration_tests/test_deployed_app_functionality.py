"""Test functionality of the LL project after it's been deployed to Heroku.
"""

import sys, re

import requests


print("\nTesting functionality of deployed app...")

# --- Anonymous home page ---
print("  Checking anonymous home page...")

# Note: app_url has a trailing slash.
app_url = sys.argv[1]
r = requests.get(app_url)

assert r.status_code == 200
assert "Track your learning." in r.text
assert "Log in" in r.text
assert "Hello, " not in r.text
assert "Log out" not in r.text


# --- Anonymous topics page ---
print("  Checking that anonymous topics page redirects to login...")
# Note that direct django testing detects a redirect; requests just sees
#   the login page.
url = f"{app_url}topics"
r = requests.get(url)

try:
    assert r.status_code == 200
    assert "Log in to your account." in r.text
    assert "Username" in r.text
    assert "Password" in r.text
except AssertionError:
    print("  *** AssertionError when accessing anonymous topics page.")
    print("status_code:", r.status_code)
    print("url", url)
    # should be like: https://immense-headland-05838.herokuapp.com/topics

# --- Anonymous register page ---
print("  Checking that anonymous register page is available...")
url = f"{app_url}users/register"
r = requests.get(url)

assert r.status_code == 200
assert "Log in" in r.text
assert "Username:" in r.text
assert "Password confirmation:" in r.text


# --- Anonymous login page ---
print("  Checking that anonymous login page is available...")
url = f"{app_url}users/login/"
r = requests.get(url)

assert r.status_code == 200
assert "Log in to your account." in r.text


# --- Create an account ---
#  Uses a session-based approach, to deal with csrf token.

print("  Checking that a user account can be made...")

register_url = f"{app_url}users/register/"

s = requests.Session()
s.get(register_url)

csrftoken = s.cookies['csrftoken']

new_username = 'user_1'
register_data = {
    'username': new_username,
    'password1': 'user_1_Pw_23',
    'password2': 'user_1_Pw_23',
    'csrfmiddlewaretoken': csrftoken,
}

headers = {
    'referer': f"{app_url}users/login/"
}

r = s.post(register_url, data=register_data, headers=headers)

try:
    assert r.status_code == 200
    assert "Track your learning." in r.text
    assert f"Hello, {new_username}." in r.text
except AssertionError:
    print("Error.")
    print(r.text)

# Create a topic, in same session where we created a user.
#   Visit topics page, then new_topic page as logged in user.
#
#   DEV: Later, may want to test logout here, then test login and then make
#     topic and entry.

print("  Checking that a new topic can be created...")
print("    Checking topics page as logged-in user...")
topics_url = f"{app_url}topics/"

r = s.get(topics_url)

assert r.status_code == 200
assert "Topics" in r.text
assert "No topics have been added yet." in r.text
assert "Add a new topic" in r.text

print("    Checking blank new_topic page as logged-in user...")
new_topic_url = f"{app_url}new_topic/"
r = s.get(new_topic_url)

assert r.status_code == 200
assert "Add a new topic:" in r.text

print("    Submitting post request for a new topic...")
csrftoken = s.cookies['csrftoken']

topic_data = {
    'text': 'Chess',
    'csrfmiddlewaretoken': csrftoken,
}

headers = {
    'referer': f"{app_url}new_topic/"
}

r = s.post(new_topic_url, data=topic_data, headers=headers)

assert r.status_code == 200
assert "Topics" in r.text
assert topic_data['text'] in r.text
assert "Add a new topic" in r.text

# Check topic page for topic tht was just created.
print("    Checking topic page for topic that was just created...")
# Search page that was just returned for link to topic page.
topic_id_re = r'<a href="/topics/(\d.*)/">'
m = re.search(topic_id_re, r.text)
topic_id_str = m.group(1)
topic_url = f"{app_url}topics/{topic_id_str}/"

r = s.get(topic_url)

assert r.status_code == 200
assert topic_data['text'] in r.text
assert "Add new entry" in r.text
assert "There are no entries for this topic yet." in r.text

# Create an entry for the topic.
print("    Checking that a new entry can be made...")
# new_entry_url can be built from the already-known topic id.
new_entry_url = f"{app_url}new_entry/{topic_id_str}/"
print("      Checking blank new entry page...")

r = s.get(new_entry_url)

assert r.status_code == 200
assert topic_data['text'] in r.text
assert "Add a new entry:" in r.text

print("      Submitting post request for new entry...")
csrftoken = s.cookies['csrftoken']

entry_data = {
    'text': 'I really love the game of Chess!',
    'csrfmiddlewaretoken': csrftoken,
}
headers = {
    'referer': f"{app_url}new_entry/{topic_id_str}/"
}

r = s.post(new_entry_url, data=entry_data, headers=headers)

assert r.status_code == 200
assert topic_data['text'] in r.text
assert "Add new entry" in r.text
assert entry_data['text'] in r.text
assert "edit entry" in r.text


# --- Everything works! (if you made it to here) --
print("  All tested functionality works.")
