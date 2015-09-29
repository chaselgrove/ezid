import types
import re
from .controlled_values import *
from .xml_utils import xml_text, xml_add_text

class MetadataValue:

    """base class for metadata values

    constructors take the value(s) as an argument and validate the given value

    update_xml(doc) will update an XML structure
    """

class MVStringBase(MetadataValue):

    def __init__(self, value):
        if not isinstance(value, basestring):
            raise ValueError('value must be a basestring')
        self.value = value
        return

    def update_xml(self, doc):
        xml_add_text(doc, self.xml_tag, self.value)
        return

    @classmethod
    def extract_from_xml(cls, doc):
        elements = doc.getElementsByTagName(cls.xml_tag)
        assert len(elements) == 1
        return xml_text(elements[0])

class MVStringListBase(MetadataValue):

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('value must be a tuple or list')
        self.value = []
        for v in value:
            if not isinstance(v, basestring):
                raise ValueError('value elements must be a basestrings')
            self.value.append(v)
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName(self.xml_container_tag)
        assert len(elements) == 1
        container_el = elements[0]
        for v in self.value:
            el = doc.createElement(self.xml_tag)
            el.appendChild(doc.createTextNode(v))
            container_el.appendChild(el)
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName(cls.xml_container_tag)
        assert len(elements) == 1
        for el in elements[0].getElementsByTagName(cls.xml_tag):
            value.append(xml_text(el))
        return value

class MVCreators(MetadataValue):

    """a tuple or list of creators:

        strings (names without affiliations)

        2-tuples of strings (names and affilitions)

    stored as a list of (name, affilition) tuples
    """

    mandatory = True

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('creators must be a list or a tuple')
        self.value = []
        seq_err = 'creators elements must be basestrings or 2-tuples'
        for v in value:
            if isinstance(v, basestring):
                self.value.append((v, None))
            elif isinstance(v, (tuple, list)):
                if len(v) != 2:
                    raise ValueError(seq_err)
                if not isinstance(v[0], basestring):
                    raise ValueError(seq_err)
                if not isinstance(v[1], (types.NoneType, basestring)):
                    raise ValueError(seq_err)
                self.value.append(tuple(v))
            else:
                raise ValueError(seq_err)
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('creators')
        assert len(elements) == 1
        parent_el = elements[0]
        for (name, affiliation) in self.value:
            creator_el = doc.createElement('creator')
            parent_el.appendChild(creator_el)
            name_el = doc.createElement('creatorName')
            creator_el.appendChild(name_el)
            name_el.appendChild(doc.createTextNode(name))
            if affiliation is not None:
                affiliation_el = doc.createElement('affiliation')
                creator_el.appendChild(affiliation_el)
                affiliation_el.appendChild(doc.createTextNode(affiliation))
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('creators')
        assert len(elements) == 1
        creators_el = elements[0]
        for el in creators_el.getElementsByTagName('creator'):
            name = xml_text(el.getElementsByTagName('creatorName')[0])
            affiliation_els = el.getElementsByTagName('affiliation')
            if affiliation_els:
                affiliation = xml_text(affiliation_els[0])
            else:
                affiliation = None
            value.append((name, affiliation))
        return value

class MVTitle(MVStringBase):

    mandatory = True
    xml_tag = 'title'

class MVPublisher(MVStringBase):

    mandatory = True
    xml_tag = 'publisher'

class MVPublicationYear(MVStringBase):

    mandatory = True
    xml_tag = 'publicationYear'

    def __init__(self, value):
        if not isinstance(value, basestring):
            raise ValueError('publicationyear must be a basestring')
        if not re.search('^[0-9]{4}$', value):
            raise ValueError('publicationyear must be a four-digit number')
        self.value = value
        return

