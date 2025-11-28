#coding:utf-8
__author__ = "ila"
import base64, copy, logging, os, time, xlrd, json, datetime
from django.http import JsonResponse
from django.apps import apps
from django.db.models.aggregates import Count,Sum
from .models import panjuxinxi
from util.codes import *
from util.auth import Auth
from util.common import Common
import util.message as mes
from django.db import connection
import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect
from django.db.models import Q
from util.baidubce_api import BaiDuBce
from .config_model import config





def panjuxinxi_register(request):
    if request.method in ["POST", "GET"]:
        msg = {'code': normal_code, "msg": mes.normal_code}
        req_dict = request.session.get("req_dict")


        error = panjuxinxi.createbyreq(panjuxinxi, panjuxinxi, req_dict)
        if error != None:
            msg['code'] = crud_error_code
            msg['msg'] = "用户已存在,请勿重复注册!"
        return JsonResponse(msg)

def panjuxinxi_login(request):
    if request.method in ["POST", "GET"]:
        msg = {'code': normal_code, "msg": mes.normal_code}
        req_dict = request.session.get("req_dict")

        datas = panjuxinxi.getbyparams(panjuxinxi, panjuxinxi, req_dict)
        if not datas:
            msg['code'] = password_error_code
            msg['msg'] = mes.password_error_code
            return JsonResponse(msg)
        try:
            __sfsh__= panjuxinxi.__sfsh__
        except:
            __sfsh__=None

        if  __sfsh__=='是':
            if datas[0].get('sfsh')!='是':
                msg['code']=other_code
                msg['msg'] = "账号已锁定，请联系管理员审核!"
                return JsonResponse(msg)
                
        req_dict['id'] = datas[0].get('id')
        return Auth.authenticate(Auth, panjuxinxi, req_dict)


def panjuxinxi_logout(request):
    if request.method in ["POST", "GET"]:
        msg = {
            "msg": "登出成功",
            "code": 0
        }

        return JsonResponse(msg)


def panjuxinxi_resetPass(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code}

        req_dict = request.session.get("req_dict")

        columns=  panjuxinxi.getallcolumn( panjuxinxi, panjuxinxi)

        try:
            __loginUserColumn__= panjuxinxi.__loginUserColumn__
        except:
            __loginUserColumn__=None
        username=req_dict.get(list(req_dict.keys())[0])
        if __loginUserColumn__:
            username_str=__loginUserColumn__
        else:
            username_str=username
        if 'mima' in columns:
            password_str='mima'
        else:
            password_str='password'

        init_pwd = '123456'
        recordsParam = {}
        recordsParam[username_str] = req_dict.get("username")
        records=panjuxinxi.getbyparams(panjuxinxi, panjuxinxi, recordsParam)
        if len(records)<1:
            msg['code'] = 400
            msg['msg'] = '用户不存在'
            return JsonResponse(msg)

        eval('''panjuxinxi.objects.filter({}='{}').update({}='{}')'''.format(username_str,username,password_str,init_pwd))
        
        return JsonResponse(msg)



def panjuxinxi_session(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code,"msg": mes.normal_code, "data": {}}

        req_dict={"id":request.session.get('params').get("id")}
        msg['data']  = panjuxinxi.getbyparams(panjuxinxi, panjuxinxi, req_dict)[0]

        return JsonResponse(msg)


def panjuxinxi_default(request):

    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code,"msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        req_dict.update({"isdefault":"是"})
        data=panjuxinxi.getbyparams(panjuxinxi, panjuxinxi, req_dict)
        if len(data)>0:
            msg['data']  = data[0]
        else:
            msg['data']  = {}
        return JsonResponse(msg)

