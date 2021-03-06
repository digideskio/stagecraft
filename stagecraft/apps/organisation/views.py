from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from stagecraft.libs.validation.validation import is_uuid
from stagecraft.libs.views.resource import ResourceView
from .models import Node, NodeType
from stagecraft.libs.views.utils import create_http_error


class NodeTypeView(ResourceView):

    model = NodeType

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    list_filters = {
        'name': 'name__iexact',
    }

    def update_model(self, model, model_json, request, parent):
        model.name = model_json['name']

    @staticmethod
    def serialize(model):
        return model.serialize()


class NodeView(ResourceView):

    model = Node

    schema = {
        "$schema": "http://json-schema.org/schema#",
        "type": "object",
        "properties": {
            "type_id": {
                "type": "string",
                "format": "uuid",
            },
            "parent_id": {
                "type": "string",
                "format": "uuid",
            },
            "name": {"type": "string"},
            "slug": {"type": "string"},
            "abbreviation": {"type": "string"},
        },
        "required": ["type_id", "name"],
        "additionalProperties": False,
    }

    list_filters = {
        'name': 'name__iexact',
        'abbreviation': 'abbreviation__iexact',
    }

    any_of_multiple_values_filter = {
        'type': 'typeOf__name',
    }

    def list(self, request, **kwargs):
        if 'parent' in kwargs:
            include_self = request.GET.get('self', 'false') == 'true'
            return kwargs['parent'].get_ancestors(include_self=include_self)
        else:
            return super(NodeView, self).list(request, **kwargs)

    def update_model(self, model, model_json, request, parent):
        try:
            node_type = NodeType.objects.get(id=model_json['type_id'])
        except NodeType.DoesNotExist:
            return create_http_error(400, 'no NodeType found', request)

        model.name = model_json['name']
        model.slug = model_json.get('slug', None)
        model.abbreviation = model_json.get('abbreviation', None)
        model.typeOf = node_type

    def update_relationships(self, model, model_json, request, parent):
        if 'parent_id' in model_json:
            parent_id = model_json['parent_id']
            if not is_uuid(parent_id):
                return create_http_error(400, 'parent_id has to be a uuid',
                                         request)

            try:
                parent_node = Node.objects.get(id=parent_id)
            except Node.DoesNotExist:
                return create_http_error(400, 'parent not found', request)

            model.parents.add(parent_node)

    @staticmethod
    def serialize(model):
        return model.serialize()


NodeView.sub_resources = {
    'ancestors': NodeView(),
}
