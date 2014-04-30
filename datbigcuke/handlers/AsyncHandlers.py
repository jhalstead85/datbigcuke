""" Container module for asynchronous request handling classes.

@TODO(halstea2): Look into used the @asynchronous decorator
"""

__author__ = 'Joshua Halstead'
__copyright__ = 'Copyright 2014 Datbigcuke Project'
__email__ = 'halstea2@illinois.edu'

import tornado.web
import tornado.auth
import uuid
import datetime
import json
import urllib
import sys
import ConfigParser

# For test async handler only
import tornado.httpclient
from datetime import datetime

from datbigcuke.scheduler import *
from datbigcuke.handlers.BaseHandlers import WebResource
from datbigcuke.handlers.BaseHandlers import WebModule
from datbigcuke.handlers.BaseHandlers import AsyncRequestHandler
from datbigcuke.handlers.BaseHandlers import WebRequestHandler
from datbigcuke.entities import User
from datbigcuke.entities import UserRepository
from datbigcuke.entities import Deadline
from datbigcuke.entities import DeadlineMetadata
from datbigcuke.entities import DeadlineRepository
from datbigcuke.entities import Group
from datbigcuke.entities import GroupRepository
from datbigcuke.cukemail import CukeMail


# @TODO(halstea2) sanitize user data??
# @TODO(halstea2) Require authentication for all via @tornado.web.authenticated

class TestHandler(AsyncRequestHandler):
    @tornado.gen.coroutine
    @tornado.web.authenticated
    def post(self):
        data = self.get_argument("data", default=None)
        if not data:
            print str(datetime.datetime.now()) + " Received: None"
            self.write(json.dumps({"date": str(datetime.datetime.now()),
                                   "Status": 404}))

        print str(datetime.datetime.now()) + " Received: " +\
              str(json.dumps(data,
                             sort_keys=True,
                             indent=4,
                             separators=(',', ': ')
                 )
        )

        http_client = tornado.httpclient.AsyncHTTPClient()
        response = yield http_client.fetch("http://google.com")
        self.write(json.dumps({"date": str(datetime.datetime.now()),
                               "response": str(response)}))
# ../group/[id]
#Required Handlers


# Example raw json call
#    <button onclick="(
#        function (e, obj) {
#            var data1 = {};
#            data1['group'] = 1234;
#            $.ajax({
#                type: 'POST',
#                url: '/leave-group',
#                data: {'data': JSON.stringify(data1)},
#                dataType: 'json',
#                success: function(data) {
#                    console.log(data);
#                },
#                error: function(data) {
#                    console.log(data);
#                }
#            });
#        })(event, this)"> Test Leave Group </button>

# - Add member to group
#   - Data: Group ID, New User ID
#   - Server-Side Checks:
#       - New User ID must be in same parent group as current user ID
#       - Current user must be member of group ID
class AddMemberHandler(AsyncRequestHandler):
    @tornado.web.authenticated
    # @TODO(halstea2) We chould create a 'complex' async handler base that
    # is aware of a dictionary of values
    def post(self):
        curr_user = self.get_current_user()
        values =  self.get_argument("data", default=None)

        if not curr_user or not values:
            return

        # We don't need the 'name' field. It's encoded in the data dictionary
        # Keys are unicode after json.loads conversion
        values = json.loads(values)
        if not self._valid_request(curr_user, "", values):
            return

        self._perform_request(curr_user, "", values)
        pass

    def _valid_request(self, curr_user, name, values):
        # Malformed request
        if u"group_id" not in values or u"user_email" not in values:
            return False

        # Malformed request
        group_id = values[u"group_id"]
        new_user_email = values[u"user_email"]
        if not group_id or not new_user_email:
            return False

        #@TODO(halstea2) We need a mechanism in Group to retrieve the parent
        # and then verify the curr_user and new_user are members of it.

        #@TODO(halstea2) Enable all of these fucking checks
        #if not curr_user.groups:
        #    return False

        # Current user must be a member of the subgroup they're trying to add a
        # member to
        #if group_id not in curr_user.groups:
        #    return False

        # New user is already a member of the group
        new_user_repo = UserRepository()
        new_user = new_user_repo.get_user_by_email(new_user_email)
        new_user_repo.close()
        
        #if not new_user:
        #    return False

        #if new_user.groups:
        #    return False

        #if group_id in new_user.groups:
        #    return False

        return True

    def _perform_request(self, user, name, values):
        group_id = values[u"group_id"]
        new_user_email = values[u"user_email"]

        new_user_repo = UserRepository()
        new_user = new_user_repo.get_user_by_email(new_user_email)
        new_user_repo.close()

        # @TODO (halstea2) This might/should use the Group_repo function
        if new_user.groups:
            new_user.groups.append(group_id)
        else:
            new_user.groups = [group_id]

        self._persist_user(new_user)
        pass


