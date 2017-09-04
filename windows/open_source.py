# -*- coding: UTF-8 -*-
import _thread
import webbrowser , threading
import requests,hashlib
import tkinter as tk
from tkinter import *
import time
from bs4 import BeautifulSoup
from multiprocessing import Queue

from tkinter import messagebox

color = "#e9e6e6"

class Page(tk.Tk):
    def __init__(self):
        self.work = Tk();
        self.work.configure(background=color)
        self.status = StringVar()
        self.status_label = Label(self.work , textvariable=self.status , bg=color )
        self.status_label.place(x=120,y=6)

    def show(self,message):
        self.status.set(message)

    def loop(self):
        self.work.mainloop();

    def cancel(self):
        self.work.destroy()
    def size(self,x,y):
        self.work.minsize(x,y)
        self.work.maxsize(x,y)


class connection():
    session = 0 # Stores cookie
    headers = {
        'Host': 'pooya.khayyam.ac.ir',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive',
    }
    def __init__(self):
        self.session = requests.session()

    def getMD5OfString(self, string): # [m.hexdigest] = md5 of parameter string , 0 = failed at creating the md5 of parameter string
        try:
            m = hashlib.md5()
            m.update(string.encode('utf-8'))
            return m.hexdigest()
        except:
            return 0

    def sendLoginRequest(self, username, password): # 0 = failed at sending request, 1 = request successfully sent
        body = {'UserPassword': self.getMD5OfString(password), 'pswdStatus': 'weak', 'UserID': username, 'DummyVar': ''}
        url = "http://pooya.khayyam.ac.ir/gateway/UserInterim.php"
        try:
            request = self.session.get(url, headers= self.headers)  # get cookies
            request = self.session.post(url, data= body, headers= self.headers)  # login and get cookies
            return 1
        except:
            return 0

    def isLoggedIn(self,): # 0 = user is logged out , 1 = user is logged in, -1 = exception has thrown
        url = "http://pooya.khayyam.ac.ir/educ/educfac/ShowStSpec.php"
        try:
            request = self.session.get(url, headers= self.headers, cookies= self.session.cookies)
            if "<title>Student Specifications</title>" in request.text:
                return 1
            else:
                return 0
        except:
            return -1

    def login(self, username, password): # 0 = login failed , 1 = login is done
        i = 0
        while i<3 and self.sendLoginRequest(username, password) == 0:
            i = i + 1
        if i<3:
            return 1
        else:
            return 0

    def checkLessonExistance(self, lesCode): # [lessonName] = lesson exists, 0 = lesson does not exist, -1 = excpetion in getting lesson page, -2 = user is not logged in
        url = "http://pooya.khayyam.ac.ir/educ/report/LessonSpec.php?LesCode=" + lesCode
        if self.isLoggedIn() == 1:
            try:
                request = self.session.get(url, headers= self.headers, cookies= self.session.cookies)
                if '<i>""</i>' in request.text:
                    return 0
                else:
                    lessonName = request.text[request.text.find("شرح فارسی</td>"):]
                    lessonName = lessonName[lessonName.find("</td>")+5:]
                    lessonName = lessonName[lessonName.find("<td>")+4:lessonName.find("</tr>")-8:1]
                    return lessonName
            except:
                return -1
        else:
            return -2


    def logout(self, ): # 1= logged out, 0= failed to log out
        url = "http://pooya.khayyam.ac.ir/gateway/SignOut.php";
        try:
            request = self.session.get(url, headers= self.headers, cookies= self.session.cookies)
            return 1
        except:
            return 0

    def _generateSelectionHeader(self, lesIDs, lesGroups): # return proper Header for given units
        unitHeader = ""
        for i in range(0, len(lesIDs)):
            unitHeader += "AddIt[]="+ str(i) + "&LsnNo[]=" + lesIDs[i] + "&LsnGrp[]=" + lesGroups[i] + "&"

        return unitHeader

    def _selectionResult(self, requestText):
        soup = BeautifulSoup(requestText, 'html.parser')
        i = 0
        try :
            for table in soup.findAll('table'):  # get all tables
                if i == 2:  # third table has the result
                    result = []
                    for tr in table.findAll('tr'):
                        if tr.get('bgcolor') != "#FFCC66":
                            tdCounter = 0
                            lesID = -1
                            lesName = ""
                            lesGrp = -1
                            profName = ""
                            lesStatus = ""
                            for td in tr.findAll('td'):
                                if tdCounter == 1:
                                    lesID = td.get_text()
                                elif tdCounter == 2:
                                    lesGrp = td.get_text()
                                elif tdCounter == 3:
                                    lesName = td.get_text()
                                elif tdCounter == 4:
                                    profName = td.get_text()
                                elif tdCounter == 7:
                                    lesStatus = td.get_text()

                                tdCounter += 1
                            result.append({
                                'lesID': lesID,
                                'lesName': lesName,
                                'profName': profName,
                                'lesStatus': lesStatus
                            })
                i += 1
            return result
        except:
            return [{"error": 'Error at parsing the requestText'}]

    def isSelectionSiteOpen(self,): # 1= selection page is open, 0= selection site is closed, -1= user is not logged in, -2= exception in getting selection page
        url = "http://pooya.khayyam.ac.ir/educ/stu_portal/ShowPreCSelsForm.php"
        if self.isLoggedIn():
            try:
                request = self.session.get(url, headers=self.headers, cookies=self.session.cookies)
                if "function reserveCourse(LesCo,LesGr){" in request.text:
                    return 1
                else:
                    return 0
            except:
                return -2
        else:
            return -1
    def selectUnits(self, lesIDs, lesGroups): # [selectionResult]= selecting units is successfully done and result of selecting units is returned, 0= failed to select units, -1= user is not logged in or Input arrays are not equally filled
        url = "http://pooya.khayyam.ac.ir/educ/stu_portal/ShowPreCSelsForm.php"
        if len(lesIDs) == len(lesGroups) and self.isLoggedIn() == 1:
            try:
                body = self._generateSelectionHeader(lesIDs, lesGroups)
                request = self.session.post(url, data=body, headers=self.headers, cookies= self.session.cookies)
                return self._selectionResult(request.text)
            except:
                return 0
        else:
            return -1


