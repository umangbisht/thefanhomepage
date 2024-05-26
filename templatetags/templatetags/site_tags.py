from django import template
from django.conf import settings
import pathlib
import os.path
from os import path
import json

class AssignNode(template.Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value
        
    def render(self, context):
        context[self.name] = self.value.resolve(context, True)
        return ''

def do_assign(parser, token):
    """
    Assign an expression to a variable in the current context.
    
    Syntax::
        {% assign [name] [value] %}
    Example::
        {% assign list entry.get_related %}
        
    """
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'%s' tag takes two arguments" % bits[0])
    value = parser.compile_filter(bits[2])
    return AssignNode(bits[1], value)

register = template.Library()
register.tag('assign', do_assign)


class SegmentNode(template.Node):
    def __init__(self, name, value,segmentCount):
        self.name = name
        self.value = value
        self.segmentCount = segmentCount
        
    def render(self, context):
        context[self.name] = self.value.resolve(context, True).split("/")[self.segmentCount]
        return ''

def get_segment(parser, token):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'%s' tag takes two arguments" % bits[0])
    value = parser.compile_filter(bits[2])
    return SegmentNode(bits[1], value,0)

register.tag('get_segment', get_segment)

def get_segment1(parser, token):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'%s' tag takes two arguments" % bits[0])
    value = parser.compile_filter(bits[2])
    return SegmentNode(bits[1], value,1)

register.tag('get_segment1', get_segment1)

def get_segment2(parser, token):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'%s' tag takes two arguments" % bits[0])
    value = parser.compile_filter(bits[2])
    return SegmentNode(bits[1], value,2)

register.tag('get_segment2', get_segment2)

def get_segment3(parser, token):
    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'%s' tag takes two arguments" % bits[0])
    value = parser.compile_filter(bits[2])
    return SegmentNode(bits[1], value,3)

register.tag('get_segment3', get_segment3)

@register.filter(name='file_exists')
def file_exists(filepath):
    if default_storage.exists(filepath):
        return filepath
    else:
        return ""
		
@register.filter(name='convert_to_integer')
def convert_to_integer(value):
	if type(value) == str:
	    val = int(value)
	else:
		val = value
	return val
		
	
	
@register.filter(name='replaceQuote')
def replaceQuote(value):
	returnList		=	[]
	for appendValue in value:
		returnList.append(int(appendValue))
	
	return returnList
	
	
@register.filter(name='split')	
def split(value):
	values		=	[]
	values = (value.split(','))
	
	return values
	
@register.filter(name='check_none_value')
def check_none_value(value):
	if value == None or value == "None" or value == "":
		value = ""
		return value
	else:
		return value


class SetVarNode(template.Node):

    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        context[self.var_name] = value

        return u""
        
        
@register.tag(name='set')
def set_var(parser, token):
    """
    {% set some_var = '123' %}
    """
    parts = token.split_contents()
    if len(parts) < 4:
        raise template.TemplateSyntaxError("'set' tag must be of the form: {% set <var_name> = <var_value> %}")

    return SetVarNode(parts[1], parts[3])
	

@register.filter(name='convertInList')
def convertInList(value):
    return value["en"]["name"]

@register.filter(name='getDiscValue')
def getDiscValue(disc_arr,args):
    #arg_list = [arg.strip() for arg in args.split(',')]
    #return arg_list
    #if key in disc_arr:
        #return disc_arr[key]
    return ""

@register.filter
def get_item(dictionary, key):
    namerr = dictionary.get(key)
    if namerr:
        return namerr['name']
    else:
        return ""
	
@register.filter
def get_item_desc(dictionary, key):
    namerr = dictionary.get(key)
    if namerr:
        return namerr['description']
    else:
        return ""
		
@register.filter
def get_item_ques(dictionary, key):
    namerr = dictionary.get(key)
    if namerr:
        return namerr['question']
    else:
        return ""
		
@register.filter
def get_item_ans(dictionary, key):
    namerr = dictionary.get(key)
    if namerr:
        return namerr['answer']
    else:
        return ""

@register.filter
def get_item_currency_usd(dictionary, key):
    value = dictionary.get(key)
    return round(value["USD"],2)
@register.filter
def get_item_currency_aud(dictionary, key):
    value = dictionary.get(key)
    return round(value["AUD"],2)
@register.filter
def get_item_currency_gbp(dictionary, key):
    value = dictionary.get(key)
    return round(value["GBP"],2)
@register.filter
def get_item_currency_eur(dictionary, key):
    value = dictionary.get(key)
    return round(value["EUR"],2)
	