# - Add subgroup to group
# - Data: Group ID, New Group Name, New Group Description
class AddSubgroupHandler(AsyncRequestHandler):
    @tornado.web.authenticated
    # @TODO(halstea2) We chould create a 'complex' async handler base that
    # is aware of a dictionary of values
    def post(self):
        curr_user = self.get_current_user()
        values = self.get_argument("data", default=None)

        if not curr_user or not values:
            print "Invalid Request. Parameters Missing"
            return

        # We don't need the 'name' field. It's encoded in the data dictionary
        # Keys are unicode after json.loads conversion
        values = json.loads(values)
        if not self._valid_request(curr_user, "", values):
            print "Invalid Request. Parameters Empty"
            return

        self._perform_request(curr_user, "", values)
        pass

    def _valid_request(self, curr_user, name, values):
        # Malformed request
        if u"group_id" not in values or u"group_name" not in values:
            return False

        # Malformed request
        group_id = values[u"group_id"]
        new_group = values[u"group_name"]
        new_description = values[u"group_description"]
        if not group_id or not new_group or not new_description:
            return False

        return True

    def _perform_request(self, user, name, values):
        print "performing request"
        group_id = values[u"group_id"]
        new_group_name = values[u"group_name"]
        new_group_desc = values[u"group_description"]

        curr_user = self.get_current_user()

        gr = GroupRepository()
        new_group = Group()
        new_group.name = new_group_name
        new_group.description = new_group_desc
        new_group.type = 0 # private group
        new_group.maintainerId = curr_user.id
        new_group = gr.persist(new_group)

        print "Group: " + str(new_group)

        # assign the subgroup as a child of the parent group
        gr.add_group_as_subgroup(group_id, new_group.id)
        gr.close()

        # assign the user as a member of the subgroup
        user_repo = UserRepository()
        user_repo.add_user_to_group(curr_user, new_group)
        user_repo.close()

        self._persist_user(curr_user)
        

        pass

# - Add deadline to group
# - Data: Group ID, New Deadline Name, New Deadline Time, New Deadline Notes
class AddDeadlineHandler(AsyncRequestHandler):
    @tornado.web.authenticated
    # @TODO(halstea2) We chould create a 'complex' async handler base that
    # is aware of a dictionary of values
    def post(self):
        curr_user = self.get_current_user()
        values = self.get_argument("data", default=None)

        if not curr_user or not values:
            return

        # We don't need the 'name' field. It's encoded in the data dictionary
        # Keys are unicode after json.loads conversion
        values = json.loads(values)
        if not self._valid_request(curr_user, "", values):
            return

        self._perform_request(curr_user, "", values)
        
        pass

    def _valid_request(self, curr_user, name, values):
        # Malformed request
        if u"group_id" not in values or u"name" not in values or u"deadline" not in values or u"notes" not in values:
            return False

        # Malformed request
        group_id = values[u"group_id"]
        name = values[u"name"]
        deadline = values[u"deadline"]
        notes = values[u"notes"]
        if not group_id or not name or not deadline or not notes:
            return False

        return True

    def _perform_request(self, user, name, values):
        group_id = values[u"group_id"]
        name = values[u"name"]
        deadline = values[u"deadline"]
        notes = values[u"notes"]
        curr_user = self.get_current_user()


        dr = DeadlineRepository()
        gr = GroupRepository()
        group = gr.fetch(group_id)
        gr.get_group_maintainer(group)

        new_deadline = Deadline()
        new_deadline.meta = DeadlineMetadata()

        new_deadline.name = name
        new_deadline.group_id = group_id
        new_deadline.deadline = datetime.strptime(deadline, u'%m/%d/%Y %I:%M %p') # private group
        if(group.maintainer and group.maintainer.id == user.id):
            new_deadline.type = 'END'
        else:
            new_deadline.type = 'PER'
        new_deadline.meta.user_id = user.id
        new_deadline.meta.notes = notes
        new_deadline = dr.persist(new_deadline)        

        dr.close()

        pass