def panjuxinxi_page(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")

        #获取全部列名
        columns=  panjuxinxi.getallcolumn( panjuxinxi, panjuxinxi)

        #当前登录用户所在表
        tablename = request.session.get("tablename")


            #authColumn=list(__authTables__.keys())[0]
            #authTable=__authTables__.get(authColumn)

            # if authTable==tablename:
                #params = request.session.get("params")
                #req_dict[authColumn]=params.get(authColumn)

        '''__authSeparate__此属性为真，params添加userid，后台只查询个人数据'''
        try:
            __authSeparate__=panjuxinxi.__authSeparate__
        except:
            __authSeparate__=None

        if __authSeparate__=="是":
            tablename=request.session.get("tablename")
            if tablename!="users" and 'userid' in columns:
                try:
                    req_dict['userid']=request.session.get("params").get("id")
                except:
                    pass

        #当项目属性hasMessage为”是”，生成系统自动生成留言板的表messages，同时该表的表属性hasMessage也被设置为”是”,字段包括userid（用户id），username(用户名)，content（留言内容），reply（回复）
        #接口page需要区分权限，普通用户查看自己的留言和回复记录，管理员查看所有的留言和回复记录
        try:
            __hasMessage__=panjuxinxi.__hasMessage__
        except:
            __hasMessage__=None
        if  __hasMessage__=="是":
            tablename=request.session.get("tablename")
            if tablename!="users":
                req_dict["userid"]=request.session.get("params").get("id")



        # 判断当前表的表属性isAdmin,为真则是管理员表
        # 当表属性isAdmin=”是”,刷出来的用户表也是管理员，即page和list可以查看所有人的考试记录(同时应用于其他表)
        __isAdmin__ = None

        allModels = apps.get_app_config('main').get_models()
        for m in allModels:
            if m.__tablename__==tablename:

                try:
                    __isAdmin__ = m.__isAdmin__
                except:
                    __isAdmin__ = None
                break

        # 当前表也是有管理员权限的表
        if  __isAdmin__ == "是" and 'panjuxinxi' != 'forum':
            if req_dict.get("userid") and 'panjuxinxi' != 'chat':
                del req_dict["userid"]

        else:
            #非管理员权限的表,判断当前表字段名是否有userid
            if tablename!="users" and 'panjuxinxi'[:7]!='discuss'and "userid" in panjuxinxi.getallcolumn(panjuxinxi,panjuxinxi):
                req_dict["userid"] = request.session.get("params").get("id")

        #当列属性authTable有值(某个用户表)[该列的列名必须和该用户表的登陆字段名一致]，则对应的表有个隐藏属性authTable为”是”，那么该用户查看该表信息时，只能查看自己的
        try:
            __authTables__=panjuxinxi.__authTables__
        except:
            __authTables__=None

        if __authTables__!=None and  __authTables__!={}:
            try:
                del req_dict['userid']
                # tablename=request.session.get("tablename")
                # if tablename=="users":
                    # del req_dict['userid']
                
            except:
                pass
            for authColumn,authTable in __authTables__.items():
                if authTable==tablename:
                    params = request.session.get("params")
                    req_dict[authColumn]=params.get(authColumn)
                    username=params.get(authColumn)
                    break

        q = Q()

        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  =panjuxinxi.page(panjuxinxi, panjuxinxi, req_dict, request, q)

        return JsonResponse(msg)

def panjuxinxi_autoSort(request):
    '''
    ．智能推荐功能(表属性：[intelRecom（是/否）],新增clicktime[前端不显示该字段]字段（调用info/detail接口的时候更新），按clicktime排序查询)
主要信息列表（如商品列表，新闻列表）中使用，显示最近点击的或最新添加的5条记录就行
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        if "clicknum"  in panjuxinxi.getallcolumn(panjuxinxi,panjuxinxi):
            req_dict['sort']='clicknum'
        elif "browseduration"  in panjuxinxi.getallcolumn(panjuxinxi,panjuxinxi):
            req_dict['sort']='browseduration'
        else:
            req_dict['sort']='clicktime'
        req_dict['order']='desc'
        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  = panjuxinxi.page(panjuxinxi,panjuxinxi, req_dict)

        return JsonResponse(msg)


def panjuxinxi_list(request):
    '''
    前台分页
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        if req_dict.__contains__('vipread'):
            del req_dict['vipread']

        #获取全部列名
        columns=  panjuxinxi.getallcolumn( panjuxinxi, panjuxinxi)
        #表属性[foreEndList]前台list:和后台默认的list列表页相似,只是摆在前台,否:指没有此页,是:表示有此页(不需要登陆即可查看),前要登:表示有此页且需要登陆后才能查看
        try:
            __foreEndList__=panjuxinxi.__foreEndList__
        except:
            __foreEndList__=None

        if __foreEndList__=="前要登":
            tablename=request.session.get("tablename")
            if tablename!="users" and 'userid' in columns:
                try:
                    req_dict['userid']=request.session.get("params").get("id")
                except:
                    pass
        #forrEndListAuth
        try:
            __foreEndListAuth__=panjuxinxi.__foreEndListAuth__
        except:
            __foreEndListAuth__=None


        #authSeparate
        try:
            __authSeparate__=panjuxinxi.__authSeparate__
        except:
            __authSeparate__=None

        if __foreEndListAuth__ =="是" and __authSeparate__=="是":
            tablename=request.session.get("tablename")
            if tablename!="users":
                req_dict['userid']=request.session.get("params",{"id":0}).get("id")

        tablename = request.session.get("tablename")
        if tablename == "users" and req_dict.get("userid") != None:#判断是否存在userid列名
            del req_dict["userid"]
        else:
            __isAdmin__ = None

            allModels = apps.get_app_config('main').get_models()
            for m in allModels:
                if m.__tablename__==tablename:

                    try:
                        __isAdmin__ = m.__isAdmin__
                    except:
                        __isAdmin__ = None
                    break

            if __isAdmin__ == "是":
                if req_dict.get("userid"):
                    # del req_dict["userid"]
                    pass
            else:
                #非管理员权限的表,判断当前表字段名是否有userid
                if "userid" in columns:
                    try:
                        pass
                    except:
                            pass
        #当列属性authTable有值(某个用户表)[该列的列名必须和该用户表的登陆字段名一致]，则对应的表有个隐藏属性authTable为”是”，那么该用户查看该表信息时，只能查看自己的
        try:
            __authTables__=panjuxinxi.__authTables__
        except:
            __authTables__=None

        if __authTables__!=None and  __authTables__!={} and __foreEndListAuth__=="是":
            try:
                del req_dict['userid']
            except:
                pass
            for authColumn,authTable in __authTables__.items():
                if authTable==tablename:
                    params = request.session.get("params")
                    req_dict[authColumn]=params.get(authColumn)
                    username=params.get(authColumn)
                    break
        
        if panjuxinxi.__tablename__[:7]=="discuss":
            try:
                del req_dict['userid']
            except:
                pass


        q = Q()

        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  = panjuxinxi.page(panjuxinxi, panjuxinxi, req_dict, request, q)

        return JsonResponse(msg)

def panjuxinxi_save(request):
    '''
    后台新增
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        if 'clicktime' in req_dict.keys():
            del req_dict['clicktime']
        tablename=request.session.get("tablename")
        __isAdmin__ = None
        allModels = apps.get_app_config('main').get_models()
        for m in allModels:
            if m.__tablename__==tablename:

                try:
                    __isAdmin__ = m.__isAdmin__
                except:
                    __isAdmin__ = None
                break


        #获取全部列名
        columns=  panjuxinxi.getallcolumn( panjuxinxi, panjuxinxi)
        if tablename!='users' and req_dict.get("userid")!=None and 'userid' in columns  and __isAdmin__!='是':
            params=request.session.get("params")
            req_dict['userid']=params.get('id')


        error= panjuxinxi.createbyreq(panjuxinxi,panjuxinxi, req_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error

        return JsonResponse(msg)


def panjuxinxi_add(request):
    '''
    前台新增
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")

        #获取全部列名
        columns=  panjuxinxi.getallcolumn( panjuxinxi, panjuxinxi)
        try:
            __authSeparate__=panjuxinxi.__authSeparate__
        except:
            __authSeparate__=None

        if __authSeparate__=="是":
            tablename=request.session.get("tablename")
            if tablename!="users" and 'userid' in columns:
                try:
                    req_dict['userid']=request.session.get("params").get("id")
                except:
                    pass

        try:
            __foreEndListAuth__=panjuxinxi.__foreEndListAuth__
        except:
            __foreEndListAuth__=None

        if __foreEndListAuth__ and __foreEndListAuth__!="否":
            tablename=request.session.get("tablename")
            if tablename!="users":
                req_dict['userid']=request.session.get("params").get("id")

        error= panjuxinxi.createbyreq(panjuxinxi,panjuxinxi, req_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg)

def panjuxinxi_thumbsup(request,id_):
    '''
     点赞：表属性thumbsUp[是/否]，刷表新增thumbsupnum赞和crazilynum踩字段，
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        id_=int(id_)
        type_=int(req_dict.get("type",0))
        rets=panjuxinxi.getbyid(panjuxinxi,panjuxinxi,id_)

        update_dict={
        "id":id_,
        }
        if type_==1:#赞
            update_dict["thumbsupnum"]=int(rets[0].get('thumbsupnum'))+1
        elif type_==2:#踩
            update_dict["crazilynum"]=int(rets[0].get('crazilynum'))+1
        error = panjuxinxi.updatebyparams(panjuxinxi,panjuxinxi, update_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg)


def panjuxinxi_info(request,id_):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}

        data = panjuxinxi.getbyid(panjuxinxi,panjuxinxi, int(id_))
        if len(data)>0:
            msg['data']=data[0]
            if msg['data'].__contains__("reversetime"):
                msg['data']['reversetime'] = msg['data']['reversetime'].strftime("%Y-%m-%d %H:%M:%S")
        #浏览点击次数
        try:
            __browseClick__= panjuxinxi.__browseClick__
        except:
            __browseClick__=None

        if __browseClick__=="是"  and  "clicknum"  in panjuxinxi.getallcolumn(panjuxinxi,panjuxinxi):
            try:
                clicknum=int(data[0].get("clicknum",0))+1
            except:
                clicknum=0+1
            click_dict={"id":int(id_),"clicknum":clicknum}
            ret=panjuxinxi.updatebyparams(panjuxinxi,panjuxinxi,click_dict)
            if ret!=None:
                msg['code'] = crud_error_code
                msg['msg'] = ret
        return JsonResponse(msg)

def panjuxinxi_detail(request,id_):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}

        data =panjuxinxi.getbyid(panjuxinxi,panjuxinxi, int(id_))
        if len(data)>0:
            msg['data']=data[0]
            if msg['data'].__contains__("reversetime"):
                msg['data']['reversetime'] = msg['data']['reversetime'].strftime("%Y-%m-%d %H:%M:%S")

        #浏览点击次数
        try:
            __browseClick__= panjuxinxi.__browseClick__
        except:
            __browseClick__=None

        if __browseClick__=="是"   and  "clicknum"  in panjuxinxi.getallcolumn(panjuxinxi,panjuxinxi):
            try:
                clicknum=int(data[0].get("clicknum",0))+1
            except:
                clicknum=0+1
            click_dict={"id":int(id_),"clicknum":clicknum}

            ret=panjuxinxi.updatebyparams(panjuxinxi,panjuxinxi,click_dict)
            if ret!=None:
                msg['code'] = crud_error_code
                msg['msg'] = retfo
        return JsonResponse(msg)


def panjuxinxi_update(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        if req_dict.get("mima") and "mima" not in panjuxinxi.getallcolumn(panjuxinxi,panjuxinxi) :
            del req_dict["mima"]
        if req_dict.get("password") and "password" not in panjuxinxi.getallcolumn(panjuxinxi,panjuxinxi) :
            del req_dict["password"]
        try:
            del req_dict["clicknum"]
        except:
            pass


        error = panjuxinxi.updatebyparams(panjuxinxi, panjuxinxi, req_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error

        return JsonResponse(msg)


def panjuxinxi_delete(request):
    '''
    批量删除
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")

        error=panjuxinxi.deletes(panjuxinxi,
            panjuxinxi,
             req_dict.get("ids")
        )
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg)


