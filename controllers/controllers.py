#-*- coding: utf-8 -*-
from odoo import http
import json
from xmlrpc.client import ServerProxy as XMLServerProxy
import datetime
import requests
import random
import time
import uuid
import logging
from os import urandom
from firebase_admin import messaging
import paho.mqtt.client as mqtt

apikey="a*zi$ct¥er@96JEPMEZ00845"
url = "http://91.134.28.181:8069"
db = "crone"
username = 'bayebass0@gmail.com'
password = "bayebass0@"

_logger = logging.getLogger(__name__)

class MoneyManagement(http.Controller):

    #Mqtt send
    def Mqtt_pub(topic,message):
    
        client = mqtt.Client()
        #client.username_pw_set("","")
        client.connect("91.121.253.231")
        client.publish(topic, message)
    
    #send notification
    def notification(cle,text='Votre rendez-vous aura lieu dans trente minutes.'):
        try:
            registration_token = cle
            message = messaging.Message(
                    data={'score': '850','time': '2:45',},
                notification=messaging.Notification(title='Rendez-vous',body=text,),
                token=registration_token,
                )
            response = messaging.send(message)
            _logger.debug('Successfully sent message:%s', response)
        except Exception as e:
            _logger.debug('Exeption:%s', e)
            

    @http.route('/money_management/money_management/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/money_management/money_management/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('money_management.listing', {
            'root': '/money_management/money_management',
            'objects': http.request.env['money_management.money_management'].search([]),
        })

    @http.route('/money_management/money_management/objects/<model("money_management.money_management"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('money_management.object', {
            'object': obj
        })
    
    @http.route(
        '/api/registration/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def client_registration(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                phone=data["telephone"]
                code = random.randint(1111,9999)
                sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                uid = sock_common.login(db, username, password)
                sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')
                client_exist=sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[['telephone', '=', phone]]],{'fields': ['id','name','pin'], 'limit': 1})
                if len(client_exist) > 0:
                    client_id = client_exist[0]["id"]
                    #if 'cni_recto' in data and 'cni_verso' in data :
                    #    sock.execute_kw(db, uid, password,'money_management.client', 'write',[[client_id], {'name': data["name"],'adresse':data["adresse"],'validation_code':str(code),'ville': data["ville"],'sex': data["sex"],'age': data["age"],'cni_recto':data["cni_recto"],'cni_verso':data["cni_verso"]}])    
                    if 'name' in data and 'sex' in data and len(client_exist[0]["name"])>0:
                        response["message"]="Impossible de s'inscrire à nouveau"
                        response["responseCode"]=0
                        return response

                    elif 'name' in data and 'sex' in data :
                        sock.execute_kw(db, uid, password,'money_management.client', 'write',[[client_id], {'name': data["name"],'validation_code':str(code),'sex': data["sex"],'age': data["age"]}])
                    else:
                        http.request.env['money_management.client'].sudo().search([('telephone','=',phone)]).write({"validation_code": str(code)})
                    #    sock.execute_kw(db, uid, password,'money_management.client', 'write',[[client_exist[0]["id"]], {'name': data["name"],'adresse':data["adresse"],'validation_code':str(code),'region': data["region"],'ville': data["ville"],'sex': data["sex"],'age': data["age"],}])
                    
                    client_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[['account_client_owner', '=', client_id ]]],{'fields': ['id','account_number','date_creation'], 'limit': 1})
                    #client_account = http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_exist[0]["id"])])
                    
                    response["message"]="Account with phone number allready exist"
                    response["responseCode"]=1
                    response["client_id"]=client_id
                    response["client_name"]=client_exist[0]["name"]
                    response["client_adress"]=""
                    response["account_number"]=client_account[0]['account_number']
                    response["account_created_date"]=client_account[0]['date_creation']

                    client = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[[ 'telephone', '=', phone ]]],{'fields': ['id','validation_code'], 'limit': 1})
                    payload = {
                        'number': phone,
                        'content': 'Votre code de validation CRONE est : '+str(client[0]['validation_code']),
                        'key':'dZaN51165420050074130180748146013011022542127230465869',
                    }
                    #print(contens)
                    requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                    return response
                else:
                    data['validation_code']=str(code)
                    _logger.debug('Client data: %s  ',data )
                    client_id =  http.request.env['money_management.client'].sudo().create(data)

                    
                    #client_account =sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', clien[0]['id'] ]]],{'fields': ['id','account_number','date_creation'], 'limit': 1})
                    client_account = http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id[0]['id'])])
                   
                    response["message"]="User registration complete"
                    response["responseCode"] = 1
                    response["client_id"]=client_id[0]['id']
                    response["account_number"]=client_account[0]['account_number']
                    response["account_created_date"]=client_account[0]['date_creation']

                    response["pin_exist"] = False

                    payload = {
                    'number': phone,
                    'content': 'Votre code de validation CRONE est : '+str(client_id[0]['validation_code']),
                    'key':'dZaN51165420050074130180748146013011022542127230465869',
                    }
                    #print(contens)
                    requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)

                    return response


                """ #client=http.request.env['money_management.client'].sudo().search([('telephone', '=', phone)])
                client = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[[ 'telephone', '=', phone ]]],{'fields': ['id','validation_code'], 'limit': 1})
                payload = {
                    'number': phone,
                    'content': 'Votre code de validation CRONE est : '+str(client[0]['validation_code']),
                    'key':'dZaN51165420050074130180748146013011022542127230465869',
                }
                #print(contens)
                requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload) """
                
        
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        return response
        #return record.id

    #api for qr_code scanning
    @http.route(
        '/api/create_avoir/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def new_avoir(self, **post):
        response={}
        try:
            data=post["data"]
            boutique_qr=data["qr"]
            amount=data["amount"]
            client_id=data["client_id"]
            key=post["api_key"]
            if key == apikey:
                sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                uid = sock_common.login(db, username, password)
                sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')
                caisses=sock.execute_kw(db, uid, password,
                    'money_management.caisse', 'search_read',
                    [[['code_marchand', '=', boutique_qr]]],
                    {'fields': ['id','designation','solde'], 'limit': 1})
                if len(caisses) > 0:
                    solde=caisses[0]["solde"]
                    if amount > solde:
                        response["message"]="Le solde de la caisse est insuffisante !"
                        response["responseCode"]=0
                    else:
                        id_caisse=caisses[0]["id"]
                        new_solde=solde-amount
                        sock.execute_kw(db, uid, password,'money_management.caisse', 'write',[[id_caisse], {'solde': new_solde}])
                        client=sock.execute_kw(db, uid, password,
                            'money_management.client', 'search_read',
                            [[['id', '=', client_id]]],
                            {'fields': ['solde'], 'limit': 1})
                        new_client_solde=amount+client[0]["solde"]
                        avoir_id=sock.execute(db, uid, password, 'money_management.avoir', 'create', {"caisse_id":id_caisse, "client_id":client_id,"montant":amount})
                        sock.execute_kw(db, uid, password,'money_management.client', 'write',[[client_id], {'solde': new_client_solde}])
                        response["message"]="Transaction Éffectuée : Monnaie transferée !"
                        response["responseCode"]=1
                        response["transation_id"]=caisses[0]["id"]
                        response["boutique_solde"]=solde
                else:
                    response["message"]="Boutique non enregistrée !"
                    response["responseCode"]=0
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  

        return response

    #api for getting customer money details
    @http.route(
        '/api/get_avoirs/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def get_client_avoirs(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            client_id=data["client_id"]
            if key == apikey:
                sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                uid = sock_common.login(db, username, password)
                sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')
                client=sock.execute_kw(db, uid, password,
                    'money_management.client', 'search_read',
                    [[['id', '=', client_id]]],
                    {'fields': ['solde']})
                response["client_solde"]=client[0]["solde"]
                avoirs=sock.execute_kw(db, uid, password,
                    'money_management.avoir', 'search_read',
                    [[['client_id', '=', client_id],['state', '=', 'actif']]],
                    {'fields': ['caisse_id','montant','date_avoir']})
                response["message"]="Access Granted !"
                response["responseCode"]=1
                response["avoirs"]=avoirs   
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
            
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response


    #api for Agent connexion 
    @http.route(
        '/api/agent_connexion/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def agents_connect(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                try:
                    agent_username = data["username"]
                    agent_password = data["password"]
                    agents = http.request.env['money_management.agent'].sudo().search([('login', '=', agent_username),('password', '=', agent_password)])
                    _logger.debug('agents: %s ', agents)
                    if len(agents)==0 :
                        response["message"]="Login or password incorrect !!"
                        response["responseCode"]=0   
                    else :
                        token = urandom(32).hex()
                        http.request.env['money_management.agent'].sudo().search([('id','=',agents[0]['id'])]).write({"token":token})
                        _logger.debug('boye: boye ')
                        caisse=http.request.env['money_management.caisse'].sudo().search([('id', '=', agents[0]['agent_caisse_id']['id'])])
                        caisse_account= http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', agents[0]['agent_caisse_id']['id'])])
                        _logger.debug('categorie: %s solde caisse: %s agents: %s ', caisse[0]['Categorie_type']['name'],caisse_account[0]['solde'],agents[0]['agent_caisse_id']['id'])
                        response["token"]=token  
                        response["agent_id"]=agents[0]['id']
                        response["category"]=caisse[0]['Categorie_type']['name']
                        response["solde_debut"]=caisse_account[0]['solde']
                        response["date_debut"]=datetime.datetime.now()
                        response["message"]="Access granted !"
                        response["responseCode"]=1
                except Exception as e:
                    response["message"]="Login or password incorrect !"
                    response["responseCode"]=0      
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response


    #api for QR_CODE générator caisse
    @http.route(
        '/api/qr_generation/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def qr_code_generator(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                token = data["token"]
                agent_id=data["agent_id"]
                amount=data["amount"]
                agents = http.request.env['money_management.agent'].sudo().search([('token','=',token)])
                _logger.debug('QR agent: %s ', agents)
                if len(agents) > 0:
                    sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                    uid = sock_common.login(db, username, password)
                    sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')
                    users=sock.execute_kw(db, uid, password,
                        'money_management.agent', 'search_read',
                        [[['id', '=', agent_id]]],
                        {'fields': ['agent_caisse_id']})
                    users1=sock.execute_kw(db, uid, password,
                        'money_management.agent', 'search_read',
                        [[['id', '=', agent_id]]],
                        {'fields': ['agent_boutique_id']})
                    
                    caisse_id=users[0]["agent_caisse_id"][0]
                    boutique_id=users1[0]["agent_boutique_id"][0]
                    """boutiques=sock.execute_kw(db, uid, password,
                        'money_management.caisse', 'search_read',
                        [[['id', '=', caisse_id]]],
                        {'fields': ['designation'], 'limit': 1})
                    print(boutiques[0]["designation"])"""
                    qrcode_id=sock.execute(db, uid, password, 'money_management.qrcode', 'create', {"amount":amount, "agent_id":agent_id, "qr_caisse_id":caisse_id,"qr_boutique_id":boutique_id})
                    response["message"]="Génération du QRCode Réussi !"
                    response["responseCode"]=1
                    response["qr_id"]=qrcode_id
                    response["amount"]=amount
                    response["caisse"]=users[0]["agent_caisse_id"][1]

                else:
                    response["message"]="Agent is logged to another device please loging again to get access !"
                    response["responseCode"]=2

            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response
    
    #api for QR_Scanner
    @http.route(
        '/api/scann_qrcode/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def scann_qr_code(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                qr_id=data["qr_id"]
                client_id=data["client_id"]
                sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                uid = sock_common.login(db, username, password)
                sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')
                qr_codes=sock.execute_kw(db, uid, password,'money_management.qrcode', 'search_read', [[['id', '=', qr_id],['state', '=', 'not_scann']]],  {'fields': ['amount','qr_caisse_id'], 'limit': 1})
               
                if len(qr_codes) == 0:
                    response["message"]="QR_Code invalide ou déjas scanné !"
                    response["responseCode"]=0
                else:
                    id_caisse=qr_codes[0]["qr_caisse_id"][0]
                    caisses=sock.execute_kw(db, uid, password,'money_management.caisse', 'search_read', [[['id', '=', id_caisse]]], {'fields': ['solde'], 'limit': 1})
                    solde=caisses[0]["solde"]
                    amount=qr_codes[0]["amount"]
                    if amount > solde:
                        response["message"]="Le solde de la boutique est insuffisante !"
                        response["responseCode"]=0
                    else:
                        new_solde=solde-amount
                        sock.execute_kw(db, uid, password,'money_management.caisse', 'write',[[id_caisse], {'solde': new_solde}])
                        date_scann=datetime.datetime.now()
                        sock.execute_kw(db, uid, password,'money_management.qrcode', 'write',[[qr_id], {'state':'scanned'}])
                        avoir_id=sock.execute(db, uid, password, 'money_management.avoir', 'create', {"caisse_id":id_caisse, "client_id":client_id,"montant":amount})
                        client=sock.execute_kw(db, uid, password,
                            'money_management.client', 'search_read',
                            [[['id', '=', client_id]]],
                            {'fields': ['solde'], 'limit': 1})
                        new_client_solde=amount+client[0]["solde"]
                        response["message"]="Transaction Éffectuée : Monnaie transferée !"
                        response["responseCode"]=1
                        response["avoir_id"]=avoir_id
                        response["caisse_new_solde"]=new_solde
                        sock.execute_kw(db, uid, password,'money_management.caisse', 'write',[[id_caisse], {'solde': new_solde}])
                        sock.execute_kw(db, uid, password,'money_management.client', 'write',[[client_id], {'solde': new_client_solde}])
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response
    
    # Api payement
    @http.route(
        '/api/createPayment/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def new_payment(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                agent_id=data["agent_id"]
                client_id=data["client_id"]
                montant= data["montant"]
                sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                uid = sock_common.login(db, username, password)
                sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')
                client=sock.execute_kw(db, uid, password,'money_management.client', 'search_read', [[['id', '=', client_id]]], {'fields': ['solde'], 'limit': 1})
                if len(client) == 0:
                    response["message"]="Client inconnue !"
                    response["responseCode"]=0
                else:
                    
                    solde_client=client[0]["solde"]
                    solde_client_after = solde_client - montant
                    if solde_client_after < 0 :
                        response["message"]="Le solde du client est insuffisante !"
                        response["responseCode"]=0
                    else:
                        agent=sock.execute_kw(db, uid, password, 'money_management.agent', 'search_read', [[['id', '=', agent_id]]], {'fields': ['agent_boutique_id']})
                        boutique_name= agent[0]["agent_boutique_id"]
                        boutique=sock.execute_kw(db, uid, password, 'money_management.boutique', 'search_read', [[['designation', '=', boutique_name]]], {'fields': ['id','solde',], 'limit': 1})
                        id_boutique=boutique[0]["id"]
                        sole_boutique=boutique[0]["solde"]
                        solde_boutique_after=sole_boutique+montant
                        sock.execute_kw(db, uid, password,'money_management.boutique', 'write',[[id_boutique], {'solde': solde_boutique_after}])
                        sock.execute_kw(db, uid, password,'money_management.client', 'write',[[client_id], {'solde': solde_client_after}])
                        paiement_id=sock.execute(db, uid, password, 'money_management.paiement', 'create', {"pm_boutique_id":id_boutique, "pm_client_id":client_id, "pm_agent_id":agent_id,"sole_client_befor":solde_client,"sole_client_after":solde_client_after,"sole_boutique_befor":sole_boutique,"sole_boutique_after":solde_boutique_after,"montant":montant})
                        response["message"]="Paiement Éffectuée avec succés !"
                        response["responseCode"]=1
                        response["paiement_id"]=paiement_id
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response
    
    # Api  Validation pin
    @http.route(
        '/api/phone_validation/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def number_validation(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                phone=data["phone"]
                code=data["code"]
                client = http.request.env['money_management.client'].sudo().search([('telephone','=',phone),('validation_code','=',code)])
                if len(client) >0 :
                    old_token = client[0]["token"]
                    if old_token == '':
                        if client[0]["good_father"] != '':
                            good_father_phone = client[0]["good_father"]
                            if good_father_phone.startswith('221') == False :
                                good_father_phone = '221'+good_father_phone
                            good_father = http.request.env['money_management.client'].sudo().search([('telephone','=',good_father_phone)])
                            if len(good_father) >0 :
                                good_father_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', good_father[0]["id"])])
                                if len(good_father_account) > 0 :
                                    crone_account = http.request.env['money_management.account'].sudo().search([('account_marchand_owner', '=', 2)])
                                    par_trans_type = http.request.env['money_management.transactiontype'].sudo().search([('type_value', '=', 'parrainage')])
                                    if crone_account[0]['solde'] > 100:
                                        good_father_solde_new = good_father_account[0]["solde"] + 100
                                        crone_new_solde = crone_account[0]["solde"] - 100
                                        transaction_values = {
                                            "transac_amount":100.0,
                                            "trasac_account_source":crone_account[0]["id"],
                                            "trasac_account_destination":good_father_account[0]["id"],
                                            "trasac_crone_commission":0.0,
                                            "trasac_partenaire_commission":0.0,
                                            "transaction_type_id":par_trans_type[0]["id"],
                                        }
                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', good_father[0]["id"])]).write({'solde': good_father_solde_new})
                                        crone_account.write({'solde': crone_new_solde})
                                        #http.request.env['money_management.account'].sudo().search([('account_marchand_owner', '=', 2)]).write({'solde': crone_new_solde})
                                        http.request.env['money_management.transaction'].sudo().create(transaction_values)

                                        pending_transac = http.request.env['money_management.transaction'].sudo().search([['status','=','in_process'],['trasac_account_source','=',good_father_account[0]["id"]]])
                                        if len(pending_transac) > 0 :
                                            _logger.debug('phone validation pending: ')
                                            for transaction in pending_transac :
                                                account_destinattion =''
                                                if transaction["transaction_type_id"]["type_value"] == 'c-to-c' :
                                                    _logger.debug('phone validation pending type11 %s ', transaction["transaction_type_id"]["type_value"])
                                                    account_destinattion = http.request.env['money_management.account'].sudo().search([['account_client_owner','=',transaction['trasac_account_destination'][0]]])[0]
                                                elif transaction["transaction_type_id"]["type_value"] == 'c-to-seller':
                                                    _logger.debug('phone validation pending type 12 %s ', transaction["transaction_type_id"]["type_value"])
                                                    account_destinattion = http.request.env['money_management.account'].sudo().search([['account_marchand_owner','=',transaction['trasac_account_destination'][0]]])[0]
                                                elif transaction["transaction_type_id"]["type_value"] == 'seller-to-c':
                                                    account_destinattion = http.request.env['money_management.account'].sudo().search([['account_marchand_owner','=',transaction['trasac_account_destination'][0]]])[0]
                                                
                                                transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                                                if good_father_solde_new >= transac_whole_amount :
                                                    source_new_solde = good_father_solde_new - transac_whole_amount
                                                    if account_destinattion!='':
                                                        _logger.debug('phone validation pending %s ', transaction["transaction_type_id"]["type_value"])
                                                        destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"]
                                                    
                                                        if transaction["transaction_type_id"]["type_value"] == 'c-to-c' :
                                                            _logger.debug('phone validation pending type21 %s ', transaction["transaction_type_id"]["type_value"])
                                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                        else:
                                                            _logger.debug('phone validation pending type 22 %s ', transaction["transaction_type_id"]["type_value"])
                                                            http.request.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', good_father[0]["id"])]).write({'solde': source_new_solde})
                                                        http.request.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
                                                        good_father_solde_new = source_new_solde
                                    else :
                                        transaction_values = {
                                            "transac_amount":100.0,
                                            "trasac_account_source":crone_account[0]["id"],
                                            "trasac_account_destination":good_father_account[0]["id"],
                                            "trasac_crone_commission":0.0,
                                            "trasac_partenaire_commission":0.0,
                                            "transaction_type_id":par_trans_type[0]["id"],
                                            "status":"in_process",
                                        }
                                        http.request.env['money_management.transaction'].sudo().create(transaction_values)
                    
                    if client[0]["pin"] != '' :
                        response["pin_exist"] = True
                    else :
                        response["pin_exist"] = False
                    token = urandom(32).hex()
                    http.request.env['money_management.client'].sudo().search([('telephone','=',phone)]).write({"token":token})
                    response["token"]=token
                    response["message"]="Verification effectué!"
                    response["responseCode"]=1
                else :
                    response["message"]="Code invalide!"
                    response["responseCode"]=0
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            print(str(e))
            response["responseCode"]=0
        
        return response

    # Processus de Transactions    
    @http.route(
        '/api/TransactionsProcess/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def transactions_process(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                uid = sock_common.login(db, username, password)
                sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')
                transac_type= data['type_transact']
                chanel = data ['chanel']
                #Monnaie
                if transac_type =='seller-to-c' :
                    #QR chanel seller-to-client
                    if chanel == 'qr' :
                        transac_amount = data['transaction_amount']
                        transac_type_id = data['transaction_type_id']
                        crone_comm = data['crone_comm']
                        partener_comm = data['partener_comm']
                        token = data["token"]
                        clients = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[['token','=',token ]]],{'fields': ['id','state_identite','telephone'], 'limit': 1})
                        #clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                        if len(clients) > 0:
                            if clients[0]["state_identite"]=="suspendu":
                                response["message"]="Votre compte est actuellement votre compte est suspendu"
                                response["responseCode"]=0
                            else :
                                qr_id = data['qr_id']
                                client_id = data['client_id']
                                qr_codes=sock.execute_kw(db, uid, password,'money_management.qrcode', 'search_read',[[['id', '=', qr_id],['state', '=', 'not_scann']]], {'fields': ['amount','qr_caisse_id'], 'limit': 1})
                                if len(qr_codes) == 0:
                                    response["message"]="QR_CODE invalide ou déjà scanné !"
                                    response["responseCode"]=0
                                else:
                                    id_caisse = qr_codes[0]["qr_caisse_id"][0]
                                    caisse_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_caisse_owner', '=', id_caisse ]]],{'fields': ['id','solde','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                                    #caisse_account = http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', id_caisse)])
                                    solde_caisse=caisse_account[0]["solde"]
                                    amount=qr_codes[0]["amount"]
                                    if amount > solde_caisse:
                                        response["message"]="Le solde de la caisse est insuffisant !"
                                        response["responseCode"]=0
                                    else :
                                        client_destination_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', client_id ]]],{'fields': ['id','solde','all_transact_month','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                                        #client_destination_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)])
                                        #check Plafond
                                        # today_date_str = datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59'
                                        # today_array = today_date_str.split('-')
                                        # first_month_day_str = today_array[0]+today_array[1]+'01' + ' 00:00:00'
                                        # trasactions = http.request.env['money_management.transaction'].sudo().search(['|',('trasac_account_source', '=', client_destination_account[0]["id"]),('trasac_account_destination', '=', client_destination_account[0]["id"]),('transac_date', '>=', first_month_day_str),('transac_date', '<=', today_date_str)])
                                        # all_trasactions_amount = 0
                                        # for transaction in trasactions :
                                        #     if transaction["trasac_account_source"]["id"] == client_destination_account[0]["id"] :
                                        #         all_trasactions_amount += transaction["transac_amount"] + transaction["trasac_crone_commission"] +transaction["trasac_partenaire_commission"]
                                        #     else :
                                        #         all_trasactions_amount += transaction["transac_amount"]

                                        all_trasactions_amount = client_destination_account[0]["all_transact_month"]
                                        plafond_mvt = client_destination_account[0]["mouvement_plafond"]
                                        plafond_s = client_destination_account[0]["solde_plafond"]
                                        if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+(transac_amount - (crone_comm + partener_comm))) > plafond_mvt or client_destination_account[0]["solde"]>=plafond_s:
                                            
                                            catego = http.request.env['money_management.categorie_facturation'].sudo().search([('type', '=', 'client')], order="numero asc")
                                            messag= "Vous avez atteint le plafond de vos transactions mensuelles.\nMerci de déplafonner votre compte \n"
                                            for categor in catego:
                                                sold_p=int(categor["solde_plafond"])
                                                mvt_p=int(categor["mvt_plafond"])
                                                messag +="\n"+str(categor["numero"])+":"+str(categor["nom"])+" Solde:"+f"{sold_p:,}".replace(",", " ")+" Cumul:"+f"{mvt_p:,}".replace(",", " ")
                                            response["message"]="Le client a atteint le plafond de ces transactions mensuelles.!"
                                            response["responseCode"]=3
                                            
                                        else :
                                            sole_client_destination = client_destination_account[0]["solde"]
                                            transaction_values = {
                                                "transac_amount":transac_amount,
                                                "trasac_account_source":caisse_account[0]["id"],
                                                "trasac_account_destination":client_destination_account[0]["id"],
                                                "trasac_crone_commission":crone_comm,
                                                "trasac_partenaire_commission":partener_comm,
                                                "transaction_type_id":transac_type_id,
                                            }
                                            transac_amount = transac_amount - (crone_comm + partener_comm)
                                            sole_client_destination_after = sole_client_destination + transac_amount
                                            solde_caisse_after =  solde_caisse - transac_amount
                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)]).write({'solde': sole_client_destination_after})
                                            http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', id_caisse)]).write({'solde': solde_caisse_after})
                                            http.request.env['money_management.qrcode'].sudo().search([('id', '=', qr_id)]).write({'state':'scanned'})
                                            
                                            my_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', id_caisse)])
                                            http.request.env['money_management.transaction'].sudo().create(transaction_values)

                                            pending_transac = http.request.env['money_management.transaction'].sudo().search([['status','=','in_process'],['trasac_account_source','=',client_destination_account[0]["id"]]])
                                            if len(pending_transac) > 0 :
                                                for transaction in pending_transac :
                                                    account_destinattion = transaction['trasac_account_destination']
                                                    transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                                                    if sole_client_destination_after >= transac_whole_amount :
                                                        source_new_solde = sole_client_destination_after - transac_whole_amount
                                                        destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"]
                                                        if transaction["transaction_type_id"]["type_value"] == 'c-to-c' :
                                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                        else:
                                                            http.request.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination_account[0]["id"])]).write({'solde': source_new_solde})
                                                        http.request.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
                                                        sole_client_destination_after = source_new_solde
                                            mont=int(transac_amount)
                                            response["message"]="Transaction éffectuée !\nVous avez reçu une monnaie de "+f"{mont:,}".replace(",", " ")+" Fcfa de chez "+my_caisse[0]['designation']+" \nMerci d'utiliser CRONE!"
                                            response["responseCode"]=1
                        else:
                            code = random.randint(1111,9999)
                            client_id = data['client_id']
                            http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                            response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                            response["responseCode"]=2

                    #Phone Chanel Seller-to-client
                    else :
                        transac_amount = data['transaction_amount']
                        transac_type_id = data['transaction_type_id']
                        crone_comm = data['crone_comm']
                        partener_comm = data['partener_comm']
                        token = data["token"]
                        agents = http.request.env['money_management.agent'].sudo().search([('token','=',token)])
                        if len(agents) > 0:
                            customer_phone = data['customer_phone']
                            agent_id = data['agent_id']
                            
                            _logger.debug('Agent id: %s ', agent_id)
                            
                            caisse= http.request.env['money_management.caisse'].sudo().search([('id','=',agents[0]['agent_caisse_id']['id'])])
                            caisse_id=caisse[0]["id"]
                            caisse_name=caisse[0]["designation"]

                            caisse_account= http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse_id)])
                            solde_caisse=caisse_account[0]["solde"]
                            
                            if transac_amount > solde_caisse :
                                response["message"]="Le solde de la caisse est insuffisant!"
                                response["responseCode"]=0
                            else:
                                customer = http.request.env['money_management.client'].sudo().search([('telephone', '=', customer_phone)])
                                if len(customer) > 0:
                                    if customer[0]["state_identite"]=="suspendu":
                                        response["message"]="Le compte du client destinataire est actuellement suspendu"
                                        response["responseCode"]=0
                                    else:
                                        client_destination_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', customer[0]['id'] ]]],{'fields': ['id','solde','all_transact_month','solde_nondispo','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                                        #client_destination_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', customer[0]['id'])])
                                        #check Plafond
                                       
                                        all_trasactions_amount = client_destination_account[0]["all_transact_month"]
                                        plafond_mvt = client_destination_account[0]["mouvement_plafond"]
                                        plafond_s = client_destination_account[0]["solde_plafond"]
                                        if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+(transac_amount - (crone_comm + partener_comm))) > plafond_mvt or client_destination_account[0]["solde"]>=plafond_s:
                                            response["message"]="Le bénéficiaire a atteint le plafond de ces transactions mensuelles."
                                            response["responseCode"]=0
                                        else :
                                            sole_client_destination = client_destination_account[0]["solde"]
                                            solde_caisse_after =  solde_caisse - transac_amount
                                            transac_amount = transac_amount - (crone_comm + partener_comm)
                                            transaction_values = {
                                                "transac_amount":transac_amount,
                                                "trasac_account_source":caisse_account[0]["id"],
                                                "trasac_account_destination":client_destination_account[0]["id"],
                                                "trasac_crone_commission":crone_comm,
                                                "trasac_partenaire_commission":partener_comm,
                                                "transaction_type_id":transac_type_id,
                                            }
                                        
                                            sole_client_destination_after = sole_client_destination + transac_amount
                                        
                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', customer[0]['id'])]).write({'solde': sole_client_destination_after})
                                            http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse_id)]).write({'solde': solde_caisse_after})
                                            http.request.env['money_management.transaction'].sudo().create(transaction_values)

                                            pending_transac = http.request.env['money_management.transaction'].sudo().search([['status','=','in_process'],['trasac_account_source','=',client_destination_account[0]["id"]]])
                                            if len(pending_transac) > 0 :
                                                for transaction in pending_transac :
                                                    account_destinattion = transaction['trasac_account_destination']
                                                    transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                                                    if sole_client_destination_after >= transac_whole_amount :
                                                        source_new_solde = sole_client_destination_after - transac_whole_amount
                                                        destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"]
                                                        if transaction["transaction_type_id"]["type_value"] == 'c-to-c' :
                                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                        else:
                                                            http.request.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination_account[0]["id"])]).write({'solde': source_new_solde})
                                                        http.request.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
                                                        sole_client_destination_after = source_new_solde
                                            
                                            response["message"]="Transaction éffectuée !\n Monnaie transférée à "+customer_phone
                                            response["responseCode"]=1

                                            topic="solde/"+customer[0]["telephone"]
                                            soldemqtt=int(sole_client_destination_after - client_destination_account[0]["solde_nondispo"])
                                            MoneyManagement.Mqtt_pub(topic,soldemqtt)

                                            mont=int(transac_amount)
                                            payload = {
                                                'number': customer_phone,
                                                'content': 'Vous avez reçu une monnaie de '+f"{mont:,}".replace(",", " ")+' Fcfa en provenance de '+caisse_name+'\n Merci d\'avoir utilisé CRONE avec Orabank',
                                                'key':'dZaN51165420050074130180748146013011022542127230465869',
                                            }
                                            requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)

                                else :
                                    client_plafond = http.request.env['ir.config_parameter'].sudo().get_param('plafond') or '200000.0'
                                    plafond = float(client_plafond)
                                    #plafond_mvt = http.request.env['money_management.categorie_facturation'].sudo().search([('nom', '=', "Classic")])[0]['mvt_plafond']
                                    if transac_amount > plafond:
                                        response["message"]="Le montant de la transaction ne peut pas etre superieur au plafond initial défini pour un nouveau compte."
                                        response["responseCode"]=0
                                    else:
                                        new_clent_value = {
                                            "name":"",
                                            "telephone":customer_phone,
                                            "adresse":""
                                        }
                                        client_dest_id = http.request.env['money_management.client'].sudo().create(new_clent_value)
                                        solde_caisse_after =  solde_caisse - transac_amount
                                        transac_amount = transac_amount - (crone_comm + partener_comm)
                                        new_client_account_values ={
                                            "solde": transac_amount,
                                            "account_type":"client",
                                            "account_client_owner":client_dest_id[0]['id']
                                        }
                                        client_destination_account_id = http.request.env['money_management.account'].sudo().create(new_client_account_values)
                                        transaction_values = {
                                            "transac_amount":transac_amount,
                                            "trasac_account_source":caisse_account[0]["id"],
                                            "trasac_account_destination":client_destination_account_id[0]['id'],
                                            "trasac_crone_commission":crone_comm,
                                            "trasac_partenaire_commission":partener_comm,
                                            "transaction_type_id":transac_type_id,
                                        }
                                        http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse_id)]).write({'solde': solde_caisse_after})
                                        http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                        response["message"]="Transaction éffectuée !\nMonnaie transférée à "+customer_phone
                                        response["responseCode"]=1
                                        mont=int(transac_amount)
                                        payload = {
                                            'number': customer_phone,
                                            'content': 'Votre compte CRONE a été créé !\n Et vous venez d\'y reçevoir une monnaie de '+f"{mont:,}".replace(",", " ")+' Fcfa en provenance de '+caisse_name[1]+'\n Merci de télécharger l\'application CRONE et accéder à votre compte.\nCRONE avec Orabank',
                                            'key':'dZaN51165420050074130180748146013011022542127230465869',
                                        }
                                        requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                        else :
                            response["message"]="Votre compte est actuellement actif dans un autre appareil \nVeuillez vous connecter à nouveau pour continuer!"
                            response["responseCode"]=2

                #Transfert
                elif transac_type =='c-to-c':
                    #QR Chanel
                    if chanel == 'qr' :
                        transac_type_id = data['transaction_type_id']
                        crone_comm = data['crone_comm']
                        partener_comm = data['partener_comm']
                        token = data["token"]
                        destination_client_id = data['client_destination']
                        clients = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[['token','=',token ]]],{'fields': ['id','state_identite','telephone'], 'limit': 1})
                        #clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                        if len(clients) > 0:
                            if clients[0]["state_identite"]=="suspendu":
                                response["message"]="Votre compte est actuellement suspendu"
                                response["responseCode"]=0
                            else:
                                qr_id = data['qr_id']
                                qr_codes = http.request.env['money_management.customerqr'].sudo().search([('id', '=', qr_id),('state', '=', 'not_scanned')])
                                if len(qr_codes) != 0:
                                    customer_src = qr_codes[0]["customer"]
                                    transac_amount = qr_codes[0]["amount"]
                                    client_source_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', customer_src[0]["id"] ]]],{'fields': ['id','solde','all_transact_month','solde_nondispo','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                                    #check plafond
                                    all_trasactions_amount = client_source_account[0]["all_transact_month"]
                                    plafond_mvt = client_source_account[0]["mouvement_plafond"]
                                    plafond_s = client_source_account[0]["solde_plafond"]
                                    if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+transac_amount) > plafond_mvt :
                                        if client_source_account[0]["account_client_owner"]["state_identite"]=="non verifié":
                                            response["message"]="Veuillez valider votre Kyc"
                                            response["responseCode"]=2
                                        else:
                                            catego = http.request.env['money_management.categorie_facturation'].sudo().search([('type', '=', 'client')], order="numero asc")
                                            messag= "Vous avez atteint le plafond de vos transactions mensuelles.\nMerci de déplafonner votre compte \n"
                                            for categor in catego:
                                                sold_p=int(categor['solde_plafond'])
                                                mvt_p=categor['mvt_plafond']
                                                messag +="\n"+str(categor["numero"])+":"+str(categor["nom"])+" Solde:"+f"{sold_p:,}".replace(",", " ")+" Cumul:"+f"{mvt_p:,}".replace(",", " ")
                                            response["message"]=messag
                                            response["responseCode"]=3
                                    else :
                                        solde_client_source = client_source_account[0]["solde"]
                                        #check restrictions
                                        
                                        unavalable_solde = client_source_account[0]["solde_nondispo"]

                                        avalable_solde = solde_client_source - unavalable_solde
                                        solde_client_source_after = avalable_solde - transac_amount
                                        if solde_client_source_after < 0 :
                                            response["message"] = "Le solde du compte de l'envoyeur est insuffisant !"
                                            response["responseCode"] = 0
                                        else:
                                            solde_client_source_after = solde_client_source - transac_amount
                                            client_des = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[[ 'id','=',destination_client_id ]]],{'fields': ['id','state_identite','telephone'], 'limit': 1})
                                            
                                            if client_des[0]["state_identite"]=="suspendu":
                                                response["message"]="Votre compte est actuellement suspendu"
                                                response["responseCode"]=0
                                            else:
                                                client_destination_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', destination_client_id ]]],{'fields': ['id','solde','all_transact_month','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                                                
                                                #check plafond
                                                all_trasactions_amount = client_destination_account[0]["all_transact_month"]
                                                plafond_mvt = client_destination_account[0]["mouvement_plafond"]
                                                plafond_s =client_destination_account[0]["solde_plafond"]
                                                if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+(transac_amount - (crone_comm + partener_comm))) > plafond_mvt or client_destination_account[0]["solde"] >= plafond_s:
                                                    response["message"]="Le bénéficiaire a atteint le plafond de ces transactions mensuelles."
                                                    response["responseCode"]=0
                                                else :
                                                    sole_client_destination=client_destination_account[0]["solde"]
                                                    #solde_client_source = avalable_solde
                                                    transac_amount = transac_amount - (crone_comm + partener_comm)
                                                    transaction_values = {
                                                        "transac_amount":transac_amount,
                                                        "trasac_account_source":client_source_account[0]["id"],
                                                        "trasac_account_destination":client_destination_account[0]["id"],
                                                        "trasac_crone_commission":crone_comm,
                                                        "trasac_partenaire_commission":partener_comm,
                                                        "transaction_type_id":transac_type_id,
                                                    }
                                                    sole_client_destination_after=sole_client_destination + transac_amount
                                                    http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', destination_client_id)]).write({'solde': sole_client_destination_after})
                                                    http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', customer_src[0]["id"])]).write({'solde': solde_client_source_after})
                                                    http.request.env['money_management.customerqr'].sudo().search([('id', '=', qr_id)]).write({'state':'scanned'})
                                                    http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                                    
                                                    pending_transac = http.request.env['money_management.transaction'].sudo().search([['status','=','in_process'],['trasac_account_source','=',client_destination_account[0]["id"]]])
                                                    if len(pending_transac) > 0 :
                                                        for transaction in pending_transac :
                                                            account_destinattion = transaction['trasac_account_destination']
                                                            transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                                                            if sole_client_destination_after >= transac_whole_amount :
                                                                source_new_solde = sole_client_destination_after - transac_whole_amount
                                                                destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"]
                                                                if transaction["transaction_type_id"]["type_value"] == 'c-to-c' :
                                                                    http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                                else:
                                                                    http.request.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                                http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination_account[0]["id"])]).write({'solde': source_new_solde})
                                                                http.request.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
                                                                sole_client_destination_after = source_new_solde
                                                    #client_source_sms = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id)])
                                                    #print("%.2f" % transac_amount)
                                                    mont=int(transac_amount)
                                                    response["message"]="Vous avez reçu un transfert de "+f"{mont:,}".replace(",", " ")+" Fcfa provenant de "+customer_src[0]['telephone']
                                                    response["responseCode"]=1
                                else :
                                    response["message"]="Erreur : QR code invalide ou déja scanné"
                                    response["responseCode"]=0
                        else:
                            code = random.randint(1111,9999)
                            http.request.env['money_management.client'].sudo().search([('id','=',destination_client_id)]).write({"validation_code": str(code)})
                            response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                            response["responseCode"]=2
                    #Phone Chanel
                    else :
                        transac_amount = data['transaction_amount']
                        transac_type_id = data['transaction_type_id']
                        crone_comm = data['crone_comm']
                        partener_comm = data['partener_comm']
                        token = data["token"]
                        source_client_id = data['client_source']
                        destination_client_phone = data['client_destination_phone']
                        clients = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[[ 'token','=',token ]]],{'fields': ['id','state_identite','telephone'], 'limit': 1})
                        
                        if len(clients) > 0:
                            if clients[0]["state_identite"]=="suspendu":
                                response["message"]="Votre compte est actuellement  suspendu"
                                response["responseCode"]=0
                            else:
                                client_source_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', source_client_id ]]],{'fields': ['id','solde','all_transact_month','solde_nondispo','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                                
                                if len(client_source_account) == 0:
                                    response["message"]="Client inconnu !"
                                    response["responseCode"]=0
                                else:
                                    # #check Plafond
                                    
                                    all_trasactions_amount = client_source_account[0]["all_transact_month"]
                                    plafond_mvt = client_source_account[0]["mouvement_plafond"]
                                    plafond_s = client_source_account[0]["solde_plafond"]
                                    solde_client = client_source_account[0]["solde"]
                                    if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+transac_amount) >plafond_mvt:
                                        if client_source_account[0]["account_client_owner"]["state_identite"]=="non verifié":
                                            response["message"]="Veuillez Renseigner le KYC"
                                            response["responseCode"]=2
                                        else:
                                            catego = http.request.env['money_management.categorie_facturation'].sudo().search([('type', '=', 'client')], order="numero asc")
                                            messag= "Vous avez atteint le plafond de vos transactions mensuelles.\nMerci de déplafonner votre compte\n "
                                            choix=[]
                                            for categor in catego:
                                                mvt_p=int(categor['mvt_plafond'])
                                                sold_p=int(categor['solde_plafond'])
                                                messag +="\n"+str(categor["numero"])+": "+str(categor["nom"])
                                                text="Vous avez choisi la catégorie "+str(categor["nom"])+" vous allez béneficier d'un solde de "+" Solde:"+f"{sold_p:,}".replace(",", " ")+" et d'un cumul de "+f"{mvt_p:,}".replace(",", " ")
                                                choix.append(text)
                                                
                                            response["message"]=messag
                                            response["choix"]=choix
                                            response["responseCode"]=3
                                    else :
                                        solde_client_source=client_source_account[0]["solde"]
                                        _logger.debug('Solde client: %s ', solde_client_source)
                                        # #check restrictions
                                        
                                        unavalable_solde = client_source_account[0]["solde_nondispo"]
                                        avalable_solde = solde_client_source - unavalable_solde
                                        #solde_client_source = avalable_solde
                                        solde_client_source_after = avalable_solde - transac_amount
                                        if solde_client_source_after < 0 :
                                            response["message"]="Le solde de votre compte est insuffisant !"
                                            response["responseCode"]=0
                                        else:
                                            solde_client_source_after = solde_client_source - transac_amount
                                            client_destination = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[[ 'telephone', '=', destination_client_phone ]]],{'fields': ['id','state_identite','telephone'], 'limit': 1})
                                            
                                            if len(client_destination) > 0:
                                                if client_destination[0]["state_identite"]=="suspendu":
                                                    response["message"]="Le compte du client destinataire est actuellement  suspendu"
                                                    response["responseCode"]=0
                                                else:
                                                    client_destination_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', client_destination[0]['id'] ]]],{'fields': ['id','solde','solde_nondispo','all_transact_month','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                                                    
                                                    #check Plafond
                                                    
                                                    all_trasactions_amount = client_destination_account[0]["all_transact_month"]
                                                    plafond_mvt = client_destination_account[0]["mouvement_plafond"]
                                                    plafond_s = client_destination_account[0]["solde_plafond"]
                                                    if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+(transac_amount - (crone_comm + partener_comm))) > plafond_mvt or client_destination_account[0]["solde"]>=plafond_s:
                                                        response["message"]="Le bénéficiaire a atteint le plafond de ces transactions mensuelles."
                                                        response["responseCode"]=0
                                                    else :
                                                        sole_client_destination=client_destination_account[0]["solde"]
                                                        transac_amount = transac_amount - (crone_comm + partener_comm)
                                                        transaction_values = {
                                                            "transac_amount":transac_amount,
                                                            "trasac_account_source":client_source_account[0]["id"],
                                                            "trasac_account_destination":client_destination_account[0]["id"],
                                                            "trasac_crone_commission":crone_comm,
                                                            "trasac_partenaire_commission":partener_comm,
                                                            "transaction_type_id":transac_type_id,
                                                        }
                                                        sole_client_destination_after=sole_client_destination + transac_amount
                                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination[0]['id'])]).write({'solde': sole_client_destination_after})
                                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)]).write({'solde': solde_client_source_after})
                                                        http.request.env['money_management.transaction'].sudo().create(transaction_values)

                                                        pending_transac = http.request.env['money_management.transaction'].sudo().search([['status','=','in_process'],['trasac_account_source','=',client_destination_account[0]["id"]]])
                                                        if len(pending_transac) > 0 :
                                                            for transaction in pending_transac :
                                                                account_destinattion = transaction['trasac_account_destination']
                                                                transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                                                                if sole_client_destination_after >= transac_whole_amount :
                                                                    source_new_solde = sole_client_destination_after - transac_whole_amount
                                                                    destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"]
                                                                    if transaction["transaction_type_id"]["type_value"] == 'c-to-c' :
                                                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                                    else:
                                                                        http.request.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                                                    http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination_account[0]["id"])]).write({'solde': source_new_solde})
                                                                    http.request.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
                                                                    sole_client_destination_after = source_new_solde

                                                        response["message"]="Transfert éffectué avec succès !"
                                                        response["responseCode"]=1

                                                        topic="solde/"+client_destination[0]["telephone"]
                                                        soldemqtt=int(sole_client_destination_after - client_destination_account[0]["solde_nondispo"])
                                                        MoneyManagement.Mqtt_pub(topic,soldemqtt)

                                                        client_source_sms = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id)])
                                                        mont=int(transac_amount)
                                                        payload = {
                                                            'number': client_destination[0]["telephone"],
                                                            'content': 'Vous avez reçu un transfert de '+f"{mont:,}".replace(",", " ")+' Fcfa provenant de '+client_source_sms[0]['telephone']+'\n Merci d\'utiliser CRONE.',
                                                            'key':'dZaN51165420050074130180748146013011022542127230465869',
                                                        }
                                                        requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                                                
                                            else :
                                                client_plafond = http.request.env['ir.config_parameter'].sudo().get_param('plafond') or '200000.0'
                                                plafond = float(client_plafond)
                                                
                                                #plafond_mvt= http.request.env['money_management.categorie_facturation'].sudo().search([('nom', '=', "Classic")])[0]['mvt_plafond']
                                                if transac_amount > plafond:
                                                    response["message"]="Le montant de la transaction ne peut pas etre superieur au plafond initial défini pour un nouveau compte."
                                                    response["responseCode"]=0
                                                else:
                                                    new_clent_value = {
                                                        "name":"",
                                                        "telephone":destination_client_phone,
                                                        "adresse":""
                                                    }
                                                    client_dest_id = http.request.env['money_management.client'].sudo().create(new_clent_value)
                                                    transac_amount = transac_amount - (crone_comm + partener_comm)
                                                    new_client_account_values ={
                                                        "solde": transac_amount,
                                                        "account_type":"client",
                                                        "account_client_owner":client_dest_id[0]['id']
                                                    }
                                                    
                                                    client_destination_account_id = http.request.env['money_management.account'].sudo().create(new_client_account_values)
                                                    transaction_values = {
                                                        "transac_amount":transac_amount,
                                                        "trasac_account_source":client_source_account[0]["id"],
                                                        "trasac_account_destination":client_destination_account_id[0]['id'],
                                                        "trasac_crone_commission":crone_comm,
                                                        "trasac_partenaire_commission":partener_comm,
                                                        "transaction_type_id":transac_type_id,
                                                    }
                                                    http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)]).write({'solde': solde_client_source_after})
                                                    http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                                    response["message"]="Transfert éffectué avec succès !"
                                                    response["responseCode"]=1
                                                    client_source_sms = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[[ 'id', '=', source_client_id ]]],{'fields': ['id','telephone'], 'limit': 1})
                                                    #client_source_sms = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id)])
                                                    mont=int(transac_amount)
                                                    payload = {
                                                        'number': destination_client_phone,
                                                        'content': 'Votre compte CRONE a été créé !\n Et vous venez d\'y reçevoir un montant de '+f"{mont:,}".replace(",", " ")+' Fcfa provenant de '+client_source_sms[0]['telephone']+'\n Merci de télécharger l\'application CRONE pour accéder à votre compte.\nhttps://play.google.com/store/apps/details?id=smartedigital.crone\nCRONE avec Orabank',
                                                        'key':'dZaN51165420050074130180748146013011022542127230465869',
                                                    }
                                                    requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                        else:
                            code = random.randint(1111,9999)
                            http.request.env['money_management.client'].sudo().search([('id','=',source_client_id)]).write({"validation_code": str(code)})
                            response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                            response["responseCode"]=2
                #Payment client to seller
                elif transac_type =='c-to-seller':
                    transac_type_id = data['transaction_type_id']
                    crone_comm = data['crone_comm']
                    partener_comm = data['partener_comm']
                    token = data["token"]
                    agents = http.request.env['money_management.agent'].sudo().search([('token','=',token)])
                    if len(agents) > 0:
                        #boutiques =  http.request.env['money_management.boutique'].sudo().search([('id','=',agents[0]["agent_boutique_id"]["id"])])
                        caisse =  http.request.env['money_management.caisse'].sudo().search([('id','=',agents[0]["agent_caisse_id"]["id"])])
                        qr_id = data['qr_id']
                        qr_codes = http.request.env['money_management.customerqr'].sudo().search([('id', '=', qr_id),('state', '=', 'not_scanned')])
                        if len(qr_codes) != 0:
                            customer = qr_codes[0]["customer"]
                            client_id = customer[0]["id"]
                            agent_id = data['agent_id']
                            transac_amount = qr_codes[0]["amount"]

                            #marchands =  http.request.env['res.users'].sudo().search([('id','=',boutiques[0]["marchand_id"]["id"])])
                            caisses= caisse
                            #marchand_restrictions = []
                            caisse_restrictions = []
                            client_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', client_id]]],{'fields': ['id','solde','all_transact_month','solde_nondispo','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                            #client_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)])

                                    
                            all_trasactions_amount = client_account[0]["all_transact_month"]
                            plafond_mvt = client_account[0]["mouvement_plafond"]
                            plafond_s = client_account[0]["solde_plafond"]
                            
                            if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+transac_amount) > plafond_mvt :
                                if client_account[0]["account_client_owner"]["state_identite"]=="non verifié":
                                    response["message"]="Veuillez renseigner Votre Kyc"
                                    response["responseCode"]=2
                                else:
                                    catego = http.request.env['money_management.categorie_facturation'].sudo().search([('type', '=', 'client')], order="numero asc")
                                    messag= "Vous avez atteint le plafond de vos transactions mensuelles.\nMerci de déplafonner votre compte\n "
                                    choix=[]
                                    for categor in catego:
                                        mvt_p=int(categor['mvt_plafond'])
                                        sold_p=int(categor['solde_plafond'])
                                        messag +="\n"+str(categor["numero"])+": "+str(categor["nom"])
                                        text="Vous avez choisi la catégorie "+str(categor["nom"])+" vous allez béneficier d'un solde de "+" Solde:"+f"{sold_p:,}".replace(",", " ")+" et d'un cumul de "+f"{mvt_p:,}".replace(",", " ")
                                        choix.append(text)
                                    response["message"]=messag
                                    response["choix"]=choix
                                    response["responseCode"]=3
                            else :
                                solde_client=client_account[0]["solde"]
                                #check restrictions
                                restrictions = http.request.env['money_management.credit_restricted'].sudo().search([('account_ref', '=', client_account[0]["id"]), ('state', '=', 'active')], order='date_creation asc')
                                unavalable_solde = 0
                                for rest in restrictions :
                                    if len(rest["cartegorie_id"]) == 0 :
                                        if  rest["consumption_date"] <= datetime.datetime.now() :
                                            soldeaft=rest["amount"]+rest["account_ref"]["solde"]
                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', rest["account_ref"]["id"])]).write({'solde': soldeaft})
                                            http.request.env['money_management.credit_restricted'].sudo().search([('id', '=', rest['id'])]).write({"notification":"envoye",'state': 'inactive'})
                                            mont=int(rest["amount"])
                                            payload = {
                                                'number': rest["account_ref"]["telephone"],
                                                'content': 'Vous avez un transfert de '+f"{mont:,}".replace(",", " ")+"F  "+rest["tag"]+'\n Merci d\'utiliser CRONE.',
                                                'key':'dZaN51165420050074130180748146013011022542127230465869',
                                            }
                                            requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                                        else:
                                            unavalable_solde += rest["amount"]
                                    else  :    
                                        if caisse[0]["Categorie_type"]["id"] == rest["cartegorie_id"]["id"]:
                                            if rest["consumption_date"] != False :
                                                if  rest["consumption_date"] <= datetime.datetime.now() :
                                                    caisse_restrictions.append(rest)
                                                else :
                                                    unavalable_solde +=(rest["amount"] - rest["used_amount"])
                                            else :
                                                caisse_restrictions.append(rest)
                                        else :
                                            unavalable_solde +=(rest["amount"] - rest["used_amount"])
                                        

                                avalable_solde = solde_client - unavalable_solde
                                solde_client_after = avalable_solde - transac_amount
                                if solde_client_after < 0 :
                                    response["message"]="Le solde du client est insuffisant !"
                                    response["responseCode"]=0
                                else:
                                    solde_client_after = solde_client - transac_amount
                                    restrict_amount = transac_amount
                                    for valid_restriction in caisse_restrictions :
                                        restrict_rest_amount =  valid_restriction["amount"] - valid_restriction["used_amount"]
                                        the_rest = restrict_rest_amount - restrict_amount
                                        if the_rest >= 0 :
                                            if the_rest == 0 :
                                                rest_state = "inactive"
                                            else :
                                                rest_state = "active"
                                            http.request.env['money_management.credit_restricted'].sudo().search([('id', '=', valid_restriction['id'])]).write({'used_amount': (valid_restriction['used_amount'] + restrict_amount) , 'state': rest_state})
                                            break
                                        else :
                                            http.request.env['money_management.credit_restricted'].sudo().search([('id', '=', valid_restriction['id'])]).write({'used_amount': valid_restriction["amount"] , 'state': 'inactive'})
                                            restrict_amount=-the_rest

                                    
                                    caisse_name= caisse[0]["designation"]
                                    
                                    caisse_id=caisse[0]["id"]
                                    caisse_account= http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse_id)])
                                    sole_caisse=caisse_account[0]["solde"]
                                    _logger.debug('Transaction caisse solde: %s ', sole_caisse)
                                    transac_amount = transac_amount - (crone_comm + partener_comm)
                                    transaction_values = {
                                        "transac_amount":transac_amount,
                                        "trasac_account_source":client_account[0]["id"],
                                        "trasac_account_destination":caisse_account[0]["id"],
                                        "trasac_crone_commission":crone_comm,
                                        "trasac_partenaire_commission":partener_comm,
                                        "transaction_type_id":transac_type_id,
                                    }
                                    payement_values={
                                    
                                    }
                                    _logger.debug('Transaction caisse solde: %s ', transaction_values)
                                    
                                    solde_caisse_after=sole_caisse + transac_amount
                                    http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse_id)]).write({'solde': solde_caisse_after})
                                    http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)]).write({'solde': solde_client_after})
                                    http.request.env['money_management.customerqr'].sudo().search([('id', '=', qr_id)]).write({'state':'scanned'})
                                    http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                    client_source_sms = http.request.env['money_management.client'].sudo().search([('id', '=', client_id)])
                                    montant=int(transac_amount)
                                    response["message"]="Vous avez reçu un paiement de "+f"{montant:,}".replace(",", " ")+" Fcfa de "+client_source_sms[0]['telephone']
                                    #+str("%.2f" % transac_amount)+
                                    response["responseCode"]=1
                        else :
                            response["message"]="Erreur : QR code invalide ou déja scanné"
                            response["responseCode"]=0
                    else :
                        response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez vous connecter à nouveau pour continuer!"
                        response["responseCode"]=2
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response

    # Api configuration
    @http.route(
        '/api/getConfiguration/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def get_params(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                uid = sock_common.login(db, username, password)
                sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')
                token = data['token']
                user_type = data['user_type']
                if user_type == 'agent':
                    agents = http.request.env['money_management.agent'].sudo().search([('token','=',token)])
                    if len(agents) == 0:
                        response["message"]="Votre compte est actuellement actif dans un autre appareil \nVeuillez vous connecter à nouveau pour continuer!"
                        response["responseCode"]=2
                        return response
                else :
                    clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                    if len(clients) == 0:
                        code = random.randint(1111,9999)
                        customer_id = data['customer_id']
                        http.request.env['money_management.client'].sudo().search([('id','=',customer_id)]).write({"validation_code": str(code)})
                        response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                        response["responseCode"]=2
                        return response

                if 'customer_id' in data :
                    customer_id = data['customer_id']
                    account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[['account_client_owner', '=', customer_id ]]],{'fields': ['id','account_number','all_transact_month','solde','date_payement','date_fist_month'], 'limit': 1})
                    #account =  http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', customer_id)])
                    restrictions = http.request.env['money_management.credit_restricted'].sudo().search([('account_ref', '=', account[0]["id"]), ('state', '=', 'active')], order='date_creation desc')
                    mount_percat=0
                    mount_sanscat=0
                    for rest in restrictions :
                        if len(rest["cartegorie_id"]) == 0 :
                            if  rest["consumption_date"]>datetime.datetime.now():
                                mount_sanscat += (rest["amount"]-rest["used_amount"])
                        else :    
                            mount_percat += (rest["amount"]-rest["used_amount"])
                                
                    mount_nondispo = mount_percat+mount_sanscat
                    mount_dispo =account[0]['solde'] - mount_nondispo
                    
                    #check Plafond
                    today_date_str = datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59'
                    first_month_day_str = account[0]['date_fist_month']
                   
                    trasactions = http.request.env['money_management.transaction'].sudo().search(['|',('trasac_account_source', '=', account[0]["id"]),('trasac_account_destination', '=', account[0]["id"]),('transac_date', '>=', first_month_day_str),('transac_date', '<=', today_date_str),('add', '=', False)])
                    _logger.debug('Transactions: %s ',trasactions)
                    all_trasactions_amount = 0
                    for transaction in trasactions :
                        if transaction["trasac_account_source"]["id"] == account[0]["id"] :
                            all_trasactions_amount += transaction["transac_amount"] + transaction["trasac_crone_commission"] +transaction["trasac_partenaire_commission"]
                            transaction.write({'add': True})
                        else :
                            all_trasactions_amount += transaction["transac_amount"]
                            transaction.write({'add': True})

                    all_trans_month = account[0]['all_transact_month'] + all_trasactions_amount

                    #response["customer_solde"]= account[0]['solde']
                    response["customer_solde"]= mount_dispo
                    http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', customer_id)]).write({'solde_nondispo': mount_nondispo,'all_transact_month': all_trans_month})

                transactions_types = http.request.env['money_management.transactiontype'].sudo().search([])
                trans_types =[]
                if len(transactions_types) > 0:
                    for x in range(len(transactions_types)) :
                        commissions =[]
                        comms = http.request.env['money_management.commission'].sudo().search([('comm_transac_type_id', '=', transactions_types[x]['id'])])
                        if len(comms) > 0:
                            for y in range(len(comms)) :
                                one_comm ={
                                    "commission_reff":comms[y]['commission_reff'],
                                    "min_amount":comms[y]['min_amount'],
                                    "max_amount":comms[y]['max_amount'],
                                    "commission_type":comms[y]['commission_type'],
                                    "commission_value":comms[y]['commission_value']
                                }
                                commissions.append(one_comm)
                        one_type = {
                            "type_id":transactions_types[x]['id'],
                            "type_value":transactions_types[x]['type_value'],
                            "crone_comm":transactions_types[x]['crone_commission'],
                            "partener_comm":transactions_types[x]['partenaire_commission'],
                            "commissions":commissions
                        }
                        trans_types.append(one_type)
                
                trading_type = http.request.env['money_management.trading_type'].sudo().search([])
                trading_array = []
                for one_trading_type in trading_type :
                    trading_type_object = {
                        "id":one_trading_type["id"],
                        "name":one_trading_type["name"],
                        "image":one_trading_type["logo"]
                    }
                    trading_array.append(trading_type_object)
                
                response["trading_type"]=trading_array
                response["message"]="Access granted!"
                response["responseCode"]=1
                response["transactions_types"]=trans_types
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response
    
    # Api listes transactions client
    @http.route(
        '/api/GetTransactions/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def getTransactions(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                token = data['token']
                client_id= data['client_id']
                clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) == 0:
                    code = random.randint(1111,9999)
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                    response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                    response["responseCode"]=2
                    return response
                account_client =  http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)])
                _logger.debug('Account Client: %s ', account_client)
                transactions_array=[]
                transactions = http.request.env['money_management.transaction'].sudo().search(['|',('trasac_account_source', '=', account_client[0]['id']),('trasac_account_destination', '=', account_client[0]['id'])])
                _logger.debug('Transaction: %s ', transactions)
                if len(transactions) > 0:
                    today_date_str = datetime.date.today().strftime('%Y-%m-%d')
                    today_array = today_date_str.split('-')
                    first_month_day_str = today_array[0]+'-'+today_array[1]+'-'+'01'
                    
                    for x in range(len(transactions)) :
                        trans_type = transactions[x]['transaction_type_id']
                        source = transactions[x]['trasac_account_source']
                        one_transac = {
                            "type":trans_type[0]['type_value'],
                            "montant":transactions[x]['transac_amount'],
                            "transaction_number":transactions[x]['transaction_reff'],
                            "date_transaction":transactions[x]['transac_date'],
                            "frais": transactions[x]['trasac_crone_commission']+transactions[x]['trasac_partenaire_commission'],
                            "tag" : transactions[x]['tag']
                        }
                        if str(source[0]['id']) == str(account_client[0]['id']):
                            one_transac["is_source"]=True
                            _logger.debug('Oneransaction source: %s ', one_transac)
                            destination_acc = transactions[x]['trasac_account_destination']
                            _logger.debug('destination: %s ', destination_acc[0]["account_type"])
                            if destination_acc[0]["account_type"] == 'client':
                                dest_client_id = destination_acc[0]["account_client_owner"]
                                dest_client = http.request.env['money_management.client'].sudo().search([('id', '=', dest_client_id[0]["id"])])
                                if len(dest_client)>0:
                                    one_transac["from_or_to"]="envoyé à " + str(dest_client[0]["name"])
                                else:
                                    one_transac["from_or_to"]=""
                            elif destination_acc[0]["account_type"] == 'boutique':
                                dest_boutique_id = destination_acc[0]["account_boutique_owner"]
                                dest_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', dest_boutique_id[0]["id"])])
                                one_transac["from_or_to"]="payé chez " + str(dest_boutique[0]["designation"])
                            elif destination_acc[0]["account_type"] == 'caisse':
                                dest_caisse_id = destination_acc[0]["account_caisse_owner"]
                                dest_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', dest_caisse_id[0]["id"])])
                                one_transac["from_or_to"]="payé chez " + str(dest_caisse[0]["designation"])
                            elif destination_acc[0]["account_type"] == 'oeuvre':
                                dest_oeuvre_id = destination_acc[0]["account_oeuvrecaritative_owner"]
                                dest_oeuvre = http.request.env['money_management.oeuvrecaritative'].sudo().search([('id', '=', dest_oeuvre_id[0]["id"])])
                                one_transac["from_or_to"]="Don à " + str(dest_oeuvre[0]["name"])
                            elif destination_acc[0]["account_type"] == 'marchand':
                                dest_marchand_id = destination_acc[0]["account_marchand_owner"]
                                dest_marchand = http.request.env['res.users'].sudo().search([('id', '=', dest_marchand_id[0]["id"])])
                                one_transac["from_or_to"]="Payement mensuel du  "+ str(first_month_day_str)+ str(dest_marchand[0]["nom_marchand"])
                            elif destination_acc[0]["account_type"] == 'wallet':
                                dest_wallet_id = destination_acc[0]["account_wallet_owner"]
                                dest_wallet = http.request.env['money_management.cronewallet'].sudo().search([('id', '=', dest_wallet_id[0]["id"])])
                                one_transac["from_or_to"]="Crone vers "+ str(dest_wallet[0]["nom"])
                            else :
                                one_transac["from_or_to"]=""
                        else :
                            one_transac["is_source"]=False
                            source_acc = transactions[x]['trasac_account_source']
                            _logger.debug('destination: %s ', source_acc[0]["account_type"])
                            if source_acc[0]["account_type"] == 'client':
                                source_client_id = source_acc[0]["account_client_owner"]
                                source_client = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id[0]["id"])])
                                if len(source_client)>0:
                                    one_transac["from_or_to"]="reçu de " + str(source_client[0]["name"])
                                else:
                                    one_transac["from_or_to"]=""
                            elif source_acc[0]["account_type"] == 'boutique':
                                source_botique_id = source_acc[0]["account_boutique_owner"]
                                sourec_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', source_botique_id[0]["id"])])
                                one_transac["from_or_to"]="reçu de chez " + str(sourec_boutique[0]["designation"])
                            elif source_acc[0]["account_type"] == 'caisse':
                                source_caisse_id = source_acc[0]["account_caisse_owner"]
                                source_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', source_caisse_id[0]["id"])])
                                one_transac["from_or_to"]="reçu de chez " + str(source_caisse[0]["designation"])
                            elif source_acc[0]["account_type"] == 'marchand':
                                #source_machand_id = source_acc[0]["account_marchand_owner"]
                                #source_marchand = http.request.env['res.users'].sudo().search([('id', '=', source_marchand_id[0]["id"])])
                                one_transac["from_or_to"]="parrainage d'un numero " 
                            elif source_acc[0]["account_type"] == 'wallet':
                                source_wallet_id = source_acc[0]["account_wallet_owner"]
                                source_wallet = http.request.env['money_management.cronewallet'].sudo().search([('id', '=', source_wallet_id[0]["id"])])
                                one_transac["from_or_to"]=str(source_wallet[0]["nom"])+" vers Crone"
                            else :
                                one_transac["from_or_to"]=""
                                
                        transactions_array.append(one_transac)
                _logger.debug('Transaction: %s ', transactions_array)
                response["message"]="Granted !"
                response["responseCode"]=1
                response['transactions']= transactions_array

            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response
    
    # Api Listes oeuvres caricative
    @http.route(
        '/api/GetOeuvresCaritatives/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def getOeuvresCaritatives(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                token = data['token']
                clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) == 0:
                    code = random.randint(1111,9999)
                    client_id = data['client_id']
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                    response["message"] = "Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                    response["responseCode"]=2
                    return response
                else :
                    oeuvres_request  = http.request.env['money_management.oeuvrecaritative'].sudo().search([])
                    oeuvres_list = []
                    for x in range(len(oeuvres_request)) :
                        one_oeuvre = {
                            "id":oeuvres_request[x]['id'],
                            "name":oeuvres_request[x]['name'],
                            "telephone":oeuvres_request[x]['telephone'],
                            "adresse":oeuvres_request[x]['adresse'],
                            "image":oeuvres_request[x]['logo'],
                            "description":oeuvres_request[x]['description'],
                        }
                        oeuvres_list.append(one_oeuvre)
                    response["message"]="Granted!"
                    response["responseCode"]=1
                    response['oeuvres']= oeuvres_list
            else:
                response["message"]="Access Denied !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response
    
    #Get solde caisse
    @http.route(
        '/api/GetSoldeCaisse/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def getSoldeCaisse(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                token = data['token']
                agents = http.request.env['money_management.agent'].sudo().search([('token','=',token)])
                if len(agents) == 0:
                    code = random.randint(1111,9999)
                    agent_id = data['agent_id']
                    #http.request.env['money_management.agent'].sudo().search([('id','=',agent_id)]).write({"validation_code": str(code)})
                    response["message"] = "Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                    response["responseCode"]=2
                    return response
                else :
                    caisse= http.request.env['money_management.caisse'].sudo().search([('id','=',agents[0]['agent_caisse_id']['id'])])
                    account_caisse =  http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse[0]['id'])])
                    _logger.debug('solde caisse : %s ', account_caisse[0]['solde'])
                    response["message"]="Granted!"
                    response["responseCode"]=1
                    response["solde"]= str(account_caisse[0]['solde'])
            else:
                response["message"]="Access Denied !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response
    
    # Api agent detail
    @http.route(
        '/api/Getdetail_agent/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def getDetail_agent(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                token = data['token']
                agent_id= data['agent_id']
                date_debut= data['date_debut']
                _logger.debug('date debut: %s ', date_debut)
                if date_debut=="debut":
                    date_debut = datetime.date.today().strftime('%Y-%m-%d')+' 05:00:00'
                    agents = http.request.env['money_management.agent'].sudo().search([('token','=',token)])
                    if len(agents) == 0:
                        code = random.randint(1111,9999)
                        #http.request.env['money_management.agent'].sudo().search([('id','=',agent_id)]).write({"validation_code": str(code)})
                        response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                        response["responseCode"]=2
                        return response
                    
                    caisse= http.request.env['money_management.caisse'].sudo().search([('caisse_boutique_id', '=', agents[0]['agent_boutique_id']['id']),('id','=',agents[0]['agent_caisse_id']['id'])])
                    account_caisse =  http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse[0]['id'])])
                    transactions_source=[]
                    transactions_destination=[]
                    transactions = http.request.env['money_management.transaction'].sudo().search(['&',('transac_date','>=',date_debut),'|',('trasac_account_source', '=', account_caisse[0]['id']),('trasac_account_destination', '=', account_caisse[0]['id'])])
                    _logger.debug('transactions: %s ', transactions)
                    if len(transactions) > 0:
                        total_source=0.0
                        total_destination=0.0
                        one_transac_source = {}
                        one_transac_destination = {}
                        for x in range(len(transactions)) :
                            trans_type = transactions[x]['transaction_type_id']
                            source = transactions[x]['trasac_account_source']
                            _logger.debug('source: %s acoount caisse: %s ', source[0]['id'],account_caisse[0]['id'])
                            if str(source[0]['id']) == str(account_caisse[0]['id']):
                                montant=transactions[x]['transac_amount']
                                _logger.debug('montant: %s ', montant)
                                total_source += int(montant)
                                
                                one_transac_source = {
                                    "type":trans_type[0]['type_value'],
                                    "montant":transactions[x]['transac_amount'],
                                    "transaction_number":transactions[x]['transaction_reff'],
                                    "date_transaction":transactions[x]['transac_date'],
                                    "frais": transactions[x]['trasac_crone_commission']+transactions[x]['trasac_partenaire_commission'],
                                    "tag" : transactions[x]['tag']
                                    }
                                
                                one_transac_source["is_source"]=True
                                destination_acc = transactions[x]['trasac_account_destination']
                                if destination_acc[0]["account_type"] == 'client':
                                    dest_client_id = destination_acc[0]["account_client_owner"]
                                    dest_client = http.request.env['money_management.client'].sudo().search([('id', '=', dest_client_id[0]["id"])])
                                    one_transac_source["from_or_to"]=dest_client[0]["telephone"]
                                   
                                elif destination_acc[0]["account_type"] == 'boutique':
                                    dest_boutique_id = destination_acc[0]["account_boutique_owner"]
                                    dest_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', dest_boutique_id[0]["id"])])
                                    one_transac_source["from_or_to"]=dest_boutique[0]["designation"]
                                
                                elif destination_acc[0]["account_type"] == 'caisse':
                                    dest_caisse_id = destination_acc[0]["account_caisse_owner"]
                                    dest_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', dest_caisse_id[0]["id"])])
                                    one_transac_source["from_or_to"]=dest_caisse[0]["designation"]
                                    
                                elif destination_acc[0]["account_type"] == 'oeuvre':
                                    dest_oeuvre_id = destination_acc[0]["account_oeuvrecaritative_owner"]
                                    dest_oeuvre = http.request.env['money_management.oeuvrecaritative'].sudo().search([('id', '=', dest_oeuvre_id[0]["id"])])
                                    one_transac_source["from_or_to"]=dest_oeuvre[0]["name"]
                                else :
                                    one_transac_source["from_or_to"]=''
                                transactions_source.append(one_transac_source)
                            else:
                                
                                
                                total_destination += transactions[x]['transac_amount']
                            
                                one_transac_destination = {
                                    "type":trans_type[0]['type_value'],
                                    "montant":transactions[x]['transac_amount'],
                                    "transaction_number":transactions[x]['transaction_reff'],
                                    "date_transaction":transactions[x]['transac_date'],
                                    "frais": transactions[x]['trasac_crone_commission']+transactions[x]['trasac_partenaire_commission'],
                                    "tag" : transactions[x]['tag']
                                    }
                                                        
   
                                one_transac_destination["is_source"]=False
                                source_acc = transactions[x]['trasac_account_source']
                                
                                if source_acc[0]["account_type"] == 'client':
                                    source_client_id = source_acc[0]["account_client_owner"]
                                    source_client = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id[0]["id"])])
                                    one_transac_destination["from_or_to"]=source_client[0]["telephone"]
                                elif source_acc[0]["account_type"] == 'boutique':
                                    source_botique_id = source_acc[0]["account_boutique_owner"]
                                    sourec_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', source_botique_id[0]["id"])])
                                    one_transac_destination["from_or_to"]=sourec_boutique[0]["designation"]
                                    
                                elif source_acc[0]["account_type"] == 'caisse':
                                    source_caisse_id = source_acc[0]["account_caisse_owner"]
                                    source_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', source_caisse_id[0]["id"])])
                                    one_transac_destination["from_or_to"]=source_caisse[0]["designation"]
                                else :
                                    one_transac_destination["from_or_to"]=''
                                transactions_destination.append(one_transac_destination)
                    
                            
                else:
                    agents = http.request.env['money_management.agent'].sudo().search([('token','=',token)])
                    if len(agents) == 0:
                        code = random.randint(1111,9999)
                        #http.request.env['money_management.agent'].sudo().search([('id','=',agent_id)]).write({"validation_code": str(code)})
                        response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                        response["responseCode"]=2
                        return response
                    
                    caisse= http.request.env['money_management.caisse'].sudo().search([('caisse_boutique_id', '=', agents[0]['agent_boutique_id']['id']),('id','=',agents[0]['agent_caisse_id']['id'])])
                    account_caisse =  http.request.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse[0]['id'])])
                    transactions_source=[]
                    transactions_destination=[]
                    transactions = http.request.env['money_management.transaction'].sudo().search(['&',('transac_date','>=',date_debut),'|',('trasac_account_source', '=', account_caisse[0]['id']),('trasac_account_destination', '=', account_caisse[0]['id'])])
                    _logger.debug('transactions: %s ', transactions)
                    if len(transactions) > 0:
                        total_source=0.0
                        total_destination=0.0
                        one_transac_source = {}
                        one_transac_destination = {}
                        for x in range(len(transactions)) :
                            trans_type = transactions[x]['transaction_type_id']
                            source = transactions[x]['trasac_account_source']
                            _logger.debug('source: %s acoount caisse: %s ', source[0]['id'],account_caisse[0]['id'])
                            if str(source[0]['id']) == str(account_caisse[0]['id']):
                                montant=transactions[x]['transac_amount']
                                _logger.debug('montant: %s ', montant)
                                total_source += int(montant)
                                
                                one_transac_source = {
                                    "type":trans_type[0]['type_value'],
                                    "montant":transactions[x]['transac_amount'],
                                    "transaction_number":transactions[x]['transaction_reff'],
                                    "date_transaction":transactions[x]['transac_date'],
                                    "frais": transactions[x]['trasac_crone_commission']+transactions[x]['trasac_partenaire_commission'],
                                    "tag" : transactions[x]['tag']
                                    }
                               
                                one_transac_source["is_source"]=True
                                destination_acc = transactions[x]['trasac_account_destination']
                                if destination_acc[0]["account_type"] == 'client':
                                    dest_client_id = destination_acc[0]["account_client_owner"]
                                    dest_client = http.request.env['money_management.client'].sudo().search([('id', '=', dest_client_id[0]["id"])])
                                    one_transac_source["from_or_to"]=dest_client[0]["telephone"]
                                   
                                elif destination_acc[0]["account_type"] == 'boutique':
                                    dest_boutique_id = destination_acc[0]["account_boutique_owner"]
                                    dest_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', dest_boutique_id[0]["id"])])
                                    one_transac_source["from_or_to"]=dest_boutique[0]["designation"]
                                
                                elif destination_acc[0]["account_type"] == 'caisse':
                                    dest_caisse_id = destination_acc[0]["account_caisse_owner"]
                                    dest_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', dest_caisse_id[0]["id"])])
                                    one_transac_source["from_or_to"]=dest_caisse[0]["designation"]
                                    
                                elif destination_acc[0]["account_type"] == 'oeuvre':
                                    dest_oeuvre_id = destination_acc[0]["account_oeuvrecaritative_owner"]
                                    dest_oeuvre = http.request.env['money_management.oeuvrecaritative'].sudo().search([('id', '=', dest_oeuvre_id[0]["id"])])
                                    one_transac_source["from_or_to"]=dest_oeuvre[0]["name"]
                                else :
                                    one_transac_source["from_or_to"]=''
                                transactions_source.append(one_transac_source)
                            else:
                                
                                
                                total_destination += transactions[x]['transac_amount']
                                
                                one_transac_destination = {
                                    "type":trans_type[0]['type_value'],
                                    "montant":transactions[x]['transac_amount'],
                                    "transaction_number":transactions[x]['transaction_reff'],
                                    "date_transaction":transactions[x]['transac_date'],
                                    "frais": transactions[x]['trasac_crone_commission']+transactions[x]['trasac_partenaire_commission'],
                                    "tag" : transactions[x]['tag']
                                    }
                                                         
    
                                one_transac_destination["is_source"]=False
                                source_acc = transactions[x]['trasac_account_source']
                                
                                if source_acc[0]["account_type"] == 'client':
                                    source_client_id = source_acc[0]["account_client_owner"]
                                    source_client = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id[0]["id"])])
                                    one_transac_destination["from_or_to"]=source_client[0]["telephone"]
                                elif source_acc[0]["account_type"] == 'boutique':
                                    source_botique_id = source_acc[0]["account_boutique_owner"]
                                    sourec_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', source_botique_id[0]["id"])])
                                    one_transac_destination["from_or_to"]=sourec_boutique[0]["designation"]
                                    
                                elif source_acc[0]["account_type"] == 'caisse':
                                    source_caisse_id = source_acc[0]["account_caisse_owner"]
                                    source_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', source_caisse_id[0]["id"])])
                                    one_transac_destination["from_or_to"]=source_caisse[0]["designation"]
                                else :
                                    one_transac_destination["from_or_to"]=''
                                transactions_destination.append(one_transac_destination)
            
                _logger.debug('solde caisse: %s ', account_caisse[0]['solde'])
                response["message"]="Granted !"
                response["responseCode"]=1
                response["solde_caisse"]=account_caisse[0]['solde']
                response["total_source"]=total_source
                response["total_destination"]=total_destination
                response["transactions_source"]= transactions_source
                response["transactions_destination"]= transactions_destination

            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response
    
    # Api oeuvre caricative
    @http.route(
        '/api/GetOeuvresCaritatives/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def getOeuvresCaritatives(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                token = data['token']
                clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) == 0:
                    code = random.randint(1111,9999)
                    client_id = data['client_id']
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                    response["message"] = "Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                    response["responseCode"]=2
                    return response
                else :
                    oeuvres_request  = http.request.env['money_management.oeuvrecaritative'].sudo().search([])
                    oeuvres_list = []
                    for x in range(len(oeuvres_request)) :
                        one_oeuvre = {
                            "id":oeuvres_request[x]['id'],
                            "name":oeuvres_request[x]['name'],
                            "telephone":oeuvres_request[x]['telephone'],
                            "adresse":oeuvres_request[x]['adresse'],
                            "image":oeuvres_request[x]['logo'],
                            "description":oeuvres_request[x]['description'],
                        }
                        oeuvres_list.append(one_oeuvre)
                    response["message"]="Granted!"
                    response["responseCode"]=1
                    response['oeuvres']= oeuvres_list
            else:
                response["message"]="Access Denied !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response

    
    @http.route(
        '/api/DonationTransaction/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def donationTransaction(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']

            sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
            uid = sock_common.login(db, username, password)
            sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')

            if key == apikey:
                token = data['token']
                client_id = data['client_id']
                clients = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[[ 'token','=',token]]],{'fields': ['id','state_identite','validation_code'], 'limit': 1})
                #clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) == 0:
                    code = random.randint(1111,9999)
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                    response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                    response["responseCode"]=2
                    return response
                else :
                    if clients[0]["state_identite"]=="suspendu":
                        response["message"]="Votre compte est actuellement  suspendu"
                        response["responseCode"]=0
                    else:
                        oeuvre_id =  data['oeuvre_id']
                        amount = data['donation_amount']
                        transaction_id = data['transaction_id']
                        client_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', client_id]]],{'fields': ['id','solde','all_transact_month','solde_nondispo','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                        #client_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)])
                        if len(client_account) == 0:
                            response["message"]="Client inconnue !"
                            response["responseCode"]=0
                        else:
                            #check Plafond
                            # today_date_str = datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59'
                            # today_array = today_date_str.split('-')
                            # first_month_day_str = today_array[0]+today_array[1]+'01' + ' 00:00:00'
                            # trasactions = http.request.env['money_management.transaction'].sudo().search(['|',('trasac_account_source', '=', client_account[0]["id"]),('trasac_account_destination', '=', client_account[0]["id"]),('transac_date', '>=', first_month_day_str),('transac_date', '<=', today_date_str)])
                            # all_trasactions_amount = 0
                            # for transaction in trasactions :
                            #     if transaction["trasac_account_source"]["id"] == client_account[0]["id"] :
                            #         all_trasactions_amount += transaction["transac_amount"] + transaction["trasac_crone_commission"] +transaction["trasac_partenaire_commission"]
                            #     else :
                            #         all_trasactions_amount += transaction["transac_amount"]
                            
                            all_trasactions_amount = client_account[0]["all_transact_month"]
                            plafond_mvt = client_account[0]["mouvement_plafond"]
                            plafond_s = client_account[0]["solde_plafond"]
                            if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+amount) > plafond_mvt or client_account[0]["solde"]>=plafond_s:
                                catego = http.request.env['money_management.categorie_facturation'].sudo().search([('type', '=', 'client')], order="numero asc")
                                messag= "Vous avez atteint le plafond de vos transactions mensuelles.\nMerci de déplafonner votre compte \n"
                                for categor in catego:
                                    sold_p=int(categor["solde_plafond"])
                                    mvt_p=int(categor["mvt_plafond"])
                                    messag +="\n"+str(categor["numero"])+": "+str(categor["nom"])+" Solde:"+f"{sold_p:,}".replace(",", " ")+" Cumul:"+f"{mvt_p:,}".replace(",", " ")
                                        
                                response["message"]=messag
                                response["responseCode"]=0
                                
                            else :
                                solde_client=client_account[0]["solde"]
                                all_trasactions_amount += amount
                                if all_trasactions_amount >= plafond_s :
                                    response["message"]="Avec ce montant votre compte dépasse le plafond de vos transactions mensuelles.\nMerci de déplafonner votre compte s'il ne l'est toujours pas!"
                                    response["responseCode"]=0
                                else :
                                    #check restrictions
                                    # restrictions = http.request.env['money_management.credit_restricted'].sudo().search([('account_ref', '=', client_account[0]["id"]), ('state', '=', 'active')], order='date_creation desc')
                                    # unavalable_solde = 0
                                    # for rest in restrictions :
                                    #     if len(rest["cartegorie_id"]) == 0 :
                                    #         if  rest["consumption_date"] <= datetime.datetime.now() :
                                    #             soldeaft=rest["amount"]+rest["account_ref"]["solde"]
                                    #             http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', rest["account_ref"]["id"])]).write({'solde': soldeaft})
                                    #             http.request.env['money_management.credit_restricted'].sudo().search([('id', '=', rest['id'])]).write({"notification":"envoye",'state': 'inactive'})
                                    #             mont=int(rest["amount"])
                                    #             payload = {
                                    #                 'number': rest["account_ref"]["telephone"],
                                    #                 'content': 'Vous avez un transfert de '+f"{mont:,}".replace(",", " ")+"F  "+rest["tag"]+'\n Merci d\'utiliser CRONE.',
                                    #                 'key':'dZaN51165420050074130180748146013011022542127230465869',
                                    #             }
                                    #             requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                                    #         else:
                                    #             unavalable_solde += rest["amount"]
                                    #     else :
                                    #         unavalable_solde +=(rest["amount"] - rest["used_amount"])
                                    unavalable_solde = client_account[0]["solde_nondispo"]
                                    avalable_solde = solde_client - unavalable_solde
                                    #solde_client_source = avalable_solde
                                    
                                    solde_client_after = avalable_solde - amount
                                    if solde_client_after < 0 :
                                        response["message"]="Le solde du client est insuffisant !"
                                        response["responseCode"]=0
                                    else:
                                        solde_client_after = solde_client - amount
                                        oeuvre_account = http.request.env['money_management.account'].sudo().search([('account_oeuvrecaritative_owner', '=', oeuvre_id)])
                                        solde_oeuvre =oeuvre_account[0]["solde"]
                                        transaction_values = {
                                            "transac_amount":amount,
                                            "trasac_account_source":client_account[0]["id"],
                                            "trasac_account_destination":oeuvre_account[0]["id"],
                                            "trasac_crone_commission":0,
                                            "trasac_partenaire_commission":0,
                                            "transaction_type_id":transaction_id,
                                        }
                                        solde_oeuvre_after=solde_oeuvre + amount
                                        http.request.env['money_management.account'].sudo().search([('account_oeuvrecaritative_owner', '=', oeuvre_id)]).write({'solde': solde_oeuvre_after})
                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)]).write({'solde': solde_client_after})
                                        http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                        mont=int(amount)
                                        response["message"]="Vous avez éffectué une donation de "+f"{mont:,}".replace(",", " ")+" Fcfa pour "
                                        response["responseCode"]=1

            else:
                response["message"]="Access Denied !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response
    
    # API resend validation
    @http.route(
        '/api/ResendSmsValidation/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def resendValidationCode(self, **post):
        response={}
        try:
            data = post['data']
            key=post['api_key']
            if key == apikey:
                phone = data['phone_number']
                clients = http.request.env['money_management.client'].sudo().search([('telephone','=',phone)])
                if len(clients) == 0:
                    response["message"]="Client inconnue !"
                    response["responseCode"]=0
                else:
                    payload = {
                        'number': phone, 
                        'content': 'Votre code de validation CRONE est : '+clients[0]['validation_code'],
                        'key':'dZaN51165420050074130180748146013011022542127230465869', 
                    }
                    requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                    response["message"]="Code de validation renvoyé à "+phone+" avec succès !"
                    response["responseCode"]=1
            else:
                response["message"]="Access Denied !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response

    # Api QR code client
    @http.route(
        '/api/CustomerQr/', 
        type='json', auth="public", 
        methods=['POST'], website=True, csrf=False)
    def cutomer_qr_generator(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                token = data["token"]
                client_id=data["client_id"]
                amount = data["amount"]
                qr_type = data["qr_type"]
                clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) > 0:
                    client_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)])
                    if len(client_account) == 0:
                        response["message"]="Client inconnue !"
                        response["responseCode"]=0
                    else:
                        solde_client=client_account[0]["solde"]
                        solde_client_after = solde_client - amount
                        if solde_client_after < 0 :
                            response["message"]="Le solde du votre compte est insuffisant !"
                            response["responseCode"]=0
                        else:
                            new_qr_dto ={
                                "amount": amount,
                                "customer": client_id,
                                "qr_type": qr_type
                            }
                            qr_code_object = http.request.env['money_management.customerqr'].sudo().create(new_qr_dto)
                            response["message"]="Génération du QRCode Réussi !"
                            response["responseCode"]=1
                            response["qr_id"]=qr_code_object[0]["id"]
                else:
                    code = random.randint(1111,9999)
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                    response["message"]="Votre compte est actuellement actif dans un autre appareil \nVeuillez vous connecter à nouveau pour continuer!"
                    response["responseCode"]=2

            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        
        return response
    
    # Api Get UV crone orabank
    @http.route(
        '/api/getCroneUv/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def get_crone_uv(self, **post):
        response={}
        try:
            key=post["api_key"]
            if key == apikey:
                print('key ok')
                crone_uv = http.request.env['ir.config_parameter'].sudo().get_param('crone_uv')
                response["responseCode"]=1
                response["crone_uv"]=crone_uv
            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response

    # Api transfert avec restriction    
    @http.route(
        '/api/restrictionTransfert/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def transfert_with_conditions(self, **post):
        response={}
        try:
            data =post["data"]
            key=post["api_key"]
            if key == apikey:
                transac_amount = data['amount']
                transac_type_id = data['type']
                crone_comm = data['crone_comm']
                partener_comm = data['partner_comm']
                token = data["token"]
                source_client_id = data['client_id']
                destination_client_phone = data['client_destination_phone']
                sector_id = data["sector_id"]
                
                try :

                    consumption_date =  datetime.datetime.strptime(data["consumption_date"], '%d-%m-%Y %H:%M:%S')
                    print("Consumption date is not none")
                    today_date = datetime.date.today()
                    if consumption_date.date() < today_date :
                        #raise ValidationError("Erreur : Date d'effet invalide !")
                        response["message"]="Erreur: La date à laquelle le montant sera disponible est invalide !"
                        response["responseCode"]=0
                        return response
                except Exception as date_except :
                    consumption_date=None
                    print("Consumption date is  none")
                    print(str(date_except))

                clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) > 0:
                    if clients[0]["state_identite"]=="suspendu":
                        response["message"]="Votre compte est actuellement suspendu"
                        response["responseCode"]=0
                    else:
                        client_source_account = http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)])
                        if len(client_source_account) == 0:
                            response["message"]="Client inconnu !"
                            response["responseCode"]=0
                        else:
                            #check Plafond
                            today_date_str = datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59'
                            today_array = today_date_str.split('-')
                            first_month_day_str = today_array[0]+'-'+today_array[1]+'-'+'01' + ' 00:00:00'
                            _logger.debug('compte source: %s today: %s Premier du Mois: %s', client_source_account[0]["id"],today_date_str,first_month_day_str)
                            trasactions = http.request.env['money_management.transaction'].sudo().search(['|',('trasac_account_source', '=', client_source_account[0]["id"]),('trasac_account_destination', '=', client_source_account[0]["id"]),('transac_date', '>=', first_month_day_str),('transac_date', '<=', today_date_str)])
                            #,('transac_date', '>=', first_month_day_str),('transac_date', '<=', today_date_str)
                            _logger.debug('transactions: %s ', trasactions)
                            all_trasactions_amount = 0
                            for transaction in trasactions :
                                if transaction["trasac_account_source"]["id"] == client_source_account[0]["id"] :
                                    all_trasactions_amount += transaction["transac_amount"] + transaction["trasac_crone_commission"] +transaction["trasac_partenaire_commission"]
                                else :
                                    all_trasactions_amount += transaction["transac_amount"]
                                    

                            plafond_mvt = client_source_account[0]["mouvement_plafond"]
                            plafond_s = client_source_account[0]["solde_plafond"]
                            if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+transac_amount) > plafond_mvt or client_source_account[0]["solde"]>=plafond_s:
                            
                                catego = http.request.env['money_management.categorie_facturation'].sudo().search([('type', '=', 'client')], order="numero asc")
                                messag= "Vous avez atteint le plafond de vos transactions mensuelles.\nMerci de déplafonner votre compte \n"
                                choix= []
                                for categor in catego:
                                    sold_p=int(categor["solde_plafond"])
                                    mvt_p=int(categor["mvt_plafond"])
                                    messag +="\n"+str(categor["numero"])+": "+str(categor["nom"])
                                    text="Vous avez choisi la catégorie "+str(categor["nom"])+" vous allez béneficier d'un solde de "+" Solde:"+f"{sold_p:,}".replace(",", " ")+" et d'un cumul de "+f"{mvt_p:,}".replace(",", " ")
                                    choix.append(text)
                                        
                                response["message"]=messag
                                response["choix"]=choix
                                response["responseCode"]=3
                            
                            else :
                                solde_client_source=client_source_account[0]["solde"]
                                #check restrictions
                                unavalable_solde = 0
                                restrictions = http.request.env['money_management.credit_restricted'].sudo().search([('account_ref', '=', client_source_account[0]["id"]), ('state', '=', 'active')], order='date_creation desc')
                                for rest in restrictions :
                                    if len(rest["cartegorie_id"]) != 0 :
                                            
                                        #if  rest["consumption_date"] <= datetime.datetime.now() :
                                        #    soldeaft=rest["amount"]+rest["account_ref"]["solde"]
                                        #    http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', rest["account_ref"]["id"])]).write({'solde': soldeaft})
                                        #    http.request.env['money_management.credit_restricted'].sudo().search([('id', '=', rest['id'])]).write({"notification":"envoye",'state': 'inactive'})
                                        #    mont=int(rest["amount"])
                                        #    payload = {
                                        #        'number': rest["account_ref"]["telephone"],
                                        #        'content': 'Vous avez un transfert de '+f"{mont:,}".replace(",", " ")+"F  "+rest["tag"]+'\n Merci d\'utiliser CRONE.',
                                        #        'key':'dZaN51165420050074130180748146013011022542127230465869',
                                        #    }
                                        #    requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                                        #else:
                                        #unavalable_solde += rest["amount"]
                                            
                                
                                        unavalable_solde +=(rest["amount"] - rest["used_amount"])
                                       
                                client_source_account.write({"solde_nondispo":unavalable_solde})
                                avalable_solde = solde_client_source - unavalable_solde
                                print("Avalable solde = " + str(avalable_solde))
                                #solde_client_source = avalable_solde
                                solde_client_source_after = avalable_solde - transac_amount
                                if solde_client_source_after < 0 :
                                    response["message"]="Le solde de votre compte est insuffisant !"
                                    response["responseCode"]=0
                                else:
                                    solde_client_source_after = solde_client_source - transac_amount
                                    client_destination = http.request.env['money_management.client'].sudo().search([('telephone', '=', destination_client_phone)])
                                    if len(client_destination) > 0:
                                        if client_destination[0]["state_identite"]=="suspendu":
                                            response["message"]="Le compte du client destinataire est actuellement suspendu"
                                            response["responseCode"]=0
                                        else:
                                            client_destination_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination[0]['id'])])

                                            #check destination Plafond
                                            trasactions = http.request.env['money_management.transaction'].sudo().search(['|',('trasac_account_source', '=', client_destination_account[0]["id"]),('trasac_account_destination', '=', client_destination_account[0]["id"]),('transac_date', '>=', first_month_day_str),('transac_date', '<=', today_date_str)])
                                            all_trasactions_amount = 0
                                            for transaction in trasactions :
                                                if transaction["trasac_account_source"]["id"] == client_destination_account[0]["id"] :
                                                    all_trasactions_amount += transaction["transac_amount"] + transaction["trasac_crone_commission"] +transaction["trasac_partenaire_commission"]
                                                else :
                                                    all_trasactions_amount += transaction["transac_amount"]

                                            if client_destination_account[0]["deplafonnement"] == False :
                                                client_plafond = http.request.env['ir.config_parameter'].sudo().get_param('plafond') or '200000.0'
                                                plafond = float(client_plafond)
                                            else :
                                                client_plafond = http.request.env['ir.config_parameter'].sudo().get_param('deplafonnement_value') or '2000000.0'
                                                plafond = float(client_plafond)
                                            
                                            if all_trasactions_amount >= plafond :
                                                response["message"]="Le bénéficiaire a atteint le plafond de ces transactions mensuelles."
                                                response["responseCode"]=0
                                            else :
                                                all_trasactions_amount += transac_amount - (crone_comm + partener_comm)
                                                if all_trasactions_amount > plafond :
                                                    response["message"]="Le bénéficiaire a atteint le plafond de ces transactions mensuelles."
                                                    response["responseCode"]=0
                                                else :
                                                    sole_client_destination=client_destination_account[0]["solde"]
                                                    transac_amount = transac_amount - (crone_comm + partener_comm)
                                                    transaction_values = {
                                                        "transac_amount":transac_amount,
                                                        "trasac_account_source":client_source_account[0]["id"],
                                                        "trasac_account_destination":client_destination_account[0]["id"],
                                                        "trasac_crone_commission":crone_comm,
                                                        "trasac_partenaire_commission":partener_comm,
                                                        "transaction_type_id":transac_type_id,
                                                    }
                                                    
                                                    print("dest client found!")
                                                    transact_tag=""
                                                    if sector_id != 0:
                                                        trading_types = http.request.env['money_management.trading_type'].sudo().search([('id', '=', sector_id)])
                                                        if consumption_date is not None :
                                                            restriction_dto = {
                                                                "amount": transac_amount,
                                                                "cartegorie_id":sector_id,
                                                                "consumption_date": consumption_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                                "account_ref": client_destination_account[0]["id"],
                                                                "tag":" Reçu de "+client_source_account[0]["account_client_owner"]["name"]+" ("+client_source_account[0]["account_client_owner"]["telephone"]+") ",
                                                                'state':'inactive'
                                                            }
                                                            transact_tag = trading_types[0]["name"]+" : Dispo le " + consumption_date.strftime('%d-%m-%Y %H:%M:%S')
                                                            
                                                            transaction_values["tag"] = transact_tag
                                                            http.request.env['money_management.credit_restricted'].sudo().create(restriction_dto)
                                                            print("restriction created!")
                                                            #sole_client_destination_after=sole_client_destination + transac_amount
                                                            #http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination[0]['id'])]).write({'solde': sole_client_destination_after})
                                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)]).write({'solde': solde_client_source_after})
                                                            http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                                            response["message"]="Transfert éffectué avec succès !"
                                                            response["responseCode"]=1
                                                            
                                                        else :
                                                            restriction_dto = {
                                                                "amount": transac_amount,
                                                                "cartegorie_id":sector_id,
                                                                "account_ref": client_destination_account[0]["id"],
                                                                "tag":"Reçu de "+client_source_account[0]["account_client_owner"]["name"]+"("+client_source_account[0]["account_client_owner"]["telephone"]+")",
                                                                "notification":"envoye"
                                                            }
                                                            transact_tag = trading_types[0]["name"]

                                                            transaction_values["tag"] = transact_tag
                                                            http.request.env['money_management.credit_restricted'].sudo().create(restriction_dto)
                                                            print("restriction created!")
                                                            sole_client_destination_after=sole_client_destination + transac_amount
                                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination[0]['id'])]).write({'solde': sole_client_destination_after})
                                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)]).write({'solde': solde_client_source_after})
                                                            http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                                            response["message"]="Transfert éffectué avec succès !"
                                                            response["responseCode"]=1
                                                            client_source_sms = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id)])
                                                            mont=int(transac_amount)
                                                            payload = {
                                                                'number': destination_client_phone,
                                                                'content': 'Vous avez reçu un transfert de '+f"{mont:,}".replace(",", " ")+' Fcfa provenant de '+client_source_sms[0]['telephone']+transact_tag+'\n Merci d\'utiliser CRONE.',
                                                                'key':'dZaN51165420050074130180748146013011022542127230465869',
                                                            }
                                                            requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                                                    else :
                                                        restriction_dto = {
                                                            "amount": transac_amount,
                                                            "consumption_date": consumption_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                            "account_ref": client_destination_account[0]["id"],
                                                            "tag":"Reçu de "+client_source_account[0]["account_client_owner"]["name"]+"("+client_source_account[0]["account_client_owner"]["telephone"]+")",
                                                            'state':'inactive'
                                                        }
                                                        transact_tag = "Dispo le " + consumption_date.strftime('%d-%m-%Y %H:%M:%S')
                                                        transaction_values["tag"] = transact_tag
                                                        http.request.env['money_management.credit_restricted'].sudo().create(restriction_dto)
                                                        
                                                        #sole_client_destination_after=sole_client_destination + transac_amount
                                                        #http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_destination[0]['id'])]).write({'solde': sole_client_destination_after})
                                                        http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)]).write({'solde': solde_client_source_after})
                                                        http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                                        response["message"]="Transfert éffectué avec succès !"
                                                        response["responseCode"]=1
                                                    
                                    else :
                                        print("dest client not found!")
                                        new_clent_value = {
                                            "name":"",
                                            "telephone":destination_client_phone,
                                            "adresse":""
                                        }
                                        client_dest_id = http.request.env['money_management.client'].sudo().create(new_clent_value)
                                        transac_amount = transac_amount - (crone_comm + partener_comm)
                                        new_client_account_values ={
                                            "solde": transac_amount,
                                            "account_type":"client",
                                            "account_client_owner":client_dest_id[0]['id']
                                            
                                        }
                                        client_destination_account_id = http.request.env['money_management.account'].sudo().create(new_client_account_values)
                                        transaction_values = {
                                            "transac_amount":transac_amount,
                                            "trasac_account_source":client_source_account[0]["id"],
                                            "trasac_account_destination":client_destination_account_id[0]['id'],
                                            "trasac_crone_commission":crone_comm,
                                            "trasac_partenaire_commission":partener_comm,
                                            "transaction_type_id":transac_type_id,
                                        }
                                        transact_tag = ""
                                        if sector_id != 0:
                                            trading_types = http.request.env['money_management.trading_type'].sudo().search([('id', '=', sector_id)])
                                            if consumption_date is not None :
                                                restriction_dto = {
                                                    "amount": transac_amount,
                                                    "cartegorie_id":sector_id,
                                                    "consumption_date": consumption_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                    "account_ref": client_destination_account_id[0]["id"],
                                                    "tag":"Reçu de "+client_source_account[0]["account_client_owner"]["name"]+"("+client_source_account[0]["account_client_owner"]["telephone"]+")",
                                                    'state':'inactive'
                                                }
                                                transaction_values["tag"] = transact_tag
                                                http.request.env['money_management.credit_restricted'].sudo().create(restriction_dto)
                                                http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)]).write({'solde': solde_client_source_after})
                                                http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                                response["message"]="Transfert éffectué avec succès !"
                                                response["responseCode"]=1
                                                
                                                
                                            else :
                                                restriction_dto = {
                                                    "amount": transac_amount,
                                                    "cartegorie_id":sector_id,
                                                    "account_ref": client_destination_account_id[0]["id"],
                                                    "tag":"Reçu de "+client_source_account[0]["account_client_owner"]["name"]+"("+client_source_account[0]["account_client_owner"]["telephone"]+")",
                                                    "notification":"envoye"
                                                }
                                                transaction_values["tag"] = transact_tag
                                                http.request.env['money_management.credit_restricted'].sudo().create(restriction_dto)
                                                http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)]).write({'solde': solde_client_source_after})
                                                http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                                response["message"]="Transfert éffectué avec succès !"
                                                response["responseCode"]=1
                                                client_source_sms = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id)])
                                                mont=int(transac_amount)
                                                payload = {
                                                    'number': destination_client_phone,
                                                    'content': 'Votre compte CRONE a été créé !\n Et vous venez d\'y reçevoir un montant de '+f"{mont:,}".replace(",", " ")+' Fcfa provenant de '+client_source_sms[0]['telephone']+'\n Merci de télécharger l\'application CRONE pour accéder à votre compte.\nhttps://play.google.com/store/apps/details?id=smartedigital.crone',
                                                    'key':'dZaN51165420050074130180748146013011022542127230465869',
                                                }
                                                requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                                        else :
                                            restriction_dto = {
                                                "amount": transac_amount,
                                                "consumption_date": consumption_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                "account_ref": client_destination_account_id[0]["id"],
                                                "tag":"Reçu de "+client_source_account[0]["account_client_owner"]["name"]+"("+client_source_account[0]["account_client_owner"]["telephone"]+")",
                                                'state':'inactive'
                                            }
                                            transact_tag = "Dispo le " + consumption_date.strftime('%d-%m-%Y %H:%M:%S')
                                            transaction_values["tag"] = transact_tag
                                            http.request.env['money_management.credit_restricted'].sudo().create(restriction_dto)
                                            http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', source_client_id)]).write({'solde': solde_client_source_after})
                                            http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                            response["message"]="Transfert éffectué avec succès !"
                                            response["responseCode"]=1
                                            
                else:
                    code = random.randint(1111,9999)
                    http.request.env['money_management.client'].sudo().search([('id','=',source_client_id)]).write({"validation_code": str(code)})
                    response["message"]="Votre compte est actuellement actif sur un autre appareil \nVeuillez à nouveau valider votre numero de téléphone pour continuer!"
                    response["responseCode"]=2
               
            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response

    # Api solde detail client
    @http.route(
        '/api/getSoldeDetails/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def get_solde_details(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            
            if key == apikey:
                sock_common = XMLServerProxy ('http://91.134.28.181:8069/xmlrpc/common')
                uid = sock_common.login(db, username, password)
                sock = XMLServerProxy('http://91.134.28.181:8069/xmlrpc/object')

                token = data["token"]
                account_number=data["account_number"]
                client_id = data["client_id"]
                clients = sock.execute_kw(db, uid, password,'money_management.client', 'search_read',[[[ 'id','=',client_id ]]],{'fields': ['id','state_identite','telephone'], 'limit': 1})
                #clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) > 0:
                    client_account = sock.execute_kw(db, uid, password,'money_management.account', 'search_read',[[[ 'account_client_owner', '=', clients[0]['id'] ]]],{'fields': ['id','account_number','solde','all_transact_month','solde_nondispo','solde_plafond','mouvement_plafond','mensuel','date_payement','deplafonnement'], 'limit': 1})
                    #client_account= http.request.env['money_management.account'].sudo().search([('account_number', '=', account_number)])
                    if len(client_account) == 0:
                        response["message"]="Client inconnue !"
                        response["responseCode"]=0
                    else:
                        restriction_array = []
                        all_nondispo=0
                        mountcat_non=0
                        restrictions = http.request.env['money_management.credit_restricted'].sudo().search([('account_ref', '=', client_account[0]["id"]), ('state', '=', 'active')], order='date_creation desc')
                        for rest in restrictions :
                            if len(rest["cartegorie_id"]) == 0 :
                                if  rest["consumption_date"] <= datetime.datetime.now() :
                                    http.request.env['money_management.credit_restricted'].sudo().search([('id', '=', rest['id'])]).write({'state': 'inactive'})
                                else :
                                    all_nondispo=rest["amount"]-rest["used_amount"]
                                    one_restriction = {
                                        "sector_name" : "All Sector",
                                        "sector_id" : 0,
                                        "amount" : rest["amount"],
                                        "used_amount" : rest["used_amount"],
                                        "date":rest["consumption_date"],
                                        "tag" : rest["tag"]
                                    }
                                    restriction_array.append(one_restriction)
                            elif len(rest["cartegorie_id"]) != 0 :
                                today=datetime.datetime.now()
                                dt=rest["consumption_date"]
                                
                                if type(dt) == bool:
                                    one_restriction = {
                                        "dispo" : 1,
                                        "sector_name" : rest["cartegorie_id"]["name"],
                                        "sector_id" : rest["cartegorie_id"]["id"],
                                        "amount" : rest["amount"],
                                        "used_amount" : rest["used_amount"],
                                        "date":rest["consumption_date"],
                                        "tag" : rest["tag"],
                                        
                                    }
                                elif dt<today :
                                    one_restriction = {
                                        "dispo" : 1,
                                        "sector_name" : rest["cartegorie_id"]["name"],
                                        "sector_id" : rest["cartegorie_id"]["id"],
                                        "amount" : rest["amount"],
                                        "used_amount" : rest["used_amount"],
                                        "date":rest["consumption_date"],
                                        "tag" : rest["tag"],   
                                    }
                                else:
                                    mountcat_non=rest["amount"]-rest["used_amount"]
                                    one_restriction = {
                                        "dispo" : 0,
                                        "sector_name" : rest["cartegorie_id"]["name"],
                                        "sector_id" : rest["cartegorie_id"]["id"],
                                        "amount" : rest["amount"],
                                        "used_amount" : rest["used_amount"],
                                        "date":rest["consumption_date"],
                                        "tag" : rest["tag"],
                                       
                                    }
                                
                                restriction_array.append(one_restriction)

                        #restrictions = http.request.env['money_management.credit_restricted'].sudo().search([('account_ref', '=', client_account[0]["id"]), ('state', '=', 'active')], order='date_creation desc')
                        _logger.debug('Solde detail: %s ', client_account[0]["solde"])
                        _logger.debug('Solde detail: %s ', client_account[0]["account_number"])
                        response["message"]="Génération du QRCode Réussi !"
                        response["responseCode"] = 1
                        response["global_solde"] = client_account[0]["solde"]
                        #-(mountcat_non+all_nondispo)
                        response["restrictions"] = restriction_array
                else:
                    code = random.randint(1111,9999)
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                    response["message"]="Votre compte est actuellement actif dans un autre appareil \nVeuillez vous connecter à nouveau pour continuer!"
                    response["responseCode"]=2

            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response

    # Api creation pin    
    @http.route(
        '/api/pincreation/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def pin_creation(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                token = data["token"]
                client_id = data["client_id"]
                pin_b=data["pin"]
                clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) > 0:
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"pin":pin_b})
                    response["responseCode"]=1
                    response["message"]="Code PIN enregistrer avec succès !"
                else:
                    code = random.randint(1111,9999)
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                    response["message"]="Votre compte est actuellement actif dans un autre appareil \nVeuillez vous connecter à nouveau pour continuer!"
                    response["responseCode"]=2
            else:
                response["message"]="Access refused !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response
    

    
    @http.route(
        '/api/upgradePlafond/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def upgradePlafond(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                if 'client_id' in data :
                    client_id = data['client_id']
                    account_number = data["account_number"]
                    account = http.request.env['money_management.account'].sudo().search([('account_number','=',account_number)])
                    client = http.request.env['money_management.client'].sudo().search([('id','=',client_id)])
                    if client[0]['state_identite']=="non verifié":
                        response["responseCode"]=1
                        response["categorie"]=account[0]['account_categorie']['nom']
                        response["plafond_mouvement"]=account[0]['mouvement_plafond']
                        response["plafond_solde"]=account[0]['solde_plafond']
                        response["client_identite"]=client[0]['state_identite']
                        response["message"]="Vous ne pouvez pas déplafonner votre compte .Le KYC n'est pas validé!"
                        
                    else:
                        catego = http.request.env['money_management.categorie_facturation'].sudo().search([('type', '=', 'client')], order="numero asc")
                        messag= "Vous avez atteint le plafond de vos transactions mensuelles.\nMerci de déplafonner votre compte \n"
                        choix=[]
                        for categor in catego:
                            sold_p=int(categor["solde_plafond"])
                            mvt_p=int(categor["mvt_plafond"])
                            messag +="\n"+str(categor["numero"])+": "+str(categor["nom"])
                            text="Vous avez choisi la catégorie "+str(categor["nom"])+" vous allez béneficier d'un solde de "+" Solde:"+f"{sold_p:,}".replace(",", " ")+" et d'un cumul de "+f"{mvt_p:,}".replace(",", " ")
                            choix.append(text)
                            
                        response["message"]=messag
                        response["choix"]=choix
                        response["responseCode"]=1
                        response["categorie"]=account[0]['account_categorie']['nom']
                        response["plafond_mouvement"]=account[0]['mouvement_plafond']
                        response["plafond_solde"]=account[0]['solde_plafond']
                        response["client_identite"]=client[0]['state_identite']
                    
                else:
                    account_number = data["account_number"]
                    type = data["type"]
                    numero  = int(data["numero"])
                    account = http.request.env['money_management.account'].sudo().search([('account_number','=',account_number)])
                    if len(account) > 0:
                        categorie = http.request.env['money_management.categorie_facturation'].sudo().search([('numero','=',numero),('type','=',type)])
                        if len(categorie) > 0:
                            cat =categorie[0]["id"]
                            account.write({"account_categorie":cat})
                            response["responseCode"]=1
                            response["message"]="votre plafond a été changé  avec succès et votre categorie est"+str(categorie[0]["nom"])
                    else:
                        response["message"]="Le compte ne correspond pas!"
                        response["responseCode"]=2
            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response
    
    @http.route(
        '/api/PinVerification/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def pin_verification(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                token = data["token"]
                client_id = data["client_id"]
                pin_b64  = data["pin"]
                clients = http.request.env['money_management.client'].sudo().search([('token','=',token)])
                if len(clients) > 0 :
                    if clients[0]["pin"] == pin_b64 :
                        response["responseCode"] = 1
                        response["message"]="Vérification du code PIN effectué avec succès"
                    else :
                        response["responseCode"]=0
                        response["message"]="Erreur : Code PIN incorrecte !"
                else:
                    code = random.randint(1111,9999)
                    http.request.env['money_management.client'].sudo().search([('id','=',client_id)]).write({"validation_code": str(code)})
                    response["message"]="Votre compte est actuellement actif dans un autre appareil \nVeuillez vous connecter à nouveau pour continuer!"
                    response["responseCode"]=2
            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response
    
    # api pour les manager
    @http.route(
        '/api/CreationManager/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def createManager(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            
            if key == apikey:
                type = data["type"]
                if type=='marchand':
                    
                    marchand_values = {
                        "name":data["name"],
                        "login":data["prenom"],
                        "nom_marchand":data["name"],
                        "telephone":data["telephone"],
                        "email":data["email"],
                        "description":data["description"],
                        "address":data["adresse"],
                        "nb_point_of_sale":data["nb_point_of_sale"],
                    }
                    _logger.debug('marchand values: %s ', marchand_values)
                    http.request.env['res.users'].sudo().create(marchand_values)
                    _logger.debug('marchand apres create')
                    response["responseCode"] = 1
                    response["message"]="Création du marchand"+data["prenom"]+"  "+data["name"]+" est effectué avec succés"
                    
                elif type=='boutique':
                    marchand = http.request.env['res.users'].sudo().search([('nom_marchand','=',data["marchand_nom"]),('telephone','=',data["marchand_telephone"])], limit=1)
                    boutique_values = {
                        "designation":data["designation"],
                        "telephone":data["telephone"],
                        "description":data["description"],
                        "adresse":data["adresse"],
                        "logo":data["logo"],
                        "marchand_id":marchand[0]['id'],
                        
                    }
                    
                    http.request.env['money_management.boutique'].sudo().create(boutique_values)
                    response["responseCode"] = 1
                    response["message"]="Création de la boutique"+str(data["designation"])+" est effectué avec succés"
                    
                elif type=='caisse':
                    boutique = http.request.env['money_management.boutique'].sudo().search([('designation','=',data["boutique_nom"]),('telephone','=',data["boutique_telephone"])], limit=1)
                    categorie=http.request.env['money_management.trading_type'].sudo().search([('name','=',data["categorie"])], limit=1)
                    caisse_values = {
                        "numero":data["numero_caisse"],
                        "designation":data["designation"],
                        "telephone":data["telephone"],
                        "description":data["description"],
                        "caisse_boutique_id":boutique[0]['id'],
                        "Categorie_type":categorie[0]['id']
                        
                    }
                    
                    http.request.env['money_management.caisse'].sudo().create(caisse_values)
                    response["responseCode"] = 1
                    response["message"]="La Caisse"+str(data["numero_caisse"])+"de la boutique est créé avec success"
                    
                elif type=='agent':
                    boutique = http.request.env['money_management.boutique'].sudo().search([('designation','=',data["boutique"])], limit=1)
                    caisse = http.request.env['money_management.caisse'].sudo().search([('designation','=',data["caisse"])], limit=1)
                    
                    agent_values = {
                        "name":data["name"],
                        "login":data["login"],
                        "password":data["password"],
                        "adresse":data["adresse"],
                        "agent_boutique_id":boutique[0]['id'],
                        "agent_caisse_id":caisse[0]['id'],
                        
                    }
                    
                    http.request.env['money_management.agent'].sudo().create(agent_values)
                    response["responseCode"] = 1
                    response["message"]="L'agent "+str(data["name"])+"est créé avec success"
                
            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response

# Requete Manager
    @http.route(
        '/api/RequetetManager/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def requeteManager(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                type=data['type']
                if type=="client": 
                    account =  http.request.env['money_management.account'].sudo().search([('account_type', '=', 'client')])
                    _logger.debug('account: %s ', account)  
                     
                    #Clients = [{"name":account[x]["account_client_owner"]["name"],"adresse":account[x]["account_client_owner"]["adresse"],"telephone":account[x]["telephone"],"compte":account[x]["account_number"],"solde":account[x]["solde"],} for x in range(len(account)) ]      
                    Clients = [{"name":account[x]["account_client_owner"]["name"],"telephone":account[x]["telephone"],"compte":account[x]["account_number"],"solde":account[x]["solde"],} for x in range(len(account)) ] 
                    _logger.debug('clients: %s ', Clients)

                    response["message"]="Granted!"
                    response["responseCode"]=1
                    response['clients']= Clients 
                    

                elif type=='caisse':
                    account =  http.request.env['money_management.account'].sudo().search([('account_type', '=', 'caisse')])
                    caisses = []
                    for x in range(len(account)) :
                        caisse={
                            "numero":account[x]["account_caisse_owner"]["numero"],
                            "caisse":account[x]["account_caisse_owner"]["designation"],
                            "compte":account[x]["account_number"],
                            "solde":account[x]["solde"],
                        }
                        caisses.append(caisse)
                    response["message"]="Granted!"
                    response["responseCode"]=1
                    response['caisses']= caisses

                elif type=='boutique':
                    account =  http.request.env['money_management.account'].sudo().search([('account_type', '=', 'boutique')])
                    boutiques = []
                    for x in range(len(account)) :
                        boutique={
                            "name":account[x]["account_boutique_owner"]["designation"],
                            "telephone":account[x]["account_boutique_owner"]["telephone"],
                            "adresse":account[x]["account_boutique_owner"]["adresse"],
                            "compte":account[x]["account_number"],
                            "solde":account[x]["solde"],
                        }
                        boutiques.append(boutique)

                    response["message"]="Granted!"
                    response["responseCode"]=1
                    response['boutiques']= boutiques

                elif type=='marchand':
                    account =  http.request.env['money_management.account'].sudo().search(['&',('account_type', '=', 'marchand'),('account_marchand_owner', '!=', 2)])
                    marchands=[]
                    _logger.debug('account: %s ', account)
                    for x in range(len(account)) :
                        marchand={
                            "nom":account[x]["account_marchand_owner"]["nom_marchand"],
                            "telephone":account[x]["account_marchand_owner"]["telephone"],
                            "addresse":account[x]["account_marchand_owner"]["address"],
                            "compte":account[x]["account_number"],
                            "solde":account[x]["solde"],
                        }
                        marchands.append(marchand)

                    response["message"]="Granted!"
                    response["responseCode"]=1
                    response['marchands']= marchands

            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        return response   

    # Manager List Transaction
    @http.route(
        '/api/ListransacManager/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def listransacManager(self, **post):
        response={}
        try:
            data=post["data"]
            key=post["api_key"]
            if key == apikey:
                type=data['type']
                if type=="all_account":
                    date_debut=data["date_debut"]
                    if "date_fin" in data:
                        date_fin=data["date_fin"]
                    else:
                        date_fin=datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59'
                    
                    #account_client =  http.request.env['money_management.account'].sudo().search([])
                    transactions_list=[]
                    transactions = http.request.env['money_management.transaction'].sudo().search(['&',('transac_date','>=',date_debut),('transac_date','<=',date_fin)])
                    _logger.debug('Otransaction: %s ',transactions)
                    if len(transactions) > 0:
                        one_transac = {}
                        
                        for x in range(len(transactions)) :
                            trans_type = transactions[x]['transaction_type_id']
                            one_transac = {
                                "type":trans_type[0]['type_value'],
                                "montant":transactions[x]['transac_amount'],
                                "transaction_number":transactions[x]['transaction_reff'],
                                "date_transaction":transactions[x]['transac_date'],
                                "frais": transactions[x]['trasac_crone_commission']+transactions[x]['trasac_partenaire_commission'],
                                "tag" : transactions[x]['tag']
                            }
                            
                            _logger.debug('One tatransaction: %s ', one_transac)
                            if transactions[x]['trasac_account_source']:
                                source_acc = transactions[x]['trasac_account_source']
                                if source_acc[0]["account_type"] == 'client':
                                    source_client_id = source_acc[0]["account_client_owner"]
                                    if len(source_client_id)>0:
                                        source_client = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id[0]["id"])])
                                        one_transac["from"]=source_client[0]["telephone"]
                                elif source_acc[0]["account_type"] == 'boutique':
                                    source_botique_id = source_acc[0]["account_boutique_owner"]
                                    if len(source_botique_id)>0:
                                        sourec_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', source_botique_id[0]["id"])])
                                        one_transac["from"]=sourec_boutique[0]["designation"]   
                                elif source_acc[0]["account_type"] == 'caisse':
                                    source_caisse_id = source_acc[0]["account_caisse_owner"]
                                    if len(source_caisse_id)>0:
                                        source_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', source_caisse_id[0]["id"])])
                                        one_transac["from"]=source_caisse[0]["designation"]
                                else :
                                    one_transac["from"]=''
                            else :
                                    one_transac["from"]=''

                            if transactions[x]['trasac_account_destination']:
                                destination_acc = transactions[x]['trasac_account_destination']
                                _logger.debug('Transaction List type: %s ', destination_acc[0]["account_type"])
                                if destination_acc[0]["account_type"] == 'client':
                                    dest_client_id = destination_acc[0]["account_client_owner"]
                                    if len(dest_client_id)>0:
                                        dest_client = http.request.env['money_management.client'].sudo().search([('id', '=', dest_client_id[0]["id"])])
                                        one_transac["to"]=dest_client[0]["telephone"]
                                    
                                elif destination_acc[0]["account_type"] == 'boutique':
                                    dest_boutique_id = destination_acc[0]["account_boutique_owner"]
                                    if len(dest_boutique_id)>0:
                                        dest_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', dest_boutique_id[0]["id"])])
                                        one_transac["to"]=dest_boutique[0]["designation"]
                                
                                elif destination_acc[0]["account_type"] == 'caisse':
                                    dest_caisse_id = destination_acc[0]["account_caisse_owner"]
                                    if len(dest_caisse_id)>0:
                                        dest_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', dest_caisse_id[0]["id"])])
                                        one_transac["from_or_to"]=dest_caisse[0]["designation"]
                                    
                                elif destination_acc[0]["account_type"] == 'oeuvre':
                                    dest_oeuvre_id = destination_acc[0]["account_oeuvrecaritative_owner"]
                                    if len(dest_oeuvre_id)>0:
                                        dest_oeuvre = http.request.env['money_management.oeuvrecaritative'].sudo().search([('id', '=', dest_oeuvre_id[0]["id"])])
                                        one_transac["to"]=dest_oeuvre[0]["name"]
                                else :
                                    one_transac["to"]=''
                            else :
                                    one_transac["to"]=''
                            
                            transactions_list.append(one_transac)
                            #_logger.debug('Transaction List: %s ', transactions_list)
            
                    response["message"]="Granted !"
                    response["responseCode"]=1
                    response["transactions_destination"]= transactions_list

                elif type=="one_account":
                    account_number=data["account_number"]
                    date_debut=data["date_debut"]
                    if "date_fin" in data:
                        date_fin=data["date_fin"]
                    else:
                        date_fin=datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59'
                    
                    account =  http.request.env['money_management.account'].sudo().search([('account_number', '=', account_number)])
                    
                    transactions_list=[]
                    transactions = http.request.env['money_management.transaction'].sudo().search(['&',('transac_date','>=',date_debut),('transac_date','<=',date_fin),'|',('trasac_account_source', '=', account[0]['id']),('trasac_account_destination', '=', account[0]['id'])])
                    if len(transactions) > 0:
                        one_transac = {}
                        for x in range(len(transactions)) :
                            trans_type = transactions[x]['transaction_type_id']
                            one_transac = {
                                "type":trans_type[0]['type_value'],
                                "montant":transactions[x]['transac_amount'],
                                "transaction_number":transactions[x]['transaction_reff'],
                                "date_transaction":transactions[x]['transac_date'],
                                "frais": transactions[x]['trasac_crone_commission']+transactions[x]['trasac_partenaire_commission'],
                                "tag" : transactions[x]['tag']
                            }
                            
                            if transactions[x]['trasac_account_destination']:
                                destination_acc = transactions[x]['trasac_account_destination']
                                if destination_acc[0]["account_type"] == 'client':
                                    dest_client_id = destination_acc[0]["account_client_owner"]
                                    if len(dest_client_id)>0:
                                        dest_client = http.request.env['money_management.client'].sudo().search([('id', '=', dest_client_id[0]["id"])])
                                        one_transac["to"]=dest_client[0]["telephone"]
                                    
                                elif destination_acc[0]["account_type"] == 'boutique':
                                    dest_boutique_id = destination_acc[0]["account_boutique_owner"]
                                    if len(dest_boutique_id)>0:
                                        dest_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', dest_boutique_id[0]["id"])])
                                        one_transac["to"]=dest_boutique[0]["designation"]
                                
                                elif destination_acc[0]["account_type"] == 'caisse':
                                    dest_caisse_id = destination_acc[0]["account_caisse_owner"]
                                    if len(dest_caisse_id)>0:
                                        dest_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', dest_caisse_id[0]["id"])])
                                        one_transac["to"]=dest_caisse[0]["designation"]
                                    
                                elif destination_acc[0]["account_type"] == 'oeuvre':
                                    dest_oeuvre_id = destination_acc[0]["account_oeuvrecaritative_owner"]
                                    if len(dest_oeuvre_id)>0:
                                        dest_oeuvre = http.request.env['money_management.oeuvrecaritative'].sudo().search([('id', '=', dest_oeuvre_id[0]["id"])])
                                        one_transac["to"]=dest_oeuvre[0]["name"]
                                else :
                                    one_transac["to"]=''
                            else :
                                    one_transac["to"]=''

                            if transactions[x]['trasac_account_source']:         
                                source_acc = transactions[x]['trasac_account_source']
                                if source_acc[0]["account_type"] == 'client':
                                    source_client_id = source_acc[0]["account_client_owner"]
                                    if len(source_client_id)>0:
                                        source_client = http.request.env['money_management.client'].sudo().search([('id', '=', source_client_id[0]["id"])])
                                        one_transac["from"]=source_client[0]["telephone"]
                                elif source_acc[0]["account_type"] == 'boutique':
                                    source_botique_id = source_acc[0]["account_boutique_owner"]
                                    if len(source_botique_id)>0:
                                        sourec_boutique = http.request.env['money_management.boutique'].sudo().search([('id', '=', source_botique_id[0]["id"])])
                                        one_transac["from"]=sourec_boutique[0]["designation"]
                                    
                                elif source_acc[0]["account_type"] == 'caisse':
                                    source_caisse_id = source_acc[0]["account_caisse_owner"]
                                    if len(source_caisse_id)>0:
                                        source_caisse = http.request.env['money_management.caisse'].sudo().search([('id', '=', source_caisse_id[0]["id"])])
                                        one_transac["from"]=source_caisse[0]["designation"]
                                else :
                                    one_transac["from"]=''
                            else :
                                    one_transac["from"]=''    
                            transactions_list.append(one_transac)
                                
            
                    response["message"]="Granted !"
                    response["responseCode"]=1
                    response["solde_client"]=account[0]['solde']
                    response["transactions_list"]= transactions_list
            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0

        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0  
        return response 

    # Aprovisionnement Manager
    @http.route(
        '/api/AprovisionnementManager/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def approvisionManager(self, **post):
        response={}
        try:
            data=post["data"]
           
            key=post["api_key"]
            if key == apikey:
                type=data['type']
                if type=="appro_boutique":
                    marchand = http.request.env['res.user'].search([('designation','=',data["marchand"]),('telephone','=',data["telephone_marchand"])], limit=1)
                    boutique = http.request.env['money_management.boutique'].search([('designation','=',data["boutique"]),('telephone','=',data["telephone_boutique"])], limit=1)
                    appro_values = {
                        "libelle":data["id"],
                        "amount ":data["montant"],
                        "appro_marchand_id":data["marchand"],
                        "appro_boutique_id":boutique[0]['id'],
                        
                    }
                    http.request.env['money_management.approvisionnement'].sudo().create(appro_values)
                    response["responseCode"] = 1
                    response["message"]="L'approvisionnement de la boutique "+str(data["boutique"])+"est effectif"
                    
                elif type=="appro_caisse":
                    boutique = http.request.env['money_management.boutique'].search([('designation','=',data["boutique"]),('telephone','=',data["telephone"])], limit=1)
                    caisse = http.request.env['money_management.caisse'].search([('designation','=',data["caisse"]),('telephone','=',data["telephone"])], limit=1)
                    appro_values = {
                        "libelle":data["id"],
                        "amount ":data["montant"],
                        "appro_marchand_id":boutique[0]['id'],
                        "appro_boutique_id":caisse[0]['id'],
                        
                    }
                    http.request.env['money_management.approvisionnement'].sudo().create(appro_values)
                    response["responseCode"] = 1
                    response["message"]="L'approvisionnement de la caisse "+str(data["caisse"])+"est effectif"
                    
            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        return response    
        
    @http.route(
        '/api/CroneWallet/',
        type='json', auth="public",
        methods=['POST'], website=True, csrf=False)
    def cronewallet(self, **post):
        response={}
        try:
            data1=post
            _logger.debug('requete: %s ', data1)
            data=post["data"]
            _logger.debug('requete: %s ', data)
            key=post["api_key"]
            if key == apikey:
                transac_type=data["transac_type"]
                
                if transac_type=='get-wallet':
                    wallets=http.request.env['money_management.cronewallet'].sudo().search([])
                    wallet_array=[]
                    for walet in wallets:
                        one_wallet={
                             "nom":walet['nom'],
                             "image":walet['image'],
                        }
                        wallet_array.append(one_wallet)
                    response["message"]="Access Granted !"
                    response["wallet_array"]=wallet_array
                    response["responseCode"]=1
                    return response
                    
                elif transac_type =='Crone-to-Wallet':
                    transac_amount = data['amount']
                    crone_comm = data['crone_comm']
                    partener_comm = data['partner_comm']
                    name = data['name']
                    numero=data['phone']
                    client_id = data['client_id']
                    transac_type_id=data['type']

                    cliens= http.request.env['money_management.client'].sudo().search([('id','=',client_id)])
                    if cliens[0]["state_identite"]=="suspendu":
                        response["message"]="Votre compte est actuellement votre compte est suspendu"
                        response["responseCode"]=0
                    else :
                        if transac_amount >100:
                            response["message"]="Pour des raisons de test les transactions Crone to wallet ne peuvent pas depasser 100 F traitement."
                            response["responseCode"]=1
                            return response
                        else:
                            wallet = http.request.env['money_management.cronewallet'].sudo().search([('nom','=',name)])
                            if len(wallet) > 0:
                                
                                client_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)])
                                #check Plafond
                                today_date_str = datetime.date.today().strftime('%Y-%m-%d')+' 23:59:59'
                                today_array = today_date_str.split('-')
                                first_month_day_str = today_array[0]+today_array[1]+'01' + ' 00:00:00'
                                trasactions = http.request.env['money_management.transaction'].sudo().search(['|',('trasac_account_source', '=', client_account[0]["id"]),('trasac_account_destination', '=', client_account[0]["id"]),('transac_date', '>=', first_month_day_str),('transac_date', '<=', today_date_str)])
                                all_trasactions_amount = 0
                                for transaction in trasactions :
                                    if transaction["trasac_account_source"]["id"] == client_account[0]["id"] :
                                        all_trasactions_amount += transaction["transac_amount"] + transaction["trasac_crone_commission"] +transaction["trasac_partenaire_commission"]
                                        
                                    else :
                                        all_trasactions_amount += transaction["transac_amount"]
                
                                
                                plafond_mvt = client_account[0]["mouvement_plafond"]
                                plafond_s = client_account[0]["solde_plafond"]
                                
                                if all_trasactions_amount >= plafond_mvt or (all_trasactions_amount+transac_amount) > plafond_mvt or client_account[0]["solde"]>=plafond_s:
                                    messag= "Vous avez atteint le plafond de vos transactions mensuelles.\nMerci  de déplafonner votre compte \n"
                                    choix=[]
                                    response["message"]=messag
                                    response["choix"]=choix
                                    response["responseCode"]=3
                                    return response
                                else :
                                    solde_client=client_account[0]["solde"]
                                    
                                    #check restrictions
                                    restrictions = http.request.env['money_management.credit_restricted'].sudo().search([('account_ref', '=', client_account[0]["id"]), ('state', '=', 'active')], order='date_creation desc')
                                    unavalable_solde = 0
                                    for rest in restrictions :
                                        if len(rest["cartegorie_id"]) == 0 :
                                            if  rest["consumption_date"] <= datetime.date.today() :
                                                soldeaft=rest["amount"]+rest["account_ref"]["solde"]
                                                http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', rest["account_ref"]["id"])]).write({'solde': soldeaft})
                                                http.request.env['money_management.credit_restricted'].sudo().search([('id', '=', rest['id'])]).write({"notification":"envoye",'state': 'inactive'})
                                                mont=int(rest["amount"])
                                                payload = {
                                                    'number': rest["account_ref"]["telephone"],
                                                    'content': 'Vous avez un transfert de '+f"{mont:,}".replace(",", " ")+"F  "+rest["tag"]+'\n Merci d\'utiliser CRONE.',
                                                    'key':'dZaN51165420050074130180748146013011022542127230465869',
                                                }
                                                requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                                            else:
                                                unavalable_solde += rest["amount"]
                                        else :
                                            unavalable_solde +=(rest["amount"] - rest["used_amount"])

                                    wallet_id=wallet[0]["id"]
                                    wallet_account= http.request.env['money_management.account'].sudo().search([('account_wallet_owner', '=', wallet_id)])
                                    sole_wallet=wallet_account[0]["solde"]
                                    transac_amount = transac_amount - (crone_comm + partener_comm)
                                    
                                    avalable_solde = solde_client - unavalable_solde
                                    solde_client_after=avalable_solde - transac_amount
                                    
                                    if solde_client_after < 0 :
                                        response["message"]="Le solde du client est insuffisant !"
                                        response["responseCode"]=0
                                        return response
                                    else:
                                        solde_client_after=solde_client - transac_amount
                                        transaction_values = {
                                            "transac_amount":transac_amount,
                                            "trasac_account_source":client_account[0]["id"],
                                            "trasac_account_destination":wallet_account[0]["id"],
                                            "trasac_crone_commission":crone_comm,
                                            "trasac_partenaire_commission":partener_comm,
                                            "transaction_type_id":transac_type_id,
                                            "status":"in_process",
                                            
                                        }
                                    
                                        solde_wallet_after=sole_wallet + transac_amount
                                        accW=http.request.env['money_management.account'].sudo().search([('account_wallet_owner', '=', wallet_id)]).write({'solde': solde_wallet_after})
                                        
                                        accC=http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)]).write({'solde': solde_client_after})
                                        
                                        transaction=transaction=http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                        
                                        reff=transaction[0]['transaction_reff']
                                        _logger.debug('Transaction reff: %s ', reff)
                                        transfert_values={
                                            "numero":numero,
                                            "refference":reff,
                                            "message":"",
                                            "etat":"en cours",
                                            "type":"transfert",
                                            "montant":transac_amount,
                                            "wallet":wallet_id,
                                        
                                        }
                                        http.request.env['money_management.transactionwallet'].sudo().create(transfert_values)
                                        
                                        payload=json.dumps({
                                            "api_key":"6b491b92257831c4ea4e3850cf31ab68",

                                            "data": {
                                                    "transaction_uid":reff,
                                                    "transaction_amount":transac_amount,
                                                    "customer_phone":numero,
                                                    "partner_uid":"3e1dbfed-e963-4f0d-9df7-a77ec7215e95",
                                                    "operator_code":"OM",
                                                    "transaction_description":"test api transaction code",
                                                    "transaction_type" : "transfert",
                                                    "transaction_code": "om_transfert"}

                                        })
                                        headers = {'Content-Type': 'application/json'}
                                        
                                        repon=requests.post('http://91.134.28.179:8001/api/InitTransaction/',headers=headers, data=payload)
                                        
                                        _logger.debug('requete: %s ', repon)
                                        montant=int(transac_amount)
                                        response["message"]="Votre transaction de "+f"{montant:,}".replace(",", " ")+" Fcfa vers "+numero+" est en cours de traitement."
                                        response["responseCode"]=1
                                        return response
                            
                elif transac_type =='Wallet-to-Crone':
                    numero=data['phone']
                    transac_amount = data['amount']
                    crone_comm = data['crone_comm']
                    partener_comm = data['partner_comm']
                    name = data['name']
                    client_id = data['client_id']
                    transac_type_id=data['type']

                    cliens= http.request.env['money_management.client'].sudo().search([('id','=',client_id)])
                    if cliens[0]["state_identite"]=="suspendu":
                        response["message"]="Votre compte est actuellement votre compte est suspendu"
                        response["responseCode"]=0
                    else :
                        if transac_amount>100:
                            response["message"]="Pour des raisons de test les transactions wallet to Crone ne peuvent pas depasser 100 F traitement."
                            response["responseCode"]=1
                            return response
                        else:
                            wallet = http.request.env['money_management.cronewallet'].sudo().search([('nom','=',name)])
                            if len(wallet) > 0:
                                wallet_id=wallet[0]["id"]
                                wallet_account= http.request.env['money_management.account'].sudo().search([('account_wallet_owner', '=', wallet_id)])
                                client_account= http.request.env['money_management.account'].sudo().search([('account_client_owner', '=', client_id)])
                                sole_wallet=wallet_account[0]["solde"]
                                transac_amount = transac_amount - (crone_comm + partener_comm)
                                solde_wallet_after=sole_wallet  - transac_amount
                                
                                if solde_wallet_after < 0 :
                                    response["message"]="Le solde wallet  est insuffisant !"
                                    response["responseCode"]=0
                                    return response
                                else:
                                    
                                    transaction_values = {
                                        "transac_amount":transac_amount,
                                        "trasac_account_source":wallet_account[0]["id"],
                                        "trasac_account_destination":client_account[0]["id"],
                                        "trasac_crone_commission":crone_comm,
                                        "trasac_partenaire_commission":partener_comm,
                                        "transaction_type_id":transac_type_id,
                                        "status":"in_process",
                                    }
                                    transaction=http.request.env['money_management.transaction'].sudo().create(transaction_values)
                                    reff=transaction[0]['transaction_reff']
                                    transfert_values={
                                        "numero":numero,
                                        "refference":reff,
                                        "message":"",
                                        "etat":"en cours",
                                        "type":"payment",
                                        "montant":transac_amount,
                                        "wallet":wallet_id,
                                    
                                    }
                                    http.request.env['money_management.transactionwallet'].sudo().create(transfert_values)
                                    
                                    payload=json.dumps({
                                        "api_key":"6b491b92257831c4ea4e3850cf31ab68",

                                        "data": {
                                                "transaction_uid":reff,
                                                "transaction_amount":transac_amount,
                                                "customer_phone":numero,
                                                "partner_uid":"3e1dbfed-e963-4f0d-9df7-a77ec7215e95",
                                                "operator_code":"OM",
                                                "transaction_description":"test api transaction code",
                                                "transaction_type" : "payment",
                                                "transaction_code": "om_depot_sans_frais"}
                                    })
                                    headers = {'Content-Type': 'application/json'}
                                    requests.post('http://91.134.28.179:8001/api/InitTransaction/',headers=headers, data=payload)
                                    
                                    montant=int(transac_amount)
                                    response["message"]="Votre transaction de "+f"{montant:,}".replace(",", " ")+" Fcfa vers "+numero+" est en cours de traitement.Veuillez effectuer la validation."
                                    response["responseCode"]=1
                                    return response
                
                elif transac_type =='callback':
                    codereponse=data['status_code']
                    
                    if codereponse==1:
                        
                        _logger.debug('Transaction type callback: %s ', data['transaction_type'])
                        if data['transaction_type']=="payment":
                            transac_wallet = http.request.env['money_management.transactionwallet'].sudo().search([('refference', '=', data['transaction_uid']),('numero', '=', data['numero']),('etat', '=', 'en cours')])
                            transac_wallet.write({'message':'','etat':'valide',})
                            transac=http.request.env['money_management.transaction'].sudo().search([('transaction_reff', '=', data['transaction_uid']),('status', '=','in_process')])
                            transac.write({'status':'validate',})
                            transac_amount=transac[0]['transac_amount']
                            
                            client_account=http.request.env['money_management.account'].sudo().search([('id', '=', transac[0]['trasac_account_destination']['id'])])
                            solde_client_after=client_account[0]["solde"] + transac_amount
                            client_account.write({'solde': solde_client_after})
                            
                            wallet_account=http.request.env['money_management.account'].sudo().search([('id', '=', transac[0]['trasac_account_source']['id'])])
                            solde_wallet_after=wallet_account[0]["solde"] - transac_amount
                            wallet_account.write({'solde': solde_wallet_after})
                            
                            payload = {
                                'number': client_account[0]['telephone'],
                                'content': 'Votre Transaction vers votre compte Crone a réussi !\n Merci d\'avoir utiliseé Crone ',
                                'key':'dZaN51165420050074130180748146013011022542127230465869',
                            }
                            requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)

                            response["message"]="callback reçu !"
                            response["responseCode"]=1
                            return response
                            
                        elif data['transaction_type']=="transfert":
                            transac_wallet=http.request.env['money_management.transactionwallet'].sudo().search([('refference', '=', data['transaction_uid']),('numero', '=', data['numero']),('etat', '=', 'en cours')])
                            transac_wallet.write({'message':'','etat':'valide',})
                            transac=http.request.env['money_management.transaction'].sudo().search([('transaction_reff', '=', data['transaction_uid']),('status', '=','in_process')])
                            transac.write({'status':'validate',})
                            
                            payload = {
                                'number': transac_wallet[0]['numero'],
                                'content': 'Votre Transaction vers votre compte Crone a réussi !\n Merci d\'avoir utiliseé Crone ',
                                'key':'dZaN51165420050074130180748146013011022542127230465869',
                            }
                            requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)

                            response["message"]="callback reçu !"
                            response["responseCode"]=1
                            return response
                    else:
                        
                        _logger.debug('Transaction type callback reponse 0: %s ', data['transaction_type'])
                        if data['transaction_type']=="payment":
                            transac_wallet = http.request.env['money_management.transactionwallet'].sudo().search([('refference', '=', data['transaction_uid']),('numero', '=', data['numero']),('etat', '=', 'en cours')])
                            transac_wallet.write({'message':'','etat':'annuler',})
                            transac=http.request.env['money_management.transaction'].sudo().search([('transaction_reff', '=', data['transaction_uid']),('status', '=','in_process')])
                            transac.write({'status':'cancelled',})
                            
                            payload = {
                                'number': transac_wallet[0]['numero'],
                                'content': 'Votre Transaction vers votre compte Crone a été annulé !\n Merci d\'avoir utiliseé Crone ',
                                'key':'dZaN51165420050074130180748146013011022542127230465869',
                            }
                            requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)

                            response["message"]="callback reçu !"
                            response["responseCode"]=1
                            return response
                            
                        elif data['transaction_type']=="transfert":
                            transac_wallet =http.request.env['money_management.transactionwallet'].sudo().search([('refference', '=', data['transaction_uid']),('numero', '=', data['numero']),('etat', '=', 'en cours')])
                            transac_wallet.write({'message':'','etat':'annuler',})
                            transac=http.request.env['money_management.transaction'].sudo().search([('transaction_reff', '=', data['transaction_uid']),('status', '=','in_process')])
                            transac.write({'status':'cancelled',})
                            transac_amount=transac[0]['transac_amount']
                            client_account=http.request.env['money_management.account'].sudo().search([('id', '=', transac[0]['trasac_account_source']['id'])])
                            solde_client_after=client_account[0]["solde"] + transac_amount
                            client_account.write({'solde': solde_client_after})
                            
                            wallet_account=http.request.env['money_management.account'].sudo().search([('id', '=', transac[0]['trasac_account_destination']['id'])])
                            solde_wallet_after=wallet_account[0]["solde"] - transac_amount
                            wallet_account.write({'solde': solde_wallet_after})
                            _logger.debug('solde wallet apres: %s  solde client apres: %s', solde_wallet_after,solde_client_after)

                            montant=int(transac_amount)
                            payload = {
                                'number': client_account[0]['telephone'],
                                'content': "Votre Transaction vers votre wallet a été annulé !\n Et vous venez de  reçevoir le  montant de "+f"{montant:,}".replace(",", " ")+" Fcfa  débité",
                                'key':'dZaN51165420050074130180748146013011022542127230465869',
                            }
                            requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)
                            response["message"]="callback reçu !"
                            response["responseCode"]=1
                            return response
                            
                            
            else:
                response["message"]="Access not allowed !"
                response["responseCode"]=0
        except Exception as e:
            response["message"]=str(e)
            response["responseCode"]=0
        
        return response
        
#/usr/lib/python3/dist-packages/odoo/coskas_addons