# - Get members of parent group (for 'Add member' auto-complete)
#   - Data: Parent Group ID
class GetMembersOfParentHandler(AsyncRequestHandler):
    # @TODO(halstea2) - Extract user auth and data checking to base class
    def get(self):
        pass

# - Create subgroup (only if parent is public)
#   - Data: Course ID, Section ID, name, desc, type (inferred), user id (from get_curr_user)
#   - Server-Side Checks:
#       - Current user is a member of the parent group of the new subgroup ID
#   @TODO(halstea2) - Save for last
#   
class CreateSubgroupHandler(AsyncRequestHandler):
    def _valid_request(self, user, name, values):
        pass

    def _perform_request(self, user, name, values):
        pass

# - Get course list (for 'Create subgroup' auto-complete)
#   - Data: All courses?
class GetCourseListHandler(AsyncRequestHandler):
    # @TODO(halstea2) - Extract user auth and data checking to base class
    @tornado.web.authenticated
    def get(self):
        pass

# - Get existing deadline names for the group (for 'Add deadline' auto-complete)
#   - Data: Group ID
class GetGroupDeadlinesHandler(AsyncRequestHandler):
    @tornado.web.authenticated
    def get(self):
        pass

## - Schedule endpoint
class ScheduleHandler(AsyncRequestHandler):
    @tornado.web.authenticated
    # @TODO(halstea2) We chould create a 'complex' async handler base that
    # is aware of a dictionary of values
    def post(self):
        curr_user = self.get_current_user()
        values =  self.get_argument("data", default=None)

        if not curr_user or not values:
            return

        # We don't need the 'name' field. It's encoded in the data dictionary
        # Keys are unicode after json.loads conversion
        values = json.loads(values)
        if not self._valid_request(curr_user, "", values):
            return

        self._perform_request(curr_user, "", values)
        pass

    def _valid_request(self, user, name, values):
        # Malformed request
        if u"group_members" not in values or u"deadline" not in values or u"duration" not in values or u"off_limits_start" not in values or u"off_limits_end" not in values:
            return False

        # Malformed request
        group_members = values[u"group_members"]
        deadline = values[u"deadline"]
        duration = values[u"duration"]
        off_limits_start = values[u"off_limits_start"]
        off_limits_end = values[u"off_limits_end"]
        if not group_members or not deadline or not duration or not off_limits_start or not off_limits_end:
            return False

        #real deadline
        dr = DeadlineRepository()
        dl = dr.fetch(deadline)
        dr.close()

        if not dl:
            sys.stderr.write("invalid deadline id: " + str(dl))
            return False

        #real users
        for email in group_members:
            new_user_repo = UserRepository()
            new_user = new_user_repo.get_user_by_email(email)
            new_user_repo.close()
            if not new_user:
                sys.stderr.write("invalid email: " + email)
                return False


        return True

    def _perform_request(self, user, name, values):

        parser = ConfigParser.ConfigParser()
        parser.read('./config/app.conf')

        section = 'General'
        client_id = parser.get(section, 'client_id')
        client_secret = parser.get(section, 'client_secret')

        group_emails = values[u"group_members"]
        deadline = values[u"deadline"]
        duration = values[u"duration"]
        off_limits_start = values[u"off_limits_start"]
        off_limits_end = values[u"off_limits_end"]

        #real deadline
        dr = DeadlineRepository()
        deadline = dr.fetch(deadline).deadline
        dr.close()

        duration = timedelta(minutes=int(duration))

        off_limits_start = datetime.strptime(off_limits_start, u'%I:%M %p').time()
        off_limits_end = datetime.strptime(off_limits_end, u'%I:%M %p').time()

        group_members = {}

        for email in group_emails:
            new_user_repo = UserRepository()
            new_user = new_user_repo.get_user_by_email(email)
            new_user_repo.close()

            #must have refresh token
            if not new_user.refreshTok:
                sys.stderr.write(email + "has not given google permission to view calendar information" + '\n')
                return

            ref_tok = new_user.refreshTok

            #get access token
            url = "https://accounts.google.com/o/oauth2/token"
            access_token_request = "refresh_token=" + ref_tok + "&" +\
                      "client_id=" + client_id + "&" +\
                      "client_secret=" + client_secret + "&" +\
                      "grant_type=refresh_token"\

            sys.stderr.write("access_token request = " + access_token_request + '\n\n')

            http_client = tornado.httpclient.HTTPClient()
            http_request = tornado.httpclient.HTTPRequest(url, 'POST', body=access_token_request)
            response = http_client.fetch(http_request)

            #handle the access token response
            #sys.stderr.write("response = " + str(response) + '\n\n')

            data = json.loads(response.body)
            a_token = data['access_token']
            sys.stderr.write("access_token = " + a_token + '\n\n')

            events = []

            cal_list_http_client = tornado.httpclient.HTTPClient()
            response2 = cal_list_http_client.fetch("https://www.googleapis.com/calendar/v3/users/me/calendarList?access_token=" + a_token)

            #handle google calendar list
            #sys.stderr.write("calendar list response = " + str(response2) + '\n\n')

            data2 = json.loads(response2.body)
            #sys.stderr.write(str(data2) + '\n\n')

            for calendar in data2['items']:

                calendar_id = calendar['id']

                #calendars without the 'selected' attribute appear to be invalid
                if 'selected' not in calendar:
                    continue

                #sys.stderr.write("Reading calendar: " + str(calendar_id) + '\n')

                event_list_http_client = tornado.httpclient.HTTPClient()
                response3 = event_list_http_client.fetch("https://www.googleapis.com/calendar/v3/calendars/" + calendar_id + "/events?singleEvents=true&access_token=" + a_token)

                #handle event list
                #sys.stderr.write("event list response = " + str(response3) + '\n\n')

                data3 = json.loads(response3.body)
                #sys.stderr.write(str(data3) + '\n\n')

                #add each event
                for event in data3['items']:
                    #I have many doubts this will work for arbitrary calendars
                    #and I am certain it will error for other timezones.....
                    start = datetime.strptime(event['start']['dateTime'], u'%Y-%m-%dT%H:%M:%S-05:00')
                    end = datetime.strptime(event['end']['dateTime'], u'%Y-%m-%dT%H:%M:%S-05:00')
                    events.append((start, end))
                    #sys.stderr.write("Event found: " + str(start) + " - " + str(end) + '\n')
                sys.stderr.write('\n')

            group_members[email] = events
        
        #print str(schedule_meeting(group_members, deadline, duration, off_limits_start, off_limits_end)[:15])

        meets = schedule_meeting(group_members, deadline, duration, off_limits_start, off_limits_end)

        result = []
        for meet in meets:
            result.append(meet[0].strftime(u'%A %b %d (%Y) at %I:%M %p'))

        self.write(json.dumps(result[:15]))
        self.flush
        self.finish
    


