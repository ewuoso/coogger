#django
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.db.models import F

from social_django.models import UserSocialAuth
from social_django.models import AbstractUserSocialAuth, DjangoStorage, USER_MODEL

#choices
from cooggerapp.choices import *

#python
from bs4 import BeautifulSoup
import random
import datetime

#steem
from steem.post import Post
from steem.amount import Amount

# sc2py.
from sc2py.sc2py import Sc2
from sc2py.operations import Operations
from sc2py.operations import Comment_options
from sc2py.operations import Comment
from sc2py.operations import Follow
from sc2py.operations import Unfollow

# 3. other
from easysteem.easysteem import EasyFollow,Oogg
from bs4 import BeautifulSoup
import mistune

# TODO: editor.md için modelfield yap

class OtherInformationOfUsers(models.Model): # kullanıcıların diğer bilgileri
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    about = models.TextField()
    hmanycontent = models.IntegerField(default = 0)
    cooggerup_confirmation = models.BooleanField(default = False, verbose_name = "Do you want to join in curation trails of the cooggerup bot with your account?")
    percents = [i for i in range(100,0,-1)]
    cooggerup_percent = models.CharField(max_length = 3,choices = make_choices(percents),default = 0)
    vote_percent = models.CharField(max_length = 3,choices = make_choices(percents),default = 100)

    @property
    def follower_count(self):
        ef = EasyFollow(username = self.user.username,node = None)
        return ef.get_follower_count()

    @property
    def following_count(self):
        ef = EasyFollow(username = self.user.username,node = None)
        return ef.get_following_count()

    def s_info(self):
        return UserSocialAuth.objects.filter(uid = self.user)[0].extra_data

