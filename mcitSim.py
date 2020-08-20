import pandas as pd
import numpy as np
import random
from collections import Counter
from graphviz import Digraph

"""
Simulation Design
    
Simulator:
    -defines student enrollment rate
    -takes course register rules
    -generates many runs of simulations
    -stores data of simulation in pandas data frame
        -rows: sim ID
        -columns: student ID
Course:
    -counts students registered in course
    -indicate when the course is full
Policy:
    -defines registration rules that student must obey
    -return possible courses to take per rules
    -visualize policy
Student:
    -stores history of classes taken
    -stores the ranking of choice of class taken
    -indicate status of student: enrolled, graduated
    -register for class: follows course registration rules
Analyzer:
    -unpack those student simulation data into tables
"""
class Simulator:
    def __init__(self, policy, coreCapacity = 350, electCapacity = 50):
        self.policy = policy
        self.simulatedStudents = []
        self.courseCatalog = {}
        coreList = ['591', '592', '593', '594', '595', '596']
        electList = ['515', '547', '549', '550', '581', '542']
        for core in coreList:
            self.courseCatalog[core] = Course(core, coreCapacity)       

        for elect in electList:
            self.courseCatalog[elect] = Course(elect, electCapacity)

    def resetCoursesEnrollment(self):
        for course in self.courseCatalog.keys():
            self.courseCatalog[course].resetEnrollment()

    def run_sim_replicates(self, replicates=3, enrollmentRate=230, duration=15):
        for i in range(replicates):
            simulData = self.run_sim(enrollmentRate=enrollmentRate, duration=duration)
            self.simulatedStudents.append(simulData)
        
    def run_sim(self, enrollmentRate=230, duration=15):
        """
        inputs:
            enrollmentRate: number of students enrolled per semester
            duration: number of semesters (time)
        """
        simStudents = []
        studentIDs = []
        for t in range(duration):        
            # enrolling new students every semester
            simStudents += [Student(i, 0) for i in range(t* enrollmentRate, enrollmentRate * (t+1))]
            studentIDs += [i for i in range(t* enrollmentRate, enrollmentRate * (t+1))]
            
            # randomized course registration order
            random.shuffle(studentIDs)        
        
            for studentID in studentIDs:        
                # register course for student
                courses = simStudents[studentID].chooseCourse(self.policy, self.courseCatalog)
                # update Course enrollment numbers
                for course in courses:
                    self.courseCatalog[course].enrollCourse()     
                if simStudents[studentID].isGraduated():
                    studentIDs.remove(studentID)                
                    
            self.resetCoursesEnrollment()            
        return simStudents

    def showCourseStatus(self):
        for course in self.courseCatalog:
            self.courseCatalog[course].showAttributes()
        