# /profile Request Handlers

# - Edit Name
#   - Data: Name
#   - Server-side Checks: None
class UpdateNameHandler(AsyncRequestHandler):
    """Async Handler for updating a user's name"""

    # Assumptions: User is authenticated. attr is string (decoded to utf-8).
    def _valid_request(self, user, attr, value):
        """Verify that the 'update name' request is valid"""
        if not hasattr(user, attr):
            return False

        if len(value) != 1:
            return False

        return True

    # Assumption: User is authenticated. attr exists. Value is list of length 1
    def _perform_request(self, user, attr, value):
        """Perform the update request. For simple (read: single attribute
        updates the 'name' is the attribute and the 'value' is a list of len 1
        containing the value. This isn't the case for multi-attribute edits."""

        value = value[0].decode("utf-8")
        setattr(user, attr, value)
        self._persist_user(user)


# - Edit Email
#   - Data: Email
#   - Server-side Checks:
#       - Require email activation
#       - Clear cookies
class UpdateEmailHandler(AsyncRequestHandler):
    """Async Handler for updating a user's email"""

    # Assumptions: User is authenticated. attr is string (decoded to utf-8).
    def _valid_request(self, user, attr, value):
        """Verify that the 'update email' request is valid"""
        print "vr attr: " + str(attr)
        if not hasattr(user, attr):
            print "attr not found"
            return False

        print "value attr: " + str(value)
        if len(value) != 1:
            print "value not found"
            return False

        print "Valid request received"
        return True

    # Assumption: User is authenticated. attr exists. Value is list of length 1
    def _perform_request(self, user, attr, value):
        """Perform the update request. For simple (read: single attribute
        updates the 'name' is the attribute and the 'value' is a list of len 1
        containing the value. This isn't the case for multi-attribute edits."""

        value = value[0].decode("utf-8")
        setattr(user, attr, value)

        unique = str(uuid.uuid4())
        user.confirmed = False
        user.confirmUUID = unique

        self._persist_user(user)

        ## Send a verification email to the user
        m = CukeMail()
        m.send_verification(unique, user.email)
        self.clear_cookie(self.cookie_name)