class Content(models.Model):
    # TODO: on_delete=models.CASCADE bunu bir araştır iyice ve ne yapman gerektiğine karar ver
    user = models.ForeignKey("auth.user" ,on_delete=models.CASCADE)
    content_list = models.CharField(max_length=30,verbose_name ="title of list",help_text = "Please, write your topic about your contents.")
    permlink = models.SlugField(max_length=200)
    title = models.CharField(max_length=100, verbose_name = "Title", help_text = "Be sure to choose the best title related to your content.")
    definition = models.CharField(max_length=400, verbose_name = "definition of content",help_text = "Briefly tell your readers about your content.")
    content = models.TextField()
    status = models.CharField(default = "shared", max_length=30,choices = make_choices(status_choices()) ,verbose_name = "content's status")
    tag = models.CharField(max_length=200, verbose_name = "keyword",help_text = "Write your keywords using spaces max:4 .") # taglar konuyu ilgilendiren içeriği anlatan kısa isimler google aramalarında çıkması için
    time = models.DateTimeField(default = timezone.now, verbose_name="date") # tarih bilgisi
    dor = models.CharField(default = 0, max_length=10)
    views = models.IntegerField(default = 0, verbose_name = "views")
    read = models.IntegerField(default = 0, verbose_name = "pageviews")
    hmanycomment=models.IntegerField(default = 0, verbose_name = "comments count")
    lastmod = models.DateTimeField(default = timezone.now, verbose_name="last modified date")
    draft = models.BooleanField(default = False,verbose_name = "content draft") # TODO:  status'e eklenebilir
    mod = models.ForeignKey("auth.user",on_delete=models.CASCADE,blank = True,null = True, related_name="moderator") # inceleyen mod bilgisi
    modcomment = models.BooleanField(default = False,verbose_name = "was it comment by mod")
    approved = models.CharField(blank = True,null = True,max_length=70,choices = make_choices(approved_choices()) ,verbose_name = "Why approved")
    cantapproved = models.CharField(blank = True,null = True,max_length=70,choices = make_choices(cantapproved_choices()) ,verbose_name = "Why can not approved")
    cooggerup = models.BooleanField(default = False,verbose_name = "was voting done")
    upvote = models.BooleanField(default = False,verbose_name = "upvote with cooggerup")

    class Meta:
        ordering = ['-time']

    def misdef(self):
        renderer = mistune.Renderer(escape=False)
        markdown = mistune.Markdown(renderer=renderer)
        return markdown(self.definition)

    @staticmethod
    def prepare_definition(text): # TODO:  zaten alınan ilk 400 karakterde resim varsa ikinci bir resmi almaması gerek
        renderer = mistune.Renderer(escape=False)
        markdown = mistune.Markdown(renderer=renderer)
        beautifultext = BeautifulSoup(markdown(text),"html.parser")
        try:
            src = beautifultext.find("img").get("src")
            alt = beautifultext.find("img").get("alt")
            image_markdown = "![{}]({})".format(alt,src)
            return beautifultext.text[0:400-len(image_markdown)-4]+"..."+image_markdown
        except:
            return  beautifultext.text[0:400-4]+"..."

    def get_absolute_url(self):
        return "@"+self.user.username+"/"+self.permlink

    @staticmethod
    def durationofread(text):
        reading_speed = 20 # 1 saniyede 20 harf okunursa
        read_content = BeautifulSoup(text, 'html.parser').get_text().replace(" ","")
        how_much_words = len(read_content)
        words_time = float((how_much_words/reading_speed)/60)
        return str(words_time)[:3]

    def save(self, *args, **kwargs): # for admin.py
        if self.content[0] != "\n":
            self.content = "\n" + self.content
        self.definition = self.prepare_definition(self.content)
        json_metadata = {
        "format":"markdown",
        "tags":self.ready_tags()["other"].split(),
        "app":"coogger/1.3.0",
        "community":"coogger",
        "content":{
            "status":self.status,
            "dor":self.dor,
            "content_list":self.content_list},
        "mod":{
            "user":self.mod.username,
            "approved":self.approved,
            "cantapproved":self.cantapproved,
            "cooggerup":self.cooggerup},
        }
        super(Content, self).save(*args, **kwargs)
        self.sc2_post(self.permlink, json_metadata)

    def content_save(self, *args, **kwargs): # for me
        if self.content[0] != "\n":
            self.content = "\n" + self.content
        self.content_list = slugify(self.content_list.lower())
        self.tag = self.ready_tags()["coogger"]
        self.dor = self.durationofread(self.content+self.title)
        self.permlink = slugify(self.title.lower())
        self.definition = self.prepare_definition(self.content)
        while  True: # hem coogger'da hemde sistem'de olmaması gerek ki kayıt sırasında sorun çıkmasın.
            try: # TODO:  buralarda sorun var aynı adres steemit de yokken coogger'da vardı ve döngüden çıkamadı.
                Content.objects.filter(user = self.user,permlink = self.permlink)[0] # db de varsa
                try:
                    Post(post = self.get_absolute_url()).url # sistem'de varsa
                    self.new_permlink() # change to self.permlink / link değişir
                except:
                    pass
            except:
                try:
                    Post(post = self.get_absolute_url()).url # sistem'de varsa
                    self.new_permlink() # change to self.permlink / link değişir
                except:
                    break
        super(Content, self).save(*args, **kwargs)
        return self.sc2_post(self.permlink, "save")

    def content_update(self,queryset,content):
        self.user = queryset[0].user
        if self.content[0] != "\n":
            self.content = "\n" + self.content
        self.title = content.title
        self.permlink = queryset[0].permlink # no change
        self.tag = content.tag
        self.status = queryset[0].status # düzenlemeni onay almaya ihtiyacı varmı diye
        # daha sonradan değiştirilebilir.
        self.draft = queryset[0].draft
        self.tag = self.ready_tags()["coogger"]
        self.dor = self.durationofread(self.content+self.title)
        queryset.update(definition = self.prepare_definition(content.content),
        content_list = slugify(content.content_list.lower()),
        permlink = self.permlink,
        title = self.title,
        content = self.content,
        tag = self.tag,
        draft = self.draft,
        dor = self.dor,
        status = self.status,
        lastmod = datetime.datetime.now(),
        )
        return self.sc2_post(self.permlink, "update")

    def sc2_post(self,permlink,json_metadata):
        def_name = json_metadata
        def get_access_token(self):
            access_token = UserSocialAuth.objects.filter(uid = self.user)[0].extra_data["access_token"]
            return str(access_token)

        if json_metadata == "update" or json_metadata == "save":
            json_metadata = {
            "format":"markdown",
            "tags":self.ready_tags()["other"].split(),
            "app":"coogger/1.3.0",
            "community":"coogger",
            "content":{"status":self.status,"dor":self.dor,"content_list":self.content_list},
            }
        ms = """\n\n----------
        \nPosted on [coogger.com](http://www.coogger.com)  - The platform that rewards information sharing
        \n- Read this content on [coogger](http://www.coogger.com/{})
        \n- Discover the {}'s [{}](http://www.coogger.com/{}/@{}) content list
        \n- Discover all coogger information about the [{}](http://www.coogger.com/explorer/list/{})
        \n----------""".format(self.get_absolute_url(),self.user.username,self.content_list,self.content_list,self.user.username,self.content_list,self.content_list)
        comment = Comment(
        parent_permlink = "coogger",
        author = str(self.user.username),
        permlink = permlink,
        title = self.title,
        body = self.content + ms,
        json_metadata = json_metadata,
        )
        if def_name == "save":
            comment_options = Comment_options(
            author = str(self.user.username),
            permlink = permlink,
            beneficiaries = {"account":"coogger","weight":100}
            )
            jsons = comment.json+comment_options.json
        else:
            jsons = comment.json
        op = Operations(json = jsons).json
        return Sc2(token = get_access_token(self),data = op).run

    def ready_tags(self):
        def clearly_tags(get_tag):
            clearly_tags = []
            tags = ""
            for i in get_tag:
                if i not in clearly_tags:
                    clearly_tags.append(i)
            for i in clearly_tags:
                if i == clearly_tags[-1]:
                    tags += slugify(i.lower())
                else:
                    tags += slugify(i.lower())+" "
            return tags
        get_tag = self.tag.split(" ")[:4]
        if get_tag[0] != "coogger":
            get_tag.insert(0,"coogger")
        return {"other":clearly_tags(get_tag),"coogger":clearly_tags(self.tag.split(" ")[:5])}

    def post_reward(self):
        try:
            post = Post(post = self.get_absolute_url())
            payout = round(self.pending_payout(post),4)
            return dict(total = payout)
        except:
            return dict(total = None)

    def pending_payout(self, post):
        payout = Amount(post.pending_payout_value).amount
        if payout == 0:
            payout = (Amount(post.total_payout_value).amount + Amount(post.curator_payout_value).amount)
        return payout

    def new_permlink(self):
        rand = str(random.randrange(9999))
        self.permlink += "-"+rand

class UserFollow(models.Model):
    user = models.ForeignKey("auth.user" ,on_delete=models.CASCADE)
    choices = models.CharField(max_length=15, choices = make_choices(follow()),verbose_name="website")
    adress = models.CharField(max_length=150, verbose_name = "write address / username")

class Following(models.Model):
    user = models.ForeignKey("auth.user" ,on_delete=models.CASCADE)
    which_user = models.ForeignKey("auth.user" ,on_delete=models.CASCADE, related_name="which_user")

    @property
    def get_token(self):
        access_token = UserSocialAuth.objects.filter(uid = self.user)[0].extra_data["access_token"]
        return str(access_token)

    def follow(self,*args, **kwargs):
        followjson = Follow(str(self.user.username),str(self.which_user.username)).json
        data = Operations(json = followjson).json
        Sc2(token = self.get_token,data = data).run
        super(Following, self).save(*args, **kwargs)

    def unfollow(self,*args, **kwargs):
        unjson = Unfollow(str(self.user.username),str(self.which_user.username)).json
        data = Operations(json = unjson).json
        Sc2(token = self.get_token,data = data).run
        super(Following, self).save(*args, **kwargs)

class SearchedWords(models.Model):
    word = models.CharField(unique=True,max_length=310)
    hmany = models.IntegerField(default = 1)

    def save(self, *args, **kwargs):
        try:
            super(SearchedWords, self).save(*args, **kwargs)
        except:
            SearchedWords.objects.filter(word = self.word).update(hmany = F("hmany") + 1)

class ReportModel(models.Model):
    choices_reports = make_choices(reports())
    user = models.ForeignKey("auth.user" ,on_delete=models.CASCADE,verbose_name = "şikayet eden kişi")
    content = models.ForeignKey("content" ,on_delete=models.CASCADE,verbose_name = "şikayet edilen içerik")
    complaints = models.CharField(choices = choices_reports,max_length=40,verbose_name="type of report")
    add = models.CharField(blank = True,null = True, max_length = 600,verbose_name = "Can you give more information ?")
    date = models.DateTimeField(default = timezone.now)

class Contentviews(models.Model):
    content = models.ForeignKey(Content ,on_delete=models.CASCADE)
    ip = models.GenericIPAddressField()

class CustomUserSocialAuth(AbstractUserSocialAuth):
    user = models.ForeignKey(USER_MODEL, related_name='custom_social_auth',on_delete=models.CASCADE)

class CustomDjangoStorage(DjangoStorage):
    user = CustomUserSocialAuth

# class Comment(models.Model):
#     content = models.ForeignKey(Content, related_name="content",on_delete = models.CASCADE)
#     parent = models.ForeignKey("self", null=True, blank=True, related_name="children",db_index=True, on_delete=models.CASCADE)
#     comment = models.CharField(max_length=500, unique=True)
#     date = models.DateTimeField(default = timezone.now, verbose_name="date")
