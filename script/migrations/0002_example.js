// fix upload url
var cursor = db.pages.find();
while (cursor.hasNext()) {
    var p = cursor.next();
    p.content = p.content.replace('/static/img/upload', '/static/upload/img', 'g');
    p.content = p.content.replace('/static/file/upload', '/static/upload/file', 'g');
    db.pages.update({_id : p._id}, p);
};