class MVSubjects(MetadataValue):

    """a list or tuple of subjects:

        strings (subject)

        2-tuples of strings: (subject, subjectScheme)

        3-tuples of strings: (subject, subjectScheme, schemeURI)

    stored as a list of (subject, subjectScheme, schemeURI)
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('contributors must be a list or a tuple')
        self.value = []
        seq_err = 'subjects elements must be strings or 2- or 3-tuples of strings'
        for v in value:
            if isinstance(v, basestring):
                self.value.append((v, None, None))
            elif isinstance(v, (tuple, list)):
                if len(v) == 2:
                    subject = v[0]
                    scheme = v[1]
                    uri = None
                elif len(v) == 3:
                    subject = v[0]
                    scheme = v[1]
                    uri = v[2]
                else:
                    raise ValueError(seq_err)
                if not isinstance(subject, basestring):
                    raise ValueError(seq_err)
                if not isinstance(scheme, basestring):
                    raise ValueError(seq_err)
                if not isinstance(uri, (types.NoneType, basestring)):
                    raise ValueError(seq_err)
                self.value.append((subject, scheme, uri))
            else:
                raise ValueError(seq_err)
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('subjects')
        assert len(elements) == 1
        subjects_el = elements[0]
        for (subject, scheme, uri) in self.value:
            el = doc.createElement('subjet')
            if scheme:
                el.setAttribute('subjectScheme', scheme)
            if uri:
                el.setAttribute('schemeURI', uri)
            el.appendChild(doc.createTextNode(subject))
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('subjects')
        assert len(elements) == 1
        for el in elements[0].getElementsByTagName('subject'):
            subject = xml_text(el)
            if el.hasAttribute('subjectScheme'):
                scheme = el.getAttribute('subjectScheme')
            if el.hasAttribute('subjectURI'):
                uri = el.getAttribute('subjectURI')
            value.append((subject, scheme, uri))
        return value

class MVContributors(MetadataValue):

    """a list or tuple of 2- or 3- tuples:

        (type, name) or (type, name, affiliation)

    stored as a list of (type, name, affiliation)
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('contributors must be a list or a tuple')
        self.value = []
        seq_err = 'contributors elements must be 2- or 3-tuples of strings'
        for v in value:
            if not isinstance(v, (tuple, list)):
                raise ValueError(seq_err)
            if len(v) == 2:
                type = v[0]
                name = v[1]
                affiliation = None
            elif len(v) == 3:
                type = v[0]
                name = v[1]
                affiliation = v[2]
            else:
                raise ValueError(seq_err)
            if not isinstance(type, basestring):
                raise ValueError(seq_err)
            if not isinstance(name, basestring):
                raise ValueError(seq_err)
            if not isinstance(affiliation, (types.NoneType, basestring)):
                raise ValueError(seq_err)
            self.value.append((type, name, affiliation))
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('contributors')
        assert len(elements) == 1
        contributors_el = elements[0]
        for (type, name, affiliation) in self.value:
            el = doc.createElement('contributor')
            contributors_el.appendChild(el)
            el.setAttribute('contributorType', type)
            el2 = doc.createElement('contributorName')
            el2.appendChild(doc.createTextNode(name))
            el.appendChild(el2)
            if affiliation is not None:
                el2 = doc.createElement('affiliation')
                el2.appendChild(doc.createTextNode(affiliation))
                el.appendChild(el2)
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('contributors')
        assert len(elements) == 1
        contributors_el = elements[0]
        for el in contributors_el.getElementsByTagName('contributor'):
            type = el.getAttribute('contributorType')
            name = xml_text(el.getElementsByTagName('contributorName')[0])
            affiliation_els = el.getElementsByTagName('affiliation')
            if affiliation_els:
                affiliation = xml_text(affiliation_els[0])
            else:
                affiliation = None
            value.append((type, name, affiliation))
        return value

