from flask import Flask,render_template,request,redirect
import json
import secrets

app = Flask(__name__)

json_path = "app/db/url_map.json"
error_url ="https://www.google.com/search?q=url+does+not+exist"

@app.route('/', methods=['GET','POST'])
def func_main(): 
    # returns render_template("index.html"). 
    # the index.html itself contains form redirects to itself.
    # thus based on the data recieved from get/post request, 
    # it will load the same index.html, but with some minor alerts
    # print(request.endpoint)
    # print(request.form.to_dict())
    if (request.method=='POST'):
            form_type = request.form.get("key_form_type") #FORM_NEW_ENTRY FORM_DELETE FORM_UPDATE 
            if(form_type=="FORM_NEW_ENTRY"):
                return handleNewEntryInsertion()
            elif(form_type=="FORM_SECRET_KEY"):
                return handleManageRequest()
            elif(form_type=="FORM_DELETE"):
                # print(">>>>>>>>>>>>>>>>>>>>>>calling delete request")
                return handleDeleteRequest()
            else : 
                return handleUpdateRequest()
    else:

        return handleGetRequest()

@app.route('/u/<short_code>')
def func_api_sc_to_url(short_code): # no html method. returns a redirect to : "some_url"(based on $shortcode) or $error_url
    global error_url

    if(checkIfShortCodeAlreadyExists(short_code)):
        return redirect(getUrlFromShortCode(short_code))
    else :
        return redirect(error_url)
    
#######################################################################3

def handleGetRequest():
    return returnFinalHomePageRequest()
def handleNewEntryInsertion():
    url =request.form.get('req_url')
    sc = request.form.get('req_sc')

    # print(request.form.to_dict())
    
    # case either of url or sc is null
    if(url==None or sc==None or url=='' or sc==''):
        error = "Null inputs received"
        data=None
        return rtInsertionWithSession(error,data)

    isScInUse  = checkIfShortCodeAlreadyExists(sc)
    if(isScInUse):
        error = f"Your shortcode '{sc}' is already in use for another url"
        data=None
        return rtInsertionWithSession(error,data)

    del_id = saveToJsonAndReturnDelID(url,sc)

    if(del_id=="error"):
        error = "Sorry, some error occurred during generation of your short url. please try with later"
        data=None
        return rtInsertionWithSession(error,data)
        
    else:
        error = None
        data=[del_id,sc]
        return rtInsertionWithSession(error,data)
def rtInsertionWithSession(error=None,data=None): # returns render_template(html_name,ae=finalAlertEntry,a_ses=finalAlertSession)  #error= None or "msg" , data = None or [del_id,short_code]
    
    alertSessionNone    =  None
    alertSessionOn      = ["sc1","sc2","sc3"]
    
    alertEntryNone      = None
    alertEntrySucc      = {"type":"success", "data":["secret_key","shortcode"]}
    alertEntryFail      = {"type":"fail",  "msg": "$error"}
    

    # todo handle session

    finalAlertEntry =None
    finalAlertSession = None

    if(error==None):
        if(data==None):
            finalAlertEntry=None  #both error and data are null therefore GET request was generated. simply handle session and return
        else:
            finalAlertEntry=dict(alertEntrySucc) #data recieved but error didn't occured . Therefor a succesful insertion happenned. return page with success template
            finalAlertEntry["data"]=data
    else: # some error happenned(like code is already in use, or or null inputs received or some error occured during insertion etc)
        finalAlertEntry=dict(alertEntryFail)
        finalAlertEntry["msg"]=error

    # print("final alert entry=",finalAlertEntry)
    # print("finalAlertSession=",finalAlertSession)

    return returnFinalHomePageRequest(ae=finalAlertEntry,a_ses=finalAlertSession) 
