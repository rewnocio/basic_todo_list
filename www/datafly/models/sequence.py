from config import db

def setval(document):
    """
    Set value for document
    """
    document['id'] = id = nextval(document.__collection__)
    document.save()
    return id

def nextval(collection_name):
    """
    Advance sequence and return new value
    """
    increment = { '$inc':
        { 'next': long(1) }
    } 
    return db.sequences.find_and_modify({'id': collection_name}, increment,
                                        upsert=True, new=True)['next']