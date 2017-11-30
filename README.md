# BACKUPS MEDIAWIKI

## Description

This script is used to make an encrypted package out of the mediawiki database and files, and then upload it to the cloud storage provider. It also has capabilities for email notifications and logging.

## Requirements

  - Install [B2 command line] tool from BackBlaze
  - python 2.7
  - Install [Requests] (pip install requests)
  - B2 bucket should be created in advance

    [Requests]: <http://docs.python-requests.org/en/master/>
    [B2 command line]: <https://www.backblaze.com/b2/docs/quick_command_line.html>

## How it's working

The script will doing a couple of things in this order:
- gather together a dump of the mediawiki database and the MK files from the installation and combine them into a single file (archive).
- the archive is encrypted using a symmetrical (gpg) encryption (aka with a password).
- save the sha1 hash of the file in the designated file (default: _data/checksums.txt_)
- upload the encrypted to BackBlaze B2 cloud storage (bucket: _wikiBackups_)
- notify by email (Sendgrid is used) the designated recipient about the result of the backup procedure
- remove the temporary files from the disk
- all the operations are logged in a local file (default: _data/backupmk.log_)

## Default configuration

Before the first run, you have to make sure the configuration file is up-to-date with all the required elements. The description of those elements is to be found in _configuration.py_

## How to run it

    python backup_mediawiki.py run

or if it's executable:

    ./backup_mediawiki.py run

## Restore a backup

In order to restore a backup, download the file from B2 cloud (probably the easiest way is just to use the webUI) and
then decrypt the file as:

    gpg --decrypt mediawiki_archive_2017-11-28_14_59_49.tar.gz.gpg > mediawiki_archive_2017-11-28_14_59_49.tar.gz
    tar xzf mediawiki_archive_2017-11-28_14_59_49.tar.gz

Now, if everything was done correctly, you should have a folder called _MediaWikiBackup_ with all the saved data.