def handleManageRequest(): 
    skey = request.form.get('req_skey')
    if(skey==None or skey==''):
        mg_req = {"type":"error","msg":"Null key recieved.","values":None}
        return returnFinalHomePageRequest(mg_req=mg_req)
    else:
        values = getAllValuesAsListFromDelID(skey)
        if(values==None):
            mg_req = {"type":"error","msg":"No entry recieved for this key.","values":None}
            return  returnFinalHomePageRequest(mg_req=mg_req)

        else:
            mg_req = {"type":"success","msg":None, "values":values}
            return  returnFinalHomePageRequest(mg_req=mg_req)
def handleDeleteRequest():

    # print(">>>>>>>>>>> call received")
    skey = request.form.get('req_scode_2')
    # print(">>>>>>>>>>skey",skey)
    
    del_resp = {}
    del_resp["type"]="error"
    del_resp["msg"]="some error occurred while updating data"

    # print(">>>>>>>>>>del_resp",del_resp)

    
    if(skey==None or skey==''):
        del_resp["msg"]= "Null inputs received"
    else:
        op = delEntryByShortCode(skey)
        if(op=="error"):
            del_resp["msg"]="some error occurred while updating data"
        else :
            del_resp["type"]="success"
            del_resp["msg"]="successfully deleted"
    
    # print(">>>>>>>>>>del_resp",del_resp)

    
    return returnFinalHomePageRequest(del_resp=del_resp)
def handleUpdateRequest():
    url  = request.form.get('req_url2')
    skey = request.form.get('req_scode_2')
    up_resp = {}
    up_resp["type"]="error"
    up_resp["msg"]="some error occurred while updating data"
    if(url==None or url =='' or skey==None or skey==''):
        up_resp["msg"]= "Null inputs received"
    else:
        op = updateUrlForShortCode(url,skey)
        if(op=="error"):
            up_resp["msg"]="some error occurred while updating data"
        else :
            up_resp["type"]="success"
            up_resp["msg"]="successfully updated"
    return returnFinalHomePageRequest(up_resp=up_resp)

def returnFinalHomePageRequest(ae=None,a_ses=None,mg_req=None,up_resp=None,del_resp=None):
    """
    ae
        =  None
        = ["sc1","sc2","sc3"]
    
    a_ses
        = None
        = {"type":"success", "data":["secret_key","shortcode"]}
        = {"type":"fail",  "msg": "$error"}

    mg_req
        = None
        = {"type":"error",  "msg":"Null key recieved","values":None}
        = {"type":"error",  "msg":"No entries  recieved for this key","values":None}
        = {"type":"success","msg":None                   ,"values":[del_id,short_code,url]}


    up_resp = None
        up_resp = {"type":"error" ,  "msg"="some error occurred while updating data"}
        up_resp = {"type":"error" ,  "msg"="null inputs received"}
        up_resp = {"type":"success" ,"msg"="succesfully updated"}
    del_resp = None
        del_resp = {"type":"error" ,  "msg"="some error occurred while deleting data"}
        del_resp = {"type":"error" ,  "msg"="null inputs received"}
        del_resp = {"type":"success" ,"msg"="succesfully updated"}
    
    """

    homepage = "index.html"
    # print(">>>>>>>>returning final page " )
    # print(f">>>>>>>>> ae     >>>>>>>>>>>>{ae}")
    # print(f">>>>>>>>> a_ses  >>>>>>>>>>{a_ses}")
    # print(f">>>>>>>>> mg_req  >>>>>>>>{mg_req}")
    # print(f">>>>>>>>> up_resp  >>>>>>>{up_resp}")
    # print(f">>>>>>>>>del_resp  >>>>>>{del_resp}")
    
    
    return render_template(homepage,ae=ae,a_ses=a_ses,mg_req=mg_req,up_resp=up_resp,del_resp=del_resp)


def checkIfShortCodeAlreadyExists(short_code): # True or False
    global json_path

    old_dict= {}
    with open(json_path) as myfile:
        old_dict = json.load(myfile)
        return short_code in old_dict
    return False
def getUrlFromShortCode(sc): #url(string) or $error_url(string)
    global json_path,error_url

    old_dict= {}
    with open(json_path) as myfile:
        old_dict = json.load(myfile)
        return old_dict[sc]['url']

    return error_url