# - receives the request from the client to authenticate the users calender
# - Server-side Checks:
#   - This is a valid user
class GoogleAuthHandler( WebRequestHandler ):
    
    @tornado.web.authenticated
    def post( self ):
        user = self.get_current_user()

        # 'Logged-in' user must be defined
        if not user:
            return

        parser = ConfigParser.ConfigParser()
        parser.read('./config/app.conf')

        section = 'General'
        client_id = parser.get(section, 'client_id')
        client_secret = parser.get(section, 'client_secret')
        auth_redirect_api = parser.get(section, 'auth_redirect_api')

        #construct the url to redirect the user to
        #that asks them to give us permission
        endpoint = "https://accounts.google.com/o/oauth2/auth?"
        request =  {'redirect_uri': auth_redirect_api,
                    'response_type': "code",
                    'client_id': client_id,
                    'scope': "https://www.googleapis.com/auth/calendar.readonly",
                    'access_type': "offline",
                    'approval_prompt': "force",
                    'state': user.id}

        sys.stderr.write("Redirecting to: " + endpoint + urllib.urlencode(request) + '\n')

        #send back the url
        self.write(endpoint + urllib.urlencode(request))
        self.flush
        self.finish


# - receives the response from Google
# - Server-side Checks:
#   - If the result is an error
#   - If not, uses the authentication code to get a refresh key, and stores it
class GoogleResponseHandler( WebRequestHandler ):
    
    def get( self ):

        #if there was an error, print it and return
        if self.get_query_argument("error", default=False):
            sys.stderr.write("Google auth returned an error: " + self.get_query_argument("error") + '\n')
            return

        #if we are receiving a refresh token, store it
        if self.get_query_argument("access_token", default=False):
            sys.stderr.write("access_token = " + self.get_query_argument("access_token") + '\n')
            sys.stderr.write("refresh_token = " + self.get_query_argument("refresh_token") + '\n')


            return
        #otherwise, ask for the refresh token
        else:
            sys.stderr.write("code = " + self.get_query_argument("code") + '\n')
            sys.stderr.write("state = " + self.get_query_argument("state") + '\n')

            #form the request
            parser = ConfigParser.ConfigParser()
            parser.read('./config/app.conf')

            section = 'General'
            client_id = parser.get(section, 'client_id')
            client_secret = parser.get(section, 'client_secret')
            auth_redirect_api = parser.get(section, 'auth_redirect_api')

            url = "https://accounts.google.com/o/oauth2/token"
            request = "code=" + self.get_query_argument("code") + "&" +\
                      "client_id=" + client_id + "&" +\
                      "client_secret=" + client_secret + "&" +\
                      "redirect_uri=" + auth_redirect_api + "&" +\
                      "grant_type=authorization_code"\

            sys.stderr.write("refresh_token request = " + request + '\n')

            def handle_response(response):
                sys.stderr.write("response = " + str(response) + '\n')

                data = json.loads(response.body)
                r_token = data['refresh_token']
                user_id = self.get_query_argument("state")

                sys.stderr.write("user_id = " + str(user_id) + '\n')
                sys.stderr.write("refresh_token = " + r_token + '\n')

                user_repo = UserRepository()
                user = user_repo.fetch(user_id)
                user.refreshTok = r_token
                user_repo.persist(user)
                user_repo.close()

            http_client = tornado.httpclient.AsyncHTTPClient()
            http_request = tornado.httpclient.HTTPRequest(url, 'POST', body=request)
            http_client.fetch(http_request, handle_response)
            self.redirect("/profile")
