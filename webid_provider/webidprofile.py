import types

from rdflib import Graph, Namespace, RDF, URIRef, Literal, BNode, RDFS #, OWL, ConjunctiveGraph
from rdflib.namespace import XSD

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext, TemplateDoesNotExist
from django.utils.decorators import classonlymethod

from django_conneg.views import ContentNegotiatedView
#from django_conneg.decorators import renderer as conneg_renderer
from django_conneg.decorators import renderer


from models import WebIDUser


# class PriorityContentNegotiatedView(ContentNegotiatedView):
#     """
#     dynamic addition
#     of renderers
#     """
# 
#     @classonlymethod
#     def as_view(cls, **initkwargs):
#         ranked_mimetypes = getattr(cls, '_mimetypes', None)
#         if ranked_mimetypes:
#             for mime, prio, name in ranked_mimetypes:
#                 renderer = cls.getRenderer(name, mime, name, prio)
#                 #print renderer
#                 cls.addMethod(renderer)
#         view = super(PriorityContentNegotiatedView, cls).as_view(**initkwargs)
#         return view
# 
#     @classonlymethod
#     def addMethod(cls, func):
# #         name = func.__name__
# #         if not name:
# #             if hasattr(func, mimetypes):
# #                 name = 'render_%s' % func.mimetypes[0].value.replace('/', '_')
# #         return setattr(cls, name, types.MethodType(func, cls))
#         return setattr(cls, func.__name__, types.MethodType(func, cls))
# 
#     @classonlymethod
#     def getRenderer(cls, format, mimetypes, name, priority):
#         if not isinstance(mimetypes, tuple):
#             mimetypes = (mimetypes,)
#         mime = mimetypes[0]
#         def renderer(cls, self, request, context, template_name):
#             template_name = self.join_template_name(template_name, name.lower())
#             if template_name is None:
#                 return NotImplemented
#             try:
#                 return render_to_response(template_name,
#                                           context,
#                                           context_instance=RequestContext(request),
#                                           mimetype=mime)
#             except TemplateDoesNotExist:
#                 return NotImplemented
# 
#         renderer = conneg_renderer(format=format,
#                                        mimetypes=mimetypes,
#                                        priority=priority)(renderer)
#         renderer.__name__ = 'render_%s' % mime.replace('/', '_')
#         return renderer
# 



#class WebIDProfileView(PriorityContentNegotiatedView):
class WebIDProfileView(ContentNegotiatedView):
    """
    View that negotiates the output format
    Supports: html, rdfa, rdf+xml, xhtml, turtle
    ... why not vcard???
    """
    _default_format = 'html'
    #fallback format???
    #_force_fallback_format = 'html'
#     _mimetypes = (('text/html', 10, 'html'),
#                   ('application/xhtml+xml', 5, 'rdfa'),
#                   ('application/rdf+xml', 1, 'rdfxml'),
#                   ('text/turtle', 2, 'turtle'))

    # TODO: rdfa

    @renderer(format='html', mimetypes=('text/html',), name='HTML', priority=10)
    def render_text_html(self, request, context, template_name):
        template_name = self.join_template_name(template_name, 'html')
        if template_name is None:
            return NotImplemented
        try:
            return render_to_response(template_name,
                                      context,
                                      context_instance=RequestContext(request),
                                      mimetype='text/html')
        except TemplateDoesNotExist:
            return NotImplemented

    @renderer(format='turtle', mimetypes=('text/turtle',), name='Turtle', priority=2)
    def render_text_turtle(self, request, context, template_name):
#         template_name = self.join_template_name(template_name, 'turtle')
#         if template_name is None:
#             return NotImplemented
#         try:
#             return render_to_response(template_name,
#                                       context,
#                                       context_instance=RequestContext(request),
#                                       mimetype='text/turtle')
#         except TemplateDoesNotExist:
#             return NotImplemented
        g = context.get('rdflibgraph')
        if not isinstance(g, Graph):
            return NotImplemented
        else :
            out = g.serialize(format='turtle')
            return HttpResponse(out, content_type="text/turtle")


    @renderer(format='rdfxml', mimetypes=('application/rdf+xml',), name='RDFXML', priority=1)
    def render_application_rdfxml(self, request, context, template_name):
#         template_name = self.join_template_name(template_name, 'rdfxml')
#         if template_name is None:
#             return NotImplemented
#         try:
#             return render_to_response(template_name,
#                                       context,
#                                       context_instance=RequestContext(request),
#                                       mimetype='application/rdf+xml')
#         except TemplateDoesNotExist:
#             return NotImplemented
        g = context.get('rdflibgraph')
        if not isinstance(g, Graph):
            return NotImplemented
        else :
            out = g.serialize(format='application/rdf+xml')
            return HttpResponse(out, content_type="application/rdf+xml")

    def get(self, request, username=None):
        uu = get_object_or_404(WebIDUser,
            username=username)
        
        # construct a rdflib graph
        g = Graph()
        
        FOAF = Namespace('http://xmlns.com/foaf/0.1/')
        CERT = Namespace('http://www.w3.org/ns/auth/cert#')
        
        g = Graph()

        g.bind('foaf', FOAF)
        g.bind('cert', CERT)

        username = uu.username
        resource_uri = '#me'
        rdfres = URIRef(resource_uri)
        type = FOAF.Person
        g.add( (rdfres, RDF.type, type) )
        g.add( (rdfres, FOAF.name, Literal(username)) )
        
        for pk in uu.keys:
            mod = pk.mod
            exp = pk.exp
            
            cert = BNode()
            g.add( (cert, RDF.type, CERT.RSAPublicKey) )
            g.add( (cert, RDFS.label, Literal("key made on [...] on my laptop")) )
            g.add( (cert, CERT.modulus, Literal(mod, datatype=XSD.hexBinary)) )
            g.add( (cert, CERT.exponent, Literal(exp)) )
            
            g.add( (rdfres, CERT.key, cert))
        
        context = {
                "webiduser": uu,
                "rdflibgraph": g,
                "MEDIA_URL": settings.MEDIA_URL,
                "STATIC_URL": settings.STATIC_URL,
        }
        # Call render, passing a template name (w/o file extension)
        return self.render(request, context,
                'webid_provider/webidprofile/webid')

    # fix head method
    # (fixed in bennomadic fork of django_conneg, which is now
    # in requirements, let's see if it's merged upstream.)

    #def head(self, request, *args, **kwargs):
    #    return self.get(request, *args, **kwargs)
