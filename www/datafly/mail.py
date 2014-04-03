from datetime import datetime
from mandrill import Mandrill

from datafly.core import template

from config import Config, db


def send_email(mailto, subject, template_name, subject_override=False,
               template_context=None, from_email=None, premailer=True):
    """ Shortcut to send emails """
    if not subject_override:        
        subject = """%s / %s""" % (Config.WEBSITE, subject)
    if template_context is None:
        template_context = {}
    template_context['subject'] = subject
    template_context['base_url'] = Config.BASE_URL
    html = template(template_name if 'html' in template_name else
                    'mail/%s.html' % template_name, **template_context)
    if premailer:
        from premailer import transform
        html = transform(html)
    try:
        if Config.__name__ != 'Production':
            raise Exception("Sent real emails only in Production env")
        mc = Mandrill(Config.MANDRILL_API_KEY)
        if from_email is None:
            from_email = Config.EMAIL
        message = {
            'to': [{'email': mailto}],
            'from_email': from_email,
            'from_name': Config.WEBSITE,
            'subject': subject,
            'html': html
        }
        mc.messages.send(message = message)
        return { 'error': False }
    except:
        log_msg = {
            'mailto': mailto,
            'subject': subject,
            'html': html,
            'sent_at': datetime.now()
        }
        db.testmail.insert(log_msg)