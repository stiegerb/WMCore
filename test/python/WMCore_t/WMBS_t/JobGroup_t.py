#!/usr/bin/env python
"""
_JobGroup_t_

Unit tests for the WMBS JobGroup class.
"""

__revision__ = "$Id: JobGroup_t.py,v 1.8 2009/01/12 16:50:09 sfoulkes Exp $"
__version__ = "$Revision: 1.8 $"

import unittest
import logging
import os
import commands
import threading
import random
from sets import Set

from WMCore.Database.DBCore import DBInterface
from WMCore.Database.DBFactory import DBFactory
from WMCore.DataStructs.Fileset import Fileset
from WMCore.DAOFactory import DAOFactory
from WMCore.WMBS.File import File
from WMCore.WMBS.Fileset import Fileset as WMBSFileset
from WMCore.WMBS.Job import Job
from WMCore.WMBS.JobGroup import JobGroup
from WMCore.WMBS.Workflow import Workflow
from WMCore.WMBS.Subscription import Subscription
from WMCore.WMFactory import WMFactory
from WMQuality.TestInit import TestInit
from WMCore.DataStructs.Run import Run

class Job_t(unittest.TestCase):
    _setup = False
    _teardown = False
    
    def setUp(self):
        """
        _setUp_

        Setup the database and logging connection.  Try to create all of the
        WMBS tables.
        """
        if self._setup:
            return

        self.testInit = TestInit(__file__, os.getenv("DIALECT"))
        self.testInit.setLogging()
        self.testInit.setDatabaseConnection()
        self.testInit.setSchema(customModules = ["WMCore.WMBS"],
                                useDefault = False)
        
        self._setup = True
        return
          
    def tearDown(self):        
        """
        _tearDown_
        
        Drop all the WMBS tables.
        """
        myThread = threading.currentThread()
        
        if self._teardown:
            return
        
        factory = WMFactory("WMBS", "WMCore.WMBS")
        destroy = factory.loadObject(myThread.dialect + ".Destroy")
        myThread.transaction.begin()
        destroyworked = destroy.execute(conn = myThread.transaction.conn)
        if not destroyworked:
            raise Exception("Could not complete WMBS tear down.")
        myThread.transaction.commit()
            
        self._teardown = True
            
    def testCreateDeleteExists(self):
        """
        _testCreateDeleteExists_

        Create a JobGroup and then delete it.  Use the JobGroup's exists()
        method to determine if it exists before it is created, after it is
        created and after it is deleted.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testFileset = WMBSFileset(name = "TestFileset")
        testFileset.create()
        
        testSubscription = Subscription(fileset = testFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroup = JobGroup(subscription = testSubscription)

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists before it was created"
        
        testJobGroup.create()

        assert testJobGroup.exists() >= 0, \
               "ERROR: Job group does not exist after it was created"
        
        testJobGroup.delete()

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists after it was deleted"

        testSubscription.delete()
        testFileset.delete()
        testWorkflow.delete()
        return

    def testCreateTransaction(self):
        """
        _testCreateTransaction_

        Create a JobGroup and commit it to the database.  Rollback the database
        transaction and verify that the JobGroup is no longer in the database.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testFileset = WMBSFileset(name = "TestFileset")
        testFileset.create()
        
        testSubscription = Subscription(fileset = testFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroup = JobGroup(subscription = testSubscription)

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists before it was created"

        myThread = threading.currentThread()
        myThread.transaction.begin()
        
        testJobGroup.create()

        assert testJobGroup.exists() >= 0, \
               "ERROR: Job group does not exist after it was created"
        
        myThread.transaction.rollback()

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists after transaction was rolled back."

        testSubscription.delete()
        testFileset.delete()
        testWorkflow.delete()
        return    

    def testDeleteTransaction(self):
        """
        _testDeleteTransaction_

        Create a JobGroup and then commit it to the database.  Begin a
        transaction and the delete the JobGroup from the database.  Using the
        exists() method verify that the JobGroup is not in the database.
        Finally, roll back the transaction and verify that the JobGroup is
        in the database.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testFileset = WMBSFileset(name = "TestFileset")
        testFileset.create()
        
        testSubscription = Subscription(fileset = testFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroup = JobGroup(subscription = testSubscription)

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists before it was created"
        
        testJobGroup.create()

        assert testJobGroup.exists() >= 0, \
               "ERROR: Job group does not exist after it was created"

        myThread = threading.currentThread()
        myThread.transaction.begin()
        
        testJobGroup.delete()

        assert testJobGroup.exists() == False, \
               "ERROR: Job group exists after it was deleted"

        myThread.transaction.rollback()

        assert testJobGroup.exists() >= 0, \
               "ERROR: Job group does not exist after transaction was rolled back."        

        testSubscription.delete()
        testFileset.delete()
        testWorkflow.delete()
        return

    def testLoad(self):
        """
        _testLoad_

        Create a JobGroup and save it to the database.  Create a new JobGroup
        and then attempt to load the first one into it from the database.
        Compare the two JobGroup to make sure they're identical.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testWMBSFileset = WMBSFileset(name = "TestFileset")
        testWMBSFileset.create()
        
        testSubscription = Subscription(fileset = testWMBSFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroupA = JobGroup(subscription = testSubscription)
        testJobGroupA.create()

        testFileA = File(lfn = "/this/is/a/lfnA", size = 1024, events = 10)
        testFileA.addRun(Run(10, *[12312]))

        testFileB = File(lfn = "/this/is/a/lfnB", size = 1024, events = 10)
        testFileB.addRun(Run(10, *[12312]))
        testFileA.create()
        testFileB.create()

        testFilesetA = Fileset(name = "TestFilesetA", files = Set([testFileA]))
        testFilesetB = Fileset(name = "TestFilesetB", files = Set([testFileB]))
        
        testJobA = Job(name = "TestJobA", files = testFilesetA)
        testJobB = Job(name = "TestJobB", files = testFilesetB)

        testJobGroupA.add(testJobA)
        testJobGroupA.add(testJobB)
        testJobGroupA.commit()

        testJobGroupB = JobGroup(id = testJobGroupA.id)
        testJobGroupB.load()

        assert testJobGroupB.subscription["id"] == testSubscription["id"], \
               "ERROR: Job group did not load subscription correctly"

        goldenJobs = [testJobA.id, testJobB.id]
        for job in testJobGroupB.jobs:
            assert job.id in goldenJobs, \
                   "ERROR: JobGroup loaded an unknown job"
            goldenJobs.remove(job.id)

        assert len(goldenJobs) == 0, \
            "ERROR: JobGroup didn't load all jobs"

        assert testJobGroupB.groupoutput.id == testJobGroupA.groupoutput.id, \
               "ERROR: Output fileset didn't load properly"
        
        return

    def testLoadByUID(self):
        """
        _testLoadByUID_

        Create a JobGroup and save it to the database.  Create a new JobGroup
        and then attempt to load the first one into it from the database using
        the UID instead of the ID.  Compare the two JobGroup to make sure
        they're identical.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()
        
        testWMBSFileset = WMBSFileset(name = "TestFileset")
        testWMBSFileset.create()
        
        testSubscription = Subscription(fileset = testWMBSFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroupA = JobGroup(subscription = testSubscription,
                                 uid = "TestJobGroup")
        testJobGroupA.create()

        testFileA = File(lfn = "/this/is/a/lfnA", size = 1024, events = 10)
        testFileA.addRun(Run(10, *[12312]))

        testFileB = File(lfn = "/this/is/a/lfnB", size = 1024, events = 10)
        testFileB.addRun(Run(10, *[12312]))
        testFileA.create()
        testFileB.create()

        testFilesetA = Fileset(name = "TestFilesetA", files = Set([testFileA]))
        testFilesetB = Fileset(name = "TestFilesetB", files = Set([testFileB]))
        
        testJobA = Job(name = "TestJobA", files = testFilesetA)
        testJobB = Job(name = "TestJobB", files = testFilesetB)

        testJobGroupA.add(testJobA)
        testJobGroupA.add(testJobB)
        testJobGroupA.commit()

        testJobGroupB = JobGroup(uid = testJobGroupA.uid)
        testJobGroupB.load()

        assert testJobGroupB.subscription["id"] == testSubscription["id"], \
               "ERROR: Job group did not load subscription correctly"

        goldenJobs = [testJobA.id, testJobB.id]
        for job in testJobGroupB.jobs:
            assert job.id in goldenJobs, \
                   "ERROR: JobGroup loaded an unknown job"
            goldenJobs.remove(job.id)

        assert len(goldenJobs) == 0, \
            "ERROR: JobGroup didn't load all jobs"

        assert testJobGroupB.groupoutput.id == testJobGroupA.groupoutput.id, \
               "ERROR: Output fileset didn't load properly"
        
        return

    def testCommit(self):
        """
        _testCommit_

        Verify that jobs are not added to a job group until commit() is called
        on the JobGroup.  Also verify that commit() correctly commits the jobs
        to the database.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()

        testWMBSFileset = WMBSFileset(name = "TestFileset")
        testWMBSFileset.create()

        testSubscription = Subscription(fileset = testWMBSFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroupA = JobGroup(subscription = testSubscription)
        testJobGroupA.create()

        testFileA = File(lfn = "/this/is/a/lfnA", size = 1024, events = 10,
                         cksum=1)
        testFileA.addRun(Run(1, *[45]))
        testFileB = File(lfn = "/this/is/a/lfnB", size = 1024, events = 10,
                         cksum=1)
        testFileB.addRun(Run(1, *[45]))
        testFileA.create()
        testFileB.create()

        testFilesetA = Fileset(name = "TestFilesetA", files = Set([testFileA]))
        testFilesetB = Fileset(name = "TestFilesetB", files = Set([testFileB]))

        testJobA = Job(name = "TestJobA", files = testFilesetA)
        testJobB = Job(name = "TestJobB", files = testFilesetB)

        testJobGroupA.add(testJobA)
        testJobGroupA.add(testJobB)

        testJobGroupB = JobGroup(id = testJobGroupA.id)
        testJobGroupB.load()

        assert len(testJobGroupA.jobs) == 0, \
               "ERROR: Original object commited too early"

        assert len(testJobGroupB.jobs) == 0, \
               "ERROR: Loaded JobGroup has too many jobs"

        testJobGroupA.commit()

        assert len(testJobGroupA.jobs) == 2, \
               "ERROR: Original object did not commit jobs"

        testJobGroupC = JobGroup(id = testJobGroupA.id)
        testJobGroupC.load()

        assert len(testJobGroupC.jobs) == 2, \
               "ERROR: Loaded object has too few jobs."

    def testCommitTransaction(self):
        """
        _testCommitTransaction_

        Create a JobGroup and then add some jobs to it.  Begin a transaction
        and then call commit() on the JobGroup.  Verify that the newly committed
        jobs can be loaded from the database.  Rollback the transaction and then
        verify that the jobs that were committed before are no longer associated
        with the JobGroup.
        """
        testWorkflow = Workflow(spec = "spec.xml", owner = "Simon",
                                name = "wf001")
        testWorkflow.create()

        testWMBSFileset = WMBSFileset(name = "TestFileset")
        testWMBSFileset.create()

        testSubscription = Subscription(fileset = testWMBSFileset,
                                        workflow = testWorkflow)
        testSubscription.create()

        testJobGroupA = JobGroup(subscription = testSubscription)
        testJobGroupA.create()

        testFileA = File(lfn = "/this/is/a/lfnA", size = 1024, events = 10,
                         cksum=1)
        testFileA.addRun(Run(1, *[45]))
        testFileB = File(lfn = "/this/is/a/lfnB", size = 1024, events = 10,
                         cksum=1)
        testFileB.addRun(Run(1, *[45]))
        testFileA.create()
        testFileB.create()

        testFilesetA = Fileset(name = "TestFilesetA", files = Set([testFileA]))
        testFilesetB = Fileset(name = "TestFilesetB", files = Set([testFileB]))

        testJobA = Job(name = "TestJobA", files = testFilesetA)
        testJobB = Job(name = "TestJobB", files = testFilesetB)

        testJobGroupA.add(testJobA)
        testJobGroupA.add(testJobB)

        testJobGroupB = JobGroup(id = testJobGroupA.id)
        testJobGroupB.load()

        assert len(testJobGroupA.jobs) == 0, \
               "ERROR: Original object commited too early"

        assert len(testJobGroupB.jobs) == 0, \
               "ERROR: Loaded JobGroup has too many jobs"

        myThread = threading.currentThread()
        myThread.transaction.begin()

        testJobGroupA.commit()

        assert len(testJobGroupA.jobs) == 2, \
               "ERROR: Original object did not commit jobs"

        testJobGroupC = JobGroup(id = testJobGroupA.id)
        testJobGroupC.load()

        assert len(testJobGroupC.jobs) == 2, \
               "ERROR: Loaded object has too few jobs."        

        myThread.transaction.rollback()

        testJobGroupD = JobGroup(id = testJobGroupA.id)
        testJobGroupD.load()

        assert len(testJobGroupD.jobs) == 0, \
               "ERROR: Loaded object has too many jobs."        

        return

if __name__ == "__main__":
    unittest.main() 
