from typing import List, Dict, Optional, Callable, Union


import jwt
import logging


def check_user_privileges(userobj : Dict, config : Dict, privilege : str) -> Dict:
    userobj['privileges'] = []
    if privilege.upper() in config:
        if userobj['email'] in config[privilege.upper()]:
            userobj['privileges'].append(privilege)
    return userobj


def get_user_from_cookie(request : Callable, config : Dict, privilege : str=None ) -> Union[Dict, None]:
    token = request.cookies.get(config['JWT_COOKIE_NAME'])
    if token:
        try:
            userobj = jwt.decode(token, key=config['JWT_SECRET'], algorithms=["HS256"])
        except:
            userobj = None
    else:
        userobj = None
    if userobj:
        if privilege:
            userobj = check_user_privileges(userobj, config, privilege)
    if userobj:
        return userobj
    else:
        return None


