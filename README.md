# BugHerder #

## What were we trying to solve? ##

Before consolidating to Atlassian JIRA, various departments in JAMF Software used different task-management tools like Trello and BugHerd. IT offered assistance in migrating content from these systems into the department's new JIRA project.

## What does it do? ##

BugHerder takes an XML output from BugHerd and generates JIRA issues within a project.

To migrate the information into a JIRA issue we used the following mapping:

| JIRA Field  | BugHerd Field |
| ------------- | ------------- |
| priority  | priority  |
| summary | summary (with newlines stripped)  |
| description | requester-email, path, os, resolution, browser, browser-size, description |
| labels | tags (string converted to list) |

Comments and attachments are also migrated. Once the JIRA issue has been POSTed, it is then updated. BugHerd's comments are a single block of text and not easily parsed into individual comments, so it was decided to take the BugHerd comment and re-post as-is.

*The JIRA REST API does not allow for comments to be posted on the behalf of another, so the user executing the script appears as the reporter.*

Attachments and screenshots are downloaded from BugHerd into '/tmp/bugherder/' before being uploaded to the JIRA issue.

If the BugHerd issue's status was 'closed', the JIRA issue would finally be updated to a status of 'done' and closed out.

## How to use this script ##

This Python script can be run on Mac, Linux and Windows (Python version 2.7.x tested). The script requires the "requests" module, which you can install on your system or in a virtual environment using the requirements.txt file.

```
pip install -r /path/to/requirements.txt
``` 

You can run the script with the -h argument to view the help text:

```
$ python bugherder.py 
usage: bugherder [-h] /path/to

Create JIRA issues in bulk from a BugHerd XML export

positional arguments:
  /path/to    input XML file path

optional arguments:
  -h, --help  show this help message and exit
```

There are a number of variables you will need to define at the top of the script to correctly generate your JIRA issues. You can find all of these IDs through the admin console or the REST API.

## License ##

```
Copyright (c) 2015, JAMF Software, LLC. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this
      list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this
      list of conditions and the following disclaimer in the documentation and/or
      other materials provided with the distribution.
    * Neither the name of the JAMF Software, LLC nor the names of its contributors
      may be used to endorse or promote products derived from this software without
      specific prior written permission.
      
THIS SOFTWARE IS PROVIDED BY JAMF SOFTWARE, LLC "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL JAMF SOFTWARE,
LLC BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```