class User():
    def __init__(self , username , passwordd):
        super().__init__(); # copy super class constractor
        self.user = username
        self.password = passwordd
        self.myconnect = connection()

    def setUserPsss(self,username,passwordd): #set new user password
        self.user = username
        self.password = passwordd


    def login(self):
        i=1
        while(i <= 3):
            if(self.myconnect.login(self.user,self.password)):
                return 1
            time.sleep(3)
            i+=1
        return 0

    def start(self):
        self.myconnect.logout()
        time.sleep(1)
        self.login()
        if self.myconnect.isSelectionSiteOpen() :
            header = self.headerCreator()
            status = self.myconnect.selectUnits(header[0],header[1])
            if(status != -1 and status != 0):
                return status 
            else: return 1
        else : return 1
    def headerCreator(self):
        out = ([],[])
        f = open("config.cfg","r")
        for line in f:
            line_list = line.split()
            out[0].append(line_list[0])
            out[1].append(line_list[1])
        f.close()
        return out






class addNewLesson():
    def __init__(self,memberr,id_,gp_):
        self.member = memberr
        self.id = id_;
        self.gp = gp_;
    def check(self):
        temp =self.member.myconnect.checkLessonExistance(self.id)
        if(type(temp) == type("s")):
            self.save(temp)
            return 1;
        else:
            return 0;

    def save(self, name):
        config_file =  open("config.cfg","a", encoding="UTF-8")
        config_file.write(self.id+ " " + self.gp + " " + name + "\n")
        config_file.close()





