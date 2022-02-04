from flask_caching import Cache

# This may seem like a bit of a waste of space, but it allows the cache to be used in Blueprints
cache = Cache()