class MVDates(MetadataValue):

    """a list or tuple of 2-tuples:

        (type, date)

    stored as a list of (type, date)
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('dates must be a list or a tuple')
        self.value = []
        seq_err = 'dates elements must be 2-tuples of strings'
        for v in value:
            if not isinstance(v, (tuple, list)):
                raise ValueError(seq_err)
            for part in v:
                if not isinstance(part, basestring):
                    raise ValueError(seq_err)
            if len(v) != 2:
                raise ValueError(seq_err)
            if v[0] not in datetype_values:
                raise ValueError('bad value for datetype')
            self.value.append(tuple(v))
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('dates')
        assert len(elements) == 1
        dates_el = elements[0]
        for (type, date) in self.value:
            el = doc.createElement('date')
            el.setAttribute('dateType', type)
            el.appendChild(doc.createTextNode(date))
            dates_el.appendChild(el)
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('dates')
        assert len(elements) == 1
        for el in elements[0].getElementsByTagName('date'):
            type = el.getAttribute('dateType')
            date = xml_text(el)
            value.append((type, date))
        return value

class MVResourceType(MetadataValue):

    """a string of the form:

        resourceTypeGeneral/ResourceType
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, basestring):
            raise ValueError('resourcetype must be a basestring')
        parts = value.split('/', 1)
        if len(parts) != 2:
            raise ValueError('resourcetype must have the form resourceTypeGeneral/resourceType')
        if parts[0] not in resourcetypegeneral_values:
            raise ValueError('bad value for resourceTypeGeneral')
        self.value = value
        return

    def update_xml(self, doc):
        parts = self.value.split('/', 1)
        elements = doc.getElementsByTagName('resourceType')
        assert len(elements) == 1
        elements[0].appendChild(doc.createTextNode(parts[1]))
        elements[0].setAttribute('resourceTypeGeneral', parts[0])
        return

    @classmethod
    def extract_from_xml(cls, doc):
        elements = doc.getElementsByTagName('resourceType')
        assert len(elements) == 1
        rt_el = elements[0]
        rt_general = rt_el.getAttribute('resourceTypeGeneral')
        rt = xml_text(rt_el)
        return '%s/%s' % (rt_general, rt)

class MVAlternateIdentifiers(MetadataValue):

    """a list or tuple of 2-tuples:

        (type, identifier)

    stored as a list of (type, identifier)
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('alternateidentifiers must be a list or a tuple')
        self.value = []
        seq_err = 'alternateidentifiers elements must be 2-tuples of strings'
        for v in value:
            if not isinstance(v, (tuple, list)):
                raise ValueError(seq_err)
            for part in v:
                if not isinstance(part, basestring):
                    raise ValueError(seq_err)
            if len(v) != 2:
                raise ValueError(seq_err)
            self.value.append(tuple(v))
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('alternateIdentifiers')
        assert len(elements) == 1
        ai_el = elements[0]
        for (type, identifier) in self.value:
            el = doc.createElement('alternateIdentifier')
            el.setAttribute('alternateIdentifierType', type)
            el.appendChild(doc.createTextNode(identifier))
            ai_el.appendChild(el)
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('alternateIdentifiers')
        assert len(elements) == 1
        for el in elements[0].getElementsByTagName('alternateIdentifier'):
            type = el.getAttribute('alternateIdentifierType')
            identifier = xml_text(el)
            value.append((type, identifier))
        return value

class MVRelatedIdentifiers(MetadataValue):

    """a list or tuple of 3-tuples:

        (identifier, identifiertype, relationtype)

    stored as a list of 3-tuples
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, (list, tuple)):
            raise ValueError('relatedidentifiers must be a list or tuple')
        self.value = []
        for v in value:
            if not isinstance(v, (list, tuple)):
                raise ValueError('relatedidentifiers elements must be 3-tuples')
            if len(v) != 3:
                raise ValueError('relatedidentifiers elements must be 3-tuples')
            for el in v:
                if not isinstance(el, basestring):
                    msg = 'relatedidentifiers elements must be strings'
                    raise ValueError(msg)
            if v[1] not in relatedidentifiertype_values:
                raise ValueError('bad value for relatedidentifiertype')
            if v[2] not in relatedidentifierrelationtype_values:
                raise ValueError('bad value for relatedidentifierrelationtype')
            self.value.append(tuple(v))
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('relatedIdentifiers')
        assert len(elements) == 1
        parent_el = elements[0]
        for (identifier, identifiertype, relationtype) in self.value:
            el = doc.createElement('relatedIdentifier')
            parent_el.appendChild(el)
            el.setAttribute('relatedIdentifierType', identifiertype)
            el.setAttribute('relationType', relationtype)
            el.appendChild(doc.createTextNode(identifier))
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('relatedIdentifiers')
        assert len(elements) == 1
        for el in elements[0].getElementsByTagName('relatedIdentifier'):
            id_type = el.getAttribute('relatedIdentifierType')
            rel_type = el.getAttribute('relationType')
            identifier = xml_text(el)
            value.append((identifier, id_type, rel_type))
        return value

