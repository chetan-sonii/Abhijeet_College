from app.models import User, Thread, Post
from app.extensions import db
import uuid

u = User(
    id=str(uuid.uuid4()),
    username="admin",
    email="admin@test.com",
    password_hash="test"
)
db.session.add(u)
db.session.commit()

t = Thread(
    id=str(uuid.uuid4()),
    title="First Thread",
    user_id=u.id
)
db.session.add(t)
db.session.commit()

p = Post(
    id=str(uuid.uuid4()),
    thread_id=t.id,
    user_id=u.id,
    content="Hello Forum"
)
db.session.add(p)
db.session.commit()

t.last_post_id = p.id
t.last_post_at = p.created_at
db.session.commit()
