from flask import current_app

from typing import List, Dict, Tuple

from common.providers import s3Provider, awsKeyProvider

from common.functions import slugify


import json
import datetime

import logging



class itemSet():

    set_slug = None
    set_key = None
    aws_config = None
    description = None
    default_structure = {
        'last_updated':None,
        'members':[],
        'created_by':'',
        'creation_type':'',
        'redirection':None,
        'context':'',
        'metadata' : {
            'title':'',
            'slug':'',
            'description':''
        }
    }


    def __init__(self, set_slug, title=None, set_type='structures'):
        """
        This method initialises the itemSet class

        Args: 
            set_slug (str): a slugified version of the set title
            title(str): the title of the set
            set_type (str): the type of set. Defaults to structures as that's currently the only type of set

        Also initialises the aws_config variable which is retrieved from the app's context
        """
        if set_slug is not None:
            self.set_slug = set_slug
        else:
            self.set_slug = slugify(title)
        self.set_key = awsKeyProvider().set_key(self.set_slug, set_type)
        self.aws_config = current_app.config['AWS_CONFIG']


    def get(self, new_slug=False) -> Tuple[Dict, bool, List]:
        """
        This method returns the itemSet whose slug is provided to the constructor

        Args:
            new_slug (str): a different slug, used when the title (and consequently the slug) is changed

        Returns:
            Dict: a dictionary containing the itemset
            bool: whether the itemset has been successfully retrieved
            List: a list of error codes
        """
        if new_slug:
            self.set_key = new_slug
        itemset, success, errors = s3Provider(self.aws_config).get(self.set_key)
        return itemset, success, errors


    def put(self, itemset):
        itemset['last_updated'] = datetime.datetime.now().isoformat()
        itemset['members'] = [member.strip() for member in itemset['members']]
        itemset, success, errors = s3Provider(self.aws_config).put(self.set_key,itemset)
        return json.loads(itemset), success, errors


    def create(self, title:str, description:str, members:List, context:str, created_by:str='pipeline', creation_type:str='algorithm') -> Tuple[Dict, bool, List]:
        """
        This method creates an itemSet whose slug is provided to the constructor

        Args:
            title (str): the title for the itemset
            description (str): the description for the itemset 
            members (List): the members of the itemset

        Returns:
            Dict: a dictionary containing the itemset
            bool: whether the itemset has been successfully retrieved
            List: a list of error codes
        """
        itemset = self.default_structure
        itemset['metadata']['title'] = title
        itemset['metadata']['description'] = description
        if not self.set_slug:
            self.set_slug = slugify(title)
        itemset['metadata']['slug'] = self.set_slug
        itemset['members'] = members
        itemset['context'] = context
        itemset['created_by'] = created_by
        itemset['creation_type'] = creation_type
        itemset, success, errors = self.put(itemset)
        return itemset, success, errors


    def create_or_update(self, title:str, description:str, members:List, context:str):
        itemset, success, errors = self.get()
        if success:
            itemset, success, errors = self.add_members(members)
        else:
            itemset, success, errors = self.create(title, description, members, context)
        return itemset, success, errors


    def change_metadata(self, title:str, description:str):
        """
        This method changes the metadata for the itemSet whose slug is provided to the constructor

        Note: if the title changes, so will the slug, so we'll need to check the new slug doesn't already exist

        Returns:
            Dict: a dictionary containing the itemset
            bool: whether the itemset has been successfully retrieved
            List: a list of error codes
        """
        pass


    def add_members(self, members:List) -> Tuple[Dict, bool, List]:
        """
        This method adds members for the itemSet whose slug is provided to the constructor

        Args:
            members (List): the members of the itemset to be added

        Returns:
            Dict: a dictionary containing the itemset
            bool: whether the itemset has been successfully retrieved
            List: a list of error codes
        """
        itemset, success, errors = s3Provider(self.aws_config).get(self.set_key)
        if success:
            new_members = list(dict.fromkeys(members))
            new_members = [member.strip() for member in new_members if member not in itemset['members']]
            itemset['members'] = [*itemset['members'], *new_members]
            itemset, success, errors = self.put(itemset)
        return itemset, success, errors


    def remove_members(self, members:List) -> Tuple[Dict, bool, List]:
        """
        This method removes members for the itemSet whose slug is provided to the constructor

        Args:
            members (List): the members of the itemset to be removed

        Returns:
            Dict: a dictionary containing the itemset
            bool: whether the itemset has been successfully retrieved
            List: a list of error codes
        """
        itemset, success, errors = s3Provider(self.aws_config).get(self.set_key)
        for member in members:
            if member.strip() in itemset['members']:
                itemset['members'].remove(member.strip())
        logging.warn(itemset)
#        itemset['members'] = [member for member in itemset['members'] if member not in members]
        itemset, success, errors = self.put(itemset)
        return itemset, success, errors



    def exists(self, new_slug=False) -> bool:
        """
        This method returns whether a specific itemset exists

        Args:
            new_slug (str): a different slug, used when the title (and consequently the slug) is changed

        Returns:
            bool: whether the itemset exists or not
        """
        if new_slug:
            itemset, success, errors = self.get(new_slug=new_slug)
        else:
            itemset, success, errors = self.get()
        if success:
            return True
        else:
            return False


    def clean_members(self, set_members) -> List:
        """
        This method returns a cleaned list of members

        Args:
            new_slug (str): a different slug, used when the title (and consequently the slug) is changed

        Returns:
            bool: whether the itemset exists or not
        """
        try:
            set_members = json.loads(set_members)
            return set_members
        except:
            if '\r' in set_members:
                set_members = set_members.replace('\r',',')
            
            if '\"' in set_members:
                set_members = set_members.replace('\"','')
            if '\'' in set_members:
                set_members = set_members.replace('\'','')
            if '[' in set_members:
                set_members = set_members.replace('[','').replace(']','')
            if ',' in set_members:
                set_members = [member.strip() for member in set_members.split(',')]
            else:
                set_members = [set_members.strip()]
        return set_members


    def hydrate(self):
        pass

