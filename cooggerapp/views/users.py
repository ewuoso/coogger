# kullanıcıların yaptıkları tüm işlemler
from django.http import *
from django.shortcuts import render
from django.contrib.auth import *
from django.contrib.auth.models import User
from django.contrib import messages as ms
from cooggerapp.models import *
from cooggerapp.views import tools
from PIL import Image
import os

def user(request,username): 
    "herhangi kullanıcının anasayfası"
    pp = False
    if os.path.exists(os.getcwd()+"/coogger/media/users/pp/pp-"+username+".jpg"):
        pp = True
    content_list = ContentList.objects.filter(username = username)
    user_info = User.objects.filter(username = username)[0]
    elastic_search = dict(
     title = username+" | coogger",
     keywords ="coogger "+username+","+username+","+user_info.first_name+","+user_info.last_name+","+user_info.first_name+","+user_info.last_name,
     description =user_info.first_name+" | "+user_info.last_name+" ,"+username+" adı ile coogger'da"
    )

    output = dict(
        users = True,
        username = username,
        pp = pp,
        content_list = content_list,
        elastic_search = elastic_search,
    )
    return render (request,"users/user.html",output)

def upload_pp(request):
    "kullanıcılar profil resmini  değiştirmeleri için"
    username = request.user.username
    if request.method == "POST":
        try:
            image=request.FILES['u-upload-pp']
        except:
            ms.error(request,"Dosya alma sırasında bir sorun oluştu")
            return HttpResponseRedirect("/@"+username)

        with open(os.getcwd()+"/coogger/media/users/pp/pp-"+username+".jpg",'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        im = Image.open(os.getcwd()+"/coogger/media/users/pp/pp-"+username+".jpg")
        im.thumbnail((150,150))
        im.save(os.getcwd()+"/coogger/media/users/pp/pp-"+username+".jpg", "JPEG")
        return HttpResponseRedirect("/@"+username)

def u_topic(request,username,utopic):
    "kullanıcıların kendi hesaplarında açmış olduğu konulara yönlendirme"
    username = username.replace("/"+utopic,"")
    queryset = Blog.objects.filter(username = username,content_list = utopic)
    if not queryset.exists():
        ms.error(request,"{} adlı kullanıcı nın {} adlı bir yazı listesi yoktur".format(username,utopic))
        return HttpResponseRedirect("/")
    blogs = tools.paginator(request,queryset)
    category = tools.Topics().category

    elastic_search = dict(
     title = username+" | "+utopic+" | coogger",
     keywords = "coogger "+username+" "+utopic+","+utopic+",coogger "+utopic+","+utopic+","+username,
     description = username+" adlı kullanıcının "+utopic+" adlı içerik listesi",
    )
    output = dict(
        blog = blogs,
        topics_category = category,
        general = True,
        username = username,
        elastic_search = elastic_search,
    )
    return render(request,"blog/blogs.html",output)