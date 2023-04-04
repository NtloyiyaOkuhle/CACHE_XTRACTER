from __future__ import print_function
import argparse
import csv
import os
import sqlite3
import sys
import json


def write_csv(data, output):
    print("[+] Writing {} contacts to {}".format(len(data), output))
    with open(output, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            "URL", "First Visit (UTC)", "Last Visit (UTC)",
            "Last Sync (UTC)", "Location", "Contact Name", "Bday",
            "Anniversary", "Emails", "Phones", "Links", "Company", "Title",
            "Notes", "Total Contacts", "Count of Contacts in Cache"])
        csv_writer.writerows(data)


def main(database, out_csv):
    print("[+] Connecting to SQLite database")
    conn = sqlite3.connect(database)
    c = conn.cursor()

    print("Querying IEF database for Yahoo Contact Fragments from the Chrome Cache Records Table")
    try:
        c.execute("select * from 'Chrome Cache Records' where URL like 'https://data.mail.yahoo.com/classicab/v2/contacts/?format=json%'")
    except sqlite3.OperationalError:
        print("Received an error querying the database -- database may be corrupt or not have a Chrome Cache Records table")
        sys.exit(2)
    contact_cache = c.fetchall()
    contact_data = process_contacts(contact_cache)
    write_csv(contact_data, out_csv)


def process_contacts(contact_cache):
    print("[+] Processing {} cache files matching Yahoo contact cache data".format(len(contact_cache)))
    results = []
   
    for contact in contact_cache:
        url = contact[0]
        first_visit = contact[1]
        last_visit = contact[2]
        last_sync = contact[3]
        loc = contact[8]
        contact_json = json.loads(contact[7].decode())
        total_contacts = contact_json["total"]
        total_count = contact_json["count"]
      
        if "contacts" not in contact_json:
            continue
        for c in contact_json["contacts"]:
            name, anni, bday, emails, phones, links = ("", "", "", "", "", "")
            if "name" in c:
                name = c["name"]["givenName"] + " " + c["name"]["middleName"] + " " + c["name"]["familyName"]
            
            if "anniversary" in c:
                anni = c["anniversary"]["month"] + "/" + c["anniversary"]["day"] + "/" + c["anniversary"]["year"]
            
            if "birthday" in c:
                bday = c["birthday"]["month"] + "/" + c["birthday"]["day"] + "/" + c["birthday"]["year"]
            
            if "emails" in c:
                emails = ', '.join([x["ep"] for x in c["emails"]])
            
            if "phones" in c:
                phones = ', '.join([x["ep"] for x in c["phones"]])
            
            if "links" in c:
                links = ', '.join([x["ep"] for x in c["links"]])

            company = c.get("company", "")
            title = c.get("jobTitle", "")
            notes = c.get("notes", "")

            results.append([url, first_visit, last_visit, last_sync, loc, name, bday, anni, emails, phones, links, company, title, notes, total_contacts, total_count])
    return results

if __name__ == '__main__':
   parser = argparse.ArgumentParser('IEF to CSV')
   parser.add_argument("IEF_DATABASE", help="Input IEF database")
   parser.add_argument("OUTPUT_DIR", help="Output DIR")
   args = parser.parse_args()
