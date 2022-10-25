"""Test functionality of the blog project after it's been deployed.

** The main goal is test the deployment process, not to test the app itself. **

The goal is to cover all core functionality, without over-testing.
- This test is usually run against a deployed project, with over-network
  load times. Thorough testing would take an excessively long time. So,
  if a core aspect of the project has been tested already, there's no need
  to test that aspect in other pages.
- So, we test creation of blogs and posts because that proves that db access 
  is working. But we don't need to test editing and deletion.
- This test script assumes an empty db. It also will fail if run twice without flushing,
  because it will try to create the same user a second time.

Overall testing approach:
- Test anonymous views of some pages before any data has been created.
- Create a user.
- Create some data, and check views for the owner.
- Test the logout process.
- Verify public data is visible to anon user.
- Verify private data is not visible to anon user.

Usage:
- Run locally, and flush db before running tests:
  $ python test_deployed_app_functionality.py --url http://localhost:8000/ --flush-db
- Run against freshly-pushed project:
  $ python test_deployed_app_functionality.py --url deployed_project_url
"""

import sys, re, subprocess, argparse

import requests


# Process CLI args.
parser = argparse.ArgumentParser()
parser.add_argument('--url', type=str, required=True)
parser.add_argument('--flush-db', action='store_true')
args = parser.parse_args()

# Get URL of deployed project from CLI args.
app_url = args.url

# Make sure app url has a trailing slash.
if not app_url[-1] == '/':
    app_url += '/'

# This option is available to make it easier to work on this script, running against
#   a local version of the project. This allows successive runs of the tests to
#   pass. Without this, subsequent runs would fail because you can't create the
#   same user twice.
if args.flush_db:
    print("Flushing db before running test...")
    cmd = 'python manage.py flush --no-input'
    cmd_parts = cmd.split(' ')
    subprocess.run(cmd_parts)
    print("  Flushed db.")


print(f"\nTesting functionality of deployed app at {app_url}...\n")

# --- Anonymous home page ---
print("  Checking anonymous home page...")
r = requests.get(app_url)

assert r.status_code == 200
assert "BlogMaker Lite" in r.text
assert "BlogMaker Lite makes your world better by" in r.text
assert "Log in" in r.text
assert "Hello, " not in r.text
assert "Log out" not in r.text


# --- Anonymous empty all_blogs ---
print("  Checking empty anonmyous all_blogs page...")
url = f"{app_url}all_blogs"
r = requests.get(url)

assert r.status_code == 200
assert "Public Blogs" in r.text
assert "There are no public blogs yet." in r.text
assert "My Blogs" not in r.text
assert "Create a new blog" not in r.text


# --- Anonymous empty latest_posts ---
print("  Checking empty anonmyous latest_posts page...")
url = f"{app_url}latest_posts"
r = requests.get(url)

assert r.status_code == 200
assert "Latest Posts" in r.text
assert "from all public blogs" in r.text
assert "There are no public posts yet." in r.text


# --- Anonymous my_blogs page ---
print("  Checking that anonymous my_blogs page redirects to login...")
# Note that direct django testing detects a redirect; requests just sees
#   the login page.
url = f"{app_url}my_blogs"
r = requests.get(url)

assert r.status_code == 200
assert "Log in" in r.text
assert "Username" in r.text
assert "Password" in r.text


# --- Anonymous register page ---
print("  Checking that anonymous register page is available...")
url = f"{app_url}users/register"
r = requests.get(url)

assert r.status_code == 200
assert "Log in" in r.text
assert "Register an account" in r.text
assert "Username" in r.text
assert "Password confirmation" in r.text


# --- Anonymous login page ---
print("  Checking that anonymous login page is available...")
url = f"{app_url}users/login/"
r = requests.get(url)

assert r.status_code == 200
assert "Log in to your account" in r.text
assert "Username" in r.text
assert "Password" in r.text


# --- Create an account ---
#  Uses a session-based approach, to deal with csrf token.

print("  Checking that a user account can be made, and checking the logged-in version of the home page...")
register_url = f"{app_url}users/register/"

s = requests.Session()
s.get(register_url)

csrftoken = s.cookies['csrftoken']

# This is a simple username and password, so you can log in after running this
#   test and see the private data that's been created.
new_username = 'user1'
register_data = {
    'username': new_username,
    'password1': 'user1user1',
    'password2': 'user1user1',
    'csrfmiddlewaretoken': csrftoken,
}

headers = {
    'referer': f"{app_url}users/login/"
}

r = s.post(register_url, data=register_data, headers=headers)

try:
    assert r.status_code == 200
    assert "BlogMaker Lite" in r.text
    assert "BlogMaker Lite makes your world better" in r.text
    assert f"Hello, {new_username}." in r.text
    assert "Log out" in r.text
    assert "Register" not in r.text
except AssertionError:
    with open('error_page.html', 'w') as f:
        f.write(r.text)
    raise AssertionError


# --- Create a public blog ---
# Create a public blog, and make sure it's visible to the owner.
# Note: Leave 'public' out of blog_data to make a private blog.
print("  Checking that a public blog can be created, and that it's visible to owner...")
csrftoken = s.cookies['csrftoken']
blog_data = {
    'title': 'My Public Blog',
    'public': 'on',
    'csrfmiddlewaretoken': csrftoken,
}

headers = {
    'referer': f"{app_url}new_blog/"
}

new_blog_url = f"{app_url}new_blog/"
r = s.post(new_blog_url, data=blog_data, headers=headers)

try:
    assert r.status_code == 200
    assert "My blogs" in r.text
    assert "My Public Blog" in r.text
    assert "Create a new blog" in r.text
