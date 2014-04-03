# STATIC ASSETS
# TYPE = { result: [files] }
# files - list of files to compile, concat, minify (relative to /www directory)

CSS = {
    'public': [
        'less/bootstrap-public',    
        'datafly/less/blog-public',
        'less/public',        
        'less/shared',
        'less/responsive'
    ],
    'admin': [
        'less/bootstrap-admin',    
        'datafly/less/default-admin',
        'datafly/less/blog-admin',
        'datafly/less/gallery-admin',
        'less/shared',
        'less/admin'
    ]
}
JS = {
    'public': [
        'js/public',        
        'js/shared'
    ],
    'admin': [
        'datafly/coffee/datafly',
        'datafly/coffee/editor',
        'datafly/coffee/blog',
        'datafly/coffee/gallery-admin',
        'js/shared',
        'js/admin'
    ]
}