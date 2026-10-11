# apps

Domain modules of the modular monolith. Each app owns its models, serializers, views, services, permissions, and tests.

users · customers · captains · vehicles · rides · payments · subscriptions · notifications · support

Apps should talk to each other through service functions, not by reaching into each other's views.
