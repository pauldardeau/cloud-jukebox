#******************************************************************************
# Cloud jukebox
# Copyright Paul Dardeau, SwampBits LLC, 2014
# BSD license -- see LICENSE file for details
#
# This cloud jukebox uses an abstract object storage system.
#
# (1) create a directory for the jukebox (e.g., ~/jukebox)
# (2) copy this source file to $JUKEBOX
# (3) create subdirectory for song imports (e.g., mkdir $JUKEBOX/import)
# (4) create subdirectory for playlist (e.g., mkdir $JUKEBOX/playlist)
#
# Song file naming convention:
#
# The-Artist-Name--The-Song-Name.ext
#       |         |       |       |
#       |         |       |       |----  file extension (e.g., 'mp3')
#       |         |       |
#       |         |       |---- name of the song with ' ' replaced with '-'
#       |         |
#       |         |---- double dashes to separate the artist name and song name
#       |
#       |---- artist name with ' ' replaced with '-'
#
# For example, the MP3 version of the song 'Under My Thumb' from artist 'The
# Rolling Stones' should be named:
#
#   The-Rolling-Stones--Under-My-Thumb.mp3
#
# first time use (or when new songs are added):
# (1) copy one or more song files to $JUKEBOX/import
# (2) import songs with command: 'python jukebox.py import'
#
# show song listings:
# python jukebox.py list-songs
#
# play songs:
# python jukebox.py play
#
#******************************************************************************

import datetime
import hashlib
import optparse
import os
import os.path
import sqlite3
import sys
import threading
import time
import zlib
from subprocess import Popen

try:
   from Crypto.Cipher import AES
   import struct
   encryptionSupport = 1
except ImportError:
   encryptionSupport = 0
   
import StorageSystem
from StorageSystem import Swift_StorageSystem
from StorageSystem import S3_StorageSystem

#******************************************************************************
#******************************************************************************

class AESBlockEncryption:
   
   #***************************************************************************

   def __init__(self,keySizeBytes, key,iv):
      self.key = key            # 32 bytes for AES-256
      self.iv = iv              # must be block_size bytes long (16 bytes)
      self.mode = AES.MODE_CBC  # Cipher-Block Chaining
      self.keySizeBytes = keySizeBytes    # AES-256
      self.ivLength = 16        # initialization vector length

      if self.key is not None:
         keyLength = len(self.key)
         if keyLength == 0:
            raise Exception('encryption key cannot be empty')
         else:
            if keyLength > self.keySizeBytes:
               # substring (shorten) it
               self.key = self.key[0:self.keySizeBytes]
            elif keyLength < self.keySizeBytes:
               # pad it
               self.key = self.key.ljust(self.keySizeBytes, '#')
            else:
               # already the required length
               pass
      else:
         raise Exception('encryption key must be provided')

      if self.iv is not None:
         ivLength = len(self.iv)
         if ivLength == 0:
            self.iv = None
         else:
            if ivLength > self.ivLength:
               # substring (shorten) it
               self.iv = self.iv[0:self.ivLength]
            elif ivLength < self.ivLength:
               # pad it
               self.iv = self.iv.ljust(self.ivLength, '@')
            else:
               # already the required length
               pass

   #***************************************************************************

   def encrypt(self, plainText):
      # the string to encrypt must be a multiple of 16
      numExtraChars = len(plainText) % 16
      if numExtraChars > 0:
         paddedText = plainText + "".ljust(16-numExtraChars,' ')
      else:
         paddedText = plainText
      aesCipher = AES.new(self.key, self.mode, self.iv)
      aesCipher.key_size = self.keySizeBytes
      return aesCipher.encrypt(paddedText)

   #***************************************************************************

   def decrypt(self, cipherText):
      aesCipher = AES.new(self.key, self.mode, self.iv)
      aesCipher.key_size = self.keySizeBytes
      return aesCipher.decrypt(cipherText).rstrip()

   #***************************************************************************

#******************************************************************************
#******************************************************************************

