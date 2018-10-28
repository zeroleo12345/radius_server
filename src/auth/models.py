from playhouse.sqliteq import SqliteQueueDatabase
import peewee as models
# 自己的库
from settings import USER_DB

db = SqliteQueueDatabase(
    USER_DB,
    use_gevent=True,  # Use the standard library "threading" module.
    autostart=False,  # The worker thread now must be started manually.
    queue_max_size=64,  # Max. # of pending writes that can accumulate.
    results_timeout=5.0)  # Max. time to wait for query to be executed.

db.start()


# 账户, 密码
class User(models.Model):
    class Meta:
        database = db
        db_table = 'user'

    username = models.CharField(max_length=255, unique=True, null=True)
    password = models.CharField(max_length=255)
    expired_at = models.DateTimeField()

    def __str__(self):
        return self.username
