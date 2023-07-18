import redis


cache = redis.Redis(host="localhost", port=6319, db=0)
