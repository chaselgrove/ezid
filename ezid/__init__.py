"""EZID module"""

import urllib
import xml.dom.minidom
import copy
import requests
from .exceptions import *
from .metadata_classes import *
from .xml_utils import *

base_url = 'https://ezid.cdlib.org'

test_prefix = '10.5072/FK2'

base_xml = """<?xml version="1.0"?>
<resource xmlns="http://datacite.org/schema/kernel-3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://datacite.org/schema/kernel-3 http://schema.datacite.org/meta/kernel-3/metadata.xsd">
  <identifier identifierType="DOI"/>
  <creators/>
  <titles>
    <title/>
  </titles>
  <publisher/>
  <publicationYear/>
  <subjects/>
  <contributors/>
  <dates/>
  <resourceType/>
  <alternateIdentifiers/>
  <relatedIdentifiers/>
  <sizes/>
  <formats/>
  <version/>
  <rightsList/>
  <descriptions/>
  <geoLocations/>
</resource>
"""

# key -> value class
metadata_values = {'creators': MVCreators, 
                   'title': MVTitle, 
                   'publisher': MVPublisher, 
                   'publicationyear': MVPublicationYear, 
                   'subjects': MVSubjects, 
                   'contributors': MVContributors, 
                   'dates': MVDates, 
                   'resourcetype': MVResourceType, 
                   'alternateidentifiers': MVAlternateIdentifiers, 
                   'relatedidentifiers': MVRelatedIdentifiers, 
                   'sizes': MVSizes, 
                   'formats': MVFormats, 
                   'version': MVVersion, 
                   'rights': MVRights, 
                   'descriptions': MVDescriptions, 
                   'geolocations': MVGeoLocations}

class DOI:

    def __init__(self, identifier):
        self.identifier = identifier
        self.load()
        return

    @property
    def is_test(self):
        return self.identifier.startswith(test_prefix)

    def record_exists(self):
        """returns False if the dx.doi.org record redirects to:

            http://datacite.org/invalidDOI
            http://www.datacite.org/testprefix

        returns True otherwise
        """
        url = 'http://dx.doi.org/%s' % self.identifier
        r = requests.get(url, allow_redirects=False)
        if r.status_code != 303:
            return True
        if 'Location' not in r.headers:
            return True
        if r.headers['Location'] == 'http://datacite.org/invalidDOI':
            return False
        if r.headers['Location'] == 'http://www.datacite.org/testprefix':
            return False
        return True

    def load(self):
        url = '%s/id/doi:%s' % (base_url, self.identifier)
        r = requests.get(url)
        if r.content.startswith('error:'):
            if 'no such identifier' in r.content:
                raise NotFoundError(self.identifier)
            raise RequestError(r.content[6:].strip())
        if not r.content.startswith('success:'):
            raise RequestError('no success line in request response')
        datacite = None
        landing_page = None
        for line in r.content.split('\n'):
            if line.startswith('datacite: '):
                datacite = urllib.unquote(line[10:])
            if line.startswith('_target: '):
                landing_page = line[9:]
        if not datacite:
            raise RequestError('no datacite field in request response')
        if not landing_page:
            raise RequestError('no landing page in request response')
        self.metadata = xml_to_metadata(datacite)
        self.landing_page = landing_page
        return

    def copy_metadata(self):
        return copy.deepcopy(self.metadata)

    def update_metadata(self, metadata, auth):
        md2 = validate_metadata(metadata)
        url = '%s/id/doi:%s' % (base_url, self.identifier)
        headers = {'Content-Type': 'text/plain'}
        body = _create_request_body(self.landing_page, 
                                    self.identifier, 
                                    md2)
        r = requests.post(url, auth=auth, headers=headers, data=body)
        if r.content.startswith('error:'):
            raise RequestError(r.content[6:].strip())
        if not r.content.startswith('success:'):
            raise UpdateError('bad content returned from EZID')
        self.metadata = md2
        return

    def update_landing_page(self, landing_page, auth):
        url = '%s/id/doi:%s' % (base_url, self.identifier)
        headers = {'Content-Type': 'text/plain'}
        body = _create_request_body(landing_page, 
                                    self.identifier, 
                                    self.metadata)
        r = requests.post(url, auth=auth, headers=headers, data=body)
        if r.content.startswith('error:'):
            raise RequestError(r.content[6:].strip())
        if not r.content.startswith('success:'):
            raise UpdateError('bad content returned from EZID')
        self.landing_page = landing_page
        return

    @property
    def xml(self):
        return create_datacite_xml(self.identifier, self.metadata)

def validate_metadata(metadata):
    if not isinstance(metadata, dict):
        raise TypeError('metadata must be a dictionary')
    md2 = {}
    for (k, v) in metadata.iteritems():
        if k not in metadata_values:
            raise ValueError('unknown metadata key "%s"' % k)
        md2[k] = metadata_values[k](v).value
    for (key, cls) in metadata_values.iteritems():
        if cls.mandatory and key not in metadata:
            raise ValueError('missing mandatory metadata key "%s"' % key)
    return md2

def mint(landing_page, metadata, doi_prefix, auth):
    md2 = validate_metadata(metadata)
    url = '%s/shoulder/doi:%s' % (base_url, doi_prefix)
    headers = {'Content-Type': 'text/plain'}
    body = _create_request_body(landing_page, None, md2)
    r = requests.post(url, auth=auth, headers=headers, data=body)
    if r.content.startswith('error:'):
        raise RequestError(r.content[6:].strip())
    if not r.content.startswith('success:'):
        raise MintError('bad content returned from EZID')
    for part in r.content[8:].strip().split('|'):
        part = part.strip()
        if part.startswith('doi:'):
            identifier = part[4:]
            break
    else:
        raise MintError('no identifier returned from EZID')
    return identifier

def create_datacite_xml(identifier, metadata):
    """return the datacite XML representation"""
    doc = xml.dom.minidom.parseString(base_xml)
    if identifier is None:
        xml_add_text(doc, 'identifier', '(:tba)')
    else:
        xml_add_text(doc, 'identifier', 'doi:%s' % identifier)
    for (key, cls) in metadata_values.iteritems():
        if key in metadata:
            cls(metadata[key]).update_xml(doc)
    return doc.toxml()

def xml_to_metadata(data):
    doc = xml.dom.minidom.parseString(data)
    metadata = {}
    for (key, cls) in metadata_values.iteritems():
        metadata[key] = cls.extract_from_xml(doc)
    return metadata

def _create_request_body(landing_page, identifier, metadata):
    datacite_xml = create_datacite_xml(identifier, metadata)
    body = '_target: %s\n' % landing_page
    body += 'datacite: %s\n' % urllib.quote(datacite_xml)
    return body

# eof
