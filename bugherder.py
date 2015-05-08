#!venv/bin/python
import argparse
import getpass
import json
import mimetypes
import requests
import os
import sys
import urllib
import xml.etree.cElementTree as etree

# Set these values to None to be prompted at the command line
jira_api_username = None
jira_api_password = None

# Hardcoded values for the JIRA production instance
jira_server = "https://your.atlassian.net"
jira_project_id = "00000"
jira_component_id = "00000"

# The user who will be displayed as the reporter of the issue
# (when ran at JAMF Software we put the owner of the JIRA project)
jira_reporter_name = "username"

# The transition and resolution IDs were used for marking JIRA issues as closed
# Historical BugHerd issues were migrated along with current issues 
jira_transition_id = "00"
jira_resolution_id = "00000"

class JIRA:
    def __init__(self, server, username=None, password=None):
        """Create an object to interact with the JIRA REST API"""
        self.session = requests.Session()
        self.api = server + "/rest/api/2/"
        self.user = username
        self._default_headers = {'Content-Type': 'application/json'}
        if not self.user:
            self.user = str(raw_input("JIRA Username: "))

        if not jira_api_password:
            password = getpass.getpass("JIRA Password: ")

        authurl = server + "/rest/auth/1/session/"
        authdata = (self.user, password)
        try:
            response = self.session.get(authurl, auth=authdata)
            response.raise_for_status()
        except Exception as e:
            print("An error occurred authenticating to JIRA:\n" + e.message)

    def findUser(self, username):
        return self.session.get(self.api + 'user?username=' + username)

    def createIssue(self, data):
        return self.session.post(self.api + 'issue', data, headers=self._default_headers)

    def createBulkIssues(self, data):
        return self.session.post(self.api + 'issue/bulk', data, headers=self._default_headers)

    def addIssueAttachment(self, issue_key, attachment):
        headers = {'X-Atlassian-Token': 'nocheck'}
        filename = os.path.basename(attachment)
        content_type = mimetypes.guess_type(filename)[0]
        if not content_type:
            content_type = 'application/octet-stream'

        with open(attachment, 'rb') as fileobj:
            files = {
                'file': (filename, fileobj, content_type)
            }
            return self.session.post(self.api + 'issue/' + issue_key + '/attachments', files=files, headers=headers)

    def addIssueComment(self, issue_key, comment, author=None):
        if not author:
            author = self.user

        data = {
            "author": {
                "name": author
            },
            "body": comment
        }
        return self.session.post(self.api + 'issue/' + issue_key + '/comment', json.dumps(data),
                                 headers=self._default_headers)

    def updateIssueStatus(self, issue_key, status_id, resolution_id):
        data = {
            "fields": {
                "resolution": {
                    "id": str(resolution_id)
                }
            },
            "transition": {
                "id": str(status_id)
            }
        }
        return self.session.post(self.api + 'issue/' + issue_key + '/transitions',
                                 json.dumps(data), headers=self._default_headers)

    def deleteIssue(self, issue_key):
        return self.session.delete(self.api + 'issue/' + issue_key)


class CreateJIRAIssue:
    '''Creates an object containing data for a single JIRA Issue
    Fields can be added/modified using CreateJIRAIssue.setField()
    use CreateJIRAIssue.json() to return JSON data'''
    def __init__(self, priority, summary, description, labels):
        # Global variables are used to populate the template below
        self.data = {
            "fields": {
                "project": {
                    "id": jira_project_id
                },
                "issuetype": {
                    "name": "Task"
                },
                "priority": {
                    "name": None
                },
                "assignee": {
                    "name": None
                },
                "reporter": {
                    "name": jira_reporter_name
                },
                "components": [
                    {
                        "id": jira_component_id
                    }
                ],
                "description": None,
                "summary": None,
                "labels": None,
            }
        }
        if priority.lower() == 'critical':
            priority = 'Critical'
        elif priority.lower() == 'important':
            priority = 'Major'
        elif priority.lower() == 'normal':
            priority = 'Minor'
        else:
            # used for 'minor' and 'not set'
            priority = 'Trivial'
            
        self.setField('priority', {'name': priority})
        self.setField('summary', summary)
        self.setField('description', description)
        self.setField('labels', labels)
    
    def setField(self, key, value):
        self.data['fields'][key] = value
        
    def json(self):
        return json.dumps(self.data)


def createJIRAIssues(xml_file):
    """Creates JIRA issues from BugHerd XML and adds comments to each issue"""
    issues = []
    root = etree.parse(xml_file)
    tasks = root.findall('task')
    count = len(tasks)
    if count < 1:
        print("No tasks to create JIRA issues from\nCheck that the input XML is a valid format")
        return False

    print("{0} issues will be created".format(count))

    for element in tasks:
        priority = element.find('priority').text

        summary = element.find('description').text[0:66] + '...'
        summary = summary.replace('\n', ' ')

        description = "Original Requester: {0}\n".format(element.find('requester-email').text)
        description += "Site Path: {0}\n".format(element.find('path').text)
        description += "OS: {0}\n".format(element.find('os').text)
        description += "Screen Resolution: {0}\n".format(element.find('resolution').text)
        description += "Browser: {0}\n".format(element.find('browser').text)
        description += "Browser Size: {0}\n".format(element.find('browser-size').text)
        description += "\n" + element.find('description').text

        labels = element.find('tags').text
        if labels:
            labels = labels.replace(' ', '_').split(',_')
        else:
            labels = []

        print("Creating JIRA issue: " + summary)
        issue = CreateJIRAIssue(priority, summary, description, labels)
        response = jira.createIssue(issue.json())
        if response.status_code >=300:
            print("Error(s) occurred creating the JIRA issue:")
            for key, value in response.json()['errors'].iteritems():
                print("{0}: {1}".format(key, value))

                continue

        issue_key = response.json()['key']
        print("New JIRA Issue created at " + issue_key)

        comment = element.find('comments').text

        attachments = element.find('attachments').text
        if attachments:
            attachments = attachments.split(',')
        else:
            attachments = []

        screenshot = element.find('screenshot').text
        if screenshot:
            attachments.append(screenshot)

        if comment:
            print("Adding comment to issue " + issue_key)
            jira.addIssueComment(issue_key, comment, jira_reporter_name)

        for attachment in attachments:
            tmp = '/tmp/bugherder/'
            if not os.path.exists(tmp):
                os.mkdir(tmp)

            filename = os.path.basename(attachment)
            filepath = os.path.join(tmp, filename)

            if urllib.urlopen(attachment).code == 200:
                print("Adding BugHerd attachment to {0}: {1} ".format(issue_key, attachment))
                urllib.urlretrieve(attachment, filepath)
                jira.addIssueAttachment(issue_key, filepath)

        if element.find('status').text == 'closed':
            print("Updating JIRA issue {0} status to 'done'".format(issue_key))
            jira.updateIssueStatus(issue_key, jira_transition_id, jira_resolution_id)

    return True
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="bugherder",
                                     description="Create JIRA issues in bulk from a BugHerd XML export",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(type=str, help="input XML file path", dest='input', metavar='/path/to')
    
    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    
    jira = JIRA(jira_server, jira_api_username, jira_api_password)

    if not createJIRAIssues(args.input):
        sys.exit(2)


sys.exit(0)
