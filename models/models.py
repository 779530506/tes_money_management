# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.http import request

#import os
import datetime
from dateutil.relativedelta import *
#import calendar
#import re
import requests
import logging
import random
import string
import firebase_admin
from firebase_admin import credentials,auth,messaging
import os
import paho.mqtt.client as mqtt

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):

    #_name = 'money_management.my_settings'
    _inherit = 'res.config.settings'

    crone_uv = fields.Float(string='CRONE UV', default=0.0, readonly=True)
    plafond = fields.Float(string='Client Plafond initiale', default=0.0, readonly=False)
    deplafonnement_value = fields.Float(string='Client Déplafonnement', default=0.0, readonly=False)
    
    last_client_account_index = fields.Char(string ='LAST CLIENT ACCOUNT INDEX', default='00000')

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        select_type = self.env['ir.config_parameter'].sudo()
        select_type.set_param('money_management.crone_uv', self.crone_uv)
        select_type.set_param('money_management.last_client_account_index', self.last_client_account_index)
        select_type.set_param('money_management.deplafonnement_value', self.deplafonnement_value)
        select_type.set_param('money_management.plafond', self.plafond)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        select_type = self.env['ir.config_parameter'].sudo()
        sell = select_type.get_param('money_management.crone_uv')
        last_client_acc_index = select_type.get_param('money_management.last_client_account_index')
        deplafonnement = select_type.get_param('money_management.deplafonnement_value')
        plafond = select_type.get_param('money_management.plafond')
        res.update({'crone_uv' : sell,'last_client_account_index':last_client_acc_index,'deplafonnement_value':deplafonnement,'plafond':plafond})
        return res

