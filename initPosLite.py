import logging
from app import db
from app.models import Company, PosPayment, PosCategory, PosConfig, PosPaymentMethod
from datetime import datetime

log = logging.getLogger(__name__)

#Init Company Data
try:
    company = Company()
    company.name = "My Company"
    db.session.add(company)
    db.session.commit()
except Exception as e:
    log.error("Creating Company: %s", e)
    db.session.rollback()

#Init Pos Category
try:
    category = PosCategory()
    category.name = "Others"
    db.session.add(category)
    db.session.commit()
except Exception as e:
    log.error("Creating Pos Cateory: %s", e)
    db.session.rollback()

#Init Payment Method
try:
    payment_method = PosPaymentMethod() 
    payment_method.name = 'Cash'
    db.session.add(payment_method)
    db.session.commit()
except Exception as e:
    log.error("Creating Company: %s", e)
    db.session.rollback()

#Ini Pos Config
try:
    config = PosConfig()
    config.company_id = company.id
    config.name = "Main Pos"
    config.code = "POS01"
    config.is_multiple_payment = False
    config.pos_payment_methods.append(payment_method)
    db.session.add(config)
    db.session.commit()
except Exception as e:
    log.error("Creating Pos Config: %s", e)
    db.session.rollback()


