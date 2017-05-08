#Version 1.0.5
import requests, datetime, time, sys

class Instagram(object):
    def __init__(self,username=None,password=None):
        self.s = requests.session()
        self.s.cookies.update({"sessionid":"",
                               "mid":"",
                               "ig_pr":"1",
                               "ig,vw":"1920",
                               "csrftoken":"",
                               "s_network":"",
                               "ds_user_id":""})
        self.s.headers.update({'Accept-Encoding': 'gzip, deflate',
                               'Accept-Language': 'en-GB,en-US;q=0.8,en;q=0.6',
                               'Connection': 'keep-alive',
                               'Content-Length': '0',
                               'Host': 'www.instagram.com',
                               'Origin': 'https://www.instagram.com',
                               'Referer': 'https://www.instagram.com/',
                               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
                               'X-Instagram-AJAX': '1',
                               'X-Requested-With': 'XMLHttpRequest'})
        
        if isinstance(username,str):
            self.username = username.lower()
            if isinstance(password,str):
                self.login(username,password)

    def login(self,username,password):
        self.username = username.lower()
        r = self.s.get("https://www.instagram.com/accounts/login/?force_classic_login")
        self.s.headers.update({"X-CSRFToken":r.cookies["csrftoken"]})
        r = self.s.post("https://www.instagram.com/accounts/login/?force_classic_login",
                        data={"username":username.lower(),
                              "password":password},
                        allow_redirects=True)
        self.csrftoken = r.cookies["csrftoken"]
        self.s.headers.update({"X-CSRFToken":self.csrftoken})
        if r.status_code == 200:
            if r.text.find(username) != -1:
                print "Sucessfully logged in!"
                return 200
            else:
                print "Failed to log in!"
                return 0
        if r.status_code == 400:
            print "Failed to log in!"
            print "User may be banned!"
            return 400

    def get_media(self,username,verbose=False):
        if verbose:
            print "Scanning page 1"
        r = self.s.get("https://www.instagram.com/"+username.lower()+"/media/")
        data = r.json()["items"]
        count = 1
        while len(r.json()["items"]) > 0:
            count += 1
            if verbose:
                print "Scanning page "+str(count)
            r = self.s.get("https://www.instagram.com/"+username.lower()+"/media/?max_id="+str(data[-1]["id"]))
            data += r.json()["items"]
        return data

    def get_media_by_query(self,username,photos=999999999):
        """Broken - left in for posterity"""
        q = self.query_ig_user(username=username,data=("media.after(0,"+str(photos)+")",("count",
                                                   "nodes",("id","caption","comments",("count",),\
                                                             "comments_disabled","date","display_src",\
                                                            "is_video","likes",("count",),"owner",\
                                                            ("id",)))))
        return q
                           

    def get_info(self,username):
        r = self.s.get("https://www.instagram.com/"+username.lower()+"/?__a=1")
        return r.json()

    def get_details(self,username,verbose=False,old_method=True):
        user = self.get_info(username)["user"]
        try:
            if old_method:
                media = sorted(self.get_media(username,verbose),key=lambda x:int(x["created_time"]))
            else:
                media = self.get_media_by_query(username)["media"]
                media = sorted(media["nodes"],key=lambda x:int(x["date"]))
        except Exception,e:
            print str(e)
        print "Username: "+user["username"]
        print "User ID: "+user["id"]
        print "Private: "+str(user["is_private"])
        print "Followed: "+str(user["followed_by_viewer"])
        print "Follows: "+str(user["follows_viewer"])
        print "-----------------------------"
        if user["full_name"]:
            print "Name: "+user["full_name"]
        print "Following: "+str(user["follows"]["count"])
        print "Followers: "+str(user["followed_by"]["count"])
        try:
            print str(float(user["followed_by"]["count"])/user["follows"]["count"])+" follower ratio."
        except ZeroDivisionError:
            print "0.0 follower ratio."
        print "Profile Picture: "+user["profile_pic_url_hd"].replace("/s320x320","")
        print "Number of Posts: "+str(user["media"]["count"])
        try:
            if old_method:
                print "Oldest Post: "+datetime.datetime.fromtimestamp(int(media[0]["created_time"])).strftime('%Y-%m-%d %H:%M:%S')
            else:
                print "Oldest Post: "+datetime.datetime.fromtimestamp(int(media[0]["date"])).strftime('%Y-%m-%d %H:%M:%S')
        except Exception,e:
            print "Failed to get oldest post."
            print str(e)

    def get_photo_likes(self,username,sort=None):
        media = self.get_media(username)
        user = self.get_info(username)["user"]
        
        sort_media = sorted(media,key=lambda x:int(x["created_time"]))
        oldest_timestamp = int(sort_media[0]["created_time"])
        newest_timestamp = int(sort_media[-1]["created_time"])
        estimated_min_followers = sort_media[0]["likes"]["count"]*1.5
        follower_range = user["followed_by"]["count"]-estimated_min_followers
        fps = follower_range/float(newest_timestamp-oldest_timestamp)
        
        data = []
        for photo in media:
            est_follow = round((float(fps)*(int(photo["created_time"])-oldest_timestamp))+estimated_min_followers)
            data.append({"id":photo["id"],
                         "url":photo["images"]["standard_resolution"]["url"],
                         "created_time":photo["created_time"],
                         "likes":photo["likes"]["count"],
                         "likes_per_follower":photo["likes"]["count"]/float(user["followed_by"]["count"]),
                         "estimated_followers":est_follow,
                         "est_lpf":photo["likes"]["count"]/est_follow
                         })
        if sort == None:
            return data
        elif sort == "est_lpf":
            data = sorted(data,reverse=True,key=lambda x:x[sort])
            return [x for x in data if int(x["created_time"]) != oldest_timestamp]
        else:
            return sorted(data,reverse=True,key=lambda x:x[sort])

    def get_photo_likes_by_query(self,username,sort=None):
        """Broken - left in for posterity"""
        media = self.get_media_by_query(username)["media"]
        user = self.get_info(username)["user"]
        
        sort_media = sorted(media["nodes"],key=lambda x:int(x["date"]))
        oldest_timestamp = int(sort_media[0]["date"])
        newest_timestamp = int(sort_media[-1]["date"])
        estimated_min_followers = sort_media[0]["likes"]["count"]*1.5
        follower_range = user["followed_by"]["count"]-estimated_min_followers
        fps = follower_range/float(newest_timestamp-oldest_timestamp)
        
        data = []
        for photo in media["nodes"]:
            est_follow = round((float(fps)*(int(photo["date"])-oldest_timestamp))+estimated_min_followers)
            try:
                data.append({"id":photo["id"],
                         "url":photo["display_src"],
                         "date":photo["date"],
                         "likes":photo["likes"]["count"],
                         "likes_per_follower":photo["likes"]["count"]/float(user["followed_by"]["count"]),
                         "estimated_followers":est_follow,
                         "est_lpf":photo["likes"]["count"]/est_follow,
                         "caption":photo["caption"]
                         })
            except:
                data.append({"id":photo["id"],
                         "url":photo["display_src"],
                         "date":photo["date"],
                         "likes":photo["likes"]["count"],
                         "likes_per_follower":photo["likes"]["count"]/float(user["followed_by"]["count"]),
                         "estimated_followers":est_follow,
                         "est_lpf":photo["likes"]["count"]/est_follow,
                         })
        if sort == None:
            return data
        elif sort == "est_lpf":
            data = sorted(data,reverse=True,key=lambda x:x[sort])
            return [x for x in data if int(x["date"]) != oldest_timestamp]
        else:
            return sorted(data,reverse=True,key=lambda x:x[sort])

    def get_most_recent_media_links(self,username):
        #media = self.get_media_by_query(username)["media"]["nodes"]
        #media = sorted(media,key=lambda x:int(x["date"]))
        #return media[-1]
        media = self.get_media(username)
        media[0]["images"]["standard_resolution"]["url"] = media[0]["images"]["standard_resolution"]["url"].replace("/s640x640","")
        try:
            return ("video",media[0]["videos"])
        except:
            return ("photo",media[0]["images"])

    def get_most_recent_media(self,username):
        media = self.get_media(username)
        return media[0]

    def get_username_from_id(self,uid):
        """Broken - left in for posterity"""
        uid = str(uid)
        q = self.s.post("https://instagram.com/query/",
                            data={"q":"ig_user("+uid+"){username}"})
        if q.json()["status"] == "ok":
            return q.json()["username"]
        else:
            return None

    def get_id_from_username(self,username):
        user = self.get_info(username)["user"]
        return user["id"]

    def query_ig_user(self,uid=None,username=None,data=None,dry=False):
        """Broken - left in for posterity"""
        if not isinstance(uid,(int,str)):
            if isinstance(username,str):
                user = self.get_info(username)
                uid = str(user["user"]["id"])
        else:
            uid = str(uid)

        def edit_query(data,string):
            if isinstance(data,tuple):
                for x in data:
                    if string[-1]=="}":
                        string+=","
                    if not isinstance(x,tuple):
                        string+=str(x)
                        string+=","
                    else:
                        string=string[:-1]+"{"
                        string = edit_query(x,string)
                        string+="}"
                if string[-1] == ",":
                    return string[:-1]
                else:
                    return string
            
        to_query = "{"
        to_query = edit_query(data,to_query)
        to_query += "}"
        if dry:
            return to_query
            
        q = self.s.post("https://instagram.com/query/",
                        data={"q":"ig_user("+uid+")"+to_query})
        j = q.json()
        if j["status"] == "ok":
            return j
        else:
            return j["status"]

    def get_followers(self,username,data=("username","id")):
        """Broken - left in for posterity"""
        followers = str(self.get_info(username)["user"]["followed_by"]["count"])
        return self.query_ig_user(username=username,
                                  data=("followed_by.first("+followers+")",
                                        ("nodes",data)))["followed_by"]["nodes"]

    def get_follows(self,username,data=("username","id")):
        """Broken - left in for posterity"""
        follows = str(self.get_info(username)["user"]["follows"]["count"])
        return self.query_ig_user(username=username,
                                  data=("follows.first("+follows+")",
                                        ("nodes",data)))["follows"]["nodes"]

    def follow(self,username):
        r = self.s.post("https://instagram.com/web/friendships/"+self.get_id_from_username(username)+"/follow/")
        return r.json()

    def get_oldest_photo(self,username):
        """Broken - left in for posterity"""
        media = self.get_media_by_query(username)["media"]["nodes"]
        media = sorted(media,key=lambda x:int(x["date"]))
        return media[0]

##    def stalker_follow(self,username,verbose=True):
##        """Broken - left in for posterity"""
##                try:
##                    following = i.get_info(user["username"])["user"]["followed_by_viewer"]
##                    requested = i.get_info(user["username"])["user"]["requested_by_viewer"]
##                    break
##                except:
##                    if verbose:
##                        print "Failed to get information about "+user["username"]
##                    failcount += 1
##                    time.sleep(5)
##            if failcount == 3:
##                if verbose:
##                    print "Skipping user "+user["username"]
##                continue
##            if (not following) and (not requested) and (user["username"] != i.username):
##                while failcount < 3:
##                    try:
##                        r = i.follow(user["username"])
##                        break
##                    except:
##                        if verbose:
##                            print "Failed to send request to "+user["username"]
##                if failcount == 3:
##                    if verbose:
##                        print "Skipping user "+user["username"]
##                    continue
##                try:
##                    if r["result"] == "requested":
##                        if verbose:
##                            print "Sending follow request to "+user["username"]
##                    else:
##                        if verbose:
##                            print "Followed "+user["username"]
##                except Exception,e:
##                    print r
##                    print user["username"]
##                    sys.exit(str(e))
##            else:
##                if verbose:
##                    print "Already following/requested "+user["username"]

