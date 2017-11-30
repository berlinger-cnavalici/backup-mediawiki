#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Script to take care of the internal wiki backup
# Cristian Năvălici

import subprocess
import tempfile
import os.path
import shutil
import logging
import tarfile
import traceback
import sys
import hashlib
import requests
from datetime import datetime, date
import argparse

VERSION = '1.0 27 Nov 2017'

BASEPATH = os.path.dirname(os.path.realpath(__file__))
if not os.path.isfile(os.path.join(BASEPATH, 'configuration.py')):
    print 'The configuration file is missing. Copy or rename', \
          'configuration.dist.py to configuration.py and try again.'
    raise SystemExit
else:
    import configuration


def do_mediawiki_backup(workplace):
    """Creates the backup, db + files of mediawiki"""
    sqlcmd = [
        "/usr/bin/mysqldump",
        "--routines",
        "--user={}".format(configuration.DB_USER),
        "--password={}".format(configuration.DB_PASSWORD),
        "{}".format(configuration.MK_DATABASE)
    ]

    dumpfile = open(os.path.join(workplace, configuration.MK_DUMPFILE), "w")
    subprocess.call(sqlcmd, stdout=dumpfile)
    dumpfile.close()
    logging.info("DB Backup finished, dumped file {}".format(
        os.path.realpath(dumpfile.name)))

    # Part II Copy the files
    shutil.copytree(configuration.MK_FILES, os.path.join(workplace, "_files"))
    logging.info("Finished to copy over Mediawiki files for backup")


def create_encrypted_archive(workplace):
    """
    Creates an archive and encrypts it. It saved the sha256 hash into a
    separated file for future reference
    :return The full path to the encrypted file
    :rtype string
    """
    archname = "mediawiki_archive_{}.tar.gz".format(
        datetime.today().__str__()[:19].replace(' ', '_'))
    archpath = os.path.join(workplace, archname)

    tar = tarfile.open(archpath, "w:gz")
    tar.add(workplace, arcname="MediaWikiBackup")
    tar.close()

    # encryption
    enccmd = "gpg -c --batch --cipher-algo AES256 --passphrase {} {}".format(
        configuration.ARCHIVE_PASSWORD, archpath)
    subprocess.check_call([enccmd], shell=True)

    # checksum written to file
    archgpg = archname + ".gpg"
    checksumfile = open(get_absolute_path(configuration.CHECKSUM_REPO), "a")
    sha1hash = sha1_hash_file(os.path.join(workplace, archgpg))
    checksumfile.write("{} {}\n".format(sha1hash, archgpg))
    checksumfile.close()

    logging.info("Encrypted archive created {}".format(archgpg))

    return os.path.join(workplace, archgpg)


def upload_to_cloud(archive_full_path):
    """Upload to cloud using the b2 command-line utility"""
    # first authorize
    authcmd = [
        "/usr/local/bin/b2",
        "authorize-account",
        "{}".format(configuration.B2_ACCOUNT_KEY),
        "{}".format(configuration.B2_APP_KEY)
    ]
    subprocess.call(authcmd)

    # upload file
    uploadcmd = [
        "/usr/local/bin/b2",
        "upload-file",
        "{}".format(configuration.B2_BUCKET_NAME),
        "{}".format(archive_full_path),
        "{}".format(os.path.basename(archive_full_path)),
    ]
    try:
        subprocess.check_call(uploadcmd)
        return True
    except CalledProcessError as e:
        logging.error(e)
        return False


def send_email(subject, content):
    """Generic email sending function"""
    headers = {
        'Authorization': 'Bearer {}'.format(configuration.SG_API_KEY)
    }

    data = {
        'personalizations': [{
            "to": [{
                "email": configuration.SG_TO_EMAIL,
                "name": configuration.SG_TO_NAME
            }]
        }],
        'from': {
            "email": configuration.SG_FROM_EMAIL,
            "name": configuration.SG_FROM_NAME
        },
        'subject': subject,
        'content': [{
            "type": "text/html",
            "value": "<html>{}</html>".format(content)
        }]
    }

    r = requests.post('https://api.sendgrid.com/v3/mail/send', headers=headers,
                      json=data)
    # r.status_code == 202 # success


def notify_success(archive_full_path):
    """Sends an notification when operations were successful"""
    subject = 'MediaWiki Backup Successful {}'.format(date.today().isoformat())
    size = os.path.getsize(archive_full_path) / (1024 * 1024)
    msg = '<p>Mediawiki archive created: {} ({} MB)</p>'.format(
        os.path.basename(archive_full_path), size)
    send_email(subject, msg)


def notify_failure(msg):
    """Sends a notification when operations failed"""
    subject = 'MediaWiki Backup FAILED {}'.format(date.today().isoformat())
    send_email(subject, msg)


def sha1_hash_file(target):
    """Helper function to hash a file"""
    sha1 = hashlib.sha1()

    with open(target, "rb") as f:
        while True:
            data = f.read(1048576)  # 1 MB at the time
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()


def get_absolute_path(target_file):
    """Gets the full path of the specified file
    for relative, the basepath is the script folder
    """
    if not os.path.isabs(target_file):
        target_file = os.path.join(BASEPATH, target_file)

    return target_file


def run():
    """The controller for all operations"""
    try:
        workplace = tempfile.mkdtemp()

        logging.info("BACKUP STARTED. Workplace: {}".format(workplace))

        do_mediawiki_backup(workplace)
        archive_full_path = create_encrypted_archive(workplace)
        result = upload_to_cloud(archive_full_path)

        if result:
            notify_success(archive_full_path)
        else:
            notify_failure(
                "Upload to cloud failed. Check logs for details and retry.")

        # cleanup
        shutil.rmtree(workplace)

        logging.info("BACKUP ENDED")
    except Exception as e:
        print "ERROR: Something went wrong. Details below:"
        print e

        ex_type, ex, tb = sys.exc_info()
        traceback.print_tb(tb)

        notify_failure(e)
        logging.error(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Script used to backup MEDIAWIKI installation.')

    parser.add_argument("run", help="Trigger the whole operation")
    parser.add_argument("--version", action='version',
                        version='%(prog)s ' + VERSION)
    args = parser.parse_args()

    if not args or args.run != 'run':
        parser.print_usage()
    else:
        logging.basicConfig(filename=get_absolute_path(configuration.LOG_FILE),
                            level=logging.DEBUG,
                            format='[%(asctime)s] [%(levelname)s] %(message)s')
        run()