def panjuxinxi_vote(request,id_):
    '''
    浏览点击次数（表属性[browseClick:是/否]，点击字段（clicknum），调用info/detail接口的时候后端自动+1）、投票功能（表属性[vote:是/否]，投票字段（votenum）,调用vote接口后端votenum+1）
统计商品或新闻的点击次数；提供新闻的投票功能
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code}


        data= panjuxinxi.getbyid(panjuxinxi, panjuxinxi, int(id_))
        for i in data:
            votenum=i.get('votenum')
            if votenum!=None:
                params={"id":int(id_),"votenum":votenum+1}
                error=panjuxinxi.updatebyparams(panjuxinxi,panjuxinxi,params)
                if error!=None:
                    msg['code'] = crud_error_code
                    msg['msg'] = error
        return JsonResponse(msg)

def panjuxinxi_importExcel(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}

        excel_file = request.FILES.get("file", "")
        file_type = excel_file.name.split('.')[1]
        
        if file_type in ['xlsx', 'xls']:
            data = xlrd.open_workbook(filename=None, file_contents=excel_file.read())
            table = data.sheets()[0]
            rows = table.nrows
            
            try:
                for row in range(1, rows):
                    row_values = table.row_values(row)
                    req_dict = {}
                    panjuxinxi.createbyreq(panjuxinxi, panjuxinxi, req_dict)
                    
            except:
                pass
                
        else:
            msg.code = 500
            msg.msg = "文件类型错误"
                
        return JsonResponse(msg)

def panjuxinxi_sendemail(request):
    if request.method in ["POST", "GET"]:
        req_dict = request.session.get("req_dict")

        code = random.sample(['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'], 4)
        to = []
        to.append(req_dict['email'])

        send_mail('用户注册', '您的注册验证码是【'+''.join(code)+'】，请不要把验证码泄漏给其他人，如非本人请勿操作。', 'yclw9@qq.com', to, fail_silently = False)

        cursor = connection.cursor()
        cursor.execute("insert into emailregistercode(email,role,code) values('"+req_dict['email']+"','用户','"+''.join(code)+"')")

        msg = {
            "msg": "发送成功",
            "code": 0
        }

        return JsonResponse(msg)

# 推荐算法接口
def panjuxinxi_autoSort2(request):
    
    if request.method in ["POST", "GET"]:
        req_dict = request.session.get("req_dict")
        cursor = connection.cursor()
        leixing = set()
        try:
            cursor.execute("select inteltype from storeup where userid = %d"%(request.session.get("params").get("id"))+" and tablename = 'panjuxinxi' order by addtime desc")
            rows = cursor.fetchall()
            for row in rows:
                for item in row:
                    if item != None:
                        leixing.add(item)
        except:
            leixing = set()
        
        L = []
        cursor.execute("select * from panjuxinxi where $intelRecomColumn in ('%s"%("','").join(leixing)+"') union all select * from panjuxinxi where $intelRecomColumn not in('%s"%("','").join(leixing)+"')")
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)


        return JsonResponse({"code": 0, "msg": '',  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":5,"list": L[0:int(req_dict["limit"])]}})

def panjuxinxi_value(request, xColumnName, yColumnName, timeStatType):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        sql = ''
        if timeStatType == '日':
            sql = "SELECT DATE_FORMAT({0}, '%Y-%m-%d') {0}, sum({1}) total FROM panjuxinxi {2} GROUP BY DATE_FORMAT({0}, '%Y-%m-%d') LIMIT 10".format(xColumnName, yColumnName, where, '%Y-%m-%d')

        if timeStatType == '月':
            sql = "SELECT DATE_FORMAT({0}, '%Y-%m') {0}, sum({1}) total FROM panjuxinxi {2} GROUP BY DATE_FORMAT({0}, '%Y-%m') LIMIT 10".format(xColumnName, yColumnName, where, '%Y-%m')

        if timeStatType == '年':
            sql = "SELECT DATE_FORMAT({0}, '%Y') {0}, sum({1}) total FROM panjuxinxi {2} GROUP BY DATE_FORMAT({0}, '%Y') LIMIT 10".format(xColumnName, yColumnName, where, '%Y')
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg)

def panjuxinxi_o_value(request, xColumnName, yColumnName):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        
        sql = "SELECT {0}, sum({1}) AS total FROM panjuxinxi {2} GROUP BY {0} LIMIT 10".format(xColumnName, yColumnName, where)
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg)




def panjuxinxi_count(request):
    '''
    总数接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        req_dict = request.session.get("req_dict")
        where = ' where 1 = 1 '
        for key in req_dict:
            if req_dict[key] != None:
                where = where + " and key like '{0}'".format(req_dict[key])
        
        sql = "SELECT count(*) AS count FROM panjuxinxi {0}".format(where)
        count = 0
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            count = online_dict['count']
        msg['data'] = count

        return JsonResponse(msg)