class SongFileInfo:
   
   #***************************************************************************

   def __init__(self):
      self.uid = ""
      self.artistName = ""
      self.songName = ""
      self.originFileSize = 0
      self.storedFileSize = 0
      self.padCharCount = 0
      self.fileDate = ""
      self.md5 = ""
      self.compressed = 0
      self.encrypted = 0
      self.container = ""
      self.objectName = ""

   #***************************************************************************
   
   def __eq__(self, other):
      return self.uid == other.uid and \
               self.artistName == other.artistName and \
               self.songName == other.songName and \
               self.originFileSize == other.originFileSize and \
               self.storedFileSize == other.storedFileSize and \
               self.padCharCount == other.padCharCount and \
               self.fileTime == other.fileTime and \
               self.md5 == other.md5 and \
               self.compressed == other.compressed and \
               self.encrypted == other.encrypted and \
               self.container == other.container and \
               self.objectName == other.objectName

   #***************************************************************************
   
   def fromDictionary(self, dictionary, prefix):
      if dictionary is not None:
         if prefix is None:
            prefix = ""
            
         if dictionary.has_key(prefix + "uid"):
            self.uid = dictionary[prefix+"uid"]
         if dictionary.has_key(prefix + "artistName"):
            self.artistName = dictionary[prefix+"artistName"]
         if dictionary.has_key(prefix + "songName"):
            self.songName = dictionary[prefix+"songName"]
         if dictionary.has_key(prefix + "originFileSize"):
            self.originFileSize = dictionary[prefix+"originFileSize"]
         if dictionary.has_key(prefix + "storedFileSize"):
            self.storedFileSize = dictionary[prefix+"storedFileSize"]
         if dictionary.has_key(prefix + "padCharCount"):
            self.padCharCount = dictionary[prefix+"padCharCount"]
         if dictionary.has_key(prefix + "fileDate"):
            self.fileDate = dictionary[prefix+"fileDate"]
         if dictionary.has_key(prefix + "md5"):
            self.md5 = dictionary[prefix+"md5"]
         if dictionary.has_key(prefix + "compressed"):
            self.compressed = dictionary[prefix+"compressed"]
         if dictionary.has_key(prefix + "encrypted"):
            self.encrypted = dictionary[prefix+"encrypted"]
         if dictionary.has_key(prefix + "container"):
            self.container = dictionary[prefix+"container"]
         if dictionary.has_key(prefix + "objectName"):
            self.objectName = dictionary[prefix+"objectName"]

   #***************************************************************************
   
   def toDictionary(self, prefix):
      dict = {}
      
      if prefix is None:
         prefix = ""
         
      dict[prefix+"uid"] = self.uid
      dict[prefix+"artistName"] = self.artistName
      dict[prefix+"songName"] = self.songName
      dict[prefix+"originFileSize"] = self.originFileSize
      dict[prefix+"storedFileSize"] = self.storedFileSize
      dict[prefix+"padCharCount"] = self.padCharCount
      dict[prefix+"fileDate"] = self.fileDate
      dict[prefix+"md5"] = self.md5
      dict[prefix+"compressed"] = self.compressed
      dict[prefix+"encrypted"] = self.encrypted
      dict[prefix+"container"] = self.container
      dict[prefix+"objectName"] = self.objectName
      
      return dict

   #***************************************************************************
   
   def getPadCharCount(self):
      return self.padCharCount

   #***************************************************************************
      
   def setPadCharCount(self, padCharCount):
      self.padCharCount = padCharCount

   #***************************************************************************

   def getUid(self):
      return self.uid

   #***************************************************************************
      
   def setUid(self, uid):
      self.uid = uid

   #***************************************************************************
      
   def getArtistName(self):
      return self.artistName

   #***************************************************************************
      
   def setArtistName(self, artistName):
      self.artistName = artistName

   #***************************************************************************
   
   def getSongName(self):
      return self.songName

   #***************************************************************************
      
   def setSongName(self, songName):
      self.songName = songName

   #***************************************************************************

   def getOriginFileSize(self):
      return self.originFileSize

   #***************************************************************************
      
   def setOriginFileSize(self, originFileSize):
      self.originFileSize = originFileSize

   #***************************************************************************

   def getStoredFileSize(self):
      return self.storedFileSize

   #***************************************************************************
      
   def setStoredFileSize(self, storedFileSize):
      self.storedFileSize = storedFileSize

   #***************************************************************************

   def getFileTime(self):
      return self.fileTime

   #***************************************************************************
      
   def setFileTime(self, fileTime):
      self.fileTime = fileTime

   #***************************************************************************

   def getMD5(self):
      return self.md5

   #***************************************************************************
      
   def setMD5(self, md5):
      self.md5 = md5

   #***************************************************************************

   def getCompressed(self):
      return self.compressed

   #***************************************************************************
      
   def setCompressed(self, compressed):
      self.compressed = compressed

   #***************************************************************************

   def getEncrypted(self):
      return self.encrypted

   #***************************************************************************
      
   def setEncrypted(self, encrypted):
      self.encrypted = encrypted

   #***************************************************************************

   def getContainer(self):
      return self.container

   #***************************************************************************
      
   def setContainer(self, container):
      self.container = container

   #***************************************************************************

   def getObjectName(self):
      return self.objectName

   #***************************************************************************
      
   def setObjectName(self, objectName):
      self.objectName = objectName

   #***************************************************************************

#******************************************************************************
#******************************************************************************

class SongDownloader(threading.Thread):

   #***************************************************************************

   def __init__(self, jukebox, listSongs):
      super(SongDownloader, self).__init__()
      self.jukebox = jukebox
      self.listSongs = listSongs

   #***************************************************************************
      
   def run(self):
      if self.jukebox is not None and self.listSongs is not None:
         self.jukebox.batchDownloadStart()
         
         for songInfo in self.listSongs:
            startDownloadTime = time.time()
            self.jukebox.downloadSong(songInfo)
            
         self.jukebox.batchDownloadComplete()

   #***************************************************************************

#******************************************************************************
#******************************************************************************

class JukeboxOptions:

   #***************************************************************************

   def __init__(self):
      self.debugMode = 0
      self.useEncryption = 0
      self.useCompression = 0
      self.checkDataIntegrity = 0
      self.fileCacheCount = 3
      self.numberSongs = 0
      self.encryptionKey = ""
      self.encryptionKeyFile = ""
      self.encryptionIV = ""

   #***************************************************************************
   
   def validateOptions(self):
      if self.fileCacheCount < 0:
         print "error: file cache count must be non-negative integer value"
         return 0

      if len(self.encryptionKeyFile) > 0 and not os.path.isfile(self.encryptionKeyFile):
         print "error: encryption key file doesn't exist '%s'" % (self.encryptionKeyFile)
         return 0

      if self.useEncryption:
         if not encryptionSupport:
            print "encryption support not available. please install Crypto.Cipher for encryption support (pycrypto-2.6.1)"
            return 0
            
         if len(self.encryptionKey) == 0 and len(self.encryptionKeyFile) == 0:
            print "error: encryption key or encryption key file is required for encryption"
            return 0

      return 1

   #***************************************************************************

   def getCheckDataIntegrity(self):
      return self.checkDataIntegrity

   #***************************************************************************
   
   def setCheckDataIntegrity(self, checkDataIntegrity):
      self.checkDataIntegrity = checkDataIntegrity

   #***************************************************************************
      
   def getDebugMode(self):
      return self.debugMode

   #***************************************************************************
   
   def setDebugMode(self, debugMode):
      self.debugMode = debugMode

   #***************************************************************************

   def getUseEncryption(self):
      return self.useEncryption

   #***************************************************************************
   
   def setUseEncryption(self, useEncryption):
      self.useEncryption = useEncryption

   #***************************************************************************
      
   def getUseCompression(self):
      return self.useCompression

   #***************************************************************************
      
   def setUseCompression(self, useCompression):
      self.useCompression = useCompression

   #***************************************************************************

   def getEncryptionKey(self):
      return self.encryptionKey

   #***************************************************************************
   
   def setEncryptionKey(self, encryptionKey):
      self.encryptionKey = encryptionKey

   #***************************************************************************

   def getEncryptionKeyFile(self):
      return self.encryptionKeyFile

   #***************************************************************************
   
   def setEncryptionKeyFile(self, encryptionKeyFile):
      self.encryptionKeyFile = encryptionKeyFile

   #***************************************************************************

   def getEncryptionIV(self):
      return self.encryptionIV

   #***************************************************************************
   
   def setEncryptionIV(self, encryptionIV):
      self.encryptionIV = encryptionIV

   #***************************************************************************

   def getFileCacheCount(self):
      return self.fileCacheCount

   #***************************************************************************
   
   def setFileCacheCount(self, fileCacheCount):
      self.fileCacheCount = fileCacheCount

   #***************************************************************************