class GUI(Page):
    def __init__(self):
        super().__init__();
        self.work.wm_title("login");
        self.size(300,140)
        self.member = User(None , None)
        self.flagstop = 0
        self.flagstopButton = 0


        self.luser = Label(self.work,text="user" , bg=color)
        self.user = Entry(self.work)

        
        self.lpassword = Label(self.work,text="password" , bg=color)
        self.password = Entry(self.work,show="*")

        self.submit = Button(self.work,text="login",command=self.login) # submit button for login
        self.cancel = Button(self.work,text="cancel",command=self.cancel)

        self.setDefaultUserPass() #set user password if user was login already

        self.luser.place(x=20,y =35)
        self.user.place(x=80,y=35)

        self.lpassword.place(x=5,y=65)
        self.password.place(x=80,y=65)

        self.submit.place(x = 90 , y=95)
        self.cancel.place(x = 170 , y=95)

        self.show("saaayaaam :D")

    def changePage(self): # create new page for user :D kos nanash alan dlm mikhad ye barname benevisam ke gerafiki in kara ro bokonm :))) i have any asab :))))
        self.work.destroy()
        super().__init__();
        self.work.wm_title("Khayyam Units");
        self.size(690,350)


        self.lid = Label(self.work,text=" lesson id ",bg=color )
        self.id = Entry(self.work)
        
        self.lgp = Label(self.work,text=" group " , bg=color)
        self.gp = Entry(self.work)

        self.textbox = Text(self.work,bg="black",fg="#5dff00")

        self.lstart = Label(self.work,text="start after",bg=color)
        self.hour = Entry(self.work)
        self.l2start = Label(self.work,text="hour",bg=color)

        self.add = Button(self.work,text="add" , command=self.addLesson)
        self.delete = Button(self.work,text="delete" , command=self.deleteLesson)
        self.start = Button(self.work,text="start",command=self.startWork)
        self.stop = Button(self.work,text="stop",command=self.stopWork)
        self.about = Button(self.work , text="about",command=self.aboutFun)
        self.donate = Button(self.work,text="donate",command=self.donateFunc)


        self.list_box = Listbox(self.work)
        self.fixListBox()

        self.lid.place(x=65,y=20)
        self.id.place(x=50,y=40, height=20, width=100)

        self.lgp.place(x=165,y=20)
        self.gp.place(x=165,y=40 , height=20, width=50)

        self.list_box.place(x=50,y=70 , height=260 , width=230)

        self.add.place(x=230,y=40 ,height=20)
        self.delete.place(x=280,y=310 ,height=20)
        self.donate.place(x=505,y=310,width=140)
        self.about.place(x=360,y=310,width=140)
        self.stop.place(x=505,y=280,width=140)
        self.stop.config(state = 'disabled')

        self.start.place(x=505,y=250,width=140)

        self.lstart.place(x=400,y=250)
        self.hour.place(x=405,y=270,width=50)
        self.hour.insert(END, "0")
        self.l2start.place(x=412,y=290)

        self.textbox.place(x=365,y=35, height=210, width=280)

        self.status_label.place(x=310,y=30)
        self.show("status : ")
        

    def login(self):
        self.member.setUserPsss(self.user.get(),self.password.get())

        login_status = self.member.login()

        if login_status == 1:
            self.addUse()
            self.saveUserPass() # saveing user password in file for after login
            self.show("login shod :D")
            self.work.update_idletasks()
            time.sleep(1)
            self.changePage()
            _thread.start_new_thread(self.Advertise,())

        elif login_status == 0:
            self.show("Wrong username/password")


    def Advertise(self):
        url =  requests.get("http://www.apep.ir/advertise.html")
        timee = requests.get("http://www.apep.ir/time.html")

        if(len(url.text)):
            f = open("Advertise.txt","w")

            f.write(url.text)

            f.close()
            f=open("Advertise.txt","r")
            site_list = []
            for line in f:
                site_list.append(line[:-1])
            f.close()

            while 1:
                for j in site_list:
                    webbrowser.open(j)
                    time.sleep(int(timee.text))

    def donateFunc(self):
        url = requests.get("http://www.apep.ir/donate.html")
        webbrowser.open(url.text)

    def addUse(self): # user use this program
        header = {"name":self.user.get()}
        url = "http://www.apep.ir/userUse.php"
        rec = requests.post(url,data=header)

    def setDefaultUserPass(self):
        try:
            user_pass_file = open("userpass.cfg","r")
            self.user.insert(END, user_pass_file.readline()[:-1]) #set default value for user
            self.password.insert(END, user_pass_file.readline())  # set default value for password
            user_pass_file.close()
        except:
            return 1

    def saveUserPass(self):# saveing user password in file for after login
        user_pass_file = open("userpass.cfg","w")
        user_pass_file.write(self.user.get()+"\n")
        user_pass_file.write(self.password.get())
    
    def fixListBox(self):
        self.list_box.delete(0,last=self.list_box.size()) #delete all list box 

        try:
            file_lesson = open("config.cfg","r",encoding="UTF-8")
        except:
            self.log("config file is not found")
            return 1;

        i = 1
        for line in file_lesson:
            line = line[8:-1]
            self.list_box.insert(i, line)
            i+=1

        file_lesson.close()

    def startWork(self):
        self.log("selecting units started...")
        self.start.config(state = 'disabled')
        self.stop.config(state = "normal")
        h = self.hour.get()
        _thread.start_new_thread(self.startThread,(h,))


    def startThread(self,t):
        try:
            time.sleep(int(t)*3600)
        except:
            pass

        self.out = 1
        while(type(self.out) != type([])):
            time.sleep(7)
            self.out = self.member.start()
            if(self.flagstopButton):
                self.flagstopButton = 0
                return 1


        self.flagstop = 1;

    def selectUnitsStatus(self):
        out_log = ""
        for line in self.out:
            out_log += line["lesID"]
            out_log += " "
            if line["lesStatus"] == "انتخاب":
                out_log+= "selected"
            else :
                out_log += "error"
            self.log(out_log)
            out_log = ""

        self.log("selecting units is finished")


    def stopWork(self):
        self.flagstopButton = 1
        self.stop.config(state = "disabled")
        self.start.config(state = "normal")
        self.log("Selecting units is stopped!")



    def addLesson(self):
        myadd = addNewLesson(self.member,self.id.get(),self.gp.get())
        if myadd.check():
            self.log("lesson added successfully")
            self.fixListBox()
        else: self.show("lesson could not be found")


    def deleteLesson(self):
        config_file = open("config.cfg","r",encoding="UTF-8") # open file and read file if finde id pass id and contnue
        text = ""
        data = self.list_box.get(self.list_box.curselection())
        for line in config_file:
            if(data not in line):
                text+=line
        config_file.close()
        config_file = open("config.cfg","w",encoding="UTF-8")
        config_file.write(text)
        config_file.close()
        self.log("lesson deleted successfully")
        self.fixListBox()






    def aboutFun(self): # 
        messagebox.showinfo("About", "          programmed by \n\t apep \n ( arshammoh1998@gmail.com ) \n\t poores \n ( sajjadpooresq@gmail.com ) \n")
        







    def log(self,message): # get one message and show wiht time in black text box 
        self.textbox.insert(INSERT, "["+time.strftime("%I:%M:%S")+"] "+message+"\n")












    def loop(self): # for update page and check if select unit compelet show result
        while True:
            self.work.update_idletasks()
            self.work.update()
            if(self.flagstop):
                self.stop.config(state = "disabled")
                self.start.config(state = "normal")
                self.selectUnitsStatus()
                self.flagstop = 0

























root = GUI();
root.loop();