def panjuxinxi_group(request, columnName):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '

        sql = "SELECT COUNT(*) AS total, " + columnName + " FROM panjuxinxi " + where + " GROUP BY " + columnName + " LIMIT 10" 
        
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    # online_dict[key] = online_dict[key].strftime("%Y-%m-%d %H:%M:%S")
                    online_dict[key] = online_dict[key].strftime("%Y-%m-%d")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg)

def panjuxinxi_sectionStat_pingfen(request):
    '''
    新增分段统计接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        token = request.META.get('HTTP_TOKEN')
        decode_str = eval(base64.b64decode(token).decode("utf8"))

        sql = """
            SELECT '6分以下' as pingfen,case when t.6分以下 is null then 0 else t.6分以下 end total
            from 
            (select
            sum(case when pingfen <= 6 then 1 else 0 end) as 6分以下,            sum(case when pingfen >= 6 and pingfen <= 7 then 1 else 0 end) as 6至7分,            sum(case when pingfen >= 7 and pingfen <= 8 then 1 else 0 end) as 7至8分,            sum(case when pingfen >= 8 and pingfen <= 9 then 1 else 0 end) as 8至9分,            sum(case when pingfen >= 9 then 1 else 0 end) as 9分以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '6至7分' as pingfen,case when t.6至7分 is null then 0 else t.6至7分 end total
            from 
            (select
            sum(case when pingfen <= 6 then 1 else 0 end) as 6分以下,            sum(case when pingfen >= 6 and pingfen <= 7 then 1 else 0 end) as 6至7分,            sum(case when pingfen >= 7 and pingfen <= 8 then 1 else 0 end) as 7至8分,            sum(case when pingfen >= 8 and pingfen <= 9 then 1 else 0 end) as 8至9分,            sum(case when pingfen >= 9 then 1 else 0 end) as 9分以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '7至8分' as pingfen,case when t.7至8分 is null then 0 else t.7至8分 end total
            from 
            (select
            sum(case when pingfen <= 6 then 1 else 0 end) as 6分以下,            sum(case when pingfen >= 6 and pingfen <= 7 then 1 else 0 end) as 6至7分,            sum(case when pingfen >= 7 and pingfen <= 8 then 1 else 0 end) as 7至8分,            sum(case when pingfen >= 8 and pingfen <= 9 then 1 else 0 end) as 8至9分,            sum(case when pingfen >= 9 then 1 else 0 end) as 9分以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '8至9分' as pingfen,case when t.8至9分 is null then 0 else t.8至9分 end total
            from 
            (select
            sum(case when pingfen <= 6 then 1 else 0 end) as 6分以下,            sum(case when pingfen >= 6 and pingfen <= 7 then 1 else 0 end) as 6至7分,            sum(case when pingfen >= 7 and pingfen <= 8 then 1 else 0 end) as 7至8分,            sum(case when pingfen >= 8 and pingfen <= 9 then 1 else 0 end) as 8至9分,            sum(case when pingfen >= 9 then 1 else 0 end) as 9分以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '9分以上' as pingfen,case when t.9分以上 is null then 0 else t.9分以上 end total
            from 
            (select
            sum(case when pingfen <= 6 then 1 else 0 end) as 6分以下,            sum(case when pingfen >= 6 and pingfen <= 7 then 1 else 0 end) as 6至7分,            sum(case when pingfen >= 7 and pingfen <= 8 then 1 else 0 end) as 7至8分,            sum(case when pingfen >= 8 and pingfen <= 9 then 1 else 0 end) as 8至9分,            sum(case when pingfen >= 9 then 1 else 0 end) as 9分以上            from panjuxinxi
            {where}
            ) t
        """.format(where=where)
        
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg)
def panjuxinxi_sectionStat_bofangliang(request):
    '''
    新增分段统计接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        token = request.META.get('HTTP_TOKEN')
        decode_str = eval(base64.b64decode(token).decode("utf8"))

        sql = """
            SELECT '1亿以内' as bofangliang,case when t.1亿以内 is null then 0 else t.1亿以内 end total
            from 
            (select
            sum(case when bofangliang <= 100000000 then 1 else 0 end) as 1亿以内,            sum(case when bofangliang >= 100000000 and bofangliang <= 200000000 then 1 else 0 end) as 1亿至2亿,            sum(case when bofangliang >= 200000000 and bofangliang <= 300000000 then 1 else 0 end) as 2亿至3亿,            sum(case when bofangliang >= 300000000 and bofangliang <= 500000000 then 1 else 0 end) as 3亿至5亿,            sum(case when bofangliang >= 500000000 then 1 else 0 end) as 5亿以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '1亿至2亿' as bofangliang,case when t.1亿至2亿 is null then 0 else t.1亿至2亿 end total
            from 
            (select
            sum(case when bofangliang <= 100000000 then 1 else 0 end) as 1亿以内,            sum(case when bofangliang >= 100000000 and bofangliang <= 200000000 then 1 else 0 end) as 1亿至2亿,            sum(case when bofangliang >= 200000000 and bofangliang <= 300000000 then 1 else 0 end) as 2亿至3亿,            sum(case when bofangliang >= 300000000 and bofangliang <= 500000000 then 1 else 0 end) as 3亿至5亿,            sum(case when bofangliang >= 500000000 then 1 else 0 end) as 5亿以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '2亿至3亿' as bofangliang,case when t.2亿至3亿 is null then 0 else t.2亿至3亿 end total
            from 
            (select
            sum(case when bofangliang <= 100000000 then 1 else 0 end) as 1亿以内,            sum(case when bofangliang >= 100000000 and bofangliang <= 200000000 then 1 else 0 end) as 1亿至2亿,            sum(case when bofangliang >= 200000000 and bofangliang <= 300000000 then 1 else 0 end) as 2亿至3亿,            sum(case when bofangliang >= 300000000 and bofangliang <= 500000000 then 1 else 0 end) as 3亿至5亿,            sum(case when bofangliang >= 500000000 then 1 else 0 end) as 5亿以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '3亿至5亿' as bofangliang,case when t.3亿至5亿 is null then 0 else t.3亿至5亿 end total
            from 
            (select
            sum(case when bofangliang <= 100000000 then 1 else 0 end) as 1亿以内,            sum(case when bofangliang >= 100000000 and bofangliang <= 200000000 then 1 else 0 end) as 1亿至2亿,            sum(case when bofangliang >= 200000000 and bofangliang <= 300000000 then 1 else 0 end) as 2亿至3亿,            sum(case when bofangliang >= 300000000 and bofangliang <= 500000000 then 1 else 0 end) as 3亿至5亿,            sum(case when bofangliang >= 500000000 then 1 else 0 end) as 5亿以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '5亿以上' as bofangliang,case when t.5亿以上 is null then 0 else t.5亿以上 end total
            from 
            (select
            sum(case when bofangliang <= 100000000 then 1 else 0 end) as 1亿以内,            sum(case when bofangliang >= 100000000 and bofangliang <= 200000000 then 1 else 0 end) as 1亿至2亿,            sum(case when bofangliang >= 200000000 and bofangliang <= 300000000 then 1 else 0 end) as 2亿至3亿,            sum(case when bofangliang >= 300000000 and bofangliang <= 500000000 then 1 else 0 end) as 3亿至5亿,            sum(case when bofangliang >= 500000000 then 1 else 0 end) as 5亿以上            from panjuxinxi
            {where}
            ) t
        """.format(where=where)
        
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg)
def panjuxinxi_sectionStat_danmu(request):
    '''
    新增分段统计接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        token = request.META.get('HTTP_TOKEN')
        decode_str = eval(base64.b64decode(token).decode("utf8"))

        sql = """
            SELECT '10万以下' as danmu,case when t.10万以下 is null then 0 else t.10万以下 end total
            from 
            (select
            sum(case when danmu <= 100000 then 1 else 0 end) as 10万以下,            sum(case when danmu >= 100000 and danmu <= 500000 then 1 else 0 end) as 10万至50万,            sum(case when danmu >= 500000 and danmu <= 1000000 then 1 else 0 end) as 50万至1百万,            sum(case when danmu >= 1000000 and danmu <= 5000000 then 1 else 0 end) as 1百万至5百万,            sum(case when danmu >= 5000000 then 1 else 0 end) as 5百万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '10万至50万' as danmu,case when t.10万至50万 is null then 0 else t.10万至50万 end total
            from 
            (select
            sum(case when danmu <= 100000 then 1 else 0 end) as 10万以下,            sum(case when danmu >= 100000 and danmu <= 500000 then 1 else 0 end) as 10万至50万,            sum(case when danmu >= 500000 and danmu <= 1000000 then 1 else 0 end) as 50万至1百万,            sum(case when danmu >= 1000000 and danmu <= 5000000 then 1 else 0 end) as 1百万至5百万,            sum(case when danmu >= 5000000 then 1 else 0 end) as 5百万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '50万至1百万' as danmu,case when t.50万至1百万 is null then 0 else t.50万至1百万 end total
            from 
            (select
            sum(case when danmu <= 100000 then 1 else 0 end) as 10万以下,            sum(case when danmu >= 100000 and danmu <= 500000 then 1 else 0 end) as 10万至50万,            sum(case when danmu >= 500000 and danmu <= 1000000 then 1 else 0 end) as 50万至1百万,            sum(case when danmu >= 1000000 and danmu <= 5000000 then 1 else 0 end) as 1百万至5百万,            sum(case when danmu >= 5000000 then 1 else 0 end) as 5百万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '1百万至5百万' as danmu,case when t.1百万至5百万 is null then 0 else t.1百万至5百万 end total
            from 
            (select
            sum(case when danmu <= 100000 then 1 else 0 end) as 10万以下,            sum(case when danmu >= 100000 and danmu <= 500000 then 1 else 0 end) as 10万至50万,            sum(case when danmu >= 500000 and danmu <= 1000000 then 1 else 0 end) as 50万至1百万,            sum(case when danmu >= 1000000 and danmu <= 5000000 then 1 else 0 end) as 1百万至5百万,            sum(case when danmu >= 5000000 then 1 else 0 end) as 5百万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '5百万以上' as danmu,case when t.5百万以上 is null then 0 else t.5百万以上 end total
            from 
            (select
            sum(case when danmu <= 100000 then 1 else 0 end) as 10万以下,            sum(case when danmu >= 100000 and danmu <= 500000 then 1 else 0 end) as 10万至50万,            sum(case when danmu >= 500000 and danmu <= 1000000 then 1 else 0 end) as 50万至1百万,            sum(case when danmu >= 1000000 and danmu <= 5000000 then 1 else 0 end) as 1百万至5百万,            sum(case when danmu >= 5000000 then 1 else 0 end) as 5百万以上            from panjuxinxi
            {where}
            ) t
        """.format(where=where)
        
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg)
def panjuxinxi_sectionStat_pfrs(request):
    '''
    新增分段统计接口
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}
        
        where = ' where 1 = 1 '
        token = request.META.get('HTTP_TOKEN')
        decode_str = eval(base64.b64decode(token).decode("utf8"))

        sql = """
            SELECT '5万以内' as pfrs,case when t.5万以内 is null then 0 else t.5万以内 end total
            from 
            (select
            sum(case when pfrs <= 50000 then 1 else 0 end) as 5万以内,            sum(case when pfrs >= 50000 and pfrs <= 100000 then 1 else 0 end) as 5万至10万,            sum(case when pfrs >= 100000 and pfrs <= 200000 then 1 else 0 end) as 10万至20万,            sum(case when pfrs >= 200000 and pfrs <= 300000 then 1 else 0 end) as 20万至30万,            sum(case when pfrs >= 300000 and pfrs <= 400000 then 1 else 0 end) as 30万至40万,            sum(case when pfrs >= 400000 then 1 else 0 end) as 40万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '5万至10万' as pfrs,case when t.5万至10万 is null then 0 else t.5万至10万 end total
            from 
            (select
            sum(case when pfrs <= 50000 then 1 else 0 end) as 5万以内,            sum(case when pfrs >= 50000 and pfrs <= 100000 then 1 else 0 end) as 5万至10万,            sum(case when pfrs >= 100000 and pfrs <= 200000 then 1 else 0 end) as 10万至20万,            sum(case when pfrs >= 200000 and pfrs <= 300000 then 1 else 0 end) as 20万至30万,            sum(case when pfrs >= 300000 and pfrs <= 400000 then 1 else 0 end) as 30万至40万,            sum(case when pfrs >= 400000 then 1 else 0 end) as 40万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '10万至20万' as pfrs,case when t.10万至20万 is null then 0 else t.10万至20万 end total
            from 
            (select
            sum(case when pfrs <= 50000 then 1 else 0 end) as 5万以内,            sum(case when pfrs >= 50000 and pfrs <= 100000 then 1 else 0 end) as 5万至10万,            sum(case when pfrs >= 100000 and pfrs <= 200000 then 1 else 0 end) as 10万至20万,            sum(case when pfrs >= 200000 and pfrs <= 300000 then 1 else 0 end) as 20万至30万,            sum(case when pfrs >= 300000 and pfrs <= 400000 then 1 else 0 end) as 30万至40万,            sum(case when pfrs >= 400000 then 1 else 0 end) as 40万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '20万至30万' as pfrs,case when t.20万至30万 is null then 0 else t.20万至30万 end total
            from 
            (select
            sum(case when pfrs <= 50000 then 1 else 0 end) as 5万以内,            sum(case when pfrs >= 50000 and pfrs <= 100000 then 1 else 0 end) as 5万至10万,            sum(case when pfrs >= 100000 and pfrs <= 200000 then 1 else 0 end) as 10万至20万,            sum(case when pfrs >= 200000 and pfrs <= 300000 then 1 else 0 end) as 20万至30万,            sum(case when pfrs >= 300000 and pfrs <= 400000 then 1 else 0 end) as 30万至40万,            sum(case when pfrs >= 400000 then 1 else 0 end) as 40万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '30万至40万' as pfrs,case when t.30万至40万 is null then 0 else t.30万至40万 end total
            from 
            (select
            sum(case when pfrs <= 50000 then 1 else 0 end) as 5万以内,            sum(case when pfrs >= 50000 and pfrs <= 100000 then 1 else 0 end) as 5万至10万,            sum(case when pfrs >= 100000 and pfrs <= 200000 then 1 else 0 end) as 10万至20万,            sum(case when pfrs >= 200000 and pfrs <= 300000 then 1 else 0 end) as 20万至30万,            sum(case when pfrs >= 300000 and pfrs <= 400000 then 1 else 0 end) as 30万至40万,            sum(case when pfrs >= 400000 then 1 else 0 end) as 40万以上            from panjuxinxi
            {where}
            ) t
            union all
            SELECT '40万以上' as pfrs,case when t.40万以上 is null then 0 else t.40万以上 end total
            from 
            (select
            sum(case when pfrs <= 50000 then 1 else 0 end) as 5万以内,            sum(case when pfrs >= 50000 and pfrs <= 100000 then 1 else 0 end) as 5万至10万,            sum(case when pfrs >= 100000 and pfrs <= 200000 then 1 else 0 end) as 10万至20万,            sum(case when pfrs >= 200000 and pfrs <= 300000 then 1 else 0 end) as 20万至30万,            sum(case when pfrs >= 300000 and pfrs <= 400000 then 1 else 0 end) as 30万至40万,            sum(case when pfrs >= 400000 then 1 else 0 end) as 40万以上            from panjuxinxi
            {where}
            ) t
        """.format(where=where)
        
        L = []
        cursor = connection.cursor()
        cursor.execute(sql)
        desc = cursor.description
        data_dict = [dict(zip([col[0] for col in desc], row)) for row in cursor.fetchall()] 
        for online_dict in data_dict:
            for key in online_dict:
                if 'datetime.datetime' in str(type(online_dict[key])):
                    online_dict[key] = online_dict[key].strftime(
                        "%Y-%m-%d %H:%M:%S")
                else:
                    pass
            L.append(online_dict)
        msg['data'] = L

        return JsonResponse(msg)








