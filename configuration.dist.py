# -*- coding: utf-8 -*-

# Mediawiki details (the dump file will be included in the archive)
MK_DATABASE = 'wikidb'
MK_FILES = '/var/www/mediawiki'
MK_DUMPFILE = 'wikidb.sql'

DB_USER = 'XXXXX'
DB_PASSWORD = 'XXXXX'

# the log file used by the script (it will not be truncated every time)
# it should be either absolute path or relative to the script folder
# the destination folder should exist!
LOG_FILE = 'data/backupmk.log'

# password used with the symmetrical encryption
ARCHIVE_PASSWORD = 'XXXXX'

# the file containing checksums for archives (sha256)
# it should be either absolute path or relative to the script folder
# the destination folder should exist!
CHECKSUM_REPO = 'data/checksums.txt'

# backblaze b2 credentials
B2_ACCOUNT_KEY = 'XXXXX'
B2_APP_KEY = 'XXXXX'
B2_BUCKET_NAME = 'wikiBackups'

# SendGrid (for notifications)
SG_API_KEY = 'SG.XXXXX.XXXXX'
SG_TO_NAME = 'Development Team'
SG_TO_EMAIL = 'development@antaris-solutions.net'
SG_FROM_EMAIL = "noreply@antaris-solutions.net"
SG_FROM_NAME = "Backups Mediawiki"
