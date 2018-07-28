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
import run
import csv
    
file_name = '../scraper_list.csv'
headers = [ 'scraper', 'base_type', 'scraper_type', 'module_name',
        'class_name', 'disabled', 'uid_only', 'uid_num', 'comment' ]

print "Writing scraper list to %s ... " % file_name

""" get a csv status table for all current scrapers """
result = run.all_scraper_attributes()
with open(file_name, 'wb') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=headers)
    writer.writeheader()
    for key in sorted(result.iterkeys()):
        out = {}
        for h in headers:
            out[h] = result[key][h]
        if out['class_name'].endswith('OldScraper') == False and out['class_name'].endswith('NewScraper') == False:
            writer.writerow(out)
        
print "Finished"
    