except AssertionError:
    with open('error_page.html', 'w') as f:
        f.write(r.text)
    raise AssertionError


# --- Create a public post on the public blog ---
# Note: The public blog was the first one created, so should have an id of 1.
print("  Checking that a public post on public blog is visible to owner...")
csrftoken = s.cookies['csrftoken']
post_data = {
    'title': 'My Public Post on Public Blog',
    'body': 'This is a wonderful public post on a public blog!',
    'public': 'on',
    'csrfmiddlewaretoken': csrftoken,
}

headers = {
    'referer': f"{app_url}new_post/"
}

new_post_url = f"{app_url}new_post/1/"
r = s.post(new_post_url, data=post_data, headers=headers)

try:
    assert r.status_code == 200
    assert post_data['title'] in r.text
    assert post_data['body'] in r.text
except AssertionError:
    with open('error_page.html', 'w') as f:
        f.write(r.text)
    raise AssertionError


# --- Create a private post on the public blog ---
# Note: The public blog was the first one created, so should have an id of 1.
print("  Checking that a private post on public blog is visible to owner...")
csrftoken = s.cookies['csrftoken']
post_data = {
    'title': 'My Private Post on Public Blog',
    'body': 'This is a wonderful private post on a public blog!',
    'csrfmiddlewaretoken': csrftoken,
}

headers = {
    'referer': f"{app_url}new_post/"
}

new_post_url = f"{app_url}new_post/1/"
r = s.post(new_post_url, data=post_data, headers=headers)

try:
    assert r.status_code == 200
    assert post_data['title'] in r.text
    assert post_data['body'] in r.text
except AssertionError:
    with open('error_page.html', 'w') as f:
        f.write(r.text)
    raise AssertionError


# --- Create a private blog ---
# Create a private blog, and make sure it's visible to the owner.
print("  Checking that a private blog can be created, and that it's visible to owner...")
csrftoken = s.cookies['csrftoken']
blog_data = {
    'title': 'My Private Blog',
    'csrfmiddlewaretoken': csrftoken,
}

headers = {
    'referer': f"{app_url}new_blog/"
}

new_blog_url = f"{app_url}new_blog/"
r = s.post(new_blog_url, data=blog_data, headers=headers)

try:
    assert r.status_code == 200
    assert "My blogs" in r.text
    assert "My Private Blog" in r.text
    assert "Create a new blog" in r.text
except AssertionError:
    with open('error_page.html', 'w') as f:
        f.write(r.text)
    raise AssertionError


# --- Create a public post on the private blog ---
# Note: The private blog was the second one created, so should have an id of 2.
print("  Checking that a public post on private blog is visible to owner...")
csrftoken = s.cookies['csrftoken']
post_data = {
    'title': 'My Public Post on Private Blog',
    'body': 'This is a wonderful public post on a private blog!',
    'public': 'on',
    'csrfmiddlewaretoken': csrftoken,
}

headers = {
    'referer': f"{app_url}new_post/"
}

new_post_url = f"{app_url}new_post/2/"
r = s.post(new_post_url, data=post_data, headers=headers)

try:
    assert r.status_code == 200
    assert post_data['title'] in r.text
    assert post_data['body'] in r.text
except AssertionError:
    with open('error_page.html', 'w') as f:
        f.write(r.text)
    raise AssertionError


# --- Test logout page ---
# Log out, then test anonymous views of the data that was just created.

print("  Checking that the logout process works...")
url = f"{app_url}users/logout/"
r = s.get(url)

assert r.status_code == 200
assert "Logged out" in r.text
assert "You have been logged out. Thank you for visiting!" in r.text
assert "Log out" not in r.text
assert "My Blogs" not in r.text


# --- Test that public blog is visible to an anon user ---
print("  Checking that public blog is visible to an anonymous user...")
url = f"{app_url}all_blogs"
r = requests.get(url)

assert r.status_code == 200
assert "My Public Blog" in r.text
assert "user1" in r.text


# --- Test that private blog is not visible to anon user ---
# We can check this with the request that was just sent.
print("  Checking that private blog is not visible to anonymous user...")
assert "My Private Blog" not in r.text
assert "My blogs" not in r.text


# --- Test that public post is visible on public blog ---
print("  Checking that public post is visible on public blog...")
url = f"{app_url}blogs/1/"
r = requests.get(url)

assert r.status_code == 200
assert "My Public Post on Public Blog" in r.text


# --- Test that private post is not visible on public blog ---
# We can check this with the request that was just sent.
print("  Checkig that private post is not visible on public blog...")
assert "My Private Post on Public Blog" not in r.text


# --- Test that public post on private blog is not visible ---
# This should redirect to the home page.
print("  Checking that public post on private blog is not visible...")
url = f"{app_url}posts/2/"
r = requests.get(url)

assert r.status_code == 200
assert "BlogMaker Lite makes your world better" in r.text


# --- Test that style is working ---
# Check the login page, and make sure the bootstrap form was rendered correctly?
print("  Checking style on login form...")
url = f"{app_url}users/login/"
r = requests.get(url)

assert r.status_code == 200
assert '<label class="form-label" for="id_username">Username</label>' in r.text


# --- Test that DEBUG is set to False correctly. ---
print("  Checking that DEBUG is set to False correctly. ---")
url = f"{app_url}nonexistent_page/"
r = requests.get(url)

assert r.status_code == 404
assert "Not Found" in r.text
assert "The requested resource was not found on this server." in r.text
assert "You're seeing this error because you have DEBUG = True in your Django settings file." not in r.text


# --- Everything works! (if you made it to here) --
print("\n  --- All tested functionality works. ---\n")