class Marchand(models.Model):
    #_name = 'money_management.marchand'
    _inherit = 'res.users'
    #_description = 'Marchand'
    #_rec_name = 'nom_marchand'

    nom_marchand = fields.Char('Marchand',required=False,default='')
    telephone = fields.Char('Téléphone', required=False,default='')
    email = fields.Char('Téléphone', required=False,default='')
    address = fields.Char('Adresse', required=False,default='')
    description = fields.Text('Description', required=False,default='')
    nb_point_of_sale = fields.Integer('Nombre de points de vente', required=False,default=0)
    date_creation = fields.Datetime('Date Enregistrement', readonly=True)
    state = fields.Selection([
        ('inactif', 'Inactif'),
        ('actif', 'Actif'),
        ], string='Statut', required=True, default="actif", readonly=False)

    cartegori_type_id = fields.Many2one('money_management.trading_type', 'Catégorie commerce', required=False, readonly=False)
    
    code = fields.Selection([
        ('1-SOHO', 'SOHO'),
        ('2-TPE', 'TPE'),
        ('3-PME', 'PME'),
        ('4-GC', 'GC'),
        ('5-Informel', 'Informel'),
        ], string='Code', required=True, default="1-SOHO", readonly=False)

    localisation= fields.Char('Code Département', required=False, default='')
    
    nb_customer_day = fields.Selection([
        ('< 10', 'Inférieur à 10'),
        ('< 50', 'Inférieur à 50'),
        ('< 100', 'Inférieur à 100'),
        ('> 100 <= 500', 'Entre 101 et 500'),
        ('> 500', 'Supérieur à 500'),
        ], string='Nombre de clients servis par jour', required=False, default="< 100", readonly=False)

    ninea = fields.Binary("NINEA", attachment=True, required=False)
    rccm = fields.Binary("Rgistre de commerce", attachment=True, required=False)
    cni = fields.Binary("CNI", attachment=True, required=False)
    other_documment = fields.Binary("Autre document justifiant votre activité", attachment=True, required=False)
    accounts = fields.One2many("money_management.account",'account_marchand_owner', string='Comptes', help="", required=True)
    boutiques = fields.One2many("money_management.boutique", 'marchand_id', string='Boutiques', help="", readonly=False)
    approvisionnement = fields.One2many("money_management.approvisionnement", 'appro_marchand_id', string='Approvisionnements', help="")
    achats_uv = fields.One2many("money_management.achat_uv", 'marchand_achat_uv', string='Achats UV', help="")
    facturation_mensuel = fields.Float('Montant Facturation mensuelle',required =False, readonly=False, default=0)
    is_facturation = fields.Boolean('Facturation(Pendant l\'achat d\'UV',required =False, readonly=False, default=False)
    facturations = fields.One2many("money_management.facturation_marchand", 'fac_marchand_id', string='Paliers Facturation', help="", readonly=False)
    
    @api.model
    def create(self, values):
        if len(self.env['res.users'].search([['nom_marchand','=',values['nom_marchand']]])) > 0:
            raise ValidationError("Un marchand avec ce nom existe dejà.")

        elif len(self.env['res.users'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Un marchand avec ce numero de téléphone existe dejà.")
        
        last_record = self.env['res.users'].search([], order='id desc', limit=1)
        ac_id = last_record[0]["id"]
        numbers = string.digits
        new_account_number ='MCD'+''.join(random.choice(numbers) for i in range(9))
        #numbers = string.digits
        #new_account_number = values['trading_type'][0]+ values['code'][0] + values['localisation'] + 'M'+''.join(random.choice(numbers) for i in range(4))
        account_dto ={
            "account_marchand_owner":ac_id,
            "account_number" : new_account_number,
            "account_type":"marchand",
        }
        self.env['money_management.account'].create(account_dto)

        values['date_creation'] = datetime.datetime.now()
        return super(Marchand, self).create(values)
    
    # @api.multi
    # def write(self, values):
    #     if 'nom_marchand' in values and len(self.env['money_management.marchand'].search([['nom_marchand','=',values['nom_marchand']]])) > 0:
    #         raise ValidationError("Une boutique avec cette désignation existe dejà.")

    #     elif 'telephone' in values and len(self.env['money_management.marchand'].search([['telephone','=',values['telephone']]])) > 0:
    #         raise ValidationError("Une boutique avec ce numero de téléphone existe dejà.")
        
    #     return super(Marchand, self).write(values)


class boutique(models.Model):
    _name = 'money_management.boutique'
    _description = 'Boutique'
    _rec_name = 'designation'
    _order = 'date_creation desc'
    #_order = 'code asc'

    designation = fields.Char()
    adresse = fields.Char()
    telephone = fields.Char()
    description = fields.Text()
    logo = fields.Binary("Logo", attachment=True)
    date_creation = fields.Datetime('Date Enregistrement', readonly=True)
    code_marchand=fields.Text("Code QR",readonly=True)
    facturation_mensuel = fields.Float('Montant Facturation mensuelle',required =False, readonly=False, default=0)
    is_facturation = fields.Boolean('Facturation(Pendant l\'Approvisionnement d\'UV',required =False, readonly=False, default=False)
    state = fields.Selection([
        ('inactif', 'Inactif'),
        ('actif', 'Actif'),
        ], string='Statut', required=True, default="actif", readonly=True)
    accounts = fields.One2many("money_management.account",'account_boutique_owner', string='Comptes', help="", required=True)
    marchand_id = fields.Many2one('res.users', 'Marchand', required=False, readonly=False)
    approvisionnement = fields.One2many("money_management.approvisionnement", 'appro_boutique_id', string='Approvisionnements', help="")
    
    #categorie_type = fields.One2many("money_management.boutique_trading_type_rel", 'boutique_id', string='Categories', help="")
    #Categorie_type = fields.many2many("money_management.trading_type", 'money_management.boutique_trading_type_rel','boutique_id', 'trading_type_id',  'Categories')

    avoirs = fields.One2many("money_management.avoir", 'boutique_id', string='Avoirs', help="", readonly=True)
    caisses=fields.One2many("money_management.caisse", 'caisse_boutique_id', string='Caisses', help="", readonly=True)
    agents=fields.One2many("money_management.agent", 'agent_boutique_id', string='Agents', help="", readonly=True)
    qr_codes=fields.One2many("money_management.qrcode", 'qr_boutique_id', string='QR_Codes', help="", readonly=True)
    paiements = fields.One2many("money_management.paiement", 'pm_boutique_id', string='Paiements', help="", readonly=True)
    facturations = fields.One2many("money_management.facturation_boutique", 'fac_boutique_id', string='Paliers Facturation', help="", readonly=False)

    @api.model
    def create(self, values):
        if len(self.env['money_management.boutique'].search([['designation','=',values['designation']]])) > 0:
            raise ValidationError("Une boutique avec cette désignation existe dejà.")

        elif len(self.env['money_management.boutique'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Une boutique avec ce numero de téléphone existe dejà.")
        
        values['date_creation'] = datetime.datetime.now()
        letters = string.ascii_letters
        values['code_marchand'] = ''.join(random.choice(letters) for i in range(30))
        last_boutique = super(boutique, self).create(values)
        
        last_record = self.env['money_management.boutique'].search([], order='id desc', limit=1)
        ac_id = last_record[0]["id"]
        numbers = string.digits
        new_account_number ='B'+''.join(random.choice(numbers) for i in range(9))
        account_dto ={
            "account_boutique_owner":ac_id,
            "account_number" : new_account_number,
            "account_type":"boutique",
        }
        self.env['money_management.account'].create(account_dto)

        return last_boutique
    
    @api.multi
    def write(self, values):
        if 'designation' in values and len(self.env['money_management.boutique'].search([['designation','=',values['designation']]])) > 0:
            raise ValidationError("Une boutique avec cette désignation existe dejà.")

        elif 'telephone' in values and len(self.env['money_management.boutique'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Une boutique avec ce numero de téléphone existe dejà.")

        elif 'telephone' in values and len(self.env['money_management.client'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Un client avec ce numero de téléphone existe dejà.")
        
        return super(boutique, self).write(values)

class caisse(models.Model):
    _name = 'money_management.caisse'
    _description = 'Caisse'
    _rec_name = 'designation'
    _order = 'date_creation desc'
    #_order = 'code asc'
    
    numero = fields.Char()
    designation = fields.Char()
    telephone = fields.Char()
    plafond_solde = fields.Char()
    description = fields.Text()
    date_creation = fields.Datetime('Date Enregistrement', readonly=True)
    code_marchand=fields.Text("Code QR",readonly=True)
    facturation_mensuel = fields.Float('Montant Facturation mensuelle',required =False, readonly=False, default=0)
    is_facturation = fields.Boolean('Facturation(Pendant l\'Approvisionnement d\'UV',required =False, readonly=False, default=False)
    state = fields.Selection([
        ('inactif', 'Inactif'),
        ('actif', 'Actif'),
        ], string='Statut', required=True, default="actif", readonly=True)
    caisse_boutique_id = fields.Many2one('money_management.boutique', 'Boutique', required=True, readonly=False)
    
    accounts = fields.One2many("money_management.account",'account_caisse_owner', string='Comptes', help="", required=True)
    approvisionnement = fields.One2many("money_management.approvisionnement", 'appro_boutique_id', string='Approvisionnements', help="")
    
    #categorie_type = fields.One2many("money_management.boutique_trading_type_rel", 'boutique_id', string='Categories', help="")
    Categorie_type = fields.Many2one("money_management.trading_type", 'Categories',required=True,readonly=False)

    avoirs = fields.One2many("money_management.avoir", 'caisse_id', string='Avoirs', help="", readonly=True)
    agents=fields.One2many("money_management.agent", 'agent_caisse_id', string='Agents', help="", readonly=True)
    qr_codes=fields.One2many("money_management.qrcode", 'qr_caisse_id', string='QR_Codes', help="", readonly=True)
    facturations = fields.One2many("money_management.facturation_caisse", 'fac_caisse_id', string='Paliers Facturation', help="", readonly=False)

    @api.model
    def create(self, values):
        if 'designation' in values and len(self.env['money_management.caisse'].search([['designation','=',values['designation']]])) > 0:
            raise ValidationError("Une caisse avec cette désignation existe dejà.")
    
        elif len(self.env['money_management.caisse'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Une caisse avec ce numero de téléphone existe dejà.")

        
        #ac_id=self._origin.id
        values['date_creation'] = datetime.datetime.now()
        letters = string.ascii_letters
        values['code_marchand'] = ''.join(random.choice(letters) for i in range(30))
        last_caisse = super(caisse, self).create(values)
        
        last_record = self.env['money_management.caisse'].search([], order='id desc', limit=1)
        ac_id = last_record[0]["id"]
        numbers = string.digits
        new_account_number ='C'+''.join(random.choice(numbers) for i in range(9))
        account_dto ={
            "account_caisse_owner":ac_id,
            "account_number" : new_account_number,
            "account_type":"caisse",
        }
        self.env['money_management.account'].create(account_dto)

        return last_caisse
    
    @api.multi
    def write(self, values):
        
        if 'telephone' in values and len(self.env['money_management.caisse'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Une caisse avec ce numero de téléphone existe dejà.")
        
        elif 'telephone' in values and len(self.env['money_management.boutique'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Une boutique avec ce numero de téléphone existe dejà.")
        
        elif 'telephone' in values and len(self.env['money_management.client'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Un client avec ce numero de téléphone existe dejà.")
        
        return super(caisse, self).write(values)

class FacturationMarchand(models.Model):
    _name = 'money_management.facturation_marchand'
    _description = 'Facturation Marchand Palier'
    _rec_name = 'facturation_reff'

    facturation_reff = fields.Char(required=False, default='Facturation')
    min_amount = fields.Float('Montant min')
    max_amount = fields.Float('Montant max')

    facturation_type = fields.Selection([
        ('percent', 'Pourcentage'),
        ('fix_value', 'Valeur Fixe'),
        ('mensuel', 'Mensuel'),
        ], string='Type de facturation', required=True, default="percent")
    facturation_value = fields.Float("Valeur")
    fac_marchand_id = fields.Many2one('res.users', 'Marchand', required=True, readonly=False)

    date_creation = fields.Datetime('Date de création', readonly=True)


    @api.model
    def create(self, values):
        if values['min_amount'] >= values['max_amount']:
            raise ValidationError("Palier invalide !")
        values['date_creation'] = datetime.datetime.now()
        return super(FacturationMarchand, self).create(values)

    @api.multi
    def write(self, values):
        if 'min_amount' in values and 'max_amount' not in values :
            commissions = self.env['money_management.facturation_marchand'].search([('id','!=',values['id'])])
            if values['min_amount'] >= commissions[0]['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")
        elif 'max_amount' in values and 'min_amount' not in values:
            commissions = self.env['money_management.facturation_marchand'].search([('id','!=',values['id'])])
            if  commissions[0]['min_amount'] >= values['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")
        elif 'max_amount' in values and 'min_amount' in values:
            if values['min_amount'] >= values['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")

        return super(FacturationMarchand, self).write(values)


class FacturationBoutique(models.Model):
    _name = 'money_management.facturation_boutique'
    _description = 'Facturation Boutique Palier'
    _rec_name = 'facturation_reff'

    facturation_reff = fields.Char(required=False, default='Facturation')
    min_amount = fields.Float('Montant min')
    max_amount = fields.Float('Montant max')

    facturation_type = fields.Selection([
        ('percent', 'Pourcentage'),
        ('fix_value', 'Valeur Fixe'),
        ('mensuel', 'Mensuel'),
        ], string='Type de facturation', required=True, default="percent")
    facturation_value = fields.Float("Valeur")
    fac_boutique_id = fields.Many2one('money_management.boutique', 'Boutique', required=True, readonly=False)
    #fac_caisse_id = fields.Many2one('money_management.boutique', 'Boutique', required=True, readonly=False)

    date_creation = fields.Datetime('Date de création', readonly=True)


    @api.model
    def create(self, values):
        if values['min_amount'] >= values['max_amount']:
            raise ValidationError("Palier invalide !")
        values['date_creation'] = datetime.datetime.now()
        return super(FacturationBoutique, self).create(values)

    @api.multi
    def write(self, values):
        if 'min_amount' in values and 'max_amount' not in values :
            commissions = self.env['money_management.facturation_boutique'].search([('id','!=',values['id'])])
            if values['min_amount'] >= commissions[0]['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")
        elif 'max_amount' in values and 'min_amount' not in values:
            commissions = self.env['money_management.facturation_boutique'].search([('id','!=',values['id'])])
            if  commissions[0]['min_amount'] >= values['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")
        elif 'max_amount' in values and 'min_amount' in values:
            if values['min_amount'] >= values['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")

        return super(FacturationBoutique, self).write(values)
        
        
class FacturationCaisse(models.Model):
    _name = 'money_management.facturation_caisse'
    _description = 'Facturation Caisse Palier'
    _rec_name = 'facturation_reff'

    facturation_reff = fields.Char(required=False, default='Facturation')
    min_amount = fields.Float('Montant min')
    max_amount = fields.Float('Montant max')

    facturation_type = fields.Selection([
        ('percent', 'Pourcentage'),
        ('fix_value', 'Valeur Fixe'),
        ('mensuel', 'Mensuel'),
        ], string='Type de facturation', required=True, default="percent")
    facturation_value = fields.Float("Valeur")
    #fac_boutique_id = fields.Many2one('money_management.boutique', 'Boutique', required=True, readonly=False)
    fac_caisse_id = fields.Many2one('money_management.caisse', 'Caisse', required=True, readonly=False)

    date_creation = fields.Datetime('Date de création', readonly=True)


    @api.model
    def create(self, values):
        if values['min_amount'] >= values['max_amount']:
            raise ValidationError("Palier invalide !")
        values['date_creation'] = datetime.datetime.now()
        return super(FacturationBoutique, self).create(values)

    @api.multi
    def write(self, values):
        if 'min_amount' in values and 'max_amount' not in values :
            commissions = self.env['money_management.facturation_caisse'].search([('id','!=',values['id'])])
            if values['min_amount'] >= commissions[0]['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")
        elif 'max_amount' in values and 'min_amount' not in values:
            commissions = self.env['money_management.facturation_caisse'].search([('id','!=',values['id'])])
            if  commissions[0]['min_amount'] >= values['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")
        elif 'max_amount' in values and 'min_amount' in values:
            if values['min_amount'] >= values['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")

        return super(FacturationCaisse, self).write(values)

class client(models.Model):
    _name = 'money_management.client'
    _description = 'Client'
    _rec_name = 'name'
    #_order = 'code asc'


    name = fields.Char('Nom')
    telephone = fields.Char('Téléphone')
    adresse = fields.Char('Adresse')
    date_creation = fields.Datetime('Date Enregistrement', readonly=True)
    email = fields.Char('Email')
    sex = fields.Selection([
        ('1-Homme', 'Homme'),
        ('2-Femme', 'Femme'),
        ('N/A', 'N/A'),
        ], string='Sex', required=True, default = 'N/A', readonly=False)
    
    age = fields.Selection([
        ('1-Adolescents', '16 à 20 ans'),
        ('2-Jeunes', '20 à 30 ans'),
        ('3-Adultes', '30 à 50 ans'),
        ('4-Senior', '50 ans et plus'),
        ('N/A', 'N/A'),
        ], string='Age', required=True, default = 'N/A', readonly=False)
    
    source_de_revevus = fields.Selection([
        ('1-Salariés dans le privé', 'Salariés dans le privé'),
        ('2-Salariés dans le public', 'Salariés dans le public'),
        ('3-Indépendant dans le commerce et les services', 'Indépendant dans le commerce et les services'),
        ('4-Chercheur d’emplois', 'Chercheur d’emplois'),
        ('5-Etudiant ou élèves', 'Etudiant ou élèves'),
        ('6-NA', 'N/A'),
        ], string='Souerce de revenu', required=True, default = '6-NA',readonly=False)

    region = fields.Char(string='Région', required=False, default = 'N/A' , readonly=False)
    
    ville = fields.Char('Ville', readonly=False, default = '' ,required = False)
    cni_recto = fields.Binary("CNI Recto", attachment=True)
    cni_verso = fields.Binary("CNI Verso", attachment=True)
    
    state_identite = fields.Selection([
        ('verifié', 'Verifié'),
        ('suspendu', 'Suspendu'),
        ('non verifié', 'Non Verifié'),
        ], string='Identite', required=False, default="non verifié", readonly=False)
    
    accounts = fields.One2many("money_management.account", 'account_client_owner',string='Comptes', help="", readonly=True)
    avoirs = fields.One2many("money_management.avoir", 'client_id', string='Monnaies', help="", readonly=True)
    paiements = fields.One2many("money_management.paiement", 'pm_client_id', string='Paiements', help="", readonly=True)
    qr_codes = fields.One2many("money_management.customerqr", 'customer', string='Dynamiques QR', help="", readonly=True)
    validation_code = fields.Char()
    good_father = fields.Char('Parrain', readonly=True, default='', required = False)
    
    token = fields.Char('Token',required = False, default = '', readonly =True)
    pin = fields.Char('PIN', default='')

    state = fields.Selection([
        ('inactif', 'Inactif'),
        ('actif', 'Actif'),
        ], string='Statut', required=True, default="actif", readonly=False)
    pin_code = fields.Char('Code PIN', readonly=True, default='', required = False)
    tok_notification = fields.Char('Code notification', readonly=True, default='', required = False)

    @api.model
    def create(self, values):
        if len(self.env['money_management.client'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Un client avec ce numero de téléphone existe dejà.")
        
        if 'sex' in values and 'age' in values  :
            last_acc_index = self.env['ir.config_parameter'].sudo().get_param('last_client_account_index') or None
            if last_acc_index is not None :
                caracters_array = list(string.digits + string.ascii_uppercase)
                index_five = int(last_acc_index[4])
                index_foure = int(last_acc_index[3])
                index_three = int(last_acc_index[2])
                index_twoo = int(last_acc_index[1])
                index_one = int(last_acc_index[0])

                if index_five + 1 > 35 :
                    index_five = 0
                    if index_foure + 1 > 35 :
                        index_foure = 0
                        if index_three + 1 > 35 :
                            index_three = 0
                            if index_twoo + 1 > 35 :
                                index_twoo = 0
                                if index_one + 1 > 35 :
                                    index_one = 0
                                else :
                                    index_one += 1
                            else :
                                index_twoo += 1
                        else:
                            index_three+=1
                    else :
                        index_foure +=1
                else :
                    index_five += 1
                new_index_str = str(index_one) +str(index_twoo)+ str(index_three)+ str(index_foure)+ str(index_five)
                new_index_values = caracters_array[index_one] +  caracters_array[index_twoo] +  caracters_array[index_three] +  caracters_array[index_foure] +  caracters_array[index_five]
                
                new_account_number = values['telephone']+'CRCL'+ new_index_values
                
                
                values['date_creation'] = datetime.datetime.now()
                last_client = super(client, self).create(values)
                last_record = self.env['money_management.client'].search([], order='id desc', limit=1)
                last_id = last_record[0]["id"]
                account_dto ={
                    "account_client_owner": last_id,
                    "account_number":new_account_number,
                    "account_type":"client",
                }
                self.env['money_management.account'].create(account_dto)
                self.env['ir.config_parameter'].sudo().set_param('last_client_account_index',new_index_str)
                
                # auto payement
                acount= self.env['money_management.account'].search([['account_number','=',new_account_number]])
                crone_account = self.env['money_management.account'].search([['account_marchand_owner','=',2]])
                _logger.debug('Crone crone account: %s ', crone_account)
                par_trans_type =self.env['money_management.transactiontype'].sudo().search([('type_value', '=', 'monthly_payment')])
                
                new_solde = acount["solde"] - acount["mensuel"]
                crone_new_solde = crone_account[0]["solde"] + acount["mensuel"]
                
                transaction_values = {
                    "transac_amount":acount["mensuel"],
                    "trasac_account_source":acount["id"],
                    "trasac_account_destination":crone_account[0]["id"],
                    "trasac_crone_commission":0,
                    "trasac_partenaire_commission":0,
                    "transaction_type_id":par_trans_type[0]["id"],
                }
                date=datetime.datetime.now() + datetime.timedelta(days=30)
                self.env['money_management.account'].search([['account_number','=',new_account_number]]).write({'solde': new_solde,'date_payement':date})
                self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', 2)]).write({'solde': crone_new_solde})
                self.env['money_management.transaction'].sudo().create(transaction_values)
            else : 
                raise ValidationError("Enable to access the last index of the client account number !.")
        else : 

            last_acc_index = self.env['ir.config_parameter'].sudo().get_param('last_client_account_index') or None
            if last_acc_index is not None :
                caracters_array = list(string.digits + string.ascii_uppercase)
                index_five = int(last_acc_index[4])
                index_foure = int(last_acc_index[3])
                index_three = int(last_acc_index[2])
                index_twoo = int(last_acc_index[1])
                index_one = int(last_acc_index[0])

                if index_five + 1 > 35 :
                    index_five = 0
                    if index_foure + 1 > 35 :
                        index_foure = 0
                        if index_three + 1 > 35 :
                            index_three = 0
                            if index_twoo + 1 > 35 :
                                index_twoo = 0
                                if index_one + 1 > 35 :
                                    index_one = 0
                                else :
                                    index_one += 1
                            else :
                                index_twoo += 1
                        else:
                            index_three+=1
                    else :
                        index_foure +=1
                else :
                    index_five += 1
                new_index_str = str(index_one) +str(index_twoo)+ str(index_three)+ str(index_foure)+ str(index_five)
                new_index_values = caracters_array[index_one] +  caracters_array[index_twoo] +  caracters_array[index_three] +  caracters_array[index_foure] +  caracters_array[index_five]
            values['date_creation'] = datetime.datetime.now()
            last_client = super(client, self).create(values)   
        return last_client
    
    @api.multi
    def write(self, values):
        if 'telephone' in values and len(self.env['money_management.client'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Un client avec ce numero de téléphone existe dejà.")

        if 'sex' in values and 'age' in values :
            last_acc_index = self.env['ir.config_parameter'].sudo().get_param('last_client_account_index') or None
            if last_acc_index is not None :
                caracters_array = list(string.digits + string.ascii_uppercase)
                index_five = int(last_acc_index[4])
                index_foure = int(last_acc_index[3])
                index_three = int(last_acc_index[2])
                index_twoo = int(last_acc_index[1])
                index_one = int(last_acc_index[0])
                if index_five + 1 > 35 :
                    index_five = 0
                    if index_foure + 1 > 35 :
                        index_foure = 0
                        if index_three + 1 > 35 :
                            index_three = 0
                            if index_twoo + 1 > 35 :
                                index_twoo = 0
                                if index_one + 1 > 35 :
                                    index_one = 0
                                else :
                                    index_one += 1
                            else :
                                index_twoo += 1
                        else:
                            index_three+=1
                    else :
                        index_foure +=1
                else :
                    index_five += 1
                new_index_str = str(index_one) +str(index_twoo)+ str(index_three)+ str(index_foure)+ str(index_five)
                new_index_values = caracters_array[index_one] +  caracters_array[index_twoo] +  caracters_array[index_three] +  caracters_array[index_foure] +  caracters_array[index_five]
                
                new_account_number = values['telephone']+'CRCL'+ new_index_values
                account_dto ={
                    "account_number":new_account_number,
                }
                self.env['money_management.account'].sudo().search([('account_client_owner', '=', self.id)]).write(account_dto)
                self.env['ir.config_parameter'].sudo().set_param('last_client_account_index',new_index_str)
            else : 
                raise ValidationError("Enable to access the last index of the client account number !.")

        return super(client, self).write(values)


class avoir(models.Model):
    _name = 'money_management.avoir'
    _description = 'Avoir'
    _order = 'date_avoir desc'
    #_order = 'code asc'

    boutique_id = fields.Many2one('money_management.boutique', 'Boutique', required=True, readonly=True)
    caisse_id = fields.Many2one('money_management.caisse', 'Caisse', required=True, readonly=True)
    client_id = fields.Many2one('money_management.client', 'Client', required=True, readonly=True)
    montant= fields.Float(required=True, readonly=True)
    date_avoir = fields.Datetime('Date ', readonly=True)

    state = fields.Selection([
        ('inactif', 'Inactif'),
        ('actif', 'Actif'),
        ], string='Statut', required=True, default="actif", readonly=False)

    @api.model
    def create(self, values):
        values['date_avoir'] = datetime.datetime.now()
        return super(avoir, self).create(values)

class agent(models.Model):
    _name = 'money_management.agent'
    _description = 'Agent'
    _rec_name = 'name'
    #_inherits = 'res.users'
    

    name = fields.Char("Nom Complet")
    login = fields.Char("Login")
    password = fields.Char("Password")
    adresse = fields.Char(default ="",required = False)
    date_creation = fields.Datetime('Date Création', readonly=True)
    dayly_threshold = fields.Float(default=0)

    paiements = fields.One2many("money_management.paiement", 'pm_agent_id', string='Paiements', help="", readonly=True)
    agent_boutique_id = fields.Many2one('money_management.boutique', string='Boutique')# default=lambda self: self.env['money_management.boutique'].search([])
    agent_caisse_id = fields.Many2one('money_management.caisse', string='Caisse')
    token = fields.Char('Token',required = False, default = '', readonly =True)

    @api.model
    def create(self, values):
        if len(self.env['money_management.agent'].search([['login','=',values['login']]])) > 0:
            raise ValidationError("Un agent avec ce login existe dejà.")

        values['date_creation'] = datetime.datetime.now()
        return super(agent, self).create(values)
    
    @api.multi
    def write(self, values):
        if 'login' in values and len(self.env['money_management.agent'].search([['login','=',values['login']]])) > 0:
            raise ValidationError("Un agent avec ce login existe dejà.")

        return super(agent, self).write(values)

class qrcode(models.Model):
    _name = 'money_management.qrcode'
    _description = 'AgentQR'
    _order = 'date_generation desc'

    amount = fields.Float()
    agent_id = fields.Many2one('money_management.agent', 'Agent', required=True, readonly=True)
    qr_boutique_id = fields.Many2one('money_management.boutique', 'Boutique', required=False, readonly=True)
    qr_caisse_id = fields.Many2one('money_management.caisse', 'Caisse', required=True, readonly=True)
    date_generation = fields.Datetime('Date de génération', readonly=True)
    date_scann = fields.Datetime('Date Scann ',  required=False)
    state = fields.Char(string='Statut', default="not_scann")

    @api.model
    def create(self, values):
        values['date_generation'] = datetime.datetime.now()
        return super(qrcode, self).create(values)
    
    @api.multi
    def write(self, values):
        values['date_scann'] = datetime.datetime.now()
        return super(qrcode, self).write(values)

class paiement(models.Model):
    _name = 'money_management.paiement'
    _description = 'Paiement'
    _order = 'date_paiement desc'

    pm_boutique_id = fields.Many2one('money_management.boutique', 'Boutique', required=True, readonly=True)
    pm_client_id = fields.Many2one('money_management.client', 'Client', required=True, readonly=True)
    pm_agent_id = fields.Many2one('money_management.agent', 'Agent', required=True, readonly=True)

    montant= fields.Float(required=True, readonly=True)
    sole_client_befor= fields.Float('Solde Source Avant',required=True, readonly=True)
    sole_client_after= fields.Float('Solde Source Aprés',required=True, readonly=True)
    sole_boutique_befor= fields.Float('Solde destinataire Avant',required=True, readonly=True)
    sole_boutique_after= fields.Float('Solde destinataire Aprés',required=True, readonly=True)

    date_paiement = fields.Datetime('Date Paiement', readonly=True)
    state = fields.Char(string='Statut', default="Validate")

    @api.model
    def create(self, values):
        values['date_paiement'] = datetime.datetime.now()
        return super(paiement, self).create(values)

class Account(models.Model):
    _name = 'money_management.account'
    _description = 'Compte'
    _rec_name = 'id'
    
    account_number = fields.Char('N° Compte',readonly=True, required = False, default='')
    telephone = fields.Char(related='account_client_owner.telephone', required = False)

    solde =fields.Float('Solde',required =False, readonly=False, default=0)
    all_transact_month =fields.Float('Transaction Moi',required =False, readonly=False, default=0)
    solde_nondispo =fields.Float('Solde Non Dispo',required =False, readonly=False, default=0)

    account_type = fields.Selection([
        ('client', 'Client'),
        ('boutique', 'Boutique/Magasin'),
        ('caisse', 'Caisse'),
        ('marchand', 'Marchand'),
        ('oeuvre', 'Oeuvre Caritative'),
        ('distributeur', 'Distributeur'),
        ('wallet', 'Wallet'),
        ], string='Type de compte', required=True, default="client")
    account_client_owner = fields.Many2one('money_management.client', 'Client Propriétaire', required=False, readonly=False)
    account_marchand_owner = fields.Many2one('res.users', 'Marchand Propriétaire', required=False, readonly=False)
    account_boutique_owner = fields.Many2one('money_management.boutique', 'Boutique Propriétaire', required=False, readonly=False)
    account_caisse_owner = fields.Many2one('money_management.caisse', 'Caisse Propriétaire', required=False, readonly=False)
    
    account_wallet_owner = fields.Many2one('money_management.cronewallet', 'Wallet Propriétaire', required=False,readonly=False)

    account_oeuvrecaritative_owner = fields.Many2one('money_management.oeuvrecaritative', 'OeuvreCaritative Propriétaire', required=False, readonly=False)
    account_distributeur_owner = fields.Many2one('money_management.distributeur', 'Distibuteur Propriétaire', required=False, readonly=False)
    
    account_categorie = fields.Many2one('money_management.categorie_facturation', 'Categorie', required=False, readonly=False,default=lambda self: self.env['money_management.categorie_facturation'].search([('nom','=','Classic')]))

    credit_trasanctions = fields.One2many("money_management.transaction", 'trasac_account_destination', string='Crédit Transactions', help="", readonly=True)
    debit_trasanctions = fields.One2many("money_management.transaction", 'trasac_account_source', string='Débit Transactions', help="", readonly=True)

    credit_with_restriction = fields.One2many("money_management.credit_restricted", 'account_ref', string='Montant avec restriction', help="", readonly=False)
    
    #plafond = fields.Datetime(String='Date de payement',required =False, readonly=False, default=)
    mensuel = fields.Float(related='account_categorie.mensualite',required =False, readonly=False)
    solde_plafond = fields.Float(related='account_categorie.solde_plafond',required =False, readonly=False)
    mouvement_plafond = fields.Float(related='account_categorie.mvt_plafond',required =False, readonly=False)
    date_fist_month = fields.Datetime('Date debut Moi', readonly=False, required =False,null=True ,default=lambda self: fields.datetime.now())
    date_payement = fields.Datetime('Date de payement', readonly=True, required =False,null=True,default=lambda self: fields.datetime.now())
    
    deplafonnement = fields.Boolean('Déplafonnement',required =False, readonly=False, default=False)
    date_creation = fields.Datetime('Date de création', readonly=True)

    @api.model
    def create(self, values):
        values['date_creation'] = datetime.datetime.now()
        values['date_payement'] =datetime.datetime.today()
        # datetime.timedelta(days=30)
        return super(Account, self).create(values)
    

class Transaction(models.Model):
    _name = 'money_management.transaction'
    _description = 'Transaction'
    _rec_name = 'transaction_reff'
    _order = 'transac_date desc'
    #_order = 'code asc'

    transaction_reff =fields.Char(required=True,readonly=True)
    transac_amount = fields.Float()
    trasac_account_source = fields.Many2one('money_management.account', 'Account source', required=True, readonly=False)
    telephone_source = fields.Char(related='trasac_account_source.telephone', required = False)
    trasac_account_destination = fields.Many2one('money_management.account', 'Account destination', required=True, readonly=False)
    telephone_destination = fields.Char(related='trasac_account_destination.telephone', required = False)
    trasac_crone_commission = fields.Float('Commission CRONE')
    trasac_partenaire_commission = fields.Float('Commission Partenaire')
    add =  fields.Boolean('Moi Ajoute',required =False, readonly=False, default=False)

    transac_date = fields.Datetime('Date Trasaction', readonly=True)

    transaction_type_id = fields.Many2one('money_management.transactiontype', 'Type Transaction', required=True, readonly=False)
    status = fields.Selection([
        ('validate', 'Validate'),
        ('in_process', 'Pending'),
        ('cancelled', 'Cancelled'),
        ], string='Statut', required=True, default="validate", readonly=True)
    
    tag = fields.Char('TAG',required=False,default='')

    @api.model
    def create(self, values):
        values['transac_date'] = datetime.datetime.now()
        chars=string.ascii_uppercase + string.digits
        values['transaction_reff'] = ''.join(random.choice(chars) for i in range(20))
        return super(Transaction, self).create(values)

    @api.multi
    def check_pending_transaction(self):
        pending_transac = self.env['money_management.transaction'].search([['status','=','in_process']])
        if len(pending_transac) > 0 :
            for transaction in pending_transac :
                if transaction["transaction_type_id"][1] == 'parrainage':
                    account_source = self.env['money_management.account'].search([['account_marchand_owner','=',transaction['trasac_account_source'][0]]])[0]
                    account_destinattion = self.env['money_management.account'].search([['account_client_owner','=',transaction['trasac_account_destination'][0]]])[0]
                    transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                    if account_source["solde"] >= transac_whole_amount :
                        source_new_solde = account_source["solde"] - transac_whole_amount
                        destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"] 
                        self.env['money_management.account'].sudo().search([('account_client_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                        self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_source["id"])]).write({'solde': source_new_solde})
                        self.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})

                elif transaction["transaction_type_id"][1] == 'monthly_payment':
                    account_source = self.env['money_management.account'].search([['account_marchand_owner','=',transaction['trasac_account_source'][0]]])[0]
                    account_destinattion = self.env['money_management.account'].search([['account_marchand_owner','=',transaction['trasac_account_destination'][0]]])[0]
                    transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                    if account_source["solde"] >= transac_whole_amount :
                        source_new_solde = account_source["solde"] - transac_whole_amount
                        destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"] 
                        self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                        self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_source["id"])]).write({'solde': source_new_solde})
                        self.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
    
    @api.multi
    def monthly_payment_task(self):
        acounts= self.env['money_management.account'].search([['date_payement','<=',datetime.datetime.now()]])
        for ac in acounts :
            crone_account = self.env['money_management.account'].search([['account_marchand_owner','=',2]])
            par_trans_type =self.env['money_management.transactiontype'].sudo().search([('type_value', '=', 'monthly_payment')])
            if ac["date_payement"] <= datetime.datetime.now() :
                if ac["solde"]  >= ac["mensuel"] :
                    new_solde = ac["solde"] - ac["mensuel"]
                    crone_new_solde = crone_account[0]["solde"] + ac["mensuel"]
                    
                    transaction_values = {
                        "transac_amount":ac["mensuel"],
                        "trasac_account_source":ac["id"],
                        "trasac_account_destination":crone_account[0]["id"],
                        "trasac_crone_commission":0,
                        "trasac_partenaire_commission":0,
                        "transaction_type_id":par_trans_type[0]["id"],
                    }
                    date=datetime.datetime.now() + datetime.timedelta(days=30)
                    date1 = datetime.datetime.now()
                    self.env['money_management.account'].sudo().search([('id', '=', ac['id'])]).write({'solde': new_solde,'date_payement':date,'date_fist_month':date1,'all_transact_month':0})
                    self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', 2)]).write({'solde': crone_new_solde})
                    self.env['money_management.transaction'].sudo().create(transaction_values)
                    
                else:
                    new_solde = ac["solde"] - ac["mensuel"]
                    crone_new_solde = crone_account[0]["solde"] + ac["mensuel"]
                    
                    transaction_values = {
                        "transac_amount":ac["mensuel"],
                        "trasac_account_source":ac["id"],
                        "trasac_account_destination":crone_account[0]["id"],
                        "trasac_crone_commission":0,
                        "trasac_partenaire_commission":0,
                        "transaction_type_id":par_trans_type[0]["id"],
                        "status":"in_process",
                    }
                    date=datetime.datetime.now() + datetime.timedelta(days=30)
                    self.env['money_management.transaction'].sudo().create(transaction_values)

        
        marchands = self.env['res.users'].search([['id','!=',2],['facturation_mensuel','>',0]])
        for marchand in marchands :
            marchand_account = self.env['money_management.account'].search([['account_marchand_owner','=',marchand['id']]])[0]
            crone_account = self.env['money_management.account'].search([['account_marchand_owner','=',2]])[0]
            par_trans_type =self.env['money_management.transactiontype'].sudo().search([('type_value', '=', 'monthly_payment')])
            if marchand_account["solde"] >= marchand["facturation_mensuel"] :
                marchand_new_solde = marchand_account["solde"] - marchand["facturation_mensuel"]
                crone_new_solde = crone_account["solde"] - marchand["facturation_mensuel"]
                
                transaction_values = {
                    "transac_amount":marchand["facturation_mensuel"],
                    "trasac_account_source":marchand_account["id"],
                    "trasac_account_destination":crone_account["id"],
                    "trasac_crone_commission":0,
                    "trasac_partenaire_commission":0,
                    "transaction_type_id":par_trans_type[0]["id"],    
                }
                self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', marchand['id'])]).write({'solde': marchand_new_solde})
                self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', 2)]).write({'solde': crone_new_solde})
                self.env['money_management.transaction'].sudo().create(transaction_values)
            
            else :
                transaction_values = {
                    "transac_amount":marchand["facturation_mensuel"],
                    "trasac_account_source":marchand_account["id"],
                    "trasac_account_destination":crone_account["id"],
                    "trasac_crone_commission":0,
                    "trasac_partenaire_commission":0,
                    "transaction_type_id":par_trans_type[0]["id"], 
                    "status":"in_process",    
                }
                self.env['money_management.transaction'].sudo().create(transaction_values)
        
        boutiques = self.env['money_management.boutique'].search([['facturation_mensuel','>',0]])
        for boutique in boutiques :
            boutique_account = self.env['money_management.account'].search([['account_boutique_owner','=',marchand['id']]])[0]
            crone_account = self.env['money_management.account'].search([['account_marchand_owner','=',2]])[0]
            par_trans_type =self.env['money_management.transactiontype'].sudo().search([('type_value', '=', 'monthly_payment')])
            if boutique_account["solde"] >= boutique["facturation_mensuel"] :
                boutique_new_solde = boutique_account["solde"] - boutique["facturation_mensuel"]
                crone_new_solde = crone_account["solde"] - boutique["facturation_mensuel"]
                
                transaction_values = {
                    "transac_amount":boutique["facturation_mensuel"],
                    "trasac_account_source":boutique_account["id"],
                    "trasac_account_destination":crone_account["id"],
                    "trasac_crone_commission":0,
                    "trasac_partenaire_commission":0,
                    "transaction_type_id":par_trans_type[0]["id"],    
                }
                self.env['money_management.account'].sudo().search([('account_boutique_owner', '=', boutique['id'])]).write({'solde': boutique_new_solde})
                self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', 2)]).write({'solde': crone_new_solde})
                self.env['money_management.transaction'].sudo().create(transaction_values)
            
            else :
                transaction_values = {
                    "transac_amount":boutique["facturation_mensuel"],
                    "trasac_account_source":boutique_account["id"],
                    "trasac_account_destination":crone_account["id"],
                    "trasac_crone_commission":0,
                    "trasac_partenaire_commission":0,
                    "transaction_type_id":par_trans_type[0]["id"], 
                    "status":"in_process",    
                }
                self.env['money_management.transaction'].sudo().create(transaction_values)


class TransactionType(models.Model):
    _name = 'money_management.transactiontype'
    _description = 'Transaction Type'
    _rec_name = 'type_value'

    type_value = fields.Selection([
        ('c-to-c', 'Transfert Client-to-Client'),
        ('Wallet-to-Crone', 'Transfert Wallet-to-Crone'),
        ('Crone-to-Wallet', 'Transfert Crone-to-Wallet'),
        ('c-to-seller', 'Paiement Client-to-Marchand'),
        ('seller-to-c', 'Avoir'),
        ('cash-in', 'Cash-in'),
        ('cash-out', 'Cash-out'),
        ('donation', 'Donation'),
        ('parrainage', 'Parrainage'),
        ('monthly_payment', 'Paiement Mensuel'),
        ('facturation', 'Facturation Marchand/Boutique'),
        ], string='Type', required=True, default="c-to-c", readonly=False)
    crone_commission = fields.Float('Commission CRONE (en pourcentage/%)',required = True)
    partenaire_commission = fields.Float('Commission Partenaire (en pourcentage/%)',required=True)

    date_creation = fields.Datetime('Date de création', readonly=True)

    commissions = fields.One2many("money_management.commission", 'comm_transac_type_id', string='Commissions', help="")
    transactions = fields.One2many("money_management.transaction", 'transaction_type_id', string='Transactions', help="")

    @api.model
    def create(self, values):
        if len(self.env['money_management.transactiontype'].search([['type_value','=',values['type_value']]])) > 0:
            raise ValidationError("Ce type de transaction existe dejà.")

        values['date_creation'] = datetime.datetime.now()
        return super(TransactionType, self).create(values)

    @api.multi
    def write(self, values):
        if 'type_value' in values and len(self.env['money_management.transactiontype'].search([['type_value','=',values['type_value']]])) > 0:
            raise ValidationError("Ce type de transaction existe dejà.")

        return super(TransactionType, self).write(values)
    

class Commission(models.Model):
    _name = 'money_management.commission'
    _description = 'Commission'
    _rec_name = 'commission_reff'

    commission_reff = fields.Char(required=False, default='Commission')
    min_amount = fields.Float('Montant min')
    max_amount = fields.Float('Montant max')

    commission_type = fields.Selection([
        ('percent', 'Pourcentage'),
        ('fix_value', 'Valeur Fixe'),
        ('mensuel', 'Mensuel'),
        ], string='Type Commission', required=True, default="percent")
    commission_value = fields.Float("Valeur")
    comm_transac_type_id = fields.Many2one('money_management.transactiontype', 'Type Transaction', required=True, readonly=False)

    date_creation = fields.Datetime('Date de création', readonly=True)


    @api.model
    def create(self, values):
        if values['min_amount'] >= values['max_amount']:
            raise ValidationError("Palier invalide !")
        values['date_creation'] = datetime.datetime.now()
        return super(Commission, self).create(values)

    @api.multi
    def write(self, values):
        if 'min_amount' in values and 'max_amount' not in values :
            commissions = self.env['money_management.commission'].search([('id','!=',values['id'])])
            if values['min_amount'] >= commissions[0]['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")
        elif 'max_amount' in values and 'min_amount' not in values:
            commissions = self.env['money_management.commission'].search([('id','!=',values['id'])])
            if  commissions[0]['min_amount'] >= values['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")
        elif 'max_amount' in values and 'min_amount' in values:
            if values['min_amount'] >= values['max_amount']:
                raise ValidationError("Palier invalide ! veuillez revoir les valeurs")

        return super(Commission, self).write(values)

class Approvisionnement(models.Model):
    _name = 'money_management.approvisionnement'
    _description = 'Approvisionnement'
    _rec_name = 'libelle'
    _order = 'date_approvisionnement desc'
    
    libelle = fields.Char('Libellé',required =True)
    amount = fields.Float('Montant',required = True)
    #appro_marchand_id = fields.Many2one('res.users', 'Marchand', required=False, readonly = True)
    appro_marchand_id = fields.Many2one('res.users', 'Marchand', required=False)
    appro_boutique_id = fields.Many2one('money_management.boutique', 'Boutique', required=False)
    appro_caisse_id = fields.Many2one('money_management.caisse', 'Caisse', required=False)

    date_approvisionnement = fields.Datetime('Date d\'approvisionnement', readonly=True)

    @api.model
    def create(self, values):
        if values['amount'] < 100 :
            raise ValidationError("Error : Montant invalide !")
        elif values['appro_marchand_id'] == False:
            boutique_account = self.env['money_management.account'].search([['account_boutique_owner','=',values['appro_boutique_id']]])
            if len(boutique_account)==0:
                raise ValidationError("Error : Cette utilisateur n'a pas de compte CRONE boutique !")
            else :
                if values['amount'] > boutique_account[0]['solde'] :
                    raise ValidationError("ERROR : Votre solde est insuffisant !")
                else:
                    caisse_account = self.env['money_management.account'].search([['account_caisse_owner','=',values['appro_caisse_id']]])
                    if len(caisse_account) == 0:
                        raise ValidationError("ERROR : La caisse dont vous voulez approvisionner ne dispose pas d'un compte CRONE; Veuillez contacter l'administrateur!")
                    else :
                        new_boutique_solde = boutique_account[0]['solde'] - values['amount']
                        new_caisse_solde = caisse_account[0]['solde'] + values['amount']
                        caisse = self.env['money_management.caisse'].search([['id','=',values['appro_caisse_id']]])
                        if caisse[0]["is_facturation"] == True :
                                facturation_value = 0
                                facturation_paliers = self.env['money_management.facturation_caisse'].search([['fac_caisse_id','=',caisse[0]["id"]]])
                                for one_fac_palier in facturation_paliers :
                                    if values['amount'] >= one_fac_palier["min_amount"] and values['uv_amount'] <= one_fac_palier["max_amount"] :
                                        if one_fac_palier["facturation_type"] == 'percent' :
                                            facturation_value = (one_fac_palier["facturation_value"] * values['amount']) / 100
                                        else:
                                            facturation_value =  one_fac_palier["facturation_value"]
                                        break
                                if facturation_value > 0 :
                                    crone_account = self.env['money_management.account'].search([['account_marchand_owner','=','2']])[0]
                                    par_trans_type =self.env['money_management.transactiontype'].sudo().search([('type_value', '=', 'facturation')])
                                    new_caisse_solde = new_caisse_solde - facturation_value
                                    crone_new_solde = crone_account["solde"] + facturation_value
                                    transaction_values = {
                                        "transac_amount":facturation_value,
                                        "trasac_account_source":caisse_account[0]["id"],
                                        "trasac_account_destination":crone_account["id"],
                                        "trasac_crone_commission":0,
                                        "trasac_partenaire_commission":0,
                                        "transaction_type_id":par_trans_type[0]["id"],
                                    }
                                    self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', '2')]).write({'solde': crone_new_solde})
                                    self.env['money_management.transaction'].sudo().create(transaction_values)

#                            pending_transac=self.env['money_management.transaction'].search([['status','=','in_process'],['trasac_account_source','=',caisse_account[0]['id']]])
#                            if len(pending_transac) > 0 :
#                               for transaction in pending_transac :
#                                    account_destinattion = transaction['trasac_account_destination']
#                                    transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
#                                    if new_boutique_solde >= transac_whole_amount :
#                                        source_new_solde = new_boutique_solde - transac_whole_amount
#                                        destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"]
#                                        self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
#                                        self.env['money_management.account'].sudo().search([('account_caisse_owner', '=', caisse_account[0]["id"])]).write({'solde': source_new_solde})
#                                        self.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
#                                        new_caisse_solde = source_new_solde
                        
                        self.env['money_management.account'].sudo().search([('account_boutique_owner','=',values['appro_boutique_id'])]).write({"solde":new_boutique_solde})
                        self.env['money_management.account'].sudo().search([('account_caisse_owner','=',values['appro_caisse_id'])]).write({"solde":new_caisse_solde})
                        values['appro_marchand_id'] = False
            
        else:
            print('Boutique_id : '+str(values['appro_boutique_id']))
            context = self._context
            current_user_uid = context.get('uid')

            marchand = self.env['res.users'].search([('id','!=',current_user_uid)])
            if len(marchand)==0:
                raise ValidationError("Error : Marchand introuvalbe!")
            else :
                marchand_account = self.env['money_management.account'].search([['account_marchand_owner','=',current_user_uid]])
                if len(marchand_account)==0:
                    raise ValidationError("ERROR : Cette utilisateur n'a pas de compte CRONE marchand !")
                else:
                    if values['amount'] > marchand_account[0]['solde'] :
                        raise ValidationError("ERROR : Votre solde est insuffisant !")
                    else:
                        boutique_account = self.env['money_management.account'].search([['account_boutique_owner','=',values['appro_boutique_id']]])
                        if len(boutique_account) == 0:
                            raise ValidationError("ERROR : La boutique dont vous voulez approvisionner ne dispose pas d'un compte CRONE; Veuillez contacter l'administrateur!")
                        else :
                            new_marchand_solde = marchand_account[0]['solde'] - values['amount']
                            new_boutique_solde = boutique_account[0]['solde'] + values['amount']
                            boutique = self.env['money_management.boutique'].search([['id','=',values['appro_boutique_id']]])
                            if boutique[0]["is_facturation"] == True :
                                facturation_value = 0
                                facturation_paliers = self.env['money_management.facturation_boutique'].search([['fac_boutique_id','=',boutique[0]["id"]]])
                                for one_fac_palier in facturation_paliers :
                                    if values['amount'] >= one_fac_palier["min_amount"] and values['uv_amount'] <= one_fac_palier["max_amount"] :
                                        if one_fac_palier["facturation_type"] == 'percent' :
                                            facturation_value = (one_fac_palier["facturation_value"] * values['amount']) / 100
                                        else:
                                            facturation_value =  one_fac_palier["facturation_value"]
                                        break
                                if facturation_value > 0 : 
                                    crone_account = self.env['money_management.account'].search([['account_marchand_owner','=','2']])[0]
                                    par_trans_type =self.env['money_management.transactiontype'].sudo().search([('type_value', '=', 'facturation')])
                                    new_boutique_solde = new_boutique_solde - facturation_value
                                    crone_new_solde = crone_account["solde"] + facturation_value
                                    transaction_values = {
                                        "transac_amount":facturation_value,
                                        "trasac_account_source":boutique_account[0]["id"],
                                        "trasac_account_destination":crone_account["id"],
                                        "trasac_crone_commission":0,
                                        "trasac_partenaire_commission":0,
                                        "transaction_type_id":par_trans_type[0]["id"],    
                                    }
                                    self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', '2')]).write({'solde': crone_new_solde})
                                    self.env['money_management.transaction'].sudo().create(transaction_values)
                            
                            pending_transac = self.env['money_management.transaction'].search([['status','=','in_process'],['trasac_account_source','=',boutique_account[0]['id']]])
                            if len(pending_transac) > 0 :
                                for transaction in pending_transac :
                                    account_destinattion = transaction['trasac_account_destination']
                                    transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                                    if new_boutique_solde >= transac_whole_amount :
                                        source_new_solde = new_boutique_solde - transac_whole_amount
                                        destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"] 
                                        self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                                        self.env['money_management.account'].sudo().search([('account_boutique_owner', '=', boutique_account[0]["id"])]).write({'solde': source_new_solde})
                                        self.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
                                        new_boutique_solde = source_new_solde
                            self.env['money_management.account'].sudo().search([('account_marchand_owner','=',current_user_uid)]).write({"solde":new_marchand_solde})
                            self.env['money_management.account'].sudo().search([('account_boutique_owner','=',values['appro_boutique_id'])]).write({"solde":new_boutique_solde})
                            values['appro_marchand_id'] = current_user_uid
        values['date_approvisionnement'] = datetime.datetime.now()
        return super(Approvisionnement, self).create(values)

class OeuvreCaritative(models.Model):
    _name = 'money_management.oeuvrecaritative'
    _description = 'Oeuvre Caritative'
    _rec_name = 'name'
    _order = 'date_enregistrement desc'
    

    name = fields.Char('Nom',required =True)
    telephone = fields.Char('Téléphone',required =False)
    adresse = fields.Char('Adresse',required =False)
    description = fields.Text('Description',required =False)
    logo = fields.Binary("Logo", attachment=True)
    date_enregistrement = fields.Datetime('Date enregistrement', readonly=True)
    accounts = fields.One2many("money_management.account", 'account_oeuvrecaritative_owner',string='Comptes', help="", readonly=True)

    @api.model
    def create(self, values):
        values['date_enregistrement'] = datetime.datetime.now()
        return super(OeuvreCaritative, self).create(values)

class Customerqr(models.Model):
    _name = 'money_management.customerqr'
    _description = 'CustomerQR'
    _order = 'date_generation desc'

    amount = fields.Float()
    customer = fields.Many2one('money_management.client', 'Client', required=True, readonly=True)

    date_generation = fields.Datetime('Date de génération', readonly=True)
    date_scann = fields.Datetime('Date Scann ',  required=False)
    state = fields.Char(string='État', default="not_scanned")
    qr_type = fields.Char(string='Type transaction',readonly = True ,required = True)
    

    @api.model
    def create(self, values):
        values['date_generation'] = datetime.datetime.now()
        return super(Customerqr, self).create(values)
    
class DistibuteurQr(models.Model):
    _name = 'money_management.distributeu_qr'
    _description = 'DistibuteurQR'
    _order = 'date_generation desc'

    amount = fields.Float()
    distributeur = fields.Many2one('money_management.distributeur', 'Distributeur', required=True, readonly=True)

    date_generation = fields.Datetime('Date de génération', readonly=True)
    date_scann = fields.Datetime('Date Scann ',  required=False)
    state = fields.Char(string='État', default="not_scanned")
    qr_type = fields.Char(string='Type transaction',readonly = True ,required = True)
    

    @api.model
    def create(self, values):
        values['date_generation'] = datetime.datetime.now()
        return super(DistibuteurQr, self).create(values)
    
    @api.multi
    def write(self, values):
        values['date_scann'] = datetime.datetime.now()
        return super(Customerqr, self).write(values)

class PrechargementUv(models.Model):
    _name = 'money_management.prechargement_uv'
    _description = 'Prechargement UV'
    _order = 'date_prechargement desc'

    prechargement_name = fields.Char(string='Libellé', default="", readonly=True)
    uv_amount = fields.Float(string="Montant UV", readonly=True)
    uv_crone_before = fields.Float(string="UV Crone Avant", readonly=True)
    uv_crone_after = fields.Float(string="UV Crone Aprés", readonly=True)



    date_prechargement = fields.Datetime('Date préchargement', readonly=True)

    @api.model
    def create(self, values):
        current_date = datetime.datetime.now()
        if values['uv_amount'] < 100 :
            raise ValidationError("Error : Le montant doit etre superieur à 100 Fcfa !")
        else:
            crone_uv = self.env['ir.config_parameter'].sudo().get_param('crone_uv') or 0
            crone_uv = float(crone_uv)
            new_crone_uv = crone_uv + values['uv_amount']
            self.env['ir.config_parameter'].sudo().set_param('crone_uv',new_crone_uv)
            values['uv_crone_before'] = crone_uv
            values['uv_crone_after'] = new_crone_uv
            movement = {
                "mouvement_amount" : values['uv_amount'],
                "mouvement_type" : "Préchargement Orabank",
                "uv_crone_before" :crone_uv,
                "uv_crone_after" :new_crone_uv,
                "date_mouvement ": current_date,
            }
            self.env['money_management.crone_uv_movement'].sudo().create(movement)

        values['date_prechargement'] = current_date
        return super(PrechargementUv, self).create(values)

class AchatUv(models.Model):
    _name = 'money_management.achat_uv'
    _description = 'Marchand Achat UV'
    _order = 'date_achat_uv desc'

    uv_amount = fields.Float(string="Montant UV acheté")
    marchand_achat_uv = fields.Many2one('res.users', 'Marchand', required=True, readonly=False)

    uv_marchand_before = fields.Float(string="UV Marchand Avant", readonly=True)
    uv_marchand_after = fields.Float(string="UV Marchand Aprés", readonly=True)


    date_achat_uv = fields.Datetime('Date achat UV', readonly=True)

    @api.model
    def create(self, values):
        current_date = datetime.datetime.now()
        if values['uv_amount'] < 100 :
            raise ValidationError("Error : Le montant doit etre superieur à 100 Fcfa !")
        else:
            crone_uv = self.env['ir.config_parameter'].sudo().get_param('crone_uv') or 0
            crone_uv = float(crone_uv)
            print('crone_uv : '+ str(crone_uv))
            if crone_uv < values['uv_amount'] :
                raise ValidationError("Error : CRONE UV  insuffisant !")
            else :
                marchand_id = values['marchand_achat_uv']
                marchand_account = self.env['money_management.account'].search([['account_marchand_owner','=',marchand_id]])
                marchand_solde = marchand_account[0]['solde']
                new_crone_uv = crone_uv - values['uv_amount']
                new_marchand_solde = marchand_solde + values['uv_amount']
                self.env['ir.config_parameter'].sudo().set_param('crone_uv',new_crone_uv)
                values['uv_marchand_before'] = marchand_solde
                values['uv_marchand_after'] = new_marchand_solde
                movement = {
                    "mouvement_amount" : -values['uv_amount'],
                    "mouvement_type" : "Vente d'UV",
                    "uv_crone_before" : crone_uv,
                    "uv_crone_after" : new_crone_uv,
                    "date_mouvement ": current_date,
                }
                self.env['money_management.crone_uv_movement'].sudo().create(movement)
                marchand = self.env['res.users'].search([['id','=',marchand_id]])
                if marchand[0]["is_facturation"] == True :
                    facturation_value = 0
                    facturation_paliers = self.env['money_management.facturation_marchand'].search([['fac_marchand_id','=',marchand_id]])
                    for one_fac_palier in facturation_paliers :
                        if values['uv_amount'] >= one_fac_palier["min_amount"] and values['uv_amount'] <= one_fac_palier["max_amount"] :
                            if one_fac_palier["facturation_type"] == 'percent' :
                                facturation_value = (one_fac_palier["facturation_value"] * values['uv_amount']) / 100
                            else:
                                facturation_value =  one_fac_palier["facturation_value"]
                            break
                    if facturation_value > 0 : 
                        crone_account = self.env['money_management.account'].search([['account_marchand_owner','=','2']])[0]
                        par_trans_type =self.env['money_management.transactiontype'].sudo().search([('type_value', '=', 'facturation')])
                        new_marchand_solde = new_marchand_solde - facturation_value
                        crone_new_solde = crone_account["solde"] + facturation_value
                        
                        transaction_values = {
                            "transac_amount":facturation_value,
                            "trasac_account_source":marchand_account["id"],
                            "trasac_account_destination":crone_account["id"],
                            "trasac_crone_commission":0,
                            "trasac_partenaire_commission":0,
                            "transaction_type_id":par_trans_type[0]["id"],    
                        }
                        self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', '2')]).write({'solde': crone_new_solde})
                        self.env['money_management.transaction'].sudo().create(transaction_values)

                pending_transac = self.env['money_management.transaction'].search([['status','=','in_process'],['trasac_account_source','=',marchand_account[0]['id']]])
                if len(pending_transac) > 0 :
                    for transaction in pending_transac :
                        account_destinattion = transaction['trasac_account_destination']
                        transac_whole_amount = transaction["transac_amount"] + transaction["trasac_crone_commission"] + transaction["trasac_partenaire_commission"]
                        if new_marchand_solde >= transac_whole_amount :
                            source_new_solde = new_marchand_solde - transac_whole_amount
                            destination_new_solde = account_destinattion["solde"] + transaction["transac_amount"] 
                            self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', account_destinattion["id"])]).write({'solde': destination_new_solde})
                            self.env['money_management.account'].sudo().search([('account_marchand_owner', '=', marchand_account["id"])]).write({'solde': source_new_solde})
                            self.env['money_management.transaction'].sudo().search([('id', '=', transaction["id"])]).write({'status': 'validate'})
                            new_marchand_solde = source_new_solde
                
                self.env['money_management.account'].sudo().search([('account_marchand_owner','=',marchand_id)]).write({"solde":new_marchand_solde})

        values['date_achat_uv'] = current_date
        return super(AchatUv, self).create(values)

class CategorieFacturation(models.Model):
    _name = 'money_management.categorie_facturation'
    _description = 'Categorie Facturation'
    _order = 'date desc'
    _rec_name ='nom'

    mensualite = fields.Float(string="Mensualite")
    nom = fields.Char(string='Categorie', default="")
    numero = fields.Integer(string='Numero',required=True)
    type = fields.Selection([
        ('boutique', 'Boutique'),
        ('marchant', 'Marchand'),
        ('client', 'Client'),
        ], string='Type compte', required=True, default="client")
    accounts = fields.One2many("money_management.account", 'account_categorie',string='Comptes', readonly=True)
    solde_plafond = fields.Float(string="Plafond Solde")
    mvt_plafond = fields.Float(string="Plafond Mouvement")

    date = fields.Datetime('Date', readonly=True)


    @api.model
    def create(self, values):
        values['date'] = datetime.datetime.now()
        return super(CategorieFacturation, self).create(values)

class MouvementsUvCrone(models.Model):
    _name = 'money_management.crone_uv_movement'
    _description = 'Mouvement Compteur UV Cro'
    _order = 'date_mouvement desc'

    mouvement_amount = fields.Float(string="Montant du mouvement")
    mouvement_type = fields.Char(string='Type de Mouvement', default="")
    #mouv_prechargement = fields.Many2one('res.users', 'Marchand', required=True, readonly=False)
    uv_crone_before = fields.Float(string="UV Crone Avant", readonly=True)
    uv_crone_after = fields.Float(string="UV Crone Aprés", readonly=True)

    date_mouvement = fields.Datetime('Date du Mouvement', readonly=True)


    @api.model
    def create(self, values):
        values['date_mouvement'] = datetime.datetime.now()
        return super(MouvementsUvCrone, self).create(values)


class Distributeur(models.Model):
    _name = 'money_management.distributeur'
    _description = 'Distributeur'
    _order = 'date_enregistrement desc'
    _rec_name = 'name'

    name = fields.Char("Nom Complet", required = True)
    telephone = fields.Char()
    adresse = fields.Char()
    email = fields.Char()
    validation_code = fields.Char(required=False, default='')
    sex = fields.Selection([
        ('1-Homme', 'Homme'),
        ('2-Femme', 'Femme'),
        ], string='Sex', required=True, default="1-Homme", readonly=False)
    
    age = fields.Selection([
        ('1-Adolescents', '16 à 20 ans'),
        ('2-Jeunes', '20 à 30 ans'),
        ('3-Adultes', '30 à 50 ans'),
        ('4-Senior', '50 ans et plus'),
        ], string='Age', required=True, default="2-Jeunes", readonly=False)
    
    source_de_revevus = fields.Selection([
        ('1-Salariés dans le privé', 'Salariés dans le privé'),
        ('2-Salariés dans le public', 'Salariés dans le public'),
        ('3-Indépendant dans le commerce et les services', 'Indépendant dans le commerce et les services'),
        ('4-Chercheur d’emplois', 'Chercheur d’emplois'),
        ('5-Etudiant ou élèves', 'Etudiant ou élèves'),
        ('6-NA', 'N/A'),
        ], string='Souerce de revenu', required=True, default="6-NA", readonly=False)

    region = fields.Selection([
        ('DK', 'DAKAR'),
        ('DL', 'Diourbel'),
        ('FK', 'Fatick'),
        ('KA', 'Kaffrine'),
        ('KL', 'Kaolack'),
        ('KE', 'Kédougou'),
        ('KD', 'Kolda'),
        ('LG', 'Louga'),
        ('MT', 'Matam'),
        ('SL', 'Saint-Louis'),
        ('SE', 'Sédhiou'),
        ('TC', 'Tambacounda'),
        ('TH', 'Thiès'),
        ('ZG', 'Ziguinchor'),
        ], string='Région', required=True, default="DK", readonly=False)
    ville = fields.Char('Ville', readonly=False, default='', required = False)
    date_enregistrement = fields.Datetime('Date d\'enregistrement', readonly=True)
    
    token = fields.Char('Token',required = False, default = '', readonly =True)

    state = fields.Selection([
        ('inactif', 'Inactif'),
        ('actif', 'Actif'),
        ], string='Statut', required=True, default="actif", readonly=False)
    accounts = fields.One2many("money_management.account", 'account_distributeur_owner',string='Comptes', help="", readonly=True)
    qr_codes = fields.One2many("money_management.distributeu_qr", 'distributeur', string='Transactions QRCodes', help="", readonly=True)
    achats_uv = fields.One2many("money_management.distributeur_achat_uv", 'distributeur_achat_uv', string='Achats UV', help="")
    
    @api.model
    def create(self, values):
        if len(self.env['money_management.distributeur'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Un client avec ce numero de téléphone existe dejà.")
        values['date_enregistrement'] = datetime.datetime.now()
        return super(Distributeur, self).create(values)
    
    @api.multi
    def write(self, values):
        if 'telephone' in values and len(self.env['money_management.distributeur'].search([['telephone','=',values['telephone']]])) > 0:
            raise ValidationError("Un distributeur avec ce numero de téléphone existe dejà.")
        last_acc_index = self.env['ir.config_parameter'].sudo().get_param('last_client_account_index') or None
        if last_acc_index is not None :
            caracters_array = list(string.digits + string.ascii_uppercase)
            index_five = int(last_acc_index[4])
            index_foure = int(last_acc_index[3])
            index_three = int(last_acc_index[2])
            index_twoo = int(last_acc_index[1])
            index_one = int(last_acc_index[0])

            if index_five + 1 > 35 :
                index_five = 0
                if index_foure + 1 > 35 :
                    index_foure = 0
                    if index_three + 1 > 35 :
                        index_three = 0
                        if index_twoo + 1 > 35 :
                            index_twoo = 0
                            if index_one + 1 > 35 :
                                index_one = 0
                            else :
                                index_one += 1
                        else :
                            index_twoo += 1
                    else:
                        index_three+=1
                else :
                    index_foure +=1
            else :
                index_five += 1
            new_index_str = str(index_one) +str(index_twoo)+ str(index_three)+ str(index_foure)+ str(index_five)
            new_account_number = values['sex'][0]+ values['age'][0] + values['source_de_revevus'][0] + values['region']+'D'+ new_index_str
            account_dto ={
                "account_distributeur_owner":self._origin.id,
                "account_number" : new_account_number,
                "account_type":"distributeur",
            }
            self.env['money_management.account'].create(account_dto)
            self.env['ir.config_parameter'].sudo().set_param('last_client_account_index',new_index_str)
        else : 
            raise ValidationError("Enable to access the last index of the client account number !.")

        return super(Distributeur, self).write(values)


class DistgributedurAchatUv(models.Model):
    _name = 'money_management.distributeur_achat_uv'
    _description = 'Distributeur Achat UV'
    _order = 'date_achat_uv desc'

    uv_amount = fields.Float(string="Montant UV acheté")
    distributeur_achat_uv = fields.Many2one('money_management.distributeur', 'Distributeur', required=True, readonly=False)

    uv_distributeur_before = fields.Float(string="UV Distributeur Avant", readonly=True)
    uv_distributeur_after = fields.Float(string="UV Distributeur Aprés", readonly=True)


    date_achat_uv = fields.Datetime('Date achat UV', readonly=True)

    @api.model
    def create(self, values):
        current_date = datetime.datetime.now()
        if values['uv_amount'] < 100 :
            raise ValidationError("Error : Le montant doit etre superieur à 100 Fcfa !")
        else:
            crone_uv = self.env['ir.config_parameter'].sudo().get_param('crone_uv') or 0
            crone_uv = float(crone_uv)
            print('crone_uv : '+ str(crone_uv))
            if crone_uv < values['uv_amount'] :
                raise ValidationError("Error : CRONE UV  insuffisant !")
            else :
                distributeur_id = values['distributeur_achat_uv']
                distributeur_account = self.env['money_management.account'].search([['account_distributeur_owner','=',distributeur_id]])
                distributeur_solde = distributeur_account[0]['solde']
                new_crone_uv = crone_uv - values['uv_amount']
                new_distributeur_solde = distributeur_solde + values['uv_amount']
                self.env['money_management.account'].sudo().search([('account_distributeur_owner','=',distributeur_id)]).write({"solde":new_distributeur_solde})
                self.env['ir.config_parameter'].sudo().set_param('crone_uv',new_crone_uv)
                values['uv_distributeur_before'] = distributeur_solde
                values['uv_distributeur_after'] = new_distributeur_solde
                movement = {
                    "mouvement_amount" : -values['uv_amount'],
                    "mouvement_type" : "Vente d'UV distributeur",
                    "uv_crone_before" : crone_uv,
                    "uv_crone_after" : new_crone_uv,
                    "date_mouvement ": current_date,
                }
                self.env['money_management.crone_uv_movement'].sudo().create(movement)

        values['date_achat_uv'] = current_date
        return super(DistgributedurAchatUv, self).create(values)


class ConsomationRestriction(models.Model):
    _name = 'money_management.credit_restricted'
    _description = 'Transfert Conditionné'
    _order = 'date_creation desc'


    amount = fields.Float(string="Montant")
    cartegorie_id = fields.Many2one('money_management.trading_type', 'Catégorie commerce', required=False, readonly=False, default=None)

    consumption_date = fields.Datetime('Date de consomation', required=False, readonly= True)
    used_amount = fields.Float(string="Montant consommé", default=0, readonly=True, required=False)
    
    state = fields.Selection([
        ('inactive', 'Inactive'),
        ('active', 'Active'),
        ], string='Statut', required=False, default="active", readonly=True)
    
    notification = fields.Selection([
        ('envoye', 'Envoye'),
        ('non envoye', 'Non Envoye'),
        ], string='Statut', required=False, default="non envoye", readonly=True)

    account_ref = fields.Many2one('money_management.account', 'Compte', required=True, readonly=False)
    
    date_creation = fields.Datetime('Date création', readonly=True)
    tag = fields.Char('TAG',required = False, default = '')


    @api.model
    def create(self, values):
        values['date_creation'] = datetime.datetime.now()
        return super(ConsomationRestriction, self).create(values)
    
    
    @api.multi
    def notification_task(self):
        restrictions= self.env['money_management.credit_restricted'].sudo().search([('state','=','inactive'),('notification','=','non envoye'),('consumption_date','<=',datetime.datetime.now())])
        for rest in restrictions:
            if len(rest["cartegorie_id"]) == 0 :                               
                if  rest["consumption_date"] <= datetime.datetime.now() :
                    soldeaft=rest["amount"]+rest["account_ref"]["solde"]
                    self.env['money_management.account'].sudo().search([('account_client_owner', '=', rest["account_ref"]["id"])]).write({'solde': soldeaft})
                    self.env['money_management.credit_restricted'].sudo().search([('id', '=', rest['id'])]).write({"notification":"envoye",'state': 'inactive'})
                    
                    topic="solde/"+rest["account_ref"]["telephone"]
                    soldeMqtt= int(soldeaft-rest["account_ref"]["solde_nondispo"])
                    client = mqtt.Client()
                    client.connect("91.121.253.231")
                    client.publish(topic, soldeMqtt)

                    mont=int(rest["amount"])
                    payload = {
                        'number': rest["account_ref"]["telephone"],
                        'content': 'Vous avez un transfert de '+f"{mont:,}".replace(",", " ")+"F  "+rest["tag"]+'\n Merci d\'utiliser CRONE.',
                        'key':'dZaN51165420050074130180748146013011022542127230465869',
                    }
                    requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)


            else:
                if  rest["consumption_date"] <= datetime.datetime.now() :
                    soldeaft=rest["amount"]+rest["account_ref"]["solde"]
                    self.env['money_management.account'].sudo().search([('account_client_owner', '=', rest["account_ref"]["id"])]).write({'solde': soldeaft})
                    mont=int(rest["amount"])
                    payload = {
                        'number': rest["account_ref"]["telephone"],
                        'content': 'Vous avez un transfert de '+f"{mont:,}".replace(",", " ")+"F  "+rest["tag"]+'\n Merci d\'utiliser CRONE.',
                        'key':'dZaN51165420050074130180748146013011022542127230465869',
                    }
                    requests.post('http://emc2-cloud.com:8025/api/sendpost', data=payload)

                    rest.write({"notification":"envoye",'state':'active'})


class CommerceCategorie(models.Model):
    _name = 'money_management.trading_type'
    _description = 'Catégorie Commerce'
    _rec_name = 'name'


    name = fields.Char("Nom Catégorie")
    logo = fields.Binary("Logo", attachment=True)
    date_creation = fields.Datetime('Date de création', readonly=True)
   
    marchands = fields.One2many("res.users", 'cartegori_type_id', string='Marchands', help="")
    transferts = fields.One2many("money_management.credit_restricted", 'cartegorie_id', string='Transferts Conditionnés', help="")

    

    @api.model
    def create(self, values):
        if len(self.env['money_management.trading_type'].search([['name','=',values['name']]])) > 0:
            raise ValidationError("Cette catégorie existe dejà.")

        values['date_creation'] = datetime.datetime.now()
        return super(CommerceCategorie, self).create(values)
    
    @api.multi
    def write(self, values):
        if 'name' in values :
            if len(self.env['money_management.trading_type'].search([['name','=',values['name']]])) > 0:
                raise ValidationError("Cette catégorie existe dejà.")
        return super(CommerceCategorie, self).create(values)
    
class CroneWallet(models.Model):
    _name = 'money_management.cronewallet'
    _description = 'Wallet de Crone'
    _order = 'date desc'
    _rec_name = 'nom'

    nom = fields.Char(string='Type de Mouvement', default="")
    image= fields.Binary("Image", attachment=True)
    soldewallet = fields.Float('Solde Wallet',  default=0)
    date = fields.Datetime('Date de Creation', readonly=True)


   
    @api.model
    def create(self, values):
        if 'nom' in values and len(self.env['money_management.cronewallet'].search([['nom','=',values['nom']]])) > 0:
            raise ValidationError("Un wallet avec ce nom existe dejà.")
        
        numbers = string.digits
        new_account_number ='W'+''.join(random.choice(numbers) for i in range(9))
        #ac_id=self._origin.id
        #ac_id=self.id
        values['date_creation'] = datetime.datetime.now()
        last_wallet = super(CroneWallet, self).create(values)
        
        last_record = self.env['money_management.cronewallet'].search([], order='id desc', limit=1)
        ac_id = last_record[0]["id"]
        account_dto ={
            "account_wallet_owner":ac_id,
            "account_number" : new_account_number,
            "account_type":"wallet",
        }
        self.env['money_management.account'].create(account_dto)

        return last_wallet
    
    @api.multi
    def write(self, values):
        if 'nom' in values and len(self.env['money_management.cronewallet'].search([['nom','=',values['nom']]])) > 0:
            raise ValidationError("Un wallet avec ce nom existe dejà.")
        
        return super(CroneWallet, self).write(values)
            

class TransactionWallet(models.Model):
    _name = 'money_management.transactionwallet'
    _description = ' Transaction Wallet'
    _order = 'date desc'

   
    numero = fields.Char(string='Numero', default="")
    refference=fields.Char(string='Refference', default="")
    message=fields.Char(string='Message', default="")
    etat=fields.Selection([
        ('en cours', 'En cours'),
        ('annuler', 'Annuler'),
        ('valide', 'Valide'),
        ], string='Etat', required=False, default="en cours", readonly=True)
    type=fields.Selection([
        ('transfert', 'Transfert'),
        ('payment', 'Payment'),
        ], string='Type', required=False, default="payment", readonly=True)
    montant=fields.Char(string='Refference', default="")
    wallet= fields.Many2one('money_management.cronewallet', 'Wallet', required=True, readonly=False)
    date = fields.Datetime('Date de Creation', readonly=True)


    @api.model
    def create(self, values):
        values['date'] = datetime.datetime.now()
        return super(TransactionWallet, self).create(values)
        
#/usr/lib/python3/dist-packages/odoo/coskas_addons