#******************************************************************************
#******************************************************************************

class Jukebox:

   #***************************************************************************
   
   def __init__(self, jukeboxOptions, storageSystem, debugPrint=0):
      
      self.jukeboxOptions = jukeboxOptions
      self.storageSystem = storageSystem
      self.debugPrint = debugPrint
      self.dbConnection = None
      self.currentDir = os.getcwd()
      self.importDir = os.path.join(self.currentDir, 'import')
      self.playlistDir = os.path.join(self.currentDir, 'playlist')
      self.downloadExtension = ".download"
      self.metaDataDBFile = 'jukebox_db.sqlite3'
      self.metaDataContainer = 'music-metadata'
      self.songList = []
      self.songIndex = -1
      self.audioPlayerCommandArgs = []
      self.songPlayLengthSeconds = 20
      self.cumulativeDownloadBytes = 0
      self.cumulativeDownloadTime = 0
      
      if jukeboxOptions is not None and jukeboxOptions.getDebugMode():
         self.debugPrint = 1
      
      if self.debugPrint:
         print "self.currentDir = '%s'" % (self.currentDir)
         print "self.importDir = '%s'" % (self.importDir)
         print "self.playlistDir = '%s'" % (self.playlistDir)
   
   #***************************************************************************
      
   def __enter__(self):
      # look for stored metadata in the storage system
      if self.storageSystem.hasContainer(self.metaDataContainer):
         # metadata container exists, retrieve container listing
         containerContents = self.storageSystem.listContainerContents(self.metaDataContainer)
         
         # does our metadata DB file exist in the metadata container?
         if containerContents is not None and self.metaDataDBFile in containerContents:
            # download it
            metaDataDBFilePath = self.getMetaDataDBFilePath()
            downloadFile = metaDataDBFilePath + ".download"
            if self.storageSystem.retrieveFile(self.metaDataContainer, self.metaDataDBFile, downloadFile) > 0:
               # have an existing metadata DB file?
               if os.path.exists(metaDataDBFilePath):
                  if self.debugPrint:
                     print "deleting existing metadata DB file"
                  os.remove(metaDataDBFilePath)
               # rename downloaded file
               if self.debugPrint:
                  print "renaming '%s' to '%s'" % (downloadFile, metaDataDBFilePath)
               os.rename(downloadFile, metaDataDBFilePath)
            else:
               if self.debugPrint:
                  print "error: unable to retrieve metadata DB file"
         else:
            if self.debugPrint:
               print "no metadata DB file in metadata container"
      else:
         if self.debugPrint:
            print "no metadata container in storage system"

      self.dbConnection = sqlite3.connect(self.getMetaDataDBFilePath())
      if self.dbConnection is not None:
         if self.debugPrint:
            print "have db connection"
            
         if not self.haveTables():
            if not self.createTables():
               print "unable to create tables"
               sys.exit(1)
      else:
         print "unable to connect to database"
      return self

   #***************************************************************************

   def __exit__(self, type, value, traceback):
      if self.dbConnection is not None:
         self.dbConnection.close()
         self.dbConnection = None

   #***************************************************************************
   
   def getMetaDataDBFilePath(self):
      return os.path.join(self.currentDir, self.metaDataDBFile)

   #***************************************************************************
      
   def unencodeValue(self, encodedValue):
      return encodedValue.replace('-', ' ')

   #***************************************************************************
   
   def artistAndSongFromFileName(self, fileName):
      posExtension = fileName.find('.')
      if posExtension > -1:
         baseFileName = fileName[0:posExtension]
      else:
         baseFileName = fileName
         
      components = baseFileName.split('--')
      if len(components) == 2:
         encodedArtist = components[0]
         encodedSong = components[1]
         return [self.unencodeValue(encodedArtist), self.unencodeValue(encodedSong)]
      else:
         return None

   #***************************************************************************
   
   def artistFromFileName(self, fileName):
      if (fileName is not None) and (len(fileName) > 0):
         components = self.artistAndSongFromFileName(fileName)
         if components is not None and len(components) == 2:
            return components[0]
         else:
            return None
      else:
         return None

   #***************************************************************************
      
   def songFromFileName(self, fileName):
      if (fileName is not None) and (len(fileName) > 0):
         components = self.artistAndSongFromFileName(fileName)
         if len(components) == 2:
            return components[1]
         else:
            return None
      else:
         return None

   #***************************************************************************
   
   def createTables(self):
      if self.dbConnection is not None:
         if self.debugPrint:
            print "creating tables"
         
         sql = 'CREATE TABLE song (uid text, filetime text, origin_filesize integer, stored_filesize integer, padchar_count integer, artist text, songname text, md5 text, compressed integer, encrypted integer, container text, objectname text)'
         try:
            self.dbConnection.execute(sql)
            return 1
         except sqlite3.Error as e:
            print 'error creating table: ' + e.args[0]

      return 0

   #***************************************************************************

   def haveTables(self):
      haveTablesInDB = 0
      if self.dbConnection is not None:
         sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='song'"
         cursor = self.dbConnection.cursor()
         cursor.execute(sql)
         name = cursor.fetchone()
         if name is not None:
            haveTablesInDB = 1
         
      return haveTablesInDB

   #***************************************************************************

   def getSongInfo(self, fileName):
      if self.dbConnection is not None:
         sql = "SELECT filetime, origin_filesize, stored_filesize, padchar_count, artist, songname, md5, compressed, encrypted, container, objectname FROM song WHERE uid = ?"
         cursor = self.dbConnection.cursor()
         cursor.execute(sql, [fileName])
         songFields = cursor.fetchone()
         if songFields is not None:
            songInfo = SongFileInfo()
            songInfo.setUid(fileName)
            songInfo.setFileTime(songFields[0])
            songInfo.setOriginFileSize(songFields[1])
            songInfo.setStoredFileSize(songFields[2])
            songInfo.setPadCharCount(songFields[3])
            songInfo.setArtistName(songFields[4])
            songInfo.setSongName(songFields[5])
            songInfo.setMD5(songFields[6])
            songInfo.setCompressed(songFields[7])
            songInfo.setEncrypted(songFields[8])
            songInfo.setContainer(songFields[9])
            songInfo.setObjectName(songFields[10])
            return songInfo

      return None

   #***************************************************************************
   
   def insertSongInfo(self, songFileInfo):
      insertSuccess = 0
      
      if (self.dbConnection is not None) and (songFileInfo is not None):
         sql = "INSERT INTO song VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
         cursor = self.dbConnection.cursor()
         sfi = songFileInfo  # alias to save typing
         uid = sfi.getUid()
         fileTime = sfi.getFileTime()
         originFileSize = sfi.getOriginFileSize()
         storedFileSize = sfi.getStoredFileSize()
         padCharCount = sfi.getPadCharCount()
         artist = sfi.getArtistName()
         song = sfi.getSongName()
         md5 = sfi.getMD5()
         compressed = sfi.getCompressed()
         encrypted = sfi.getEncrypted()
         container = sfi.getContainer()
         objectName = sfi.getObjectName()
         
         try:
            cursor.execute(sql, [uid, fileTime, originFileSize, storedFileSize, padCharCount, artist, song, md5, compressed, encrypted, container, objectName])
            self.dbConnection.commit()
            insertSuccess = 1
         except sqlite3.Error as e:
            print "error inserting song: " + e.args[0]

      return insertSuccess

   #***************************************************************************
      
   def updateSongInfo(self, songFileInfo):
      updateSuccess = 0

      if (self.dbConnection is not None) and (songFileInfo is not None) and (len(songFileInfo.getUid()) > 0):
         sql = "UPDATE song SET filetime=?, origin_filesize=?, stored_filesize=?, padchar_count=?, artist=?, songname=?, md5=?, compressed=?, encrypted=?, container=?, objectname=? WHERE uid = ?"
         cursor = self.dbConnection.cursor()
         sfi = songFileInfo  # alias to save typing
         uid = sfi.getUid()
         fileTime = sfi.getFileTime()
         originFileSize = sfi.getOriginFileSize()
         storedFileSize = sfi.getStoredFileSize()
         padCharCount = sfi.getPadCharCount()
         artist = sfi.getArtistName()
         song = sfi.getSongName()
         md5 = sfi.getMD5()
         compressed = sfi.getCompressed()
         encrypted = sfi.getEncrypted()
         container = sfi.getContainer()
         objectName = sfi.getObjectName()
         
         try:
            cursor.execute(sql, [fileTime, originFileSize, storedFileSize, padCharCount, artist, song, md5, compressed, encrypted, container, objectName, uid])
            self.dbConnection.commit()
            updateSuccess = 1
         except sqlite3.Error as e:
            print "error updating song: " + e.args[0]
      
      return updateSuccess

   #***************************************************************************
   
   def md5ForFile(self, pathToFile):
      f = open(pathToFile, mode='rb')
      d = hashlib.md5()
      for buf in f.read(4096):
         d.update(buf)
      f.close()
      return d.hexdigest()

   #***************************************************************************
         
   def storeSongMetadata(self, fsSongInfo):
      dbSongInfo = self.getSongInfo(fsSongInfo.getUid())
      if dbSongInfo is not None:
         if fsSongInfo != dbSongInfo:
            return self.updateSongInfo(fsSongInfo)
         else:
            return 1  # no insert or update needed (already up-to-date)
      else:
         # song is not in the database, insert it
         return self.insertSongInfo(fsSongInfo)

   #***************************************************************************
   
   def getEncryptor(self):
      #keyBlockSize = 16  # AES-128
      #keyBlockSize = 24  # AES-192
      keyBlockSize = 32  # AES-256
      return AESBlockEncryption(keyBlockSize, self.jukeboxOptions.getEncryptionKey(), self.jukeboxOptions.getEncryptionIV())

   #***************************************************************************

   def importSongs(self):
      if self.dbConnection is not None:
         dirListing = os.listdir(self.importDir)
         numEntries = float(len(dirListing))
         
         if not self.debugPrint:
            percentComplete = 0
            i = 0
            progressbar_width = 40
            progresschars_per_iteration = progressbar_width / numEntries
            progressbar_chars = 0.0
            progressbar_char = '#'
            bar_chars = 0

            # setup progressbar
            sys.stdout.write("[%s]" % (" " * progressbar_width))
            sys.stdout.flush()
            sys.stdout.write("\b" * (progressbar_width+1)) # return to start of line, after '['
         
         
         encrypting = 0
         compressing = 0
         encryption = None
         
         if self.jukeboxOptions is not None:
            encrypting = self.jukeboxOptions.getUseEncryption()
            compressing = self.jukeboxOptions.getUseCompression()
            if encrypting:
               encryption = self.getEncryptor()
         
         containerSuffix = "-artist-songs"
         appendedFileExt = ""
         
         if encrypting and compressing:
            containerSuffix += "-ez"
            appendedFileExt = ".egz"
         elif encrypting:
            containerSuffix += "-e"
            appendedFileExt = ".e"
         elif compressing:
            containerSuffix += "-z"
            appendedFileExt = ".gz"

         cumulativeUploadTime = 0
         cumulativeUploadBytes = 0
         fileImportCount = 0

         for listingEntry in dirListing:
            fullPath = os.path.join(self.importDir, listingEntry)

            # ignore it if it's not a file
            if os.path.isfile(fullPath):
               fileName = listingEntry
               extension = os.path.splitext(fullPath)[1]
               if len(extension) > 0:
                  lowerExtension = extension.lower()
                  fileSize = os.path.getsize(fullPath)
                  artist = self.artistFromFileName(fileName)
                  if fileSize > 0 and artist is not None:
                     objectName = fileName + appendedFileExt
                     fsSongInfo = SongFileInfo()
                     fsSongInfo.setUid(objectName)
                     fsSongInfo.setOriginFileSize(fileSize)
                     fsSongInfo.setFileTime(datetime.datetime.fromtimestamp(os.path.getmtime(fullPath)))
                     fsSongInfo.setArtistName(artist)
                     fsSongInfo.setSongName(self.songFromFileName(fileName))
                     fsSongInfo.setMD5(self.md5ForFile(fullPath))
                     fsSongInfo.setCompressed(self.jukeboxOptions.getUseCompression())
                     fsSongInfo.setEncrypted(self.jukeboxOptions.getUseEncryption())
                     fsSongInfo.setObjectName(objectName)
                     fsSongInfo.setPadCharCount(0)
                     
                     # get first letter of artist name, ignoring 'A ' and 'The '
                     if artist.startswith('A '):
                        artistLetter = artist[2:3]
                     elif artist.startswith('The '):
                        artistLetter = artist[4:5]
                     else:
                        artistLetter = artist[0:1]
                     
                     container = artistLetter.lower() + containerSuffix
                     
                     fsSongInfo.setContainer(container)
                     
                     # read file contents
                     fileRead = 0
                     fileContents = None
         
                     try:
                        with open(fullPath, 'r') as content_file:
                            fileContents = content_file.read()
                        fileRead = 1
                     except IOError:
                        print "error: unable to read file %s" % (filePath)

                     if fileRead and fileContents is not None:
                        if len(fileContents) > 0:
                           # for general purposes, it might be useful or helpful to have
                           # a minimum size for compressing
                           if compressing:
                              if self.debugPrint:
                                 print "compressing file"

                              compressedContents = zlib.compress(fileContents, 9)
                              fileContents = compressedContents
                           
                           if encrypting:
                              if self.debugPrint:
                                 print "encrypting file"
                              
                              # the length of the data to encrypt must be a multiple of 16
                              numExtraChars = len(fileContents) % 16
                              if numExtraChars > 0:
                                 if self.debugPrint:
                                    print "padding file for encryption"
                                 numPadChars = 16 - numExtraChars
                                 fileContents += "".ljust(numPadChars,' ')
                                 fsSongInfo.setPadCharCount(numPadChars)
                              
                              cipherText = encryption.encrypt(fileContents)
                              fileContents = cipherText
                              
                        # now that we have the data that will be stored, set the file size for
                        # what's being stored
                        fsSongInfo.setStoredFileSize(len(fileContents))
                        
                        startUploadTime = time.time()
                        
                        # store song file to storage system
                        if self.storageSystem.storeSongFile(fsSongInfo, fileContents):
                           
                           endUploadTime = time.time()
                           uploadElapsedTime = endUploadTime - startUploadTime
                           cumulativeUploadTime += uploadElapsedTime
                           cumulativeUploadBytes += len(fileContents)
                           
                           # store song metadata in local database
                           if not self.storeSongMetadata(fsSongInfo):
                              # we stored the song to the storage system, but were unable to store
                              # the metadata in the local database. we need to delete the song
                              # from the storage system since we won't have any way to access it
                              # since we can't store the song metadata locally.
                              self.storageSystem.deleteSongFile(fsSongInfo)
                           else:
                              fileImportCount += 1

            
            if not self.debugPrint:
               progressbar_chars += progresschars_per_iteration
               if int(progressbar_chars) > bar_chars:
                  num_new_chars = int(progressbar_chars) - bar_chars

                  if num_new_chars > 0:
                     # update progress bar
                     for j in xrange(num_new_chars):
                        sys.stdout.write(progressbar_char)
                     sys.stdout.flush()
                     bar_chars += num_new_chars

         if not self.debugPrint:
            # if we haven't filled up the progress bar, fill it now
            if bar_chars < progressbar_width:
               num_new_chars = progressbar_width - bar_chars
               for j in xrange(num_new_chars):
                  sys.stdout.write(progressbar_char)
               sys.stdout.flush()

            sys.stdout.write("\n")
            
         if fileImportCount > 0:
            haveMetaDataContainer = 0
            if not self.storageSystem.hasContainer(self.metaDataContainer):
               haveMetaDataContainer = self.storageSystem.createContainer(self.metaDataContainer)
            else:
               haveMetaDataContainer = 1
               
            if haveMetaDataContainer:
               if self.debugPrint:
                  print "uploading metadata db file to storage system"
                  
               self.dbConnection.close()
               self.dbConnection = None
               
               metaDataDBUpload = self.storageSystem.addFileFromPath(self.metaDataContainer, self.metaDataDBFile, self.getMetaDataDBFilePath())
               
               if self.debugPrint:
                  if metaDataDBUpload:
                     print "metadata db file uploaded"
                  else:
                     print "unable to upload metadata db file"


         print "%s song files imported" % (fileImportCount)

         if cumulativeUploadTime > 0:
            cumulativeUploadKB = cumulativeUploadBytes / 1000.0
            print "average upload throughput = %s KB/sec" % (int(cumulativeUploadKB / cumulativeUploadTime))

   #***************************************************************************
   
   def songPathInPlaylist(self, songInfo):
      return os.path.join(self.playlistDir, songInfo.getUid())

   #***************************************************************************

   def checkFileIntegrity(self, songInfo):
      fileIntegrityPassed = 1
      
      if self.jukeboxOptions is not None and self.jukeboxOptions.getCheckDataIntegrity():
         filePath = self.songPathInPlaylist(songInfo)
         if os.path.exists(filePath):
            if self.debugPrint:
               print "checking integrity for %s" % (songInfo.getUid())

            playlistMD5 = self.md5ForFile(filePath)
            if playlistMD5 == songInfo.getMD5():
               if self.debugPrint:
                  print "integrity check SUCCESS"

               fileIntegrityPassed = 1
            else:
               print "file integrity check failed: %s" % (songInfo.getUid())
               fileIntegrityPassed = 0
         else:
            # file doesn't exist
            print "file doesn't exist"
            fileIntegrityPassed = 0
      else:
         if self.debugPrint:
            print "file integrity bypassed, no jukebox options or check integrity not turned on"
      
      return fileIntegrityPassed

   #***************************************************************************
   
   def batchDownloadStart(self):
      self.cumulativeDownloadBytes = 0
      self.cumulativeDownloadTime = 0

   #***************************************************************************

   def batchDownloadComplete(self):
      if self.cumulativeDownloadTime > 0:
         cumulativeDownloadKB = self.cumulativeDownloadBytes / 1000.0
         print "average download throughput = %s KB/sec" % (int(cumulativeDownloadKB / self.cumulativeDownloadTime))
      self.cumulativeDownloadBytes = 0
      self.cumulativeDownloadTime = 0

   #***************************************************************************

   def downloadSong(self, songInfo):
      if songInfo is not None:
         filePath = self.songPathInPlaylist(songInfo)
         downloadStartTime = time.time()
         songBytesRetrieved = self.storageSystem.retrieveSongFile(songInfo, self.playlistDir)
         
         if self.debugPrint:
            print "bytes retrieved: %s" % (songBytesRetrieved)

         if songBytesRetrieved > 0:
            downloadEndTime = time.time()
            downloadElapsedTime = downloadEndTime - downloadStartTime
            self.cumulativeDownloadTime += downloadElapsedTime
            self.cumulativeDownloadBytes += songBytesRetrieved
            
            # are we checking data integrity?
            # if so, verify that the storage system retrieved the same length that has been stored
            if self.jukeboxOptions is not None and self.jukeboxOptions.getCheckDataIntegrity():
               if self.debugPrint:
                  print "verifying data integrity"

               if songBytesRetrieved != songInfo.getStoredFileSize():
                  print "error: data integrity check failed for '%s'" % (filePath)
                  return 0
            
            
            # is it encrypted? if so, unencrypt it
            encrypted = songInfo.getEncrypted()
            compressed = songInfo.getCompressed()
            
            if encrypted or compressed:
               storageFileContents = None
               try:
                  with open(filePath, 'rb') as content_file:
                     storageFileContents = content_file.read()
               except IOError:
                  print "error: unable to read file %s" % (filePath)
                  return 0
                  
               fileContents = storageFileContents
               
               if encrypted and compressed:
                  fileExt = ".egz"
               elif encrypted:
                  fileExt = ".e"
               else:
                  fileExt = ".gz"
               
               if encrypted:
                  encryption = self.getEncryptor()
                  fileContents = encryption.decrypt(fileContents)

               if compressed:
                  fileContents = zlib.decompress(fileContents)

               # re-write out the uncompressed, unencrypted file contents
               try:
                  with open(filePath, 'wb') as content_file:
                     content_file.write(fileContents)
               except IOError:
                  print "error: unable to write unencrypted/uncompressed file '%s'" % (filePath)
                  return 0

            if self.checkFileIntegrity(songInfo):
               return 1
            else:
               # we retrieved the file, but it failed our integrity check
               # if file exists, remove it
               if os.path.exists(filePath):
                  os.remove(filePath)
         
      return 0

   #***************************************************************************
   
   def getSQLWhereClause(self):
      encryption = 0
      compression = 0
         
      if self.jukeboxOptions is not None:
         if self.jukeboxOptions.getUseEncryption():
            encryption = 1

         if self.jukeboxOptions.getUseCompression():
            compression = 1

      whereClause = ""
      whereClause += " WHERE "
      whereClause += "encrypted = "
      whereClause += str(encryption)
      whereClause += " AND "
      whereClause += "compressed = "
      whereClause += str(compression)
      
      return whereClause

   #***************************************************************************
   
   def getSongs(self):
      songs = []
      if self.dbConnection is not None:
         sql = "SELECT uid, filetime, origin_filesize, stored_filesize, padchar_count, artist, songname, md5, compressed, encrypted, container, objectname FROM song"
         sql += self.getSQLWhereClause()
         
         cursor = self.dbConnection.cursor()
         for row in cursor.execute(sql):
            songInfo = SongFileInfo()
            songInfo.setUid(row[0])
            songInfo.setFileTime(row[1])
            songInfo.setOriginFileSize(row[2])
            songInfo.setStoredFileSize(row[3])
            songInfo.setPadCharCount(row[4])
            songInfo.setArtistName(row[5])
            songInfo.setSongName(row[6])
            songInfo.setMD5(row[7])
            songInfo.setCompressed(row[8])
            songInfo.setEncrypted(row[9])
            songInfo.setContainer(row[10])
            songInfo.setObjectName(row[11])
            
            songs.append(songInfo)
      return songs

   #***************************************************************************
   
   def playSong(self, songFilePath):
      if os.path.exists(songFilePath):
         print "playing %s" % (songFilePath)
         
         songPlaySuccess = 0
         
         if len(self.audioPlayerCommandArgs) > 0:
            cmdArgs = self.audioPlayerCommandArgs[:]
            cmdArgs.append(songFilePath)
            exitCode = -1
            try:
               self.proc = Popen(cmdArgs)
               if self.proc is not None:
                  exitCode = self.proc.wait()
            except OSError:
               # audio player not available
               self.audioPlayerCommandArgs = []
               exitCode = -1

            # if the audio player failed or is not present, just sleep
            # for the length of time that audio would be played
            if exitCode != 0:
               time.sleep(self.songPlayLengthSeconds)
         else:
            # we don't know about an audio player, so simulate a
            # song being played by sleeping
            time.sleep(self.songPlayLengthSeconds)
                  
         # delete the song file from the play list directory
         os.remove(songFilePath)

      else:
         print "song file doesn't exist: '%s'" % (songFilePath)

   #***************************************************************************
   
   def downloadSongs(self):
      # scan the play list directory to see if we need to download more songs
      dirListing = os.listdir(self.playlistDir)
      songFileCount = 0
      for listingEntry in dirListing:
         fullPath = os.path.join(self.playlistDir, listingEntry)
         if os.path.isfile(fullPath):
            fileName = listingEntry
            extension = os.path.splitext(fullPath)[1]
            if len(extension) > 0 and extension != self.downloadExtension:
               songFileCount += 1
               
      fileCacheCount = self.jukeboxOptions.getFileCacheCount()
      
      if songFileCount < fileCacheCount:
         dlSongs = []
         # start looking at the next song in the list
         checkIndex = self.songIndex + 1
         for j in xrange(self.numberSongs):
            if checkIndex >= self.numberSongs:
               checkIndex = 0
                     
            if checkIndex != self.songIndex:
               si = self.songList[checkIndex]
               filePath = self.songPathInPlaylist(si)
               if not os.path.exists(filePath):
                  dlSongs.append(si)
                  if len(dlSongs) >= fileCacheCount:
                     break
                              
            checkIndex += 1
                     
         if len(dlSongs) > 0:
            downloadThread = SongDownloader(self, dlSongs)
            downloadThread.start()

   #***************************************************************************
      
   def playSongs(self):
      self.songList = self.getSongs()
      if self.songList is not None:
         self.numberSongs = len(self.songList)
            
         if self.numberSongs == 0:
            print "no songs in jukebox"
            sys.exit(0)
            
         # does play list directory exist?
         if not os.path.exists(self.playlistDir):
            if self.debugPrint:
               print "playlist directory does not exist, creating it"
            os.makedirs(self.playlistDir)
         else:
            # play list directory exists, delete any files in it
            if self.debugPrint:
               print "deleting existing files in playlist directory"

            for theFile in os.listdir(self.playlistDir):
                filePath = os.path.join(self.playlistDir, theFile)
                try:
                    if os.path.isfile(filePath):
                        os.unlink(filePath)
                except Exception, e:
                    pass

         self.songIndex = 0
         
         if sys.platform == "darwin":
            self.audioPlayerCommandArgs = ["afplay"]
            self.audioPlayerCommandArgs.extend(["-t", str(self.songPlayLengthSeconds)])
         elif os.name == "posix":
            self.audioPlayerCommandArgs = ["mplayer", "-nolirc", "-really-quiet"]
            self.audioPlayerCommandArgs.extend(["-endpos", str(self.songPlayLengthSeconds)])
         else:
            self.audioPlayerCommandArgs = []
         
         print "downloading first song..."
         
         if self.downloadSong(self.songList[0]):
            print "first song downloaded. starting playing now."
            
            while True:
               self.downloadSongs()
               
               self.playSong(self.songPathInPlaylist(self.songList[self.songIndex]))
               
               self.songIndex += 1
               if self.songIndex >= self.numberSongs:
                  self.songIndex = 0
                  
         else:
            print "error: unable to download songs"
            sys.exit(1)

   #***************************************************************************
      
   def showListings(self):
      if self.dbConnection is not None:
         sql = "SELECT artist, songname FROM song "
         sql += self.getSQLWhereClause()
         sql += " ORDER BY artist, songname"
         cursor = self.dbConnection.cursor()
         for row in cursor.execute(sql):
            artist = row[0]
            song = row[1]
            print "%s, %s" % (artist, song)

   #***************************************************************************

   def showListContainers(self):
      if self.storageSystem is not None:
         for containerName in self.storageSystem.getListContainers():
            print containerName