class Policy:
    listOfPolicies = ["no-restrictions", "core-first"]
    
    def __init__(self, policy):
        """
        policy must be within this list: no-restrictions, core-first
        """
        if policy not in self.listOfPolicies:
            raise ValueError('policy name "%s" does not match available policy names "%s"' % (policy, str(self.listOfPolicies)))
        else:
            self.policy = policy
            self.courseGraph = {}
            if (policy == self.listOfPolicies[0]):
                self.courseGraph = {
                    '591' : {'pre' : None, 'co' : None },
                    '592' : {'pre' : None, 'co' : None },
                    '593' : {'pre' : ['591'], 'co' : ['591'] },
                    '594' : {'pre' : ['591'], 'co' : None },
                    '595' : {'pre' : ['593'], 'co' : None },
                    '596' : {'pre' : ['592', '594'], 'co' : ['594'] },
                    '515' : {'pre' : None, 'co' : None },
                    '547' : {'pre' : ['592', '594', '595'], 'co' : None },
                    '549' : {'pre' : ['593', '595'], 'co' : None },
                    '550' : {'pre' : ['591', '592', '596'], 'co' : ['596'] },
                    '581' : {'pre' : ['591', '592', '593', '594'], 'co' : None },
                    '542' : {'pre' : ['592'], 'co' : None },
                }
            elif (policy == self.listOfPolicies[1]):
                coreCourseReq = {'pre' : ['591', '592', '593', '594', '595', '596'], 'co' : None }
                self.courseGraph = {
                    '591' : {'pre' : None, 'co' : None },
                    '592' : {'pre' : None, 'co' : None },
                    '593' : {'pre' : ['591'], 'co' : ['591'] },
                    '594' : {'pre' : ['591'], 'co' : None },
                    '595' : {'pre' : ['593'], 'co' : None },
                    '596' : {'pre' : ['592', '594'], 'co' : ['594'] },
                    '515' : coreCourseReq,
                    '547' : coreCourseReq,
                    '549' : coreCourseReq,
                    '550' : coreCourseReq,
                    '581' : coreCourseReq,
                    '542' : coreCourseReq,
                }
                
    def getCourseOptions(self, coursesTaken):
        """
        input: list of courses taken
        output: list of courses that you can take
        """
        options = {}
        for key in self.courseGraph:
            prerequisites = self.courseGraph[key]['pre']   
            corequisites = self.courseGraph[key]['co']
            if (key in coursesTaken):
                continue
            elif (prerequisites is None):
                if (key not in options): options[key] = []
            elif (all(item in coursesTaken for item in prerequisites)):
                if (key not in options): options[key] = []
            elif (corequisites is not None):
                remainderPreReq = set(prerequisites) - coursesTaken
                remainderCoReq = set(corequisites) - coursesTaken
                if (remainderPreReq != remainderCoReq): 
                    continue                    
                elif (self.passCoReq(coursesTaken, remainderCoReq)):                    
                    temp = list(remainderCoReq)[0]
                    options[temp] = [key] if key not in options else options[temp].append(key)
                    
        return options
    
    def passCoReq(self, coursesTaken, remainderCoReq):
        for co in remainderCoReq:
            coPrereq = self.courseGraph[co]['pre']
            if not (coPrereq is None or 
                    all(item in coursesTaken for item in coPrereq)): 
                return False
        return True
    
    def showCourseGraph(self):
        """
        Visualizes the course graph to show course dependencies
        """
        visualGraph = Digraph()
        nodeChar = 'A'
        dictCourseToNode = {}
        
        # initialize nodes
        for key in self.courseGraph:
            corequisites = self.courseGraph[key]['co']
            prerequisites = self.courseGraph[key]['pre']
            dictCourseToNode[key] = nodeChar
            if (corequisites is None):
                visualGraph.node(nodeChar, key)
            else:
                visualGraph.node(nodeChar, key + str(corequisites).replace("'",""))
            nodeChar = chr(ord(nodeChar) + 1)
        
        # build edges
        edges = []
        for key in self.courseGraph:
            if (self.courseGraph[key]['pre'] == None):
                continue
            else:
                prerequisites = self.courseGraph[key]['pre']
                for pre in prerequisites:
                    edges.append(dictCourseToNode[pre] + dictCourseToNode[key])
        
        visualGraph.edges(edges)
        return visualGraph
            
class Course:
    def __init__(self, courseId, capacity):
        self.id = courseId
        self.numEnrolled = 0
        self.capacity = capacity        
    def isCourseFull(self):
        return self.numEnrolled >= self.capacity
    def enrollCourse(self):
        self.numEnrolled += 1
    def resetEnrollment(self):
        self.numEnrolled = 0
    def showAttributes(self):
        print("id, numEnrolled, capacity = %s, %s, %s" % (self.id, self.numEnrolled, self.capacity) )
        
