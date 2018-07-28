#!/usr/bin/env python
"""
Copyright (C) 2013-2017  Andrew Speakman

This file is part of UKPlanning, a library of scrapers for UK planning applications

UKPlanning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

UKPlanning is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>."""
import subprocess
from datetime import date
import os

def git_tag(version, message=None, commit=None):
    if not message:
        source = os.path.basename(__file__) # file name of module
        today = date.today().isoformat()
        message = "Tagged by %s on %s" % (source, today)
    if version.startswith('v') or version.startswith('V'):
        git_ver = 'V' + version[1:]
    else:
        git_ver = 'V' + version
    if not commit: # if commit is not supplied, find it from current HEAD 
        commit = get_commit()
    try:
        cmd = 'git tag -a -f %s %s -m "%s"' % (git_ver, commit, message)        
        subprocess.check_output(cmd) # forces replace if it exists
    except subprocess.CalledProcessError:
        raise RuntimeError("Cannot add/replace git tag using: %s" % cmd)
    return git_ver, message
    
def get_commit(version=None):
    if not version:
        version = 'HEAD'
    try:
        cmd = 'git rev-parse --verify --short %s' % version
        commit = subprocess.check_output(cmd)
        commit = commit.split() # split on white space
        if len(commit) > 0:
            return commit[0]
        else:
            raise RuntimeError("Cannot find %s commit using: %s" % (version, cmd))
    except subprocess.CalledProcessError:
        raise RuntimeError("Cannot find %s commit using: %s" % (version, cmd))

def get_tags():
    try:
        tags = subprocess.check_output('git tag -l -n1') # includes first line of message
        tags = tags.split('\n') # split on new lines
    except subprocess.CalledProcessError:
        raise RuntimeError("Cannot find current git tags using: %s" % cmd)
    result = []
    for t in tags:
        t = t.split() # split on spaces/tabs
        if not t:
            continue # empty line at end
        tag = t[0]
        message = " ".join(t[1:])
        commit = get_commit(tag)
        result.append((tag, commit, message))
    return result
    
        
def print_tags():
    for t in get_tags():
        print "%s\t%s\t%s" % t
        

    