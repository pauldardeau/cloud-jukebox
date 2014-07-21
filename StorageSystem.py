#******************************************************************************
# Storage system for cloud jukebox
# Copyright Paul Dardeau, SwampBits LLC, 2014
# BSD license -- see LICENSE file for details
#
# StorageSystem - abstract base class for an object storage system
#
# Swift_StorageSystem - storage system using Swift Object Storage (https://wiki.openstack.org/wiki/Swift)
# For getting started with Swift, see: http://docs.openstack.org/developer/swift/development_saio.html
#
# S3_StorageSystem - storage system using Amazon's S3 (using boto client)
#******************************************************************************

import os.path

storageSystemSwiftSupported = 0
storageSystemS3Supported = 0

try:
   import swiftclient
   storageSystemSwiftSupported = 1
except ImportError:
   storageSystemSwiftSupported = 0

try:
   import boto
   from boto.s3.connection import S3Connection
   from boto.s3.key import Key
   storageSystemS3Supported = 1
except ImportError:
   storageSystemS3Supported = 0

#******************************************************************************

def isSwiftAvailable():
   return storageSystemSwiftSupported

#******************************************************************************
   
def isS3Available():
   return storageSystemS3Supported

#******************************************************************************
#******************************************************************************

class StorageSystem:
   
   #***************************************************************************

   def __init__(self, storageSystemType, debugMode=0):
      self.debugMode = debugMode
      self.isAuthenticated = 0
      self.compressFiles = 0
      self.encryptFiles = 0
      self.listContainers = []
      self.containerPrefix = ""
      self.metaDataPrefix = ""
      self.storageSystemType = storageSystemType

   #***************************************************************************

   def getStorageSystemType(self):
      return self.storageSystemType

   #***************************************************************************

   def getContainerPrefix(self):
      return self.containerPrefix

   #***************************************************************************
      
   def setContainerPrefix(self, containerPrefix):
      self.containerPrefix = containerPrefix

   #***************************************************************************
   
   def unPrefixedContainer(self, containerName):
      if len(self.containerPrefix) > 0 and len(containerName) > 0:
         if containerName.startswith(self.containerPrefix):
            return containerName[len(self.containerPrefix):]
      return containerName

   #***************************************************************************

   def getPrefixedContainer(self, containerName):
      return self.containerPrefix + containerName

   #***************************************************************************

   def hasContainer(self, containerName):
      return containerName in self.listContainers

   #***************************************************************************
   
   def addContainer(self, containerName):
      self.listContainers.append(containerName)

   #***************************************************************************
   
   def removeContainer(self, containerName):
      self.listContainers.remove(containerName)
      
   #***************************************************************************
      
   def getListContainers(self):
      return self.listContainers

   #***************************************************************************
   
   def setListContainers(self, listContainers):
      if listContainers is not None:
         self.listContainers = listContainers
      else:
         self.listContainers = []

   #***************************************************************************

   def setFileCompression(self, compressFiles):
      self.compressFiles = compressFiles

   #***************************************************************************
      
   def getFileCompression(self):
      return self.compressFiles

   #***************************************************************************
   
   def setFileEncryption(self, encryptFiles):
      self.encryptFiles = encryptFiles

   #***************************************************************************
      
   def getFileEncryption(self):
      return self.encryptFiles

   #***************************************************************************
   
   def isAuthenticated(self):
      return self.isAuthenticated
      
   #***************************************************************************
   
   def setAuthenticated(self, isAuthenticated):
      self.isAuthenticated = isAuthenticated

   #***************************************************************************

   def isDebugMode(self):
      return self.debugMode

   #***************************************************************************
      
   def setDebugMode(self, debugMode):
      self.debugMode = debugMode
      
   #***************************************************************************
   
   def getMetaDataPrefix(self):
      return self.metaDataPrefix

   #***************************************************************************
      
   def setMetaDataPrefix(self, metaDataPrefix):
      self.metaDataPrefix = metaDataPrefix

   #***************************************************************************

   def deleteSongFile(self, songFileInfo):
      if songFileInfo is not None:
         sfi = songFileInfo
         return self.deleteFile(sfi.getContainer(), sfi.getObjectName())

      return 0

   #***************************************************************************
   
   def retrieveSongFile(self, songFileInfo, localDirectory):
      if songFileInfo is not None and localDirectory is not None:
         sfi = songFileInfo
         filePath = os.path.join(localDirectory, sfi.getUid())
         return self.retrieveFile(sfi.getContainer(), sfi.getObjectName(), filePath)
      
      return 0

   #***************************************************************************

   def storeSongFile(self, songFileInfo, fileContents):
      if songFileInfo is not None and fileContents is not None:
         sfi = songFileInfo
         return self.addFile(sfi.getContainer(), sfi.getObjectName(), fileContents, sfi.toDictionary(self.getMetaDataPrefix()))
         
      return 0

   #***************************************************************************
   
   def addFileFromPath(self, containerName, objectName, filePath):
      try:
         with open(filePath, 'rb') as input_file:
            fileContents = input_file.read()
         return self.addFile(containerName, objectName, fileContents)
      except IOError:
         print "error: unable to read file %s" % (filePath)
         return 0

   #***************************************************************************

   #@abstractmethod
   def listAccountContainers(self):
      return None
      
   #***************************************************************************

   #@abstractmethod
   def createContainer(self, containerName):
      return 0

   #***************************************************************************

   #@abstractmethod
   def deleteContainer(self, containerName):
      return 0

   #***************************************************************************

   #@abstractmethod
   def listContainerContents(self, containerName):
      return None

   #***************************************************************************

   #@abstractmethod
   def getFileMetadata(self, containerName, objectName):
      return None

   #***************************************************************************

   #@abstractmethod
   def addFile(self, containerName, objectName, fileContents, headers=None):
      return 0
      
   #***************************************************************************

   #@abstractmethod
   def deleteFile(self, containerName, objectName):
      return 0

   #***************************************************************************

   #@abstractmethod
   def retrieveFile(self, containerName, objectName, localFilePath):
      return 0
      
   #***************************************************************************
   
#******************************************************************************
#******************************************************************************

class Swift_StorageSystem(StorageSystem):

   #***************************************************************************

   def __init__(self,auth_host,account,username,password,debugMode=0):
      StorageSystem.__init__(self, "Swift", debugMode)
      self.authHost = auth_host
      self.authPort = 8080
      self.authVersion = "1"
      self.authPrefix = "/auth/"
      self.authSSL = 0
      self.account = account
      self.username = username
      self.password = password
      
      self.setMetaDataPrefix("x-meta-")

      self.authUrl = ""
      
      if self.authSSL:
         self.authUrl += "https://"
      else:
         self.authUrl += "http://"
         
      self.authUrl += "%s:%s%s" % (self.authHost, self.authPort, self.authPrefix)
      
      if self.authVersion == "1":
         self.authUrl += "v1.0"
      
      self.accountUsername = "%s:%s" % (self.account, self.username)

   #***************************************************************************
   
   def __enter__(self):
      if self.isDebugMode():
         print "attempting to connect to swift server at %s" % (self.authUrl)

      self.conn = swiftclient.Connection(
                  self.authUrl, self.accountUsername, self.password,
                  auth_version=self.authVersion, retries=1)
      dictHeaders = self.conn.head_account()
      if dictHeaders is not None:
         self.setAuthenticated(1)
         self.setListContainers(self.listAccountContainers())

      return self

   #***************************************************************************

   def __exit__(self, type, value, traceback):
      if self.conn is not None:
         if self.isDebugMode():
            print "closing swift connection object"

         self.setAuthenticated(0)
         self.setListContainers([])
         self.conn.close()
         self.conn = None

   #***************************************************************************
   
   def listAccountContainers(self):
      if self.conn is not None:
         try:
            dictHeaders, listContainers = self.conn.get_account()
            if dictHeaders is not None and listContainers is not None:
               listContainerNames = []
               for dictContainer in listContainers:
                  listContainerNames.append(dictContainer['name'])
               return listContainerNames
         except swiftclient.client.ClientException:
            pass

      return None
      
   #***************************************************************************

   def createContainer(self, containerName):
      containerCreated = 0
      if self.conn is not None:
         try:
            self.conn.put_container(containerName)
            self.addContainer(containerName)
            containerCreated = 1
         except swiftclient.client.ClientException:
            pass
            
      return containerCreated

   #***************************************************************************
   
   def deleteContainer(self, containerName):
      containerDeleted = 0
      if self.conn is not None:
         try:
            self.conn.delete_container(containerName)
            self.removeContainer(containerName)
            containerDeleted = 1
         except swiftclient.client.ClientException:
            pass
            
      return containerDeleted

   #***************************************************************************

   def listContainerContents(self, containerName):
      if self.conn is not None:
         try:
            dictHeaders, listContents = self.conn.get_container(containerName)
            if dictHeaders is not None and listContents is not None:
               listObjectNames = []
               for objectRecord in listContents:
                  listObjectNames.append(objectRecord['name'])
               return listObjectNames
         except swiftclient.client.ClientException:
            pass
            
      return None

   #***************************************************************************
   
   def getFileMetadata(self, containerName, objectName):
      if self.conn is not None and containerName is not None and objectName is not None:
         try:
            return self.conn.head_object(containerName, objectName)
         except swiftclient.client.ClientException:
            pass
            
      return None

   #***************************************************************************

   def addFile(self, containerName, objectName, fileContents, headers=None):
      fileAdded = 0
      
      if self.conn is not None and containerName is not None and objectName is not None and fileContents is not None:
         if not self.hasContainer(containerName):
            self.createContainer(containerName)

         try:
            self.conn.put_object(containerName, objectName, fileContents, headers=headers)
            fileAdded = 1
         except swiftclient.client.ClientException:
            pass
            
      return fileAdded
      
   #***************************************************************************
   
   def deleteFile(self, containerName, objectName):
      fileDeleted = 0
      
      if self.conn is not None and containerName is not None and objectName is not None:
         try:
            self.conn.delete_object(containerName, objectName)
            fileDeleted = 1
         except swiftclient.client.ClientException:
            pass
            
      return fileDeleted

   #***************************************************************************

   def retrieveFile(self, containerName, objectName, localFilePath):
      fileBytesRetrieved = 0
      
      if self.conn is not None and containerName is not None and objectName is not None and localFilePath is not None:
         try:
            dictHeaders, fileContents = self.conn.get_object(containerName, objectName)
            if dictHeaders is not None and fileContents is not None:
               if len(fileContents) > 0:
                  try:
                     with open(localFilePath, 'wb') as content_file:
                        content_file.write(fileContents)
                     fileBytesRetrieved = len(fileContents)
                  except IOError:
                     print "error: unable to write to file '%s'" % (localFilePath)
               else:
                  # create empty file
                  try:
                     open(localFilePath, 'w').close()
                     fileBytesRetrieved = 0
                  except IOError:
                     print "error: unable to write to file '%s'" % (localFilePath) 
         except swiftclient.client.ClientException:
            pass
            
      return fileBytesRetrieved
      
   #***************************************************************************
   
#******************************************************************************
#******************************************************************************

class S3_StorageSystem(StorageSystem):
   
   #***************************************************************************

   def __init__(self,aws_access_key,aws_secret_key,container_prefix,debugMode=0):
      StorageSystem.__init__(self, "S3", debugMode)
      self.aws_access_key = aws_access_key
      self.aws_secret_key = aws_secret_key
      if container_prefix is not None and len(container_prefix) > 0:
         self.setContainerPrefix(container_prefix)

   #***************************************************************************
   
   def __enter__(self):
      if self.isDebugMode():
         print "attempting to connect to S3"

      self.conn = S3Connection(self.aws_access_key, self.aws_secret_key)
      self.setAuthenticated(1)
      self.setListContainers(self.listAccountContainers())

      return self

   #***************************************************************************

   def __exit__(self, type, value, traceback):
      if self.conn is not None:
         if self.isDebugMode():
            print "closing S3 connection object"

         self.setAuthenticated(0)
         self.setListContainers([])
         self.conn.close()
         self.conn = None

   #***************************************************************************
   
   def listAccountContainers(self):
      if self.conn is not None:
         try:
            rs = self.conn.get_all_buckets()
            
            listContainerNames = []
            
            for container in rs:
               listContainerNames.append(self.unPrefixedContainer(container.name))

            return listContainerNames
         except boto.exception.S3ResponseError:
            pass

      return None
      
   #***************************************************************************

   def createContainer(self, containerName):
      containerCreated = 0
      if self.conn is not None:
         try:
            self.conn.create_bucket(self.getPrefixedContainer(containerName))
            self.addContainer(containerName)
            containerCreated = 1
         except (boto.exception.S3CreateError, boto.exception.S3ResponseError):
            pass
            
      return containerCreated

   #***************************************************************************
   
   def deleteContainer(self, containerName):
      containerDeleted = 0
      if self.conn is not None:
         try:
            self.conn.delete_bucket(self.getPrefixedContainer(containerName))
            self.removeContainer(containerName)
            containerDeleted = 1
         except boto.exception.S3ResponseError:
            pass
            
      return containerDeleted

   #***************************************************************************

   def listContainerContents(self, containerName):
      if self.conn is not None:
         try:
            container = self.conn.get_bucket(self.getPrefixedContainer(containerName))
            rs = container.list()
            listContents = []
            
            for key in rs:
               listContents.append(key.name)
            
            return listContents
         except boto.exception.S3ResponseError:
            pass
            
      return None

   #***************************************************************************
   
   def getFileMetadata(self, containerName, objectName):
      if self.conn is not None and containerName is not None and objectName is not None:
         try:
            bucket = self.conn.get_bucket(self.getPrefixedContainer(containerName))
            objectKey = bucket.get_key(objectName)
            if objectKey is not None:
               pass
            
            #TODO: retrieve metadata key/values as dictionary
            return None
         except boto.exception.S3ResponseError:
            pass
            
      return None

   #***************************************************************************

   def addFile(self, containerName, objectName, fileContents, headers=None):
      fileAdded = 0
      
      if self.conn is not None and containerName is not None and objectName is not None and fileContents is not None:
         if not self.hasContainer(containerName):
            self.createContainer(containerName)

         try:
            bucket = self.conn.get_bucket(self.getPrefixedContainer(containerName))
            objectKey = Key(bucket)
            objectKey.key = objectName
            objectKey.set_contents_from_string(fileContents)
            fileAdded = 1
         except boto.exception.S3ResponseError:
            pass
            
      return fileAdded
      
   #***************************************************************************
   
   def deleteFile(self, containerName, objectName):
      fileDeleted = 0
      
      if self.conn is not None and containerName is not None and objectName is not None:
         try:
            bucket = self.conn.get_bucket(self.getPrefixedContainer(containerName))
            objectKey = bucket.get_key(objectName)
            objectKey.delete()
            fileDeleted = 1
         except boto.exception.S3ResponseError:
            pass
            
      return fileDeleted

   #***************************************************************************

   def retrieveFile(self, containerName, objectName, localFilePath):
      fileBytesRetrieved = 0
      
      if self.conn is not None and containerName is not None and objectName is not None and localFilePath is not None:
         try:
            bucket = self.conn.get_bucket(self.getPrefixedContainer(containerName))
            objectKey = bucket.get_key(objectName)
            objectKey.get_contents_to_filename(localFilePath)
            if os.path.exists(localFilePath):
               fileBytesRetrieved = os.path.getsize(localFilePath)
         except (Exception, boto.exception.S3ResponseError):
            pass
            
      return fileBytesRetrieved
      
   #***************************************************************************

#******************************************************************************
#******************************************************************************

