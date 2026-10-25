# apps

Domain modules of the modular monolith. Each app owns its models, serializers, views and services.

users · customers · captains · vehicles · rides · payments · wallets · subscriptions · promotions · notifications · support · backoffice (API for admin_web)

Cross-cutting code (platform config, audit log, geo helpers, reports, custom Django admin, periodic jobs) is in `../core/`.

Apps should talk to each other through service functions, not by reaching into each other's views.