#******************************************************************************
#******************************************************************************

def ShowUsage():
   print 'Usage: python jukebox.py [options] <command>'
   print ''
   print 'Options:'
   print '\t--debug                                - run in debug mode'
   print '\t--file-cache-count <positive integer>  - specify number of songs to buffer in cache'
   print '\t--integrity-checks                     - check file integrity after download'
   print '\t--compress                             - use gzip compression'
   print '\t--encrypt                              - encrypt file contents'
   print '\t--key <encryption_key>                 - specify encryption key'
   print '\t--keyfile <keyfile_path>               - specify path to file containing encryption key'
   print '\t--storage <storage type>               - specifies storage system type (s3 or swift)'
   print ''
   print 'Commands:'
   print '\thelp            - show this help message'
   print '\timport          - import all new songs in import subdirectory'
   print '\tlist-songs      - show listing of all available songs'
   print '\tlist-containers - show listing of all available storage containers'
   print '\tplay            - start playing songs'
   print '\tusage           - show this help message'
   print ''

#******************************************************************************

if __name__ == '__main__':

   isDebugMode = 0
   swift_system = "swift"
   s3_system = "s3"
   storageSystem = swift_system
   
   optParser = optparse.OptionParser()
   
   optKeyDebug             = "debug"
   optKeyFileCacheCount    = "fileCacheCount"
   optKeyIntegrityChecks   = "integrityChecks"
   optKeyCompression       = "compression"
   optKeyEncryption        = "encrypt"
   optKeyEncryptionKey     = "encryptionKey"
   optKeyEncryptionKeyFile = "encryptionKeyFile"
   optKeyStorageType       = "storageType"
   
   optParser.add_option("--debug", action="store_true", dest=optKeyDebug)
   optParser.add_option("--file-cache-count", action="store", type="int", dest=optKeyFileCacheCount)
   optParser.add_option("--integrity-checks", action="store_true", dest=optKeyIntegrityChecks)
   optParser.add_option("--compress", action="store_true", dest=optKeyCompression)
   optParser.add_option("--encrypt", action="store_true", dest=optKeyEncryption)
   optParser.add_option("--key", action="store", type="string", dest=optKeyEncryptionKey)
   optParser.add_option("--keyfile", action="store", type="string", dest=optKeyEncryptionKeyFile)
   optParser.add_option("--storage", action="store", type="string", dest=optKeyStorageType)
   
   opt, args = optParser.parse_args()
   stemVar = "opt."
   optValDebug = eval(stemVar + optKeyDebug)
   optValFileCacheCount = eval(stemVar + optKeyFileCacheCount)
   optValIntegrityChecks = eval(stemVar + optKeyIntegrityChecks)
   optValCompression = eval(stemVar + optKeyCompression)
   optValEncryption = eval(stemVar + optKeyEncryption)
   optValEncryptionKey = eval(stemVar + optKeyEncryptionKey)
   optValEncryptionKeyFile = eval(stemVar + optKeyEncryptionKeyFile)
   optValStorageType = eval(stemVar + optKeyStorageType)
      
   jukeboxOptions = JukeboxOptions()
      
   if optValDebug is not None:
      isDebugMode = 1
      jukeboxOptions.setDebugMode(optValDebug)
      
   if optValFileCacheCount is not None:
      if isDebugMode:
         print "setting file cache count=" + repr(optValFileCacheCount)
            
      jukeboxOptions.setFileCacheCount(optValFileCacheCount)
      
   if optValIntegrityChecks is not None:
      if isDebugMode:
         print "setting integrity checks on"
         
      jukeboxOptions.setCheckDataIntegrity(optValIntegrityChecks)
         
   if optValCompression is not None:
      if isDebugMode:
         print "setting compression on"
            
      jukeboxOptions.setUseCompression(optValCompression)
         
   if optValEncryption is not None:
      if isDebugMode:
         print "setting encryption on"

      jukeboxOptions.setUseEncryption(optValEncryption)
         
   if optValEncryptionKey is not None:
      if isDebugMode:
         print "setting encryption key='%s'" % (optValEncryptionKey)

      jukeboxOptions.setEncryptionKey(optValEncryptionKey)
         
   if optValEncryptionKeyFile is not None:
      if isDebugMode:
         print "reading encryption key file='%s'" % (optValEncryptionKeyFile)

      encryptionKey = ''
      
      try:
         with open(optValEncryptionKeyFile, 'rt') as key_file:
            encryptionKey = key_file.read().strip()
      except IOError:
         print "error: unable to read key file '%s'" % (optValEncryptionKeyFile)
         sys.exit(1)

      if encryptionKey is not None and len(encryptionKey) > 0:
         jukeboxOptions.setEncryptionKey(encryptionKey)
      else:
         print "error: no key found in file '%s'" % (optValEncryptionKeyFile)
         sys.exit(1)

   if optValStorageType is not None:
      if optValStorageType != swift_system and optValStorageType != s3_system:
         print "error: invalid storage type '%s'" % (optValStorageType)
         print "valid values are '%s' and '%s'" % (swift_system, s3_system)
         sys.exit(1)
      else:
         if isDebugMode:
            print "setting storage system to '%s'" % (optValStorageType)
         storageSystem = optValStorageType
         
   if len(args) > 0:
      swift_auth_host = "127.0.0.1"
      swift_account   = ""
      swift_user      = ""
      swift_password  = ""
   
      aws_access_key = ""
      aws_secret_key = ""
      
      container_prefix = "com.swampbits.jukebox."
      
      if storageSystem == swift_system:
         if not StorageSystem.isSwiftAvailable():
            print "error: swift is not supported on this system. please install swiftclient first."
            sys.exit(1)
      elif storageSystem == s3_system:
         if not StorageSystem.isS3Available():
            print "error: s3 is not supported on this system. please install boto (s3 client) first."
            sys.exit(1)

      if isDebugMode:
         print "using storage system type '%s'" % (storageSystem)
         
      creds_file = storageSystem + "_creds.txt"
      dictCreds = {}
      
      creds_file_path = os.path.join(os.getcwd(), creds_file)

      if os.path.exists(creds_file_path):
         if isDebugMode:
            print "reading creds file '%s'" % (creds_file_path)
         try:
            with open(creds_file, 'r') as input_file:
               for line in input_file.readlines():
                  line = line.strip()
                  if len(line) > 0:
                     key,value = line.split("=")
                     key = key.strip()
                     value = value.strip()
                     dictCreds[key] = value
         except IOError:
            if isDebugMode:
               print "error: unable to read file %s" % (creds_file_path)
      else:
         print "no creds file (%s)" % (creds_file_path)

      if storageSystem == swift_system:
         if dictCreds.has_key("swift_auth_host"):
            swift_auth_host = dictCreds["swift_auth_host"]
         if dictCreds.has_key("swift_account"):
            swift_account = dictCreds["swift_account"]
         if dictCreds.has_key("swift_user"):
            swift_user = dictCreds["swift_user"]
         if dictCreds.has_key("swift_password"):
            swift_password = dictCreds["swift_password"]
            
         if isDebugMode:
            print "swift_auth_host='%s'" % (swift_auth_host)
            print "swift_account='%s'" % (swift_account)
            print "swift_user='%s'" % (swift_user)
            print "swift_password='%s'" % (swift_password)
            
         if len(swift_account) == 0 or len(swift_user) == 0 or len(swift_password) == 0:
            print "error: no swift credentials given. please specify swift_account, swift_user, and swift_password in " + creds_file
            sys.exit(1)
            
      elif storageSystem == s3_system:
         if dictCreds.has_key("aws_access_key"):
            aws_access_key = dictCreds["aws_access_key"]
         if dictCreds.has_key("aws_secret_key"):
            aws_secret_key = dictCreds["aws_secret_key"]
         
         if isDebugMode:
            print "aws_access_key='%s'" % (aws_access_key)
            print "aws_secret_key='%s'" % (aws_secret_key)
            
         if len(aws_access_key) == 0 or len(aws_secret_key) == 0:
            print "error: no s3 credentials given. please specify aws_access_key and aws_secret_key in " + creds_file
            sys.exit(1)
            
      enc_iv = "sw4mpb1ts.juk3b0x"
      
      jukeboxOptions.setEncryptionIV(enc_iv)

      command = args[0]
      
      if command == 'help' or command == 'usage':
         ShowUsage()
      elif command == 'import':
         if not jukeboxOptions.validateOptions():
            sys.exit(1)

         if storageSystem == swift_system:
            with Swift_StorageSystem(swift_auth_host, swift_account, swift_user, swift_password, isDebugMode) as storageSystem:
               with Jukebox(jukeboxOptions, storageSystem) as jukebox:
                  jukebox.importSongs()
         elif storageSystem == s3_system:
            with S3_StorageSystem(aws_access_key, aws_secret_key, container_prefix, isDebugMode) as storageSystem:
               with Jukebox(jukeboxOptions, storageSystem) as jukebox:
                  jukebox.importSongs()
      elif command == 'play':
         if not jukeboxOptions.validateOptions():
            sys.exit(1)

         if storageSystem == swift_system:
            with Swift_StorageSystem(swift_auth_host, swift_account, swift_user, swift_password, isDebugMode) as storageSystem:
               with Jukebox(jukeboxOptions, storageSystem) as jukebox:
                  jukebox.playSongs()
         elif storageSystem == s3_system:
            with S3_StorageSystem(aws_access_key, aws_secret_key, container_prefix, isDebugMode) as storageSystem:
               with Jukebox(jukeboxOptions, storageSystem) as jukebox:
                  jukebox.playSongs()
      elif command == 'list-songs':
         if not jukeboxOptions.validateOptions():
            sys.exit(1)

         with Jukebox(jukeboxOptions, None) as jukebox:
            jukebox.showListings()
      elif command == 'list-containers':
         if not jukeboxOptions.validateOptions():
            sys.exit(1)

         if storageSystem == swift_system:
            with Swift_StorageSystem(swift_auth_host, swift_account, swift_user, swift_password, isDebugMode) as storageSystem:
               with Jukebox(jukeboxOptions, storageSystem) as jukebox:
                  jukebox.showListContainers()
         elif storageSystem == s3_system:
            with S3_StorageSystem(aws_access_key, aws_secret_key, container_prefix, isDebugMode) as storageSystem:
               with Jukebox(jukeboxOptions, storageSystem) as jukebox:
                  jukebox.showListContainers()
      else:
         print "Unrecognized command '%s'" % (command)
         print ''
         ShowUsage()
   else:
      print "Error: no command given"
      ShowUsage()

#******************************************************************************