def saveToJsonAndReturnDelID(url,sc,del_id=None): #del_id(string) or "error"
    # would overwrite if sc already exists
    # can also be used for passing unsafe ids, so not at all secure
    if(del_id==None):
        del_id = secrets.token_urlsafe(8)
    
    newdata = {'url':url,'del_id':del_id}
    global json_path

    old_dict= {}
    with open(json_path) as myfile:
        old_dict = json.load(myfile)
    old_dict[sc]=newdata

    with open(json_path,"w") as myfile:
        json.dump(old_dict,myfile,sort_keys=True,indent=4)
        return del_id
    
    return "error"
def getAllValuesAsListFromDelID(skey): #None or [del_id,short_code,url] (remember to disable key in user form)
    global json_path
    old_dict= {}
    with open(json_path) as myfile:
        old_dict = json.load(myfile)
        for k in old_dict:
            if(old_dict[k]["del_id"]==skey):
                return [ old_dict[k]["del_id"], k , old_dict[k]["url"]  ]
    
    return None
def updateUrlForShortCode(url,short_code): # "success" or "error"
    global json_path

    old_dict= {}
    with open(json_path) as myfile:
        old_dict = json.load(myfile)
        if(short_code in old_dict):
            saveToJsonAndReturnDelID(url,short_code,old_dict[short_code]['del_id'])
            return "success"

    return "error"
def delEntryByShortCode(short_code): # "success" or "error"
    global json_path

    old_dict= {}

    read_and_delete =False
    update= False

    with open(json_path) as myfile:
        old_dict = json.load(myfile)
        if(short_code in old_dict):
            del old_dict[short_code]
            read_and_delete =True

    with open(json_path,'w') as myfile:
        json.dump(old_dict,myfile,sort_keys=True,indent=4)
        update =True
    if(read_and_delete and update):
        return "success"
    else:
        return "error"

def temp():


    """ 
    Basic form . there can be...:

    - form opening same page after submitting
    - form opening different page after submitting
    - form opening no page at all, rather making ajax request and updating 
    the current form page with server response.

    we are not currently talking about the 3rd aproach, but 1st and 2nd approach 
    can be very easily achieved  using the exact same approach for both cases.
    And that approach will be as follows:

    1. our <form> tag in html has an attribute "action" which will call some particular
    file with the data on submission.(It could be a get or a post format, 
    but that's not imp right now)

    2. we could set this action to # to load the current page only. in the background,
    our browser is going to make a request at url localhost:5000/# (i.e our current page's)
    url. to the server. the server is gonna check the route and call the appropiate function.
    The appropiate function will also be recieving the data in the form of 
    request.form object of type multi-atr-Dict.Once we recieve such request we can either 
    load our current page with new modifications or redirect to some other page

    3. we could also directly pass url to another route (i.e url to another page) directly to 
    action so that some other function will handle which page to open next

    """

    """
    So when we "recieve" a request i.e our method is marked methods = GET/POST
    etc, we can simply "recieve" the various apects of a request in the 
    following manner :


    0. @app.route("/route , methods=['GET','POST','DELETE','PATCH'])
    def func():
            .............

    1.   x = request.method   // "POST" or "GET"
    2.   s_value     = request.values.get("some_key")  //the keys are usually the names in <input> tags // use values if you don't know weather the response is coming from get or post req
    3.   post_value2 = request.form.get("post_key") 
    3.2. post_value2 = request.form['post_key]//same as 3
    4. get_value   = request.args.get("get_key",default="optional_smth", type="optional_smth))
    5. route = request.path // "/route"

    6. filedata =request.files['file_key']    //https://flask.palletsprojects.com/en/1.1.x/quickstart/#file-uploads
    filedata.save("server_folder_path/filename.txt")

    7 print(request.__dict__) = all content related to request use for k,v in list(req.__dict__.items()) for traversal

    8. print(request.form.to_dict()) gives allformdata as k-v pairs



    8 request.form.validate_on_submit() / validate() / submit() TODO : uses flask wtf forms
    """

    x=5



if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)