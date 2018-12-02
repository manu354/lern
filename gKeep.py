from pprint import pprint
def addToList(keep, note):
    gnotes = keep.find(func=lambda x: x.type._name_ == 'List' and x.title == note.title)
    list = next(gnotes)
    if not list:
        list = crea