class MVSizes(MVStringListBase):

    mandatory = False
    xml_container_tag = 'sizes'
    xml_tag = 'size'

class MVFormats(MVStringListBase):

    mandatory = False
    xml_container_tag = 'formats'
    xml_tag = 'format'

class MVVersion(MVStringBase):

    mandatory = False
    xml_tag = 'version'

class MVRights(MetadataValue):

    """a list or tuple of:

        strings (rights)

        2-tuples (rights, rightsURI)

    stored as a list of (rights, rightsURI)
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('rights must be a list or a tuple')
        self.value = []
        seq_err = 'rights elements must be strings or 2-tuples of strings'
        for v in value:
            if isinstance(v, basestring):
                self.value.append((v, None))
            elif isinstance(v, (tuple, list)):
                if len(v) != 2:
                    raise ValueError(seq_err)
                if not isinstance(v[0], basestring):
                    raise ValueError(seq_err)
                if not isinstance(v[1], (types.NoneType, basestring)):
                    raise ValueError(seq_err)
                self.value.append(tuple(v))
            else:
                raise ValueError(seq_err)
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('rightsList')
        assert len(elements) == 1
        rights_list_el = elements[0]
        for (rights, uri) in self.value:
            el = doc.createElement('rights')
            if uri:
                el.setAttribute('rightsURI', uri)
            el.appendChild(doc.createTextNode(rights))
            rights_list_el.appendChild(el)
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('rightsList')
        assert len(elements) == 1
        for el in elements[0].getElementsByTagName('rights'):
            rights = xml_text(el)
            if el.hasAttribute('rightsURI'):
                uri = el.getAttribute('rightsURI')
            else:
                uri = None
            value.append((rights, uri))
        return value

class MVDescriptions(MetadataValue):

    """a list or tuple of 2-tuples:

        (descriptiontype, description)

    stored as a list of (descriptiontype, description)
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('descriptions must be a list or a tuple')
        self.value = []
        seq_err = 'descriptions elements must be 2-tuples of strings'
        for v in value:
            if not isinstance(v, (tuple, list)):
                raise ValueError(seq_err)
            for part in v:
                if not isinstance(part, basestring):
                    raise ValueError(seq_err)
            if len(v) != 2:
                raise ValueError(seq_err)
            if v[0] not in descriptiontype_values:
                raise ValueError('bad value for descriptiontype')
            self.value.append(tuple(v))
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('descriptions')
        assert len(elements) == 1
        descriptions_el = elements[0]
        for (type, description) in self.value:
            el = doc.createElement('description')
            el.setAttribute('descriptionType', type)
            el.appendChild(doc.createTextNode(description))
            descriptions_el.appendChild(el)
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('descriptions')
        assert len(elements) == 1
        for el in contributors_el.getElementsByTagName('description'):
            type = el.getAttribute('descriptionType')
            description = xml_text(el)
            value.append((type, description))
        return value

class MVGeoLocations(MetadataValue):

    """a list of strings (used as geoLocationPlace)
    """

    mandatory = False

    def __init__(self, value):
        if not isinstance(value, (tuple, list)):
            raise ValueError('geolocations must be a list or a tuple')
        self.value = []
        for v in value:
            if not isinstance(v, basestring):
                raise ValueError('geolocations values must be strings')
            self.value.append(v)
        return

    def update_xml(self, doc):
        elements = doc.getElementsByTagName('geoLocations')
        assert len(elements) == 1
        geolocations_el = elements[0]
        for v in self.value:
            el = doc.createElement('geoLocation')
            el2 = doc.createElement('geoLocationPlace')
            el2.appendChild(doc.createTextNode(v))
            el.appendChild(el2)
            geolocations_el.appendChild(el)
        return

    @classmethod
    def extract_from_xml(cls, doc):
        value = []
        elements = doc.getElementsByTagName('geoLocations')
        assert len(elements) == 1
        for el in elements[0].getElementsByTagName('geoLocationPlace'):
            value.append(xml_text(el))
        return value

# eof
