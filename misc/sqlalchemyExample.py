# Run from fpa
import fp_common.models as md

# Make trial object without db:
t = md.Trial(1, 'fred', 'a', 1234, 'd')
engine = md.create_engine('mysql://{0}:{1}@localhost/{2}'.format(md.APPUSR, md.APPPWD, 'fp_mk'))
engine
xsess = md.sessionmaker(bind=engine)
xsess
dbc = xsess()
dbc

# Note t has no db:
md.Session.object_session(t)

# Get trial object from db:
t = dbc.query(md.Trial).filter(md.Trial.id == 1).one()
sess = md.Session.object_session(t)    # now we should have db

# get dbname:
engString = str(sess.get_bind())
dbnameTmp = engString.split('/')[-1]
dbname = dbnameTmp[:-1]

# use some raw sql:
e = sess.get_bind()
results = e.execute('select * from trial')
for row in results:
  print row[0:2]
  print row[3]
  print row['site']