class Student:
    def __init__(self, studentId, startTime, oneClassOnly=0.5):        
        self.id = studentId
        self.startTime = startTime
        self.courseTaken = set()
        self.registerTrialsOfCourses = {}
        self.coursesNotAvailable = 0
        self.semesterCount = 0
        self.graduated = False
        # probability of registering for 1 class instead of 2
        self.oneClassOnly = oneClassOnly        

    def chooseCourse(self, policy, courseCatalog):
        options = policy.getCourseOptions(self.courseTaken)
        selected = []
        
        # choose no more than 2 courses && while there are still course options
        while  (len(selected) < 2 and len(options) >= 1):
            
            myCourses = list(options.keys())
            myCourse = random.choice(myCourses)
            if not courseCatalog[myCourse].isCourseFull():
                # unpack avaialble cocurrent course
                for coCurrentCourse in options[myCourse]:
                    options[coCurrentCourse] = []
                del options[myCourse]
                selected.append(myCourse)
                if (random.uniform(0, 1) < self.oneClassOnly):
                    break # sometimes take only 1 course                    
            else:
                del options[myCourse]
                self.registerTrialsOfCourses[myCourse] = 1 \
                    if myCourse not in self.registerTrialsOfCourses.keys() \
                    else self.registerTrialsOfCourses[myCourse] + 1

        self.updateStudent(selected)
        return selected
    
    def updateStudent(self, courses): 
        self.semesterCount += 1
        self.courseTaken.update(courses)
        
        # failed to register for a course and must take a leave of absence
        if (len(courses) == 0): 
            self.coursesNotAvailable += 1            
        # check graduation criteria and update
        if ({'591', '592', '593', '594', '595', '596'}.issubset(self.courseTaken) and
            len(self.courseTaken) >= 10):
            self.graduated = True
            
    def isGraduated(self):
        return self.graduated
    def showAttributes(self):
        print("id, semesterCount, registerTrialsOfCourses, coursesNotAvailable, graduated = %s, %s, %s, %s, %s" % (self.id, self.semesterCount, self.registerTrialsOfCourses, self.coursesNotAvailable, self.graduated) )

class Analyzer:
    coreList = ['591', '592', '593', '594', '595', '596']
    electList = ['515', '547', '549', '550', '581', '542']
    def summary(studentData):
        pass
    
    def averageGradTime(self, studentData):
        totalSumTime = 0
        counter = 0
        for sim in studentData:
            for student in sim:
                if (student.isGraduated):
                    totalSumTime += student.semesterCount
                    counter += 1
        return totalSumTime / counter
    
    def leavesPerStudent(self, studentData):
        totalSum = 0
        for sim in studentData:
            for student in sim:
                totalSum += student.coursesNotAvailable
        return totalSum / (len(studentData) * len(studentData[0]))
    
    def averageRegisterTrialsPerStudent(self, studentData):
        registerTrialsOfCourses = Counter()
        allCoursesList = self.coreList + self.electList
        # initialize dict for counting
        for course in allCoursesList:
            registerTrialsOfCourses[course] = 0
            
        for sim in studentData:
            for student in sim:
                registerTrialsOfCourses += Counter(student.registerTrialsOfCourses)
        totalSum = 0
        for key in registerTrialsOfCourses.keys():
            totalSum += registerTrialsOfCourses[key]
        return totalSum / (len(studentData) * len(studentData[0]))
                
    def showRegisterTrials(self, studentData):
        registerTrialsOfCourses = Counter()
        allCoursesList = self.coreList + self.electList
        # initialize dict for counting
        for course in allCoursesList:
            registerTrialsOfCourses[course] = 0
            
        for sim in studentData:
            for student in sim:
                registerTrialsOfCourses += Counter(student.registerTrialsOfCourses)
                
        registerTrialsOfCourses = {k: v / len(studentData) for k, v in registerTrialsOfCourses.items()}
        df = pd.DataFrame.from_dict(registerTrialsOfCourses, orient='index').reset_index()
        df.columns = ['courseID', 'registerTrials']
        return df.sort_values(by=['registerTrials'], ascending=False)
    
    def countCoursesTaken(self, studentData):
        registerTrialsPerCourse = Counter()
        allCoursesList = self.coreList + self.electList
        # initialize dict for counting
        for course in allCoursesList:
            registerTrialsPerCourse[course] = 0
            
        for sim in studentData:
            for student in sim:
                for course in student.courseTaken:
                    registerTrialsPerCourse[course] += 1
        
        #registerTrialsPerCourse = {k: v / len(studentData) for k, v in registerTrialsPerCourse.items()}
        df = pd.DataFrame.from_dict(registerTrialsPerCourse, orient='index').reset_index()
        df.columns = ['courseID', 'takenCounts']
        return df.sort_values(by=['takenCounts'], ascending